import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../config/theme.dart';
import '../providers/app_state.dart';
import '../widgets/invest_trade_dialog.dart';
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

  bool _recognizing = false;
  String? _errorText;
  String? _selectedImageName;
  List<Map<String, dynamic>> _candidates = const [];
  Map<String, dynamic>? _selectedCandidate;

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

  String _candidateKey(Map<String, dynamic> item) {
    final code = item['code']?.toString().trim() ?? '';
    final name = item['name']?.toString().trim() ?? '';
    final qty = item['qty']?.toString().trim() ?? '';
    final price = item['price']?.toString().trim() ?? '';
    return '$code|$name|$qty|$price';
  }

  Future<void> _pickAndParseScreenshot() async {
    if (_recognizing) return;
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
            final name = item['name']?.toString().trim() ?? '';
            return name.isNotEmpty;
          })
          .toList();
      setState(() {
        _recognizing = false;
        _candidates = candidates;
        _selectedCandidate = candidates.isEmpty ? null : candidates.first;
      });
      if (candidates.isEmpty) {
        setState(() {
          _errorText = '这张图里没有识别出可添加的资产，请换一张更清晰的持仓截图';
        });
        return;
      }
      TopToast.showInfo(context, '已生成识别结果，请点编辑进入添加资产弹窗');
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _recognizing = false;
        _errorText = '截图识别失败，请稍后重试';
      });
      TopToast.showError(context, _errorText!);
    }
  }

  void _selectCandidate(Map<String, dynamic> item) {
    setState(() {
      _selectedCandidate = item;
      _errorText = null;
    });
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

  bool _candidateIsComplete(Map<String, dynamic> item) {
    final name = item['name']?.toString().trim() ?? '';
    final code = item['code']?.toString().trim() ?? '';
    final qty = _asDouble(item['qty']);
    final price = _asDouble(item['price']);
    return name.isNotEmpty &&
        code.isNotEmpty &&
        qty != null &&
        qty > 0 &&
        price != null &&
        price > 0;
  }

  String _typeNameForItem(Map<String, dynamic> item) {
    final assetType = item['asset_type']?.toString().trim().toLowerCase() ?? '';
    final code = item['code']?.toString().trim().toLowerCase() ?? '';
    if (assetType == 'fund' || code.startsWith('f_') || code.startsWith('ft_')) {
      return '基金';
    }
    if (assetType == 'hk' || code.startsWith('hk') || code.endsWith('.hk')) {
      return '港股';
    }
    if (assetType == 'us' || code.startsWith('gb_')) {
      return '美股';
    }
    if (assetType == 'a' ||
        code.startsWith('sh') ||
        code.startsWith('sz') ||
        code.startsWith('bj')) {
      return 'A股';
    }
    return '资产';
  }

  String _assetTypeForItem(Map<String, dynamic> item) {
    switch (_typeNameForItem(item)) {
      case '基金':
        return 'fund';
      case '港股':
        return 'hk';
      case '美股':
        return 'us';
      case 'A股':
        return 'a';
      default:
        return '';
    }
  }

  String _currencyCodeForItem(Map<String, dynamic> item) {
    switch (_typeNameForItem(item)) {
      case '港股':
        return 'HKD';
      case '美股':
        return 'USD';
      default:
        return 'CNY';
    }
  }

  String _currencySymbolForItem(Map<String, dynamic> item) {
    switch (_typeNameForItem(item)) {
      case '港股':
        return 'HK\$';
      case '美股':
        return '\$';
      default:
        return '¥';
    }
  }

  String _quantityUnit(Map<String, dynamic> item) {
    final typeName = _typeNameForItem(item);
    final code = item['code']?.toString().trim().toLowerCase() ?? '';
    final name = item['name']?.toString().trim() ?? '';
    final isFund =
        typeName == '基金' || code.startsWith('f_') || code.startsWith('ft_') || name.contains('基金');
    return isFund ? '份' : '股';
  }

  Map<String, dynamic>? _buildInitialSelectedAsset(Map<String, dynamic> item) {
    final code = item['code']?.toString().trim() ?? '';
    final name = item['name']?.toString().trim() ?? '';
    if (code.isEmpty || name.isEmpty) return null;
    return {
      'code': code,
      'name': name,
      'currency': _currencyCodeForItem(item),
      'asset_type': _assetTypeForItem(item),
      'type_name': _typeNameForItem(item),
    };
  }

  String _initialSearchQueryForItem(Map<String, dynamic> item) {
    final displayCode = _formatDisplayCode(item['code']?.toString() ?? '');
    if (displayCode.isNotEmpty) return displayCode;
    return item['name']?.toString().trim() ?? '';
  }

  Future<void> _openAddAssetDialog(Map<String, dynamic> item) async {
    _selectCandidate(item);
    await showInvestTradeSheet<void>(
      context: context,
      mode: 'add',
      presentation: InvestTradeDialogPresentation.centered,
      initialSelectedAsset: _buildInitialSelectedAsset(item),
      initialSearchQuery: _initialSearchQueryForItem(item),
      initialPrice: _asDouble(item['price']),
      initialQty: _asDouble(item['qty']),
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

  Widget _buildCandidateCard(Map<String, dynamic> item, bool selected) {
    final confidence = ((_asDouble(item['confidence']) ?? 0) * 100).clamp(0, 100);
    final currSymbol = _currencySymbolForItem(item);
    final rawNote = item['note']?.toString().trim() ?? '';
    final note = rawNote.contains('本地演示') ? '' : rawNote;
    final displayCode = _formatDisplayCode(item['code']?.toString() ?? '');
    final qtyValue = _asDouble(item['qty']);
    final qtyText = qtyValue == null ? '待补' : _formatNumber(qtyValue);
    final qtyUnit = _quantityUnit(item);
    final complete = _candidateIsComplete(item);

    return InkWell(
      onTap: () => _selectCandidate(item),
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
                          _buildTag(_typeNameForItem(item)),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              displayCode.isEmpty ? '待补代码' : displayCode,
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
                  width: 132,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        '买入价 $currSymbol${item['price'] ?? '待补'}',
                        style: _dm(size: 12, color: AppTheme.textSecondary),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                Expanded(
                  child: Text(
                    complete
                        ? '当前识别准确率 ${confidence.toStringAsFixed(0)}%，点编辑可直接带入添加资产弹窗'
                        : '当前识别准确率 ${confidence.toStringAsFixed(0)}%，有缺项时点编辑进入添加资产弹窗补齐',
                    style: _dm(size: 11, color: AppTheme.textMuted),
                  ),
                ),
                IconButton(
                  onPressed: () => _openAddAssetDialog(item),
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

  @override
  Widget build(BuildContext context) {
    final selectedCandidateKey =
        _selectedCandidate == null ? '' : _candidateKey(_selectedCandidate!);
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
                        icon: Icon(
                          _recognizing ? Icons.hourglass_top : Icons.photo_library_outlined,
                        ),
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
                    '截图最好包含资产名称、代码、数量、买入价；缺的字段可以在添加资产弹窗里补。',
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
                    _candidateKey(item) == selectedCandidateKey,
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Text(
                '点每条结果右侧的编辑，就会直接打开原来的添加资产弹窗；识别到的内容会自动带进去，没有的字段你再手动补。',
                style: _dm(
                  size: 12,
                  weight: FontWeight.w600,
                  color: AppTheme.textMuted,
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
    );
  }
}
