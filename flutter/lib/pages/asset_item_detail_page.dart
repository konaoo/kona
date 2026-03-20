import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../models/asset.dart';
import '../providers/app_state.dart';
import '../config/theme.dart';
import '../widgets/asset_adjust_dialog.dart';

/// 单次调整记录
class _AdjustRecord {
  final String mode; // 'add' | 'sub'
  final double delta;
  final String note;
  final DateTime time;
  final double balanceAfter;

  const _AdjustRecord({
    required this.mode,
    required this.delta,
    required this.note,
    required this.time,
    required this.balanceAfter,
  });
}

/// 单个资产详情页（现金/其他/负债）
class AssetItemDetailPage extends StatefulWidget {
  final int assetId;
  final String assetType; // cash | other | liability

  const AssetItemDetailPage({
    super.key,
    required this.assetId,
    required this.assetType,
  });

  @override
  State<AssetItemDetailPage> createState() => _AssetItemDetailPageState();
}

class _AssetItemDetailPageState extends State<AssetItemDetailPage> {
  // 跨页面实例的静态缓存，App 生命周期内有效
  static final Map<String, List<_AdjustRecord>> _cache = {};

  List<_AdjustRecord> _history = [];
  bool _historyLoaded = false;

  String get _cacheKey => '${widget.assetType}/${widget.assetId}';

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    // 有缓存先展示，后台静默刷新
    final cached = _cache[_cacheKey];
    if (cached != null && mounted) {
      setState(() {
        _history = cached;
        _historyLoaded = true;
      });
    }

    try {
      final appState = context.read<AppState>();
      final records = await appState.getAssetAdjustments(
        type: widget.assetType,
        id: widget.assetId,
      );
      if (!mounted) return;
      final parsed = records.map((r) {
        final map = r as Map<String, dynamic>;
        return _AdjustRecord(
          mode: map['mode'] as String,
          delta: (map['delta'] as num).toDouble(),
          note: (map['note'] as String?) ?? '',
          time: DateTime.tryParse(map['created_at'] as String? ?? '') ?? DateTime.now(),
          balanceAfter: (map['balance_after'] as num).toDouble(),
        );
      }).toList();
      _cache[_cacheKey] = parsed;
      setState(() {
        _history = parsed;
        _historyLoaded = true;
      });
    } catch (_) {
      if (mounted && !_historyLoaded) setState(() => _historyLoaded = true);
    }
  }

  // ── 类型标签 ──
  String get _typeLabel {
    switch (widget.assetType) {
      case 'cash':
        return '现金账户';
      case 'other':
        return '其他资产';
      case 'liability':
        return '我的负债';
      default:
        return '资产账户';
    }
  }

  List<Asset> _getAssets(AppState s) {
    switch (widget.assetType) {
      case 'cash':
        return s.cashAssets;
      case 'other':
        return s.otherAssets;
      case 'liability':
        return s.liabilities;
      default:
        return [];
    }
  }

  // ── 金额格式化（千分位 + 两位小数）──
  String _formatAmount(double amount) {
    final abs = amount.abs();
    final intPart = abs.floor();
    final decPart = ((abs - intPart) * 100).round();
    final raw = intPart.toString();
    final buf = StringBuffer();
    for (var i = 0; i < raw.length; i++) {
      final posFromEnd = raw.length - i;
      buf.write(raw[i]);
      if (posFromEnd > 1 && posFromEnd % 3 == 1) buf.write(',');
    }
    buf.write('.');
    buf.write(decPart.toString().padLeft(2, '0'));
    return buf.toString();
  }

  // ── 时间格式化 ──
  String _formatTime(DateTime t) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final yesterday = today.subtract(const Duration(days: 1));
    final day = DateTime(t.year, t.month, t.day);
    final hm =
        '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
    if (day == today) return '今天 $hm';
    if (day == yesterday) return '昨天 $hm';
    return '${t.month}月${t.day}日 $hm';
  }

  // ── 货币符号 ──
  String _currencySymbol(String curr) {
    switch (curr.toUpperCase()) {
      case 'USD':
        return r'$';
      case 'HKD':
        return 'HK\$';
      default:
        return '¥';
    }
  }

  // ── 打开编辑弹窗并等待结果 ──
  Future<void> _showAdjustDialog(Asset asset) async {
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      barrierDismissible: false,
      barrierColor: const Color(0x9E000000),
      builder: (_) => AssetAdjustDialog(
        asset: asset,
        assetType: widget.assetType,
        hostContext: context,
        onDeleteSuccess: () => Navigator.of(context).pop(),
      ),
    );

    if (result != null && mounted) {
      setState(() {
        _history.insert(
          0,
          _AdjustRecord(
            mode: result['mode'] as String,
            delta: result['delta'] as double,
            note: (result['note'] as String).isEmpty
                ? (result['mode'] == 'add' ? '增加' : '减少')
                : result['note'] as String,
            time: DateTime.now(),
            balanceAfter: result['balanceAfter'] as double,
          ),
        );
        _cache[_cacheKey] = List.from(_history); // 同步更新缓存
      });
    }
  }

  // ── 顶部导航栏 ──
  Widget _buildHeader(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 18, 18, 14),
      child: Row(
        children: [
          Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: () => Navigator.of(context).pop(),
              borderRadius: BorderRadius.circular(10),
              child: Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: AppTheme.surface2,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppTheme.border),
                ),
                alignment: Alignment.center,
                child: Icon(
                  Icons.arrow_back_ios_new_rounded,
                  size: 16,
                  color: AppTheme.textPrimary,
                ),
              ),
            ),
          ),
          Expanded(
            child: Center(
              child: Text(
                title,
                style: GoogleFonts.dmSans(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary,
                ),
              ),
            ),
          ),
          const SizedBox(width: 32),
        ],
      ),
    );
  }

  // ── 余额卡片 ──
  Widget _buildBalanceCard(BuildContext context, Asset asset) {
    final isLight = AppTheme.isLight;
    final sym = _currencySymbol(asset.curr);
    final formattedAmount = _formatAmount(asset.amount.abs());

    final cardGradient = LinearGradient(
      begin: const Alignment(-0.6, -0.6),
      end: const Alignment(1, 1),
      colors: isLight
          ? [const Color(0xFFDDE8FF), const Color(0xFFC8D5F0)]
          : [const Color(0xFF1A2744), const Color(0xFF0F1829)],
    );
    final borderColor = const Color(0x2E5B8DEF);
    final labelColor =
        isLight ? AppTheme.textSecondary : const Color(0xFF9AA3B7);
    final symColor =
        isLight ? AppTheme.textSecondary : const Color(0xFF8B909F);
    final amountColor = AppTheme.heroValueColor;
    final editBg = isLight ? const Color(0x14000000) : const Color(0x12FFFFFF);
    final editBorder =
        isLight ? const Color(0x14000000) : const Color(0x1AFFFFFF);
    final editIconColor =
        isLight ? AppTheme.textSecondary : const Color(0xFF8B909F);

    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        gradient: cardGradient,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: borderColor),
        boxShadow: [
          BoxShadow(
            color: isLight
                ? const Color(0x1A222C48)
                : Colors.black.withValues(alpha: 0.35),
            blurRadius: isLight ? 20 : 26,
            offset: const Offset(0, 12),
          ),
        ],
      ),
      child: Stack(
        children: [
          // 右上角光晕
          Positioned(
            top: -20,
            right: -20,
            child: Container(
              width: 90,
              height: 90,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    const Color(0xFF5B8DEF).withValues(
                      alpha: isLight ? 0.08 : 0.14,
                    ),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 类型标签
                Row(
                  children: [
                    Container(
                      width: 5,
                      height: 5,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: AppTheme.accent,
                        boxShadow: isLight
                            ? []
                            : [
                                BoxShadow(
                                  color:
                                      AppTheme.accent.withValues(alpha: 0.6),
                                  blurRadius: 4,
                                ),
                              ],
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      _typeLabel,
                      style: GoogleFonts.dmSans(
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                        color: labelColor,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                // 金额
                RichText(
                  text: TextSpan(
                    children: [
                      TextSpan(
                        text: sym,
                        style: GoogleFonts.jetBrainsMono(
                          fontSize: 20,
                          fontWeight: FontWeight.w500,
                          color: symColor,
                        ),
                      ),
                      TextSpan(
                        text: formattedAmount,
                        style: GoogleFonts.jetBrainsMono(
                          fontSize: 34,
                          fontWeight: FontWeight.w600,
                          color: amountColor,
                          letterSpacing: -1,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          // 右上角编辑图标
          Positioned(
            top: 14,
            right: 14,
            child: GestureDetector(
              onTap: () => _showAdjustDialog(asset),
              child: Container(
                width: 28,
                height: 28,
                decoration: BoxDecoration(
                  color: editBg,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: editBorder),
                ),
                alignment: Alignment.center,
                child: Icon(
                  Icons.edit_outlined,
                  size: 13,
                  color: editIconColor,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ── 单条历史记录 ──
  Widget _buildHistoryItem(_AdjustRecord rec, String sym, bool isLast) {
    final isAdd = rec.mode == 'add';
    // 中文惯例：增加=红，减少=绿（与 H5 一致）
    final dotColor = isAdd ? AppTheme.danger : AppTheme.success;
    final deltaColor = isAdd ? AppTheme.danger : AppTheme.success;
    final sign = isAdd ? '+' : '−';
    final deltaStr = '$sign$sym${_formatAmount(rec.delta)}';
    final balanceStr = '$sym${_formatAmount(rec.balanceAfter)}';

    return Container(
      decoration: BoxDecoration(
        border: isLast
            ? null
            : Border(
                bottom: BorderSide(color: AppTheme.borderSubtle, width: 1),
              ),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // 彩色圆点
          Container(
            width: 7,
            height: 7,
            margin: const EdgeInsets.only(top: 1),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: dotColor,
            ),
          ),
          const SizedBox(width: 12),
          // 内容
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        rec.note.isEmpty ? (isAdd ? '增加' : '减少') : rec.note,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: GoogleFonts.dmSans(
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      deltaStr,
                      style: GoogleFonts.jetBrainsMono(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: deltaColor,
                        letterSpacing: -0.3,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 3),
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        _formatTime(rec.time),
                        style: GoogleFonts.dmSans(
                          fontSize: 11,
                          color: AppTheme.textTertiary,
                        ),
                      ),
                    ),
                    Text(
                      balanceStr,
                      style: GoogleFonts.jetBrainsMono(
                        fontSize: 11,
                        color: AppTheme.textTertiary,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ── 调整记录列表 ──
  Widget _buildHistorySection(String sym) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '调整记录',
          style: GoogleFonts.dmSans(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: AppTheme.textTertiary,
            letterSpacing: 0.7,
          ),
        ),
        const SizedBox(height: 10),
        Container(
          width: double.infinity,
          decoration: BoxDecoration(
            color: AppTheme.isLight
                ? AppTheme.bgCard
                : const Color(0xA81A1D25),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppTheme.border),
          ),
          child: !_historyLoaded
              ? const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16, vertical: 28),
                  child: Center(
                    child: SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                  ),
                )
              : _history.isEmpty
              ? Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 28,
                  ),
                  child: Column(
                    children: [
                      Icon(
                        Icons.history_rounded,
                        size: 28,
                        color: AppTheme.textDim,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '暂无调整记录',
                        style: GoogleFonts.dmSans(
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '点击右上角编辑图标进行调整',
                        style: GoogleFonts.dmSans(
                          fontSize: 12,
                          color: AppTheme.textMuted,
                        ),
                      ),
                    ],
                  ),
                )
              : ClipRRect(
                  borderRadius: BorderRadius.circular(13),
                  child: Column(
                    children: [
                      for (var i = 0; i < _history.length; i++)
                        _buildHistoryItem(
                          _history[i],
                          sym,
                          i == _history.length - 1,
                        ),
                    ],
                  ),
                ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    context.watch<AppState>();

    return Scaffold(
      backgroundColor: AppTheme.bgPrimary,
      body: Container(
        decoration: BoxDecoration(
          gradient: RadialGradient(
            center: const Alignment(0.8, -1.1),
            radius: 1.1,
            colors: AppTheme.isLight
                ? [const Color(0x145B8DEF), const Color(0x00EEF2F8)]
                : [const Color(0x1F5B8DEF), const Color(0x000D0E12)],
          ),
        ),
        child: SafeArea(
          bottom: false,
          child: Consumer<AppState>(
            builder: (context, appState, _) {
              final assets = _getAssets(appState);
              final asset = assets
                  .cast<Asset?>()
                  .firstWhere(
                    (a) => a?.id == widget.assetId,
                    orElse: () => null,
                  );

              // 资产被删除时自动返回
              if (asset == null) {
                WidgetsBinding.instance.addPostFrameCallback((_) {
                  if (context.mounted) Navigator.of(context).pop();
                });
                return const SizedBox.shrink();
              }

              final sym = _currencySymbol(asset.curr);

              return Column(
                children: [
                  _buildHeader(context, asset.displayName),
                  Expanded(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.fromLTRB(16, 4, 16, 48),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildBalanceCard(context, asset),
                          const SizedBox(height: 22),
                          _buildHistorySection(sym),
                        ],
                      ),
                    ),
                  ),
                ],
              );
            },
          ),
        ),
      ),
    );
  }
}
