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

enum _PadField { none, price, qty, adjustPrice, adjustAmount }

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
  final _adjustPriceController = TextEditingController();
  final _adjustController = TextEditingController();
  final _priceFocusNode = FocusNode();
  final _qtyFocusNode = FocusNode();
  final _adjustPriceFocusNode = FocusNode();
  final _adjustFocusNode = FocusNode();

  bool _saving = false;
  bool _inlineClosed = false;
  bool _searching = false;
  String? _errorText;
  String? _searchErrorText;
  List<dynamic> _results = [];
  Map<String, dynamic>? _selected;
  String _tradeMode = 'buy';
  int? _selectedCashAssetId;
  int _searchSeq = 0;
  bool _normalizingInput = false;
  _PadField _activePadField = _PadField.none;
  final Map<String, _SearchCacheEntry> _searchCache =
      <String, _SearchCacheEntry>{};
  static const Duration _searchCacheTtl = Duration(seconds: 20);
  static const int _maxRecentCashAssets = 5;
  static final List<int> _recentCashAssetIds = <int>[];
  static final List<TextInputFormatter> _qtyInputFormatters =
      <TextInputFormatter>[
        FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d{0,2}$')),
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
    _adjustPriceController.addListener(_onInputControllerChanged);
    _adjustController.addListener(_onInputControllerChanged);
    _priceFocusNode.addListener(() => _syncPadFieldByFocus(_PadField.price));
    _qtyFocusNode.addListener(() => _syncPadFieldByFocus(_PadField.qty));
    _adjustPriceFocusNode.addListener(
      () => _syncPadFieldByFocus(_PadField.adjustPrice),
    );
    _adjustFocusNode.addListener(
      () => _syncPadFieldByFocus(_PadField.adjustAmount),
    );
    _syncDefaultCashAsset();
    if (!_isAdd && widget.item != null) {
      _prefillPriceFromCurrent();
      if (_isTrade) {
        _tradeMode = 'buy';
        _adjustController.clear();
        _adjustPriceController.clear();
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
    _adjustPriceController.removeListener(_onInputControllerChanged);
    _adjustController.removeListener(_onInputControllerChanged);
    _queryController.dispose();
    _priceController.dispose();
    _qtyController.dispose();
    _adjustPriceController.dispose();
    _adjustController.dispose();
    _priceFocusNode.dispose();
    _qtyFocusNode.dispose();
    _adjustPriceFocusNode.dispose();
    _adjustFocusNode.dispose();
    super.dispose();
  }

  void _onInputControllerChanged() {
    if (!mounted || _normalizingInput) return;
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
      _searching = false;
      _searchSeq += 1;
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

  TextEditingController? _controllerForField(_PadField field) {
    switch (field) {
      case _PadField.price:
        return _priceController;
      case _PadField.qty:
        return _qtyController;
      case _PadField.adjustPrice:
        return _adjustPriceController;
      case _PadField.adjustAmount:
        return _adjustController;
      case _PadField.none:
        return null;
    }
  }

  bool _fieldAllowsMinus(_PadField field) {
    return field == _PadField.price ||
        field == _PadField.adjustPrice ||
        field == _PadField.adjustAmount;
  }

  int? _fieldMaxDecimals(_PadField field) {
    if (field == _PadField.qty) return 2;
    return null;
  }

  void _syncPadFieldByFocus(_PadField field) {
    final hasFocus = switch (field) {
      _PadField.price => _priceFocusNode.hasFocus,
      _PadField.qty => _qtyFocusNode.hasFocus,
      _PadField.adjustPrice => _adjustPriceFocusNode.hasFocus,
      _PadField.adjustAmount => _adjustFocusNode.hasFocus,
      _PadField.none => false,
    };
    if (hasFocus) {
      _activatePadField(field);
      return;
    }
    if (_activePadField == field &&
        !_priceFocusNode.hasFocus &&
        !_qtyFocusNode.hasFocus &&
        !_adjustPriceFocusNode.hasFocus &&
        !_adjustFocusNode.hasFocus) {
      _activatePadField(_PadField.none);
    }
  }

  void _activatePadField(_PadField field) {
    if (_activePadField == field) return;
    setState(() {
      _activePadField = field;
    });
  }

  void _dismissPad() {
    FocusScope.of(context).unfocus();
    _activatePadField(_PadField.none);
  }

  void _closeDialog() {
    final navigator = Navigator.maybeOf(context);
    if (navigator != null && navigator.canPop()) {
      navigator.pop();
      return;
    }
    setState(() {
      _inlineClosed = true;
      _activePadField = _PadField.none;
    });
  }

  String _normalizeNumericText(String raw, _PadField field) {
    final allowsMinus = _fieldAllowsMinus(field);
    final maxDecimals = _fieldMaxDecimals(field);
    final buffer = StringBuffer();
    var hasDot = false;
    var minusAdded = false;
    var decimals = 0;

    for (var i = 0; i < raw.length; i++) {
      final ch = raw[i];
      final isDigit = ch.codeUnitAt(0) >= 48 && ch.codeUnitAt(0) <= 57;
      if (isDigit) {
        if (hasDot && maxDecimals != null && decimals >= maxDecimals) {
          continue;
        }
        buffer.write(ch);
        if (hasDot) decimals += 1;
        continue;
      }
      if (ch == '.') {
        if (hasDot) continue;
        hasDot = true;
        if (buffer.isEmpty) {
          buffer.write('0.');
        } else if (buffer.toString() == '-') {
          buffer.write('0.');
        } else {
          buffer.write('.');
        }
        continue;
      }
      if (ch == '-' && allowsMinus && !minusAdded && buffer.isEmpty) {
        buffer.write('-');
        minusAdded = true;
      }
    }
    return buffer.toString();
  }

  void _normalizeControllerText(
    TextEditingController controller,
    _PadField field,
  ) {
    final normalized = _normalizeNumericText(controller.text, field);
    if (normalized == controller.text) return;
    _normalizingInput = true;
    controller.value = TextEditingValue(
      text: normalized,
      selection: TextSelection.collapsed(offset: normalized.length),
    );
    _normalizingInput = false;
  }

  void _handleFieldChanged(TextEditingController controller, _PadField field) {
    if (_normalizingInput) return;
    final before = controller.text;
    _normalizeControllerText(controller, field);
    if (!mounted) return;
    if (before != controller.text) {
      setState(() {});
      return;
    }
    // 即使文本未被规整改写，也要刷新按钮可用态（依赖 controller 文本）
    setState(() {});
  }

  String _appendDigit(String text, String digit) {
    if (text == '0') return digit;
    if (text == '-0') return '-$digit';
    return '$text$digit';
  }

  String _appendDecimalPoint(String text) {
    if (text.contains('.')) return text;
    if (text.isEmpty) return '0.';
    if (text == '-') return '-0.';
    return '$text.';
  }

  String _prependMinus(String text) {
    if (text.startsWith('-')) return text;
    return '-$text';
  }

  String _deleteLast(String text) {
    if (text.isEmpty) return text;
    return text.substring(0, text.length - 1);
  }

  void _applyPadInput(_PadField field, String key) {
    final controller = _controllerForField(field);
    if (controller == null) return;
    var next = controller.text;

    if (key == 'confirm') {
      _dismissPad();
      return;
    }
    if (key == 'clear') {
      next = '';
    } else if (key == 'backspace') {
      next = _deleteLast(next);
    } else if (key == '.') {
      next = _appendDecimalPoint(next);
    } else if (key == '-') {
      if (!_fieldAllowsMinus(field)) return;
      next = _prependMinus(next);
    } else {
      next = _appendDigit(next, key);
    }

    next = _normalizeNumericText(next, field);
    if (next == controller.text) return;

    _normalizingInput = true;
    controller.value = TextEditingValue(
      text: next,
      selection: TextSelection.collapsed(offset: next.length),
    );
    _normalizingInput = false;
    setState(() {});
  }

  Widget _buildPadButton({
    required String text,
    required VoidCallback? onTap,
    bool highlighted = false,
  }) {
    final disabled = onTap == null;
    return SizedBox(
      height: 44,
      child: ElevatedButton(
        style: ElevatedButton.styleFrom(
          elevation: 0,
          foregroundColor: disabled
              ? AppTheme.textTertiary
              : (highlighted ? AppTheme.textPrimary : AppTheme.textSecondary),
          backgroundColor: disabled
              ? AppTheme.bgCard.withOpacity(0.4)
              : (highlighted
                    ? AppTheme.accent
                    : AppTheme.bgElevated.withOpacity(
                        AppTheme.isLight ? 0.95 : 0.45,
                      )),
          side: BorderSide(
            color: AppTheme.border.withOpacity(AppTheme.isLight ? 0.8 : 0.3),
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
        ),
        onPressed: onTap,
        child: Text(
          text,
          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
        ),
      ),
    );
  }

  Widget _buildNumericPad() {
    if (_activePadField == _PadField.none) return const SizedBox.shrink();
    final minusEnabled = _fieldAllowsMinus(_activePadField);

    Widget row(List<Widget> children) {
      return Row(
        children: children
            .map(
              (child) => Expanded(
                child: Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 4,
                    vertical: 3,
                  ),
                  child: child,
                ),
              ),
            )
            .toList(),
      );
    }

    return Container(
      margin: const EdgeInsets.only(top: 10),
      padding: const EdgeInsets.fromLTRB(8, 8, 8, 6),
      decoration: BoxDecoration(
        color: AppTheme.bgCard.withOpacity(AppTheme.isLight ? 0.98 : 0.6),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppTheme.border.withOpacity(AppTheme.isLight ? 0.8 : 0.3),
        ),
      ),
      child: Column(
        children: [
          row([
            _buildPadButton(
              text: '1',
              onTap: () => _applyPadInput(_activePadField, '1'),
            ),
            _buildPadButton(
              text: '2',
              onTap: () => _applyPadInput(_activePadField, '2'),
            ),
            _buildPadButton(
              text: '3',
              onTap: () => _applyPadInput(_activePadField, '3'),
            ),
          ]),
          row([
            _buildPadButton(
              text: '4',
              onTap: () => _applyPadInput(_activePadField, '4'),
            ),
            _buildPadButton(
              text: '5',
              onTap: () => _applyPadInput(_activePadField, '5'),
            ),
            _buildPadButton(
              text: '6',
              onTap: () => _applyPadInput(_activePadField, '6'),
            ),
          ]),
          row([
            _buildPadButton(
              text: '7',
              onTap: () => _applyPadInput(_activePadField, '7'),
            ),
            _buildPadButton(
              text: '8',
              onTap: () => _applyPadInput(_activePadField, '8'),
            ),
            _buildPadButton(
              text: '9',
              onTap: () => _applyPadInput(_activePadField, '9'),
            ),
          ]),
          row([
            _buildPadButton(
              text: '.',
              onTap: () => _applyPadInput(_activePadField, '.'),
            ),
            _buildPadButton(
              text: '0',
              onTap: () => _applyPadInput(_activePadField, '0'),
            ),
            _buildPadButton(
              text: '-',
              onTap: minusEnabled
                  ? () => _applyPadInput(_activePadField, '-')
                  : null,
            ),
          ]),
          row([
            _buildPadButton(
              text: '清空',
              onTap: () => _applyPadInput(_activePadField, 'clear'),
            ),
            _buildPadButton(
              text: '删除',
              onTap: () => _applyPadInput(_activePadField, 'backspace'),
            ),
            _buildPadButton(
              text: '确认',
              onTap: () => _applyPadInput(_activePadField, 'confirm'),
              highlighted: true,
            ),
          ]),
        ],
      ),
    );
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
      _activePadField = _PadField.none;
      _errorText = null;
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
    });
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
      if (_selected == null) {
        setState(() {
          _saving = false;
          _errorText = '必须从下拉列表选择资产';
        });
        return;
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
              setState(() {
                _selected = item;
                _queryController.text = name;
                _results = [];
              });
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

  bool _isSaveInputReady() {
    final mode = _currentActionMode();
    final priceReady = _priceController.text.trim().isNotEmpty;
    final qtyReady = _qtyController.text.trim().isNotEmpty;
    if (_isAdd) {
      return _selected != null && priceReady && qtyReady;
    }
    if (mode == 'adjust') {
      return _adjustController.text.trim().isNotEmpty &&
          _adjustPriceController.text.trim().isNotEmpty;
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
                    if (_isTrade && _isAdjust) ...[
                      TextField(
                        controller: _adjustPriceController,
                        focusNode: _adjustPriceFocusNode,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                          signed: true,
                        ),
                        onTap: () => _activatePadField(_PadField.adjustPrice),
                        onChanged: (_) => _handleFieldChanged(
                          _adjustPriceController,
                          _PadField.adjustPrice,
                        ),
                        style: TextStyle(color: AppTheme.textPrimary),
                        decoration: _compactDecoration('平均成本'),
                      ),
                      const SizedBox(height: Spacing.md),
                      TextField(
                        controller: _adjustController,
                        focusNode: _adjustFocusNode,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                          signed: true,
                        ),
                        onTap: () => _activatePadField(_PadField.adjustAmount),
                        onChanged: (_) => _handleFieldChanged(
                          _adjustController,
                          _PadField.adjustAmount,
                        ),
                        style: TextStyle(color: AppTheme.textPrimary),
                        decoration: _compactDecoration('调整金额'),
                      ),
                    ] else ...[
                      TextField(
                        controller: _priceController,
                        focusNode: _priceFocusNode,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                          signed: true,
                        ),
                        onTap: () => _activatePadField(_PadField.price),
                        onChanged: (_) => _handleFieldChanged(
                          _priceController,
                          _PadField.price,
                        ),
                        style: TextStyle(color: AppTheme.textPrimary),
                        decoration: _compactDecoration(_isAdd ? '买入成本价' : '价格'),
                      ),
                      const SizedBox(height: Spacing.md),
                      TextField(
                        controller: _qtyController,
                        focusNode: _qtyFocusNode,
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                        ),
                        inputFormatters: _qtyInputFormatters,
                        onTap: () => _activatePadField(_PadField.qty),
                        onChanged: (_) =>
                            _handleFieldChanged(_qtyController, _PadField.qty),
                        style: TextStyle(color: AppTheme.textPrimary),
                        decoration: _compactDecoration('数量'),
                      ),
                    ],
                    _buildNumericPad(),
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
