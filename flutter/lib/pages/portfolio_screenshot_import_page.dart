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
  bool _submitting = false;
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

  List<Map<String, dynamic>> _mergeCandidates(
    List<Map<String, dynamic>> existing,
    List<Map<String, dynamic>> incoming,
  ) {
    final merged = List<Map<String, dynamic>>.from(existing);
    final seen = existing.map(_candidateKey).toSet();
    for (final item in incoming) {
      final key = _candidateKey(item);
      if (seen.contains(key)) continue;
      seen.add(key);
      merged.add(item);
    }
    return merged;
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
      final previousCount = _candidates.length;
      final mergedCandidates = _mergeCandidates(_candidates, candidates);
      setState(() {
        _recognizing = false;
        if (candidates.isNotEmpty) {
          _candidates = mergedCandidates;
          _selectedCandidate = candidates.first;
        }
      });
      if (candidates.isEmpty) {
        setState(() {
          _errorText = '识别失败可能是因为主人没钱买API，麻烦请使用手动录入😭';
        });
        return;
      }
      TopToast.showInfo(
        context,
        mergedCandidates.length > previousCount
            ? '已追加识别结果，请继续编辑后提交'
            : '这张图没有新的识别结果',
      );
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _recognizing = false;
        _errorText = '识别失败可能是因为主人没钱买API，麻烦请使用手动录入😭';
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
    final itemKey = _candidateKey(item);
    final result = await showInvestTradeSheet<Map<String, dynamic>>(
      context: context,
      mode: 'add',
      presentation: InvestTradeDialogPresentation.centered,
      draftOnly: true,
      initialSelectedAsset: _buildInitialSelectedAsset(item),
      initialSearchQuery: _initialSearchQueryForItem(item),
      initialPrice: _asDouble(item['price']),
      initialQty: _asDouble(item['qty']),
      preserveDraftInputsOnClear: true,
      onDeletePressed: () {
        if (!mounted) return;
        final itemKey = _candidateKey(item);
        final nextCandidates = _candidates
            .where((candidate) => _candidateKey(candidate) != itemKey)
            .toList();
        setState(() {
          _candidates = nextCandidates;
          if (_candidateKey(_selectedCandidate ?? const {}) == itemKey) {
            _selectedCandidate = nextCandidates.isEmpty ? null : nextCandidates.first;
          }
          _errorText = nextCandidates.isEmpty ? '这条识别结果已删除' : null;
        });
      },
    );
    if (!mounted || result == null) return;
    final updatedItem = Map<String, dynamic>.from(item)
      ..['name'] =
          (result['name']?.toString().trim() ?? item['name']?.toString() ?? '')
      ..['code'] =
          (result['code']?.toString().trim() ?? item['code']?.toString() ?? '')
      ..['qty'] = result['qty'] ?? item['qty']
      ..['price'] = result['price'] ?? item['price']
      ..['curr'] =
          (result['curr']?.toString().trim() ?? item['curr']?.toString() ?? '')
      ..['asset_type'] = (result['asset_type']?.toString().trim() ??
          item['asset_type']?.toString() ??
          '')
      ..['type_name'] =
          (result['type_name']?.toString().trim() ?? item['type_name']?.toString() ?? '');
    final nextCandidates = _candidates
        .map((candidate) => _candidateKey(candidate) == itemKey ? updatedItem : candidate)
        .toList();
    setState(() {
      _candidates = nextCandidates;
      if (_candidateKey(_selectedCandidate ?? const {}) == itemKey) {
        _selectedCandidate = updatedItem;
      }
      _errorText = null;
    });
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

  bool get _canSubmitCandidates =>
      !_submitting &&
      _candidates.isNotEmpty &&
      _candidates.every(_candidateIsComplete);

  Future<void> _submitCandidates() async {
    if (!_canSubmitCandidates) return;
    final appState = context.read<AppState>();
    setState(() {
      _submitting = true;
      _errorText = null;
    });
    var successCount = 0;
    for (var i = 0; i < _candidates.length; i += 1) {
      final item = _candidates[i];
      final code = item['code']?.toString().trim() ?? '';
      final name = item['name']?.toString().trim() ?? '';
      final qty = _asDouble(item['qty']);
      final price = _asDouble(item['price']);
      if (code.isEmpty || name.isEmpty || qty == null || price == null) {
        setState(() {
          _submitting = false;
          _errorText = '还有资产信息没补完整，请先编辑后再提交';
        });
        return;
      }
      final result = await appState.addInvestment(
        code: code,
        name: name,
        price: price,
        qty: qty,
        curr: item['curr']?.toString(),
        assetType: item['asset_type']?.toString(),
        awaitRefresh: false,
      );
      if (!mounted) return;
      if (!result.ok) {
        setState(() {
          _submitting = false;
          _errorText = successCount > 0
              ? '前 $successCount 条已添加，后续提交失败：${result.message ?? '请稍后重试'}'
              : (result.message ?? '提交失败，请稍后重试');
        });
        TopToast.showError(context, _errorText!);
        return;
      }
      successCount += 1;
    }
    await appState.refreshAll(force: true);
    if (!mounted) return;
    TopToast.showSuccess(context, '添加成功');
    Navigator.of(context).maybePop();
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
    final currSymbol = _currencySymbolForItem(item);
    final rawNote = item['note']?.toString().trim() ?? '';
    final note = rawNote.contains('本地演示') ? '' : rawNote;
    final displayCode = _formatDisplayCode(item['code']?.toString() ?? '');
    final qtyValue = _asDouble(item['qty']);
    final qtyText = qtyValue == null ? '待补' : _formatNumber(qtyValue);
    final qtyUnit = _quantityUnit(item);

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
                    '识别不正确可以点击编辑修正',
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
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 96),
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
                    '截图最好包含资产名称、代码、数量、买入价。',
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
      bottomNavigationBar: _candidates.isEmpty
          ? null
          : SafeArea(
              top: false,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                child: FilledButton(
                  onPressed: _canSubmitCandidates ? _submitCandidates : null,
                  child: Text(_submitting ? '正在提交' : '提交'),
                ),
              ),
            ),
    );
  }
}
