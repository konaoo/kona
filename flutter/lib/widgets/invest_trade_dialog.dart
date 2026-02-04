import 'dart:async';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../providers/app_state.dart';
import '../models/portfolio.dart';

class InvestTradeDialog extends StatefulWidget {
  final String mode; // add | buy | sell
  final PortfolioItem? item;

  const InvestTradeDialog({super.key, required this.mode, this.item});

  @override
  State<InvestTradeDialog> createState() => _InvestTradeDialogState();
}

class _InvestTradeDialogState extends State<InvestTradeDialog> {
  final _queryController = TextEditingController();
  final _priceController = TextEditingController();
  final _qtyController = TextEditingController();
  final _adjustController = TextEditingController();

  Timer? _debounce;
  bool _saving = false;
  bool _searching = false;
  String? _errorText;
  List<dynamic> _results = [];
  Map<String, dynamic>? _selected;
  String _tradeMode = 'buy';

  bool get _isAdd => widget.mode == 'add';
  bool get _isBuy => widget.mode == 'buy';
  bool get _isTrade => widget.mode == 'trade';
  bool get _isAdjust => _tradeMode == 'adjust';

  @override
  void initState() {
    super.initState();
    if (_isTrade && widget.item != null) {
      _adjustController.text = widget.item!.adjustment.toStringAsFixed(2);
    }
  }

  @override
  void dispose() {
    _queryController.dispose();
    _priceController.dispose();
    _qtyController.dispose();
    _adjustController.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  String _formatDisplayCode(String code) {
    const customMap = {
      'ft_LU1116320737': 'BLK',
    };
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
    String label = 'A';
    Color color = AppTheme.accent;
    switch (typeName) {
      case '美股':
        label = 'US';
        color = AppTheme.danger;
        break;
      case '港股':
        label = 'HK';
        color = AppTheme.success;
        break;
      case '基金':
        label = 'F';
        color = const Color(0xFFF59E0B);
        break;
      default:
        label = 'A';
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
    if (value.trim().isEmpty) {
      setState(() {
        _selected = null;
        _results = [];
        _errorText = null;
        _searching = false;
      });
      return;
    }
    if (_selected != null && value == (_selected?['name'] ?? '')) {
      return;
    }
    _selected = null;
    _errorText = null;
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 300), () => _search(value.trim()));
  }

  Future<void> _search(String query) async {
    setState(() => _searching = true);
    final appState = context.read<AppState>();
    final results = await appState.searchStocks(query);
    if (!mounted) return;
    setState(() {
      _results = results;
      _searching = false;
    });
  }

  Future<void> _submit() async {
    final appState = context.read<AppState>();

    double? price;
    double? qty;

    setState(() {
      _saving = true;
      _errorText = null;
    });

    bool ok = false;
    if (_isAdd) {
      final priceStr = _priceController.text.trim();
      final qtyStr = _qtyController.text.trim();
      price = double.tryParse(priceStr);
      qty = double.tryParse(qtyStr);
      if (price == null || price <= 0 || qty == null || qty <= 0) {
        setState(() {
          _saving = false;
          _errorText = '请输入有效价格和数量';
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
      ok = await appState.addInvestment(code: code, name: name, price: price, qty: qty, curr: curr, assetType: assetType);
    } else {
      final code = widget.item?.code ?? '';
      if (code.isEmpty) {
        setState(() {
          _saving = false;
          _errorText = '未找到持仓代码';
        });
        return;
      }
      final mode = _isTrade ? _tradeMode : (_isBuy ? 'buy' : 'sell');
      if (mode == 'adjust') {
        final adjustStr = _adjustController.text.trim();
        final adjustVal = double.tryParse(adjustStr);
        if (adjustVal == null) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效调整金额';
          });
          return;
        }
        final qtyVal = widget.item?.qty ?? 0;
        final priceVal = widget.item?.price ?? 0;
        ok = await appState.modifyInvestment(code: code, qty: qtyVal, price: priceVal, adjustment: adjustVal);
      } else if (mode == 'buy') {
        final priceStr = _priceController.text.trim();
        final qtyStr = _qtyController.text.trim();
        price = double.tryParse(priceStr);
        qty = double.tryParse(qtyStr);
        if (price == null || price <= 0 || qty == null || qty <= 0) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效价格和数量';
          });
          return;
        }
        ok = await appState.buyInvestment(code: code, price: price, qty: qty);
      } else {
        final priceStr = _priceController.text.trim();
        final qtyStr = _qtyController.text.trim();
        price = double.tryParse(priceStr);
        qty = double.tryParse(qtyStr);
        if (price == null || price <= 0 || qty == null || qty <= 0) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效价格和数量';
          });
          return;
        }
        ok = await appState.sellInvestment(code: code, price: price, qty: qty);
      }
    }

    if (!ok) {
      setState(() {
        _saving = false;
        _errorText = '保存失败，请稍后重试';
      });
      return;
    }

    if (mounted) Navigator.pop(context);
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
                    style: TextStyle(color: AppTheme.textPrimary, fontSize: FontSize.base),
                  ),
                  const SizedBox(height: 2),
                  Row(
                    children: [
                      _marketBadge(typeName),
                      const SizedBox(width: 6),
                      Text(
                        code,
                        style: TextStyle(color: AppTheme.textTertiary, fontSize: FontSize.sm),
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
            onTap: () => setState(() => _tradeMode = 'buy'),
            borderRadius: BorderRadius.circular(10),
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 10),
              decoration: BoxDecoration(
                color: _tradeMode == 'buy' ? AppTheme.accent : Colors.transparent,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: _tradeMode == 'buy' ? AppTheme.accent : AppTheme.border,
                  width: 1,
                ),
              ),
              child: Text(
                '买入',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: _tradeMode == 'buy' ? AppTheme.textPrimary : AppTheme.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: InkWell(
            onTap: () => setState(() => _tradeMode = 'sell'),
            borderRadius: BorderRadius.circular(10),
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 10),
              decoration: BoxDecoration(
                color: _tradeMode == 'sell' ? AppTheme.danger : Colors.transparent,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: _tradeMode == 'sell' ? AppTheme.danger : AppTheme.border,
                  width: 1,
                ),
              ),
              child: Text(
                '卖出',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: _tradeMode == 'sell' ? AppTheme.textPrimary : AppTheme.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: InkWell(
            onTap: () => setState(() => _tradeMode = 'adjust'),
            borderRadius: BorderRadius.circular(10),
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 10),
              decoration: BoxDecoration(
                color: _tradeMode == 'adjust' ? AppTheme.accent : Colors.transparent,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: _tradeMode == 'adjust' ? AppTheme.accent : AppTheme.border,
                  width: 1,
                ),
              ),
              child: Text(
                '调整',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: _tradeMode == 'adjust' ? AppTheme.textPrimary : AppTheme.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final title = _isAdd
        ? '添加投资资产'
        : _isTrade
            ? '买入 / 卖出 / 调整'
            : _isBuy
                ? '买入'
                : '卖出';
    final actionColor = (_isTrade ? _tradeMode == 'buy' : _isBuy)
        ? AppTheme.accent
        : (_isTrade && _tradeMode == 'adjust' ? AppTheme.accent : AppTheme.danger);
    final canSave = !_saving && (!_isAdd || _selected != null);

    return Dialog(
      backgroundColor: Colors.transparent,
      insetPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(18),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
          child: Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: AppTheme.bgCard.withOpacity(AppTheme.isLight ? 0.98 : 0.88),
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
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontSize: FontSize.xxl,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.textPrimary,
                  ),
                ),
                const SizedBox(height: Spacing.lg),
                if (_isAdd) ...[
                  TextField(
                    controller: _queryController,
                    onChanged: _onQueryChanged,
                    style: TextStyle(color: AppTheme.textPrimary),
                    decoration: const InputDecoration(
                      labelText: '股票代码/名称',
                      hintText: '输入代码或名称搜索',
                    ),
                  ),
                  if (_searching)
                    Padding(
                      padding: EdgeInsets.only(top: 8),
                      child: Text('搜索中...', style: TextStyle(color: AppTheme.textTertiary)),
                    ),
                  _buildSearchResults(),
                  if (_selected != null) ...[
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Text(
                          '已选择：',
                          style: TextStyle(color: AppTheme.textSecondary, fontSize: FontSize.sm),
                        ),
                        Text(
                          '${_selected?['name']}  ',
                          style: TextStyle(color: AppTheme.textSecondary, fontSize: FontSize.sm),
                        ),
                        _marketBadge(_selected?['type_name'] ?? ''),
                        const SizedBox(width: 6),
                        Text(
                          _formatDisplayCode(_selected?['code'] ?? ''),
                          style: TextStyle(color: AppTheme.textSecondary, fontSize: FontSize.sm),
                        ),
                      ],
                    ),
                  ],
                  const SizedBox(height: Spacing.lg),
                ] else ...[
                  Text(
                    '${widget.item?.name ?? ''} · ${_formatDisplayCode(widget.item?.code ?? '')}',
                    style: TextStyle(color: AppTheme.textSecondary, fontSize: FontSize.base),
                  ),
                  const SizedBox(height: Spacing.lg),
                ],
                _buildTradeToggle(),
                if (_isTrade) const SizedBox(height: Spacing.lg),
                if (_isTrade && _isAdjust) ...[
                  TextField(
                    controller: _adjustController,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
                    style: TextStyle(color: AppTheme.textPrimary),
                    decoration: const InputDecoration(labelText: '调整金额'),
                  ),
                ] else ...[
                  TextField(
                    controller: _priceController,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    style: TextStyle(color: AppTheme.textPrimary),
                    decoration: const InputDecoration(labelText: '价格'),
                  ),
                  const SizedBox(height: Spacing.lg),
                  TextField(
                    controller: _qtyController,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    style: TextStyle(color: AppTheme.textPrimary),
                    decoration: const InputDecoration(labelText: '数量'),
                  ),
                ],
                if (_errorText != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    _errorText!,
                    style: TextStyle(color: AppTheme.danger, fontSize: FontSize.base),
                  ),
                ],
                const SizedBox(height: Spacing.xl),
                Row(
                  children: [
                    Expanded(
                      child: TextButton(
                        onPressed: _saving ? null : () => Navigator.pop(context),
                        child: Text('取消'),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(backgroundColor: actionColor),
                        onPressed: canSave ? _submit : null,
                        child: _saving
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(strokeWidth: 2),
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
    );
  }
}
