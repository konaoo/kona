import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../providers/app_state.dart';

class AddAssetDialog extends StatefulWidget {
  final String? fixedAssetType; // cash | other | liability

  const AddAssetDialog({super.key, this.fixedAssetType});

  @override
  State<AddAssetDialog> createState() => _AddAssetDialogState();
}

class _AddAssetDialogState extends State<AddAssetDialog> {
  final _nameController = TextEditingController();
  final _amountController = TextEditingController();

  String _assetType = 'cash';
  bool _saving = false;
  String? _errorText;

  @override
  void initState() {
    super.initState();
    if (widget.fixedAssetType != null) {
      _assetType = widget.fixedAssetType!;
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _amountController.dispose();
    super.dispose();
  }

  String _typeLabel(String type) {
    switch (type) {
      case 'cash':
        return '现金资产';
      case 'other':
        return '其他资产';
      case 'liability':
        return '我的负债';
      default:
        return '资产';
    }
  }

  Future<void> _save(AppState appState) async {
    final name = _nameController.text.trim();
    final amountStr = _amountController.text.trim();

    if (name.isEmpty || amountStr.isEmpty) {
      setState(() => _errorText = '请填写名称和金额');
      return;
    }

    final amount = double.tryParse(amountStr);
    if (amount == null || amount <= 0) {
      setState(() => _errorText = '请输入有效金额');
      return;
    }

    setState(() {
      _saving = true;
      _errorText = null;
    });

    final ok = await appState.addAsset(
      type: _assetType,
      name: name,
      amount: amount,
    );

    if (!ok) {
      setState(() {
        _saving = false;
        _errorText = '保存失败，请稍后重试';
      });
      return;
    }

    if (mounted) Navigator.pop(context);
  }

  Widget _buildTypeChips() {
    final options = const [
      {'value': 'cash', 'label': '现金资产'},
      {'value': 'other', 'label': '其他资产'},
      {'value': 'liability', 'label': '我的负债'},
    ];

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: options.map((opt) {
        final isSelected = _assetType == opt['value'];
        return ChoiceChip(
          label: Text(opt['label']!),
          selected: isSelected,
          onSelected: (_) => setState(() => _assetType = opt['value']!),
          selectedColor: AppTheme.accent.withOpacity(0.25),
          backgroundColor: AppTheme.bgCard,
          labelStyle: TextStyle(
            color: isSelected ? AppTheme.textPrimary : AppTheme.textSecondary,
            fontSize: FontSize.base,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
            side: BorderSide(
              color: isSelected ? AppTheme.accent : AppTheme.border,
              width: 1,
            ),
          ),
        );
      }).toList(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final appState = context.read<AppState>();
    final title = widget.fixedAssetType == null ? '记一笔' : '添加${_typeLabel(_assetType)}';

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
                if (widget.fixedAssetType == null) ...[
                  const Text(
                    '资产类型',
                    style: TextStyle(fontSize: FontSize.base, color: AppTheme.textSecondary),
                  ),
                  const SizedBox(height: 8),
                  _buildTypeChips(),
                  const SizedBox(height: Spacing.lg),
                ],
                TextField(
                  controller: _nameController,
                  style: const TextStyle(color: AppTheme.textPrimary),
                  decoration: const InputDecoration(
                    labelText: '名称',
                    hintText: '例如：工资 / 现金 / 车贷',
                  ),
                ),
                const SizedBox(height: Spacing.lg),
                TextField(
                  controller: _amountController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  style: const TextStyle(color: AppTheme.textPrimary),
                  decoration: const InputDecoration(
                    labelText: '金额',
                    hintText: '请输入金额（正数）',
                  ),
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
                        onPressed: _saving ? null : () => _save(appState),
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
