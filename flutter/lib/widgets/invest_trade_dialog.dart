import 'dart:async';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../providers/app_state.dart';
import '../models/asset_action_result.dart';
import '../models/portfolio.dart';
import '../models/asset.dart';
import 'top_toast.dart';

class _SearchCacheEntry {
  final List<dynamic> results;
  final DateTime savedAt;

  const _SearchCacheEntry({required this.results, required this.savedAt});
}

class InvestTradeDialog extends StatefulWidget {
  final String mode; // add | buy | sell
  final PortfolioItem? item;
  final BuildContext? hostContext;

  const InvestTradeDialog({
    super.key,
    required this.mode,
    this.item,
    this.hostContext,
  });

  @override
  State<InvestTradeDialog> createState() => _InvestTradeDialogState();
}

class _InvestTradeDialogState extends State<InvestTradeDialog> {
  final _queryController = TextEditingController();
  final _priceController = TextEditingController();
  final _qtyController = TextEditingController();
  final _amountController = TextEditingController();
  final _adjustPriceController = TextEditingController();
  final _adjustController = TextEditingController();

  bool _saving = false;
  bool _inlineClosed = false;
  bool _searching = false;
  bool _navLoading = false;
  String? _errorText;
  String? _searchErrorText;
  String? _navErrorText;
  List<dynamic> _results = [];
  Map<String, dynamic>? _selected;
  String _tradeMode = 'buy';
  String _fundInputMode = 'qty';
  int? _selectedCashAssetId;
  int _searchSeq = 0;
  int _navFetchSeq = 0;
  final Map<String, _SearchCacheEntry> _searchCache =
      <String, _SearchCacheEntry>{};
  static const Duration _searchCacheTtl = Duration(seconds: 20);
  static const int _maxRecentCashAssets = 5;
  static final List<int> _recentCashAssetIds = <int>[];
  static final List<TextInputFormatter> _qtyInputFormatters =
      <TextInputFormatter>[
        FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d{0,2}$')),
      ];
  static final List<TextInputFormatter> _fundQtyInputFormatters =
      <TextInputFormatter>[
        FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d{0,4}$')),
      ];

  bool get _isAdd => widget.mode == 'add';
  bool get _isBuy => widget.mode == 'buy';
  bool get _isSell => widget.mode == 'sell';
  bool get _isTrade => widget.mode == 'trade';
  bool get _isAdjust => _tradeMode == 'adjust';

  @override
  void initState() {
    super.initState();
    _queryController.addListener(_onInputControllerChanged);
    _priceController.addListener(_onInputControllerChanged);
    _qtyController.addListener(_onInputControllerChanged);
    _amountController.addListener(_onInputControllerChanged);
    _adjustPriceController.addListener(_onInputControllerChanged);
    _adjustController.addListener(_onInputControllerChanged);
    _syncDefaultCashAsset();
    if (!_isAdd && widget.item != null) {
      _prefillPriceFromCurrent();
      if (_isTrade) {
        _tradeMode = 'buy';
        _adjustController.clear();
        _adjustPriceController.clear();
        if (_isCurrentFundTarget()) {
          _fundInputMode = 'amount';
          unawaited(_prefillFundNavForCode(widget.item!.code));
        }
      }
    }
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _syncDefaultCashAsset();
  }

  @override
  void dispose() {
    _queryController.removeListener(_onInputControllerChanged);
    _priceController.removeListener(_onInputControllerChanged);
    _qtyController.removeListener(_onInputControllerChanged);
    _amountController.removeListener(_onInputControllerChanged);
    _adjustPriceController.removeListener(_onInputControllerChanged);
    _adjustController.removeListener(_onInputControllerChanged);
    _queryController.dispose();
    _priceController.dispose();
    _qtyController.dispose();
    _amountController.dispose();
    _adjustPriceController.dispose();
    _adjustController.dispose();
    super.dispose();
  }

  void _onInputControllerChanged() {
    if (!mounted) return;
    setState(() {});
  }

  String _formatDisplayCode(String code) {
    const customMap = {'ft_LU1116320737': 'BLK'};
    if (customMap.containsKey(code)) {
      return customMap[code]!;
    }
    var c = code;
    if (c.toLowerCase().startsWith('gb_')) {
      c = c.substring(3).toUpperCase();
    } else if (c.toLowerCase().startsWith('f_')) {
      c = c.substring(2);
    } else if (c.toLowerCase().startsWith('ft_')) {
      c = c.substring(3);
    } else if (c.toLowerCase().startsWith('sh') ||
        c.toLowerCase().startsWith('sz') ||
        c.toLowerCase().startsWith('bj')) {
      c = c.substring(2);
    }
    if (c.toUpperCase().endsWith('.HK')) {
      c = c.substring(0, c.length - 3);
    }
    return c;
  }

  Widget _marketBadge(String typeName) {
    String label = 'A股';
    Color color = AppTheme.accent;
    switch (typeName) {
      case '美股':
        label = '美股';
        color = AppTheme.danger;
        break;
      case '港股':
        label = '港股';
        color = AppTheme.success;
        break;
      case '基金':
        label = '基金';
        color = const Color(0xFFF59E0B);
        break;
      default:
        label = 'A股';
        color = AppTheme.accent;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.18),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withOpacity(0.6), width: 1),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: FontSize.xs,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }

  void _onQueryChanged(String value) {
    final next = value.trim();
    final selectedName = (_selected?['name']?.toString() ?? '').trim();
    if (_selected != null && next.isNotEmpty && next == selectedName) {
      return;
    }
    setState(() {
      _selected = null;
      _results = [];
      _errorText = null;
      _searchErrorText = null;
      _navErrorText = null;
      _navLoading = false;
      _fundInputMode = 'qty';
      _amountController.clear();
      _searching = false;
      _searchSeq += 1;
      _navFetchSeq += 1;
    });
  }

  Future<void> _onSearchTap() async {
    if (_searching) return;
    final query = _queryController.text.trim();
    if (query.isEmpty) {
      setState(() {
        _selected = null;
        _results = [];
        _searchErrorText = '请输入代码或名称后再搜索';
      });
      return;
    }
    await _search(query);
  }

  Future<void> _search(String query) async {
    final key = query.toLowerCase();
    final now = DateTime.now();
    final cached = _searchCache[key];
    if (cached != null && now.difference(cached.savedAt) < _searchCacheTtl) {
      if (!mounted) return;
      setState(() {
        _results = cached.results;
        _searching = false;
        _searchErrorText = null;
      });
      return;
    }

    final seq = ++_searchSeq;
    setState(() {
      _searching = true;
      _searchErrorText = null;
    });
    final appState = context.read<AppState>();
    List<dynamic> results;
    try {
      results = await appState.searchStocks(query);
    } catch (_) {
      if (!mounted || seq != _searchSeq) return;
      if (_queryController.text.trim() != query) return;
      setState(() {
        _searching = false;
        _searchErrorText = '搜索失败，请稍后重试';
      });
      return;
    }
    if (!mounted) return;
    if (seq != _searchSeq) return;

    // 放弃过期的结果（如用户已清空或改变了搜索词）
    if (_queryController.text.trim() != query) {
      return;
    }

    _searchCache[key] = _SearchCacheEntry(results: results, savedAt: now);
    setState(() {
      _results = results;
      _searching = false;
      _searchErrorText = null;
    });
  }

  void _closeDialog() {
    final navigator = Navigator.maybeOf(context);
    if (navigator != null && navigator.canPop()) {
      navigator.pop();
      return;
    }
    setState(() {
      _inlineClosed = true;
    });
  }

  String _formatInputNumber(double value, {int decimals = 3}) {
    final text = value.toStringAsFixed(decimals);
    return text.replaceFirst(RegExp(r'\.?0+$'), '');
  }

  bool _isFundAsset({String? assetType, String? code}) {
    final normalizedType = (assetType ?? '').trim().toLowerCase();
    if (normalizedType == 'fund') return true;
    final normalizedCode = (code ?? '').trim().toLowerCase();
    return normalizedCode.startsWith('f_') || normalizedCode.startsWith('ft_');
  }

  bool _isCurrentFundTarget() {
    final mode = _currentActionMode();
    if (mode == 'sell' || mode == 'adjust') return false;
    if (_isAdd) {
      return _isFundAsset(
        assetType: _selected?['asset_type']?.toString(),
        code: _selected?['code']?.toString(),
      );
    }
    final item = widget.item;
    if (item == null) return false;
    return _isFundAsset(assetType: item.assetType, code: item.code);
  }

  bool _isFundAmountMode() {
    return _isCurrentFundTarget() && _fundInputMode == 'amount';
  }

  void _setFundInputMode(String mode) {
    if (_fundInputMode == mode) return;
    setState(() {
      _fundInputMode = mode;
      _errorText = null;
      _navErrorText = null;
    });
    if (mode == 'amount' && _isCurrentFundTarget()) {
      final code = _isAdd
          ? (_selected?['code']?.toString() ?? '')
          : (widget.item?.code ?? '');
      if (code.isNotEmpty) {
        unawaited(_prefillFundNavForCode(code));
      }
    }
  }

  double? _deriveFundQtyFromAmountNav() {
    final amount = double.tryParse(_amountController.text.trim());
    final nav = double.tryParse(_priceController.text.trim());
    if (amount == null || nav == null || amount <= 0 || nav <= 0) return null;
    final rawQty = amount / nav;
    final qty = (rawQty * 10000).floor() / 10000;
    if (qty <= 0) return null;
    return qty;
  }

  String _formatQtyDisplay(double value) {
    final text = value.toStringAsFixed(4);
    return text.replaceFirst(RegExp(r'\.?0+$'), '');
  }

  Future<void> _prefillFundNavForCode(String code) async {
    final normalizedCode = code.trim();
    if (normalizedCode.isEmpty) return;
    final seq = ++_navFetchSeq;
    setState(() {
      _navLoading = true;
      _navErrorText = null;
    });
    final appState = context.read<AppState>();
    final nav = await appState.fetchLatestPriceForCode(normalizedCode);
    if (!mounted || seq != _navFetchSeq) return;
    setState(() {
      _navLoading = false;
      if (nav != null && nav > 0) {
        _priceController.text = _formatInputNumber(nav, decimals: 4);
        _navErrorText = null;
      } else {
        _navErrorText = '净值获取失败，可手动输入';
      }
    });
  }

  void _syncDefaultCashAsset() {
    final appState = context.read<AppState>();
    final cashOptions = appState.cashAssets
        .where((asset) => (asset.id ?? 0) > 0)
        .toList();
    if (_currentActionMode() != 'sell') {
      cashOptions.insert(
        0,
        Asset(id: -999, name: '外部资金/初始转入', amount: 0.0, curr: 'CNY'),
      );
    }
    if (cashOptions.isEmpty) {
      _selectedCashAssetId = null;
      return;
    }
    final selected = _selectedCashAssetId;
    final exists =
        selected != null && cashOptions.any((asset) => asset.id == selected);
    if (!exists) {
      _selectedCashAssetId = cashOptions.first.id;
    }
  }

  String _currentActionMode() {
    if (_isTrade) return _tradeMode;
    if (_isBuy) return 'buy';
    if (_isSell) return 'sell';
    return 'buy';
  }

  bool _requiresCashSource(String mode) {
    return _isAdd || mode == 'buy' || mode == 'sell';
  }

  InputDecoration _compactDecoration(String labelText, {String? hintText}) {
    return InputDecoration(
      labelText: labelText,
      hintText: hintText,
      isDense: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
    );
  }

  void _rememberCashAsset(int? assetId) {
    if (assetId == null) return;
    _recentCashAssetIds.remove(assetId);
    _recentCashAssetIds.insert(0, assetId);
    if (_recentCashAssetIds.length > _maxRecentCashAssets) {
      _recentCashAssetIds.removeRange(
        _maxRecentCashAssets,
        _recentCashAssetIds.length,
      );
    }
  }

  List<Asset> _recentCashAssets(List<Asset> options) {
    final byId = <int, Asset>{
      for (final asset in options)
        if (asset.id != null) asset.id!: asset,
    };
    final result = <Asset>[];
    for (final id in _recentCashAssetIds) {
      final asset = byId[id];
      if (asset != null) result.add(asset);
    }
    return result;
  }

  Widget _buildCashAssetTile({
    required Asset asset,
    required bool selected,
    required VoidCallback onTap,
  }) {
    final isExternal = asset.id == -999;
    final amountText = isExternal ? '外部' : _formatInputNumber(asset.amount);

    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          border: Border(
            bottom: BorderSide(
              color: AppTheme.border.withOpacity(
                AppTheme.isLight ? 0.55 : 0.22,
              ),
              width: 1,
            ),
          ),
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    asset.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    isExternal ? '外部资金' : asset.curr,
                    style: TextStyle(
                      fontSize: 12,
                      color: AppTheme.textTertiary,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 10),
            Text(
              amountText,
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(width: 10),
            Icon(
              selected ? Icons.check_circle : Icons.radio_button_unchecked,
              size: 18,
              color: selected ? AppTheme.accent : AppTheme.textTertiary,
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _openCashAssetPicker({
    required String actionMode,
    required List<Asset> cashOptions,
  }) async {
    if (_saving || cashOptions.isEmpty) return;

    final currencySet = cashOptions
        .map((e) => e.curr.trim().toUpperCase())
        .where((e) => e.isNotEmpty && e != 'CNY')
        .toSet();
    final subtitle = currencySet.isEmpty
        ? '（CNY）'
        : '（含 ${currencySet.join("/")}）';

    final picked = await showModalBottomSheet<int>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (sheetContext) {
        var query = '';
        return SafeArea(
          child: StatefulBuilder(
            builder: (context, setSheetState) {
              final filtered = cashOptions.where((asset) {
                if (query.trim().isEmpty) return true;
                final key = query.trim().toLowerCase();
                return asset.name.toLowerCase().contains(key) ||
                    asset.curr.toLowerCase().contains(key);
              }).toList();

              final recent = _recentCashAssets(filtered);
              final recentIds = recent
                  .map((asset) => asset.id)
                  .whereType<int>()
                  .toSet();
              final all = filtered.where((asset) {
                final id = asset.id;
                return id == null || !recentIds.contains(id);
              }).toList();

              Widget sectionTitle(String text) {
                return Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                  child: Text(
                    text,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                );
              }

              return FractionallySizedBox(
                heightFactor: 0.7,
                child: Container(
                  decoration: BoxDecoration(
                    color: AppTheme.bgCard,
                    borderRadius: const BorderRadius.vertical(
                      top: Radius.circular(18),
                    ),
                    border: Border.all(
                      color: AppTheme.border.withOpacity(
                        AppTheme.isLight ? 0.7 : 0.3,
                      ),
                      width: 1,
                    ),
                  ),
                  child: Column(
                    children: [
                      const SizedBox(height: 10),
                      Container(
                        width: 38,
                        height: 4,
                        decoration: BoxDecoration(
                          color: AppTheme.textTertiary.withOpacity(0.45),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 14, 16, 2),
                        child: Row(
                          children: [
                            Expanded(
                              child: Text(
                                actionMode == 'sell' ? '选择回款账户' : '选择转入账户',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.w700,
                                  color: AppTheme.textPrimary,
                                ),
                              ),
                            ),
                            TextButton(
                              onPressed: () => Navigator.pop(sheetContext),
                              child: const Text('关闭'),
                            ),
                          ],
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 0, 16, 10),
                        child: Align(
                          alignment: Alignment.centerLeft,
                          child: Text(
                            subtitle,
                            style: TextStyle(
                              fontSize: 12,
                              color: AppTheme.textTertiary,
                            ),
                          ),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 0, 16, 10),
                        child: TextField(
                          autofocus: false,
                          style: TextStyle(
                            fontSize: 14,
                            color: AppTheme.textPrimary,
                          ),
                          decoration: InputDecoration(
                            isDense: true,
                            prefixIcon: Icon(
                              Icons.search,
                              size: 18,
                              color: AppTheme.textSecondary,
                            ),
                            hintText: '搜索账户名 / 币种',
                            hintStyle: TextStyle(
                              fontSize: 14,
                              color: AppTheme.textTertiary,
                            ),
                            contentPadding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 10,
                            ),
                          ),
                          onChanged: (value) {
                            setSheetState(() => query = value);
                          },
                        ),
                      ),
                      Expanded(
                        child: filtered.isEmpty
                            ? Center(
                                child: Text(
                                  '没有匹配账户',
                                  style: TextStyle(
                                    fontSize: 13,
                                    color: AppTheme.textTertiary,
                                  ),
                                ),
                              )
                            : ListView(
                                children: [
                                  if (recent.isNotEmpty) ...[
                                    sectionTitle('最近使用'),
                                    ...recent.map(
                                      (asset) => _buildCashAssetTile(
                                        asset: asset,
                                        selected:
                                            asset.id == _selectedCashAssetId,
                                        onTap: () => Navigator.pop(
                                          sheetContext,
                                          asset.id,
                                        ),
                                      ),
                                    ),
                                  ],
                                  if (all.isNotEmpty) ...[
                                    sectionTitle('全部账户'),
                                    ...all.map(
                                      (asset) => _buildCashAssetTile(
                                        asset: asset,
                                        selected:
                                            asset.id == _selectedCashAssetId,
                                        onTap: () => Navigator.pop(
                                          sheetContext,
                                          asset.id,
                                        ),
                                      ),
                                    ),
                                  ],
                                  const SizedBox(height: 10),
                                ],
                              ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        );
      },
    );

    if (picked != null && mounted) {
      setState(() => _selectedCashAssetId = picked);
      _rememberCashAsset(picked);
    }
  }

  void _prefillPriceFromCurrent() {
    final item = widget.item;
    if (item == null) return;
    final appState = context.read<AppState>();
    final livePrice = appState.prices[item.code]?.price ?? 0;
    final defaultPrice = livePrice > 0 ? livePrice : item.price;
    if (defaultPrice > 0) {
      final decimals = _isFundAsset(assetType: item.assetType, code: item.code)
          ? 4
          : 3;
      _priceController.text = _formatInputNumber(
        defaultPrice,
        decimals: decimals,
      );
    }
  }

  void _setTradeMode(String mode) {
    if (_saving || _tradeMode == mode) return;
    FocusScope.of(context).unfocus();
    setState(() {
      _tradeMode = mode;
      _errorText = null;
      _navErrorText = null;
      _navLoading = false;
      if (mode == 'adjust') {
        _adjustController.clear();
        final item = widget.item;
        if (item != null) {
          final decimals =
              _isFundAsset(assetType: item.assetType, code: item.code) ? 4 : 3;
          _adjustPriceController.text = _formatInputNumber(
            item.price,
            decimals: decimals,
          );
        } else {
          _adjustPriceController.clear();
        }
      } else if (_priceController.text.trim().isEmpty) {
        _prefillPriceFromCurrent();
      }
      if (mode != 'buy') {
        _fundInputMode = 'qty';
        _amountController.clear();
        _navFetchSeq += 1;
      } else if (_isCurrentFundTarget()) {
        _fundInputMode = 'amount';
        _amountController.clear();
      }
    });
    if (mode == 'buy' && _isCurrentFundTarget()) {
      final code = widget.item?.code ?? '';
      if (code.isNotEmpty) {
        unawaited(_prefillFundNavForCode(code));
      }
    }
  }

  Future<void> _submit() async {
    if (_saving) return;
    final appState = context.read<AppState>();
    final toastContext = widget.hostContext ?? context;
    final mode = _currentActionMode();

    double? price;
    double? qty;

    setState(() {
      _saving = true;
      _errorText = null;
    });

    late final Future<AssetActionResult> actionFuture;
    final needsCashSource = _requiresCashSource(mode);
    if (needsCashSource &&
        (_selectedCashAssetId == null ||
            (_selectedCashAssetId! <= 0 && _selectedCashAssetId != -999))) {
      setState(() {
        _saving = false;
        _errorText = '请选择资金来源账户';
      });
      return;
    }
    if (needsCashSource) {
      _rememberCashAsset(_selectedCashAssetId);
    }
    if (_isAdd) {
      final priceStr = _priceController.text.trim();
      price = double.tryParse(priceStr);
      if (price == null) {
        setState(() {
          _saving = false;
          _errorText = '请输入有效价格';
        });
        return;
      }
      if (price <= 0) {
        setState(() {
          _saving = false;
          _errorText = '价格必须大于 0';
        });
        return;
      }
      if (_selected == null) {
        setState(() {
          _saving = false;
          _errorText = '必须从下拉列表选择资产';
        });
        return;
      }
      final isFund = _isCurrentFundTarget();
      if (isFund && _isFundAmountMode()) {
        final amount = double.tryParse(_amountController.text.trim());
        if (amount == null || amount <= 0) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效买入金额';
          });
          return;
        }
        qty = _deriveFundQtyFromAmountNav();
        if (qty == null || qty <= 0) {
          setState(() {
            _saving = false;
            _errorText = '金额过小，按当前净值不足以买入最小份额（0.0001）';
          });
          return;
        }
      } else {
        final qtyStr = _qtyController.text.trim();
        qty = double.tryParse(qtyStr);
        if (qty == null) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效数量';
          });
          return;
        }
        if (qty <= 0) {
          setState(() {
            _saving = false;
            _errorText = '数量必须大于 0';
          });
          return;
        }
      }
      final code = _selected?['code'] ?? '';
      final name = _selected?['name'] ?? '';
      final curr = _selected?['currency'];
      final assetType = _selected?['asset_type'];
      actionFuture = appState.buyInvestmentWithCash(
        code: code,
        name: name,
        price: price,
        qty: qty,
        cashAssetId: _selectedCashAssetId!,
        curr: curr,
        assetType: assetType,
        awaitRefresh: false,
      );
    } else {
      final code = widget.item?.code ?? '';
      if (code.isEmpty) {
        setState(() {
          _saving = false;
          _errorText = '未找到持仓代码';
        });
        return;
      }
      if (mode == 'adjust') {
        final adjustStr = _adjustController.text.trim();
        final adjustPriceStr = _adjustPriceController.text.trim();
        final adjustVal = double.tryParse(adjustStr);
        final adjustPriceVal = double.tryParse(adjustPriceStr);
        if (adjustVal == null) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效调整金额';
          });
          return;
        }
        if (adjustPriceVal == null) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效平均成本';
          });
          return;
        }
        final qtyVal = widget.item?.qty ?? 0;
        if (qtyVal <= 0) {
          setState(() {
            _saving = false;
            _errorText = '未找到有效持仓数量';
          });
          return;
        }
        actionFuture = appState.modifyInvestment(
          code: code,
          qty: qtyVal,
          price: adjustPriceVal,
          adjustment: adjustVal,
          awaitRefresh: false,
        );
      } else if (mode == 'buy') {
        final priceStr = _priceController.text.trim();
        price = double.tryParse(priceStr);
        if (price == null) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效价格';
          });
          return;
        }
        if (price <= 0) {
          setState(() {
            _saving = false;
            _errorText = '价格必须大于 0';
          });
          return;
        }
        final isFund = _isCurrentFundTarget();
        if (isFund && _isFundAmountMode()) {
          final amount = double.tryParse(_amountController.text.trim());
          if (amount == null || amount <= 0) {
            setState(() {
              _saving = false;
              _errorText = '请输入有效买入金额';
            });
            return;
          }
          qty = _deriveFundQtyFromAmountNav();
          if (qty == null || qty <= 0) {
            setState(() {
              _saving = false;
              _errorText = '金额过小，按当前净值不足以买入最小份额（0.0001）';
            });
            return;
          }
        } else {
          final qtyStr = _qtyController.text.trim();
          qty = double.tryParse(qtyStr);
          if (qty == null) {
            setState(() {
              _saving = false;
              _errorText = '请输入有效数量';
            });
            return;
          }
          if (qty <= 0) {
            setState(() {
              _saving = false;
              _errorText = '数量必须大于 0';
            });
            return;
          }
        }
        actionFuture = appState.buyInvestmentWithCash(
          code: code,
          name: widget.item?.name ?? code,
          price: price,
          qty: qty,
          cashAssetId: _selectedCashAssetId!,
          curr: widget.item?.curr,
          assetType: widget.item?.assetType,
          awaitRefresh: false,
        );
      } else {
        final priceStr = _priceController.text.trim();
        final qtyStr = _qtyController.text.trim();
        price = double.tryParse(priceStr);
        qty = double.tryParse(qtyStr);
        if (price == null) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效价格';
          });
          return;
        }
        if (qty == null) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效数量';
          });
          return;
        }
        if (qty <= 0) {
          setState(() {
            _saving = false;
            _errorText = '数量必须大于 0';
          });
          return;
        }
        if (price <= 0) {
          setState(() {
            _saving = false;
            _errorText = '价格必须大于 0';
          });
          return;
        }
        actionFuture = appState.sellInvestmentToCash(
          code: code,
          price: price,
          qty: qty,
          cashAssetId: _selectedCashAssetId!,
          awaitRefresh: false,
        );
      }
    }

    final result = await actionFuture;
    if (!mounted || !toastContext.mounted) return;
    if (!result.ok) {
      setState(() {
        _saving = false;
        _errorText = result.message ?? '保存失败，请稍后重试';
      });
      TopToast.showError(toastContext, result.message ?? '保存失败，请稍后重试');
      return;
    }

    TopToast.showSuccess(toastContext, '已保存');
    _closeDialog();

    final undoToken = result.data?['undo_token']?.toString();
    if (undoToken != null && undoToken.isNotEmpty) {
      TopToast.showAction(
        toastContext,
        message: '已保存',
        actionLabel: '撤销',
        onAction: () {
          unawaited(() async {
            final undoResult = await appState.undoInvestmentOperation(
              undoToken,
            );
            if (!toastContext.mounted) return;
            if (undoResult.ok) {
              TopToast.showInfo(toastContext, '已撤销');
            } else {
              TopToast.showError(toastContext, undoResult.message ?? '撤销失败');
            }
          }());
        },
        duration: const Duration(seconds: 15),
      );
    }
  }

  Future<void> _confirmCorrectiveDelete() async {
    if (_saving) return;
    final item = widget.item;
    if (item == null) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('删除并清理历史'),
          content: Text(
            '仅用于误录入纠错：将删除「${item.name}」持仓、相关交易记录，并清理受影响快照。\n'
            '注意：不会回款到现金账户。\n'
            '如果是正常平仓，请使用“卖出”并选择回款账户。',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('取消'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('仍要纠错删除'),
            ),
          ],
        );
      },
    );
    if (confirmed != true) return;
    if (!mounted) return;
    // ignore: use_build_context_synchronously
    final appState = context.read<AppState>();
    // ignore: use_build_context_synchronously
    final toastContext = widget.hostContext ?? context;
    // ignore: use_build_context_synchronously
    _closeDialog();
    // ignore: use_build_context_synchronously
    TopToast.showSuccess(toastContext, '已删除');
    unawaited(() async {
      final result = await appState.deleteInvestment(
        code: item.code,
        corrective: true,
        awaitRefresh: false,
      );
      // ignore: use_build_context_synchronously
      if (!toastContext.mounted) return;
      if (!result.ok) {
        TopToast.showError(toastContext, result.message ?? '删除失败，请稍后重试');
      }
    }());
  }

  void _onMoreMenuSelect(String value) {
    if (value == 'corrective_delete') {
      _confirmCorrectiveDelete();
    }
  }

  Widget _buildSearchResults() {
    if (_results.isEmpty) return const SizedBox.shrink();
    return Container(
      margin: const EdgeInsets.only(top: 8),
      constraints: const BoxConstraints(maxHeight: 200),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.border, width: 1),
      ),
      child: ListView.builder(
        shrinkWrap: true,
        itemCount: _results.length,
        itemBuilder: (context, index) {
          final item = _results[index] as Map<String, dynamic>;
          final name = item['name'] ?? '';
          final typeName = item['type_name'] ?? '';
          final code = _formatDisplayCode(item['code'] ?? '');
          return InkWell(
            onTap: () {
              final codeRaw = item['code']?.toString() ?? '';
              final isFund = _isFundAsset(
                assetType: item['asset_type']?.toString(),
                code: codeRaw,
              );
              setState(() {
                _selected = item;
                _queryController.text = name;
                _results = [];
                _errorText = null;
                _fundInputMode = isFund ? 'amount' : 'qty';
                _amountController.clear();
                _navErrorText = null;
                _navLoading = false;
              });
              if (isFund) {
                unawaited(_prefillFundNavForCode(codeRaw));
              }
            },
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name,
                    style: TextStyle(
                      color: AppTheme.textPrimary,
                      fontSize: FontSize.base,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Row(
                    children: [
                      _marketBadge(typeName),
                      const SizedBox(width: 6),
                      Text(
                        code,
                        style: TextStyle(
                          color: AppTheme.textTertiary,
                          fontSize: FontSize.sm,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildTradeToggle() {
    if (!_isTrade) return const SizedBox.shrink();
    return Row(
      children: [
        Expanded(
          child: InkWell(
            onTap: () => _setTradeMode('buy'),
            borderRadius: BorderRadius.circular(10),
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 10),
              decoration: BoxDecoration(
                color: _tradeMode == 'buy'
                    ? AppTheme.accent
                    : Colors.transparent,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: _tradeMode == 'buy'
                      ? AppTheme.accent
                      : AppTheme.border,
                  width: 1,
                ),
              ),
              child: Text(
                '买入',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: _tradeMode == 'buy'
                      ? AppTheme.textPrimary
                      : AppTheme.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: InkWell(
            onTap: () => _setTradeMode('sell'),
            borderRadius: BorderRadius.circular(10),
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 10),
              decoration: BoxDecoration(
                color: _tradeMode == 'sell'
                    ? AppTheme.danger
                    : Colors.transparent,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: _tradeMode == 'sell'
                      ? AppTheme.danger
                      : AppTheme.border,
                  width: 1,
                ),
              ),
              child: Text(
                '卖出',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: _tradeMode == 'sell'
                      ? AppTheme.textPrimary
                      : AppTheme.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: InkWell(
            onTap: () => _setTradeMode('adjust'),
            borderRadius: BorderRadius.circular(10),
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 10),
              decoration: BoxDecoration(
                color: _tradeMode == 'adjust'
                    ? AppTheme.accent
                    : Colors.transparent,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: _tradeMode == 'adjust'
                      ? AppTheme.accent
                      : AppTheme.border,
                  width: 1,
                ),
              ),
              child: Text(
                '调整',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: _tradeMode == 'adjust'
                      ? AppTheme.textPrimary
                      : AppTheme.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildFundInputModeToggle() {
    if (!_isCurrentFundTarget()) return const SizedBox.shrink();
    final isAmountMode = _isFundAmountMode();
    Widget item(String value, String label) {
      final selected = _fundInputMode == value;
      return Expanded(
        child: InkWell(
          onTap: _saving ? null : () => _setFundInputMode(value),
          borderRadius: BorderRadius.circular(10),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 8),
            decoration: BoxDecoration(
              color: selected ? AppTheme.accent : Colors.transparent,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: selected ? AppTheme.accent : AppTheme.border,
                width: 1,
              ),
            ),
            child: Text(
              label,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: selected ? AppTheme.textPrimary : AppTheme.textSecondary,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '基金买入方式',
          style: TextStyle(
            color: AppTheme.textSecondary,
            fontSize: FontSize.sm,
          ),
        ),
        const SizedBox(height: 6),
        Row(
          children: [
            item('qty', '按份额'),
            const SizedBox(width: 8),
            item('amount', '按金额'),
          ],
        ),
        if (isAmountMode && _navLoading)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(
              '正在获取最新净值…',
              style: TextStyle(
                color: AppTheme.textTertiary,
                fontSize: FontSize.xs,
              ),
            ),
          ),
        if (isAmountMode && _navErrorText != null)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(
              _navErrorText!,
              style: TextStyle(color: AppTheme.danger, fontSize: FontSize.xs),
            ),
          ),
      ],
    );
  }

  Widget _buildTradeInputFields() {
    if (_isTrade && _isAdjust) {
      return Column(
        children: [
          TextField(
            controller: _adjustPriceController,
            keyboardType: const TextInputType.numberWithOptions(
              decimal: true,
              signed: true,
            ),
            style: TextStyle(color: AppTheme.textPrimary),
            decoration: _compactDecoration('平均成本'),
          ),
          const SizedBox(height: Spacing.md),
          TextField(
            controller: _adjustController,
            keyboardType: const TextInputType.numberWithOptions(
              decimal: true,
              signed: true,
            ),
            style: TextStyle(color: AppTheme.textPrimary),
            decoration: _compactDecoration('调整金额'),
          ),
        ],
      );
    }

    final showFundMode = _isCurrentFundTarget();
    final amountMode = _isFundAmountMode();

    return Column(
      children: [
        if (showFundMode) ...[
          _buildFundInputModeToggle(),
          const SizedBox(height: Spacing.md),
        ],
        TextField(
          controller: _priceController,
          keyboardType: const TextInputType.numberWithOptions(
            decimal: true,
            signed: true,
          ),
          style: TextStyle(color: AppTheme.textPrimary),
          decoration: _compactDecoration(
            amountMode ? '净值' : (_isAdd ? '买入成本价' : '价格'),
          ),
        ),
        const SizedBox(height: Spacing.md),
        if (amountMode) ...[
          TextField(
            controller: _amountController,
            keyboardType: const TextInputType.numberWithOptions(
              decimal: true,
              signed: false,
            ),
            style: TextStyle(color: AppTheme.textPrimary),
            decoration: _compactDecoration('买入金额'),
          ),
          const SizedBox(height: 8),
          Builder(
            builder: (context) {
              final qty = _deriveFundQtyFromAmountNav();
              final text = qty == null ? '--' : _formatQtyDisplay(qty);
              return Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  '预计份额：$text',
                  style: TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: FontSize.sm,
                  ),
                ),
              );
            },
          ),
        ] else ...[
          TextField(
            controller: _qtyController,
            keyboardType: const TextInputType.numberWithOptions(
              decimal: true,
              signed: false,
            ),
            inputFormatters: showFundMode
                ? _fundQtyInputFormatters
                : _qtyInputFormatters,
            style: TextStyle(color: AppTheme.textPrimary),
            decoration: _compactDecoration('数量'),
          ),
        ],
      ],
    );
  }

  bool _isSaveInputReady() {
    final mode = _currentActionMode();
    final priceReady = _priceController.text.trim().isNotEmpty;
    final qtyReady = _qtyController.text.trim().isNotEmpty;
    final amountReady = _amountController.text.trim().isNotEmpty;
    if (_isAdd) {
      if (_isFundAmountMode()) {
        return _selected != null && amountReady && priceReady;
      }
      return _selected != null && priceReady && qtyReady;
    }
    if (mode == 'adjust') {
      return _adjustController.text.trim().isNotEmpty &&
          _adjustPriceController.text.trim().isNotEmpty;
    }
    if (mode == 'buy' && _isFundAmountMode()) {
      return amountReady && priceReady;
    }
    return priceReady && qtyReady;
  }

  @override
  Widget build(BuildContext context) {
    if (_inlineClosed) return const SizedBox.shrink();
    final appState = context.watch<AppState>();
    final cashOptions = appState.cashAssets
        .where((asset) => (asset.id ?? 0) > 0)
        .toList();
    final actionMode = _currentActionMode();
    if (actionMode != 'sell') {
      cashOptions.insert(
        0,
        Asset(id: -999, name: '外部资金/初始转入', amount: 0.0, curr: 'CNY'),
      );
    }
    if (_selectedCashAssetId != null &&
        cashOptions.every((asset) => asset.id != _selectedCashAssetId)) {
      _selectedCashAssetId = null;
    }
    if (_selectedCashAssetId == null && cashOptions.isNotEmpty) {
      _selectedCashAssetId = cashOptions.first.id;
    }
    final needsCashSource = _requiresCashSource(actionMode);

    final title = _isAdd
        ? '添加投资资产'
        : _isTrade
        ? '买入 / 卖出 / 调整'
        : _isBuy
        ? '买入'
        : (_isSell ? '卖出' : '买入 / 卖出 / 调整');
    final actionColor = (_isTrade ? _tradeMode == 'buy' : _isBuy)
        ? AppTheme.accent
        : (_isTrade && _tradeMode == 'adjust'
              ? AppTheme.accent
              : AppTheme.danger);
    final canSave =
        !_saving &&
        _isSaveInputReady() &&
        (!needsCashSource || _selectedCashAssetId != null);

    final maxDialogHeight = MediaQuery.of(context).size.height * 0.72;

    return Dialog(
      backgroundColor: Colors.transparent,
      insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(18),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
          child: ConstrainedBox(
            constraints: BoxConstraints(maxHeight: maxDialogHeight),
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppTheme.bgCard.withOpacity(
                  AppTheme.isLight ? 0.98 : 0.88,
                ),
                borderRadius: BorderRadius.circular(18),
                border: Border.all(
                  color: AppTheme.isLight
                      ? AppTheme.border.withOpacity(0.7)
                      : Colors.white.withOpacity(0.08),
                  width: 1,
                ),
                gradient: LinearGradient(
                  colors: AppTheme.dialogGradient,
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                boxShadow: AppTheme.cardShadow,
              ),
              child: SingleChildScrollView(
                keyboardDismissBehavior:
                    ScrollViewKeyboardDismissBehavior.onDrag,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            title,
                            style: TextStyle(
                              fontSize: FontSize.xxl,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.textPrimary,
                            ),
                          ),
                        ),
                        if (_isTrade)
                          PopupMenuButton<String>(
                            enabled: !_saving,
                            onSelected: _onMoreMenuSelect,
                            icon: Icon(
                              Icons.more_horiz,
                              color: AppTheme.textSecondary,
                            ),
                            itemBuilder: (menuContext) {
                              return [
                                PopupMenuItem<String>(
                                  value: 'corrective_delete',
                                  child: Row(
                                    children: [
                                      Icon(
                                        Icons.delete_outline,
                                        size: 18,
                                        color: AppTheme.danger,
                                      ),
                                      const SizedBox(width: 8),
                                      Text(
                                        '纠错删除（不回款）',
                                        style: TextStyle(
                                          color: AppTheme.danger,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ];
                            },
                          ),
                      ],
                    ),
                    const SizedBox(height: Spacing.md),
                    if (_isAdd) ...[
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _queryController,
                              onChanged: _onQueryChanged,
                              style: TextStyle(color: AppTheme.textPrimary),
                              decoration: _compactDecoration(
                                '股票代码/名称',
                                hintText: '输入代码或名称',
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          SizedBox(
                            height: 42,
                            child: ElevatedButton.icon(
                              onPressed: _searching ? null : _onSearchTap,
                              icon: const Icon(Icons.search, size: 16),
                              label: Text(_searching ? '搜索中' : '搜索'),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppTheme.accent,
                                foregroundColor: AppTheme.textPrimary,
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                ),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(10),
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        '仅点击“搜索”后返回结果',
                        style: TextStyle(
                          color: AppTheme.textTertiary,
                          fontSize: FontSize.xs,
                        ),
                      ),
                      _buildSearchResults(),
                      if (_searchErrorText != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(
                            _searchErrorText!,
                            style: TextStyle(
                              color: AppTheme.danger,
                              fontSize: FontSize.sm,
                            ),
                          ),
                        ),
                      if (_selected != null) ...[
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            Text(
                              '已选择：',
                              style: TextStyle(
                                color: AppTheme.textSecondary,
                                fontSize: FontSize.sm,
                              ),
                            ),
                            Text(
                              '${_selected?['name']}  ',
                              style: TextStyle(
                                color: AppTheme.textSecondary,
                                fontSize: FontSize.sm,
                              ),
                            ),
                            _marketBadge(_selected?['type_name'] ?? ''),
                            const SizedBox(width: 6),
                            Text(
                              _formatDisplayCode(_selected?['code'] ?? ''),
                              style: TextStyle(
                                color: AppTheme.textSecondary,
                                fontSize: FontSize.sm,
                              ),
                            ),
                          ],
                        ),
                      ],
                      const SizedBox(height: Spacing.md),
                    ] else ...[
                      Text(
                        '${widget.item?.name ?? ''} · ${_formatDisplayCode(widget.item?.code ?? '')}',
                        style: TextStyle(
                          color: AppTheme.textSecondary,
                          fontSize: FontSize.base,
                        ),
                      ),
                      const SizedBox(height: Spacing.md),
                    ],
                    _buildTradeToggle(),
                    if (_isTrade) const SizedBox(height: Spacing.md),
                    if (needsCashSource) ...[
                      InkWell(
                        onTap: _saving || cashOptions.isEmpty
                            ? null
                            : () => _openCashAssetPicker(
                                actionMode: actionMode,
                                cashOptions: cashOptions,
                              ),
                        borderRadius: BorderRadius.circular(10),
                        child: InputDecorator(
                          decoration: _compactDecoration(
                            actionMode == 'sell' ? '回款账户' : '资金来源账户',
                          ),
                          child: Row(
                            children: [
                              Expanded(
                                child: Builder(
                                  builder: (context) {
                                    Asset? selected;
                                    for (final asset in cashOptions) {
                                      if (asset.id == _selectedCashAssetId) {
                                        selected = asset;
                                        break;
                                      }
                                    }
                                    if (selected == null) {
                                      return Text(
                                        '请选择账户',
                                        style: TextStyle(
                                          fontSize: 14,
                                          color: AppTheme.textTertiary,
                                        ),
                                      );
                                    }
                                    final tail = selected.id == -999
                                        ? '外部'
                                        : '${selected.curr} ${_formatInputNumber(selected.amount)}';
                                    return Text(
                                      '${selected.name} · $tail',
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: TextStyle(
                                        fontSize: 15,
                                        color: AppTheme.textPrimary,
                                      ),
                                    );
                                  },
                                ),
                              ),
                              Icon(
                                Icons.keyboard_arrow_down_rounded,
                                size: 20,
                                color: AppTheme.textSecondary,
                              ),
                            ],
                          ),
                        ),
                      ),
                      if (cashOptions.isEmpty) ...[
                        const SizedBox(height: 8),
                        Text(
                          actionMode == 'sell' ? '请先添加回款现金账户' : '请先添加现金资产账户',
                          style: TextStyle(
                            color: AppTheme.danger,
                            fontSize: FontSize.sm,
                          ),
                        ),
                      ],
                      const SizedBox(height: Spacing.md),
                    ],
                    _buildTradeInputFields(),
                    if (_errorText != null) ...[
                      const SizedBox(height: 8),
                      Text(
                        _errorText!,
                        style: TextStyle(
                          color: AppTheme.danger,
                          fontSize: FontSize.base,
                        ),
                      ),
                    ],
                    const SizedBox(height: Spacing.lg),
                    Row(
                      children: [
                        Expanded(
                          child: TextButton(
                            onPressed: _saving ? null : _closeDialog,
                            child: Text('取消'),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: actionColor,
                            ),
                            onPressed: canSave ? _submit : null,
                            child: _saving
                                ? const SizedBox(
                                    width: 18,
                                    height: 18,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : Text('保存'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
