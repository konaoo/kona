import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../config/theme.dart';
import '../providers/app_state.dart';
import '../widgets/top_toast.dart';

class PortfolioScreenshotImportPage extends StatefulWidget {
  const PortfolioScreenshotImportPage({super.key});

  @override
  State<PortfolioScreenshotImportPage> createState() =>
      _PortfolioScreenshotImportPageState();
}

class _PortfolioScreenshotImportPageState
    extends State<PortfolioScreenshotImportPage> {
  final ImagePicker _imagePicker = ImagePicker();
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _codeController = TextEditingController();
  final TextEditingController _qtyController = TextEditingController();
  final TextEditingController _priceController = TextEditingController();

  bool _recognizing = false;
  bool _saving = false;
  String? _errorText;
  String? _selectedImageName;
  List<Map<String, dynamic>> _candidates = const [];
  Map<String, dynamic>? _selectedCandidate;

  @override
  void dispose() {
    _nameController.dispose();
    _codeController.dispose();
    _qtyController.dispose();
    _priceController.dispose();
    super.dispose();
  }

  TextStyle _dm({
    double? size,
    FontWeight? weight,
    Color? color,
    double? letterSpacing,
  }) {
    return GoogleFonts.dmSans(
      fontSize: size,
      fontWeight: weight,
      color: color,
      letterSpacing: letterSpacing,
    );
  }

  TextStyle _mono({
    double? size,
    FontWeight? weight,
    Color? color,
  }) {
    return GoogleFonts.jetBrainsMono(
      fontSize: size,
      fontWeight: weight,
      color: color,
    );
  }

  Future<void> _pickAndParseScreenshot() async {
    if (_recognizing || _saving) return;
    final file = await _imagePicker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 85,
      maxWidth: 1800,
    );
    if (file == null || !mounted) return;

    setState(() {
      _recognizing = true;
      _errorText = null;
      _selectedImageName = file.name;
    });

    try {
      final payload = await context.read<AppState>().parsePortfolioAssetScreenshot(
            file.path,
          );
      if (!mounted) return;
      final rawItems = (payload['items'] as List?) ?? const [];
      final candidates = rawItems
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .where((item) {
            final code = item['code']?.toString().trim() ?? '';
            final name = item['name']?.toString().trim() ?? '';
            return code.isNotEmpty && name.isNotEmpty;
          })
          .toList();
      setState(() {
        _recognizing = false;
        _candidates = candidates;
        _selectedCandidate = null;
      });
      if (candidates.isEmpty) {
        setState(() {
          _errorText = '这张图里没有识别出可添加的资产，请换一张更清晰的持仓截图';
        });
        return;
      }
      _applyCandidate(candidates.first);
      TopToast.showInfo(context, '已生成识别结果，请确认后保存');
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _recognizing = false;
        _errorText = '截图识别失败，请稍后重试';
      });
      TopToast.showError(context, _errorText!);
    }
  }

  void _applyCandidate(Map<String, dynamic> item) {
    final qty = _asDouble(item['qty']);
    final price = _asDouble(item['price']);
    setState(() {
      _selectedCandidate = item;
      _nameController.text = item['name']?.toString() ?? '';
      _codeController.text = _formatDisplayCode(item['code']?.toString() ?? '');
      _qtyController.text = qty == null ? '' : _formatNumber(qty);
      _priceController.text = price == null ? '' : _formatNumber(price);
      _errorText = null;
    });
  }

  Future<void> _openEditDialog(Map<String, dynamic> item) async {
    _applyCandidate(item);
    final nameController = TextEditingController(text: _nameController.text);
    final qtyController = TextEditingController(text: _qtyController.text);
    final priceController = TextEditingController(text: _priceController.text);
    String? dialogError;

    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              backgroundColor: AppTheme.bgCard,
              title: Text(
                '编辑识别结果',
                style: _dm(
                  size: 18,
                  weight: FontWeight.w700,
                  color: AppTheme.textPrimary,
                ),
              ),
              content: SizedBox(
                width: 360,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildField(label: '资产名称', controller: nameController),
                    const SizedBox(height: 12),
                    _buildField(
                      label: '数量',
                      controller: qtyController,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    ),
                    const SizedBox(height: 12),
                    _buildField(
                      label: '买入价',
                      controller: priceController,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    ),
                    if ((dialogError ?? '').isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Text(
                        dialogError!,
                        style: _dm(
                          size: 12,
                          weight: FontWeight.w600,
                          color: AppTheme.danger,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(dialogContext).pop(),
                  child: Text(
                    '取消',
                    style: _dm(size: 13, color: AppTheme.textMuted),
                  ),
                ),
                FilledButton(
                  onPressed: () {
                    final name = nameController.text.trim();
                    final qty = double.tryParse(qtyController.text.trim());
                    final price = double.tryParse(priceController.text.trim());
                    if (name.isEmpty || qty == null || qty <= 0 || price == null || price <= 0) {
                      setDialogState(() {
                        dialogError = '请把资产名称、数量、买入价填完整';
                      });
                      return;
                    }
                    Navigator.of(dialogContext).pop({
                      'name': name,
                      'qty': qty,
                      'price': price,
                    });
                  },
                  child: Text(
                    '保存修改',
                    style: _dm(size: 13, weight: FontWeight.w700),
                  ),
                ),
              ],
            );
          },
        );
      },
    );

    nameController.dispose();
    qtyController.dispose();
    priceController.dispose();

    if (result == null || !mounted) return;
    _updateCandidateDraft(
      item,
      name: result['name'] as String,
      qty: result['qty'] as double,
      price: result['price'] as double,
    );
  }

  void _updateCandidateDraft(
    Map<String, dynamic> item, {
    required String name,
    required double qty,
    required double price,
  }) {
    final rawCode = item['code']?.toString() ?? '';
    final updated = Map<String, dynamic>.from(item)
      ..['name'] = name
      ..['qty'] = qty
      ..['price'] = price;
    final nextCandidates = _candidates
        .map((candidate) => (candidate['code']?.toString() ?? '') == rawCode
            ? updated
            : candidate)
        .toList();
    setState(() {
      _candidates = nextCandidates;
      _selectedCandidate = updated;
      _nameController.text = name;
      _codeController.text = _formatDisplayCode(rawCode);
      _qtyController.text = _formatNumber(qty);
      _priceController.text = _formatNumber(price);
      _errorText = null;
    });
  }

  Future<void> _submit() async {
    if (_saving) return;
    final name = _nameController.text.trim();
    final code = _codeController.text.trim();
    final qty = double.tryParse(_qtyController.text.trim());
    final price = double.tryParse(_priceController.text.trim());
    if (name.isEmpty || code.isEmpty || qty == null || qty <= 0 || price == null || price <= 0) {
      setState(() {
        _errorText = '请先把名称、代码、数量、成本价填完整';
      });
      return;
    }
    setState(() {
      _saving = true;
      _errorText = null;
    });
    final candidate = _selectedCandidate;
    final result = await context.read<AppState>().addInvestment(
          code: code,
          name: name,
          qty: qty,
          price: price,
          curr: candidate?['curr']?.toString(),
          assetType: candidate?['asset_type']?.toString(),
        );
    if (!mounted) return;
    setState(() => _saving = false);
    if (!result.ok) {
      setState(() {
        _errorText = result.message ?? '保存失败，请稍后重试';
      });
      TopToast.showError(context, _errorText!);
      return;
    }
    TopToast.showSuccess(context, '已添加资产');
    Navigator.of(context).pop(true);
  }

  double? _asDouble(dynamic value) {
    if (value == null) return null;
    if (value is num) return value.toDouble();
    return double.tryParse(value.toString().trim());
  }

  String _formatNumber(double value) {
    final text = value.toStringAsFixed(value.abs() >= 1000 ? 0 : 4);
    return text.replaceFirst(RegExp(r'0+$'), '').replaceFirst(RegExp(r'\.$'), '');
  }

  String _formatDisplayCode(String code) {
    var c = code.trim();
    if (c.isEmpty) return '';
    final lower = c.toLowerCase();
    if (lower.startsWith('gb_')) {
      c = c.substring(3).toUpperCase();
    } else if (lower.startsWith('f_')) {
      c = c.substring(2);
    } else if (lower.startsWith('ft_')) {
      c = c.substring(3);
    } else if (lower.startsWith('sh') ||
        lower.startsWith('sz') ||
        lower.startsWith('bj') ||
        lower.startsWith('hk')) {
      c = c.substring(2);
    }
    if (c.toUpperCase().endsWith('.HK')) {
      c = c.substring(0, c.length - 3);
    }
    return c;
  }

  String _currencySymbol(String curr) {
    switch (curr.trim().toUpperCase()) {
      case 'HKD':
        return 'HK\$';
      case 'USD':
        return '\$';
      default:
        return '¥';
    }
  }

  String _quantityUnit(Map<String, dynamic> item) {
    final assetType = item['asset_type']?.toString().trim().toLowerCase() ?? '';
    final typeName = item['type_name']?.toString().trim() ?? '';
    final code = item['code']?.toString().trim().toLowerCase() ?? '';
    final isFund = assetType == 'fund' ||
        typeName.contains('基金') ||
        code.startsWith('f_') ||
        code.startsWith('ft_');
    return isFund ? '份' : '股';
  }

  Widget _buildCandidateCard(Map<String, dynamic> item, bool selected) {
    final confidence = ((_asDouble(item['confidence']) ?? 0) * 100).clamp(0, 100);
    final currSymbol = _currencySymbol(item['curr']?.toString() ?? 'CNY');
    final rawNote = item['note']?.toString().trim() ?? '';
    final note = rawNote.contains('本地演示') ? '' : rawNote;
    final displayCode = _formatDisplayCode(item['code']?.toString() ?? '');
    final qtyValue = _asDouble(item['qty']);
    final qtyText = qtyValue == null ? '待确认' : _formatNumber(qtyValue);
    final qtyUnit = _quantityUnit(item);
    return InkWell(
      onTap: () => _applyCandidate(item),
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: selected
              ? AppTheme.accent.withValues(alpha: AppTheme.isLight ? 0.14 : 0.20)
              : AppTheme.bgCard,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: selected ? AppTheme.accent : AppTheme.border,
            width: selected ? 1.4 : 1.0,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      RichText(
                        text: TextSpan(
                          children: [
                            TextSpan(
                              text: item['name']?.toString() ?? '--',
                              style: _dm(
                                size: 15,
                                weight: FontWeight.w700,
                                color: AppTheme.textPrimary,
                              ),
                            ),
                            TextSpan(
                              text: '  x $qtyText $qtyUnit',
                              style: _dm(
                                size: 12,
                                color: AppTheme.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          _buildTag(item['type_name']?.toString() ?? '资产'),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              displayCode.isEmpty ? '--' : displayCode,
                              style: _mono(size: 12, color: AppTheme.textMuted),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 12),
                SizedBox(
                  width: 124,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        '买入价 $currSymbol${item['price'] ?? '待确认'}',
                        style: _dm(size: 12, color: AppTheme.textSecondary),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Expanded(
                  child: Text(
                    '当前识别准确率 ${confidence.toStringAsFixed(0)}%，如果有误请编辑修正',
                    style: _dm(size: 11, color: AppTheme.textMuted),
                  ),
                ),
                IconButton(
                  onPressed: () => _openEditDialog(item),
                  tooltip: '编辑识别结果',
                  visualDensity: VisualDensity.compact,
                  icon: Icon(
                    Icons.edit_outlined,
                    size: 18,
                    color: AppTheme.accent,
                  ),
                ),
              ],
            ),
            if (note.isNotEmpty) ...[
              const SizedBox(height: 10),
              Text(
                note,
                style: _dm(size: 11, color: AppTheme.textMuted),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildTag(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppTheme.accent.withValues(alpha: AppTheme.isLight ? 0.12 : 0.18),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        text,
        style: _dm(
          size: 10,
          weight: FontWeight.w700,
          color: AppTheme.accent,
          letterSpacing: 0.2,
        ),
      ),
    );
  }

  Widget _buildField({
    required String label,
    required TextEditingController controller,
    TextInputType? keyboardType,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: _dm(
            size: 12,
            weight: FontWeight.w600,
            color: AppTheme.textMuted,
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: controller,
          keyboardType: keyboardType,
          decoration: InputDecoration(
            filled: true,
            fillColor: AppTheme.bgCard,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: BorderSide(color: AppTheme.border),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: BorderSide(color: AppTheme.border),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: BorderSide(color: AppTheme.accent, width: 1.2),
            ),
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final selectedCode = _selectedCandidate?['code']?.toString() ?? '';
    return Scaffold(
      backgroundColor: AppTheme.bgPrimary,
      appBar: AppBar(
        title: Text(
          '截图录入',
          style: _dm(
            size: 18,
            weight: FontWeight.w700,
            color: AppTheme.textPrimary,
          ),
        ),
        backgroundColor: AppTheme.bgPrimary,
        foregroundColor: AppTheme.textPrimary,
        elevation: 0,
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.bgCard,
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: AppTheme.border),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      FilledButton.icon(
                        onPressed: _recognizing ? null : _pickAndParseScreenshot,
                        icon: Icon(_recognizing ? Icons.hourglass_top : Icons.photo_library_outlined),
                        label: Text(_recognizing ? '正在识别截图' : '上传图片'),
                      ),
                      if ((_selectedImageName ?? '').isNotEmpty) ...[
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            '已选择：$_selectedImageName',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: _dm(size: 12, color: AppTheme.textMuted),
                          ),
                        ),
                      ],
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    '截图需要包括完整的资产代码/数量/买入价',
                    style: _dm(size: 13, color: AppTheme.textMuted),
                  ),
                ],
              ),
            ),
            if (_candidates.isNotEmpty) ...[
              const SizedBox(height: 18),
              Text(
                '识别结果',
                style: _dm(
                  size: 15,
                  weight: FontWeight.w700,
                  color: AppTheme.textPrimary,
                ),
              ),
              const SizedBox(height: 10),
              ..._candidates.map(
                (item) => Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: _buildCandidateCard(
                    item,
                    (item['code']?.toString() ?? '') == selectedCode,
                  ),
                ),
              ),
            ],
            if ((_errorText ?? '').isNotEmpty) ...[
              const SizedBox(height: 14),
              Text(
                _errorText!,
                style: _dm(
                  size: 13,
                  weight: FontWeight.w600,
                  color: AppTheme.danger,
                ),
              ),
            ],
          ],
        ),
      ),
      bottomNavigationBar: SafeArea(
        minimum: const EdgeInsets.fromLTRB(16, 8, 16, 16),
        child: SizedBox(
          height: 52,
          child: FilledButton(
            onPressed: (_selectedCandidate == null || _saving) ? null : _submit,
            child: Text(_saving ? '正在保存...' : '确认添加资产'),
          ),
        ),
      ),
    );
  }
}
