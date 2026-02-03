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

  Timer? _debounce;
  bool _saving = false;
  bool _searching = false;
  String? _errorText;
  List<dynamic> _results = [];
  Map<String, dynamic>? _selected;

  bool get _isAdd => widget.mode == 'add';
  bool get _isBuy => widget.mode == 'buy';

  @override
  void dispose() {
    _queryController.dispose();
    _priceController.dispose();
    _qtyController.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  String _formatDisplayCode(String code) {
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

    final priceStr = _priceController.text.trim();
    final qtyStr = _qtyController.text.trim();
    final price = double.tryParse(priceStr);
    final qty = double.tryParse(qtyStr);

    if (price == null || price <= 0 || qty == null || qty <= 0) {
      setState(() => _errorText = '请输入有效价格和数量');
      return;
    }

    setState(() {
      _saving = true;
      _errorText = null;
    });

    bool ok = false;
    if (_isAdd) {
      final raw = _queryController.text.trim();
      if (_selected == null && raw.isEmpty) {
        setState(() {
          _saving = false;
          _errorText = '请选择股票或输入代码';
        });
        return;
      }
      final code = _selected?['code'] ?? raw;
      final name = _selected?['name'] ?? raw;
      final curr = _selected?['currency'];
      ok = await appState.addInvestment(code: code, name: name, price: price, qty: qty, curr: curr);
    } else {
      final code = widget.item?.code ?? '';
      if (code.isEmpty) {
        setState(() {
          _saving = false;
          _errorText = '未找到持仓代码';
        });
        return;
      }
      if (_isBuy) {
        ok = await appState.buyInvestment(code: code, price: price, qty: qty);
      } else {
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
                    style: const TextStyle(color: AppTheme.textPrimary, fontSize: FontSize.base),
                  ),
                  const SizedBox(height: 2),
                  Row(
                    children: [
                      _marketBadge(typeName),
                      const SizedBox(width: 6),
                      Text(
                        code,
                        style: const TextStyle(color: AppTheme.textTertiary, fontSize: FontSize.sm),
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

  @override
  Widget build(BuildContext context) {
    final title = _isAdd
        ? '添加投资资产'
        : _isBuy
            ? '买入'
            : '卖出';
    final actionColor = _isBuy ? AppTheme.accent : AppTheme.danger;

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
              color: AppTheme.bgCard.withOpacity(0.88),
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: Colors.white.withOpacity(0.08), width: 1),
              gradient: const LinearGradient(
                colors: [Color(0xCC1A2744), Color(0xB30F1829)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
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
                    style: const TextStyle(color: AppTheme.textPrimary),
                    decoration: const InputDecoration(
                      labelText: '股票代码/名称',
                      hintText: '输入代码或名称搜索',
                    ),
                  ),
                  if (_searching)
                    const Padding(
                      padding: EdgeInsets.only(top: 8),
                      child: Text('搜索中...', style: TextStyle(color: AppTheme.textTertiary)),
                    ),
                  _buildSearchResults(),
                  if (_selected != null) ...[
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Text(
                          '已选择：',
                          style: TextStyle(color: AppTheme.textSecondary, fontSize: FontSize.sm),
                        ),
                        Text(
                          '${_selected?['name']}  ',
                          style: const TextStyle(color: AppTheme.textSecondary, fontSize: FontSize.sm),
                        ),
                        _marketBadge(_selected?['type_name'] ?? ''),
                        const SizedBox(width: 6),
                        Text(
                          _formatDisplayCode(_selected?['code'] ?? ''),
                          style: const TextStyle(color: AppTheme.textSecondary, fontSize: FontSize.sm),
                        ),
                      ],
                    ),
                  ],
                  const SizedBox(height: Spacing.lg),
                ] else ...[
                  Text(
                    '${widget.item?.name ?? ''} · ${_formatDisplayCode(widget.item?.code ?? '')}',
                    style: const TextStyle(color: AppTheme.textSecondary, fontSize: FontSize.base),
                  ),
                  const SizedBox(height: Spacing.lg),
                ],
                TextField(
                  controller: _priceController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  style: const TextStyle(color: AppTheme.textPrimary),
                  decoration: const InputDecoration(labelText: '价格'),
                ),
                const SizedBox(height: Spacing.lg),
                TextField(
                  controller: _qtyController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  style: const TextStyle(color: AppTheme.textPrimary),
                  decoration: const InputDecoration(labelText: '数量'),
                ),
                if (_errorText != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    _errorText!,
                    style: const TextStyle(color: AppTheme.danger, fontSize: FontSize.base),
                  ),
                ],
                const SizedBox(height: Spacing.xl),
                Row(
                  children: [
                    Expanded(
                      child: TextButton(
                        onPressed: _saving ? null : () => Navigator.pop(context),
                        child: const Text('取消'),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(backgroundColor: actionColor),
                        onPressed: _saving ? null : _submit,
                        child: _saving
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Text('保存'),
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
