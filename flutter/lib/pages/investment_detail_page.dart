import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../config/theme.dart';
import '../models/portfolio.dart';
import '../providers/app_state.dart';
import '../widgets/invest_trade_dialog.dart';

/// 投资持仓详情页
class InvestmentDetailPage extends StatefulWidget {
  final PortfolioItem item;

  const InvestmentDetailPage({super.key, required this.item});

  @override
  State<InvestmentDetailPage> createState() => _InvestmentDetailPageState();
}

class _InvestmentDetailPageState extends State<InvestmentDetailPage> {
  // 跨页面实例的静态缓存，App 生命周期内有效
  static final Map<String, List<Map<String, dynamic>>> _cache = {};

  List<Map<String, dynamic>> _transactions = [];
  bool _transactionsLoaded = false;

  String get _cacheKey => widget.item.code;

  @override
  void initState() {
    super.initState();
    _loadTransactions();
  }

  Future<void> _loadTransactions({bool forceRemote = false}) async {
    if (forceRemote) {
      _cache.remove(_cacheKey);
    }
    // 有缓存先展示，后台静默刷新
    final cached = _cache[_cacheKey];
    if (cached != null && mounted) {
      setState(() {
        _transactions = cached;
        _transactionsLoaded = true;
      });
    }

    try {
      final appState = context.read<AppState>();
      final records = await appState.getInvestmentTransactions(
        widget.item.code,
      );
      if (!mounted) return;
      final parsed = records
          .map((r) => Map<String, dynamic>.from(r as Map))
          .toList();
      _cache[_cacheKey] = parsed;
      setState(() {
        _transactions = parsed;
        _transactionsLoaded = true;
      });
    } catch (_) {
      if (mounted && !_transactionsLoaded) {
        setState(() => _transactionsLoaded = true);
      }
    }
  }

  Future<void> _refreshData() async {
    final appState = context.read<AppState>();
    await appState.refreshPortfolio();
    await _loadTransactions(forceRemote: true);
  }

  PortfolioItem get _currentItem {
    final appState = context.read<AppState>();
    return appState.portfolio.firstWhere(
      (p) => p.code == widget.item.code,
      orElse: () => widget.item,
    );
  }

  // ── 金额格式化（千分位）──
  String _formatAmount(
    double amount, {
    int decimals = 2,
    bool trimTrailingZeros = false,
  }) {
    final abs = amount.abs();
    final fixed = abs.toStringAsFixed(decimals);
    final parts = fixed.split('.');
    final intPart = parts.first;
    var decPart = parts.length > 1 ? parts[1] : '';
    final raw = intPart.toString();
    final buf = StringBuffer();
    for (var i = 0; i < raw.length; i++) {
      final posFromEnd = raw.length - i;
      buf.write(raw[i]);
      if (posFromEnd > 1 && posFromEnd % 3 == 1) buf.write(',');
    }
    if (decimals > 0) {
      if (trimTrailingZeros) {
        decPart = decPart.replaceFirst(RegExp(r'0+$'), '');
      }
      if (decPart.isNotEmpty) {
        buf.write('.');
        buf.write(decPart);
      }
    }
    return buf.toString();
  }

  String _formatSignedAmount(
    double amount,
    String symbol, {
    bool alwaysShowSign = false,
    int decimals = 2,
  }) {
    final sign = amount < 0 ? '-' : (alwaysShowSign && amount > 0 ? '+' : '');
    return '$sign$symbol${_formatAmount(amount, decimals: decimals)}';
  }

  String _formatDisplayQty(double value) {
    return _formatAmount(value, decimals: 2, trimTrailingZeros: true);
  }

  String _formatDisplayCode(String code) {
    const customMap = {'ft_LU1116320737': 'BLK'};
    if (customMap.containsKey(code)) return customMap[code]!;
    var c = code.trim();
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

  // ── 资产类型标签 ──
  String _assetTypeLabel(String assetType) {
    switch (assetType.toLowerCase()) {
      case 'hk':
        return '港股';
      case 'us':
        return '美股';
      case 'fund':
        return '基金';
      default:
        return 'A股';
    }
  }

  ({Color fg, Color bg}) _assetTypeStyle(String assetType) {
    switch (_assetTypeLabel(assetType)) {
      case '港股':
        return (fg: const Color(0xFFE06B3A), bg: const Color(0x1FE06B3A));
      case '美股':
        return (fg: const Color(0xFF5B8DEF), bg: const Color(0x1F5B8DEF));
      case '基金':
        return (fg: const Color(0xFFB57ADB), bg: const Color(0x1FB57ADB));
      default:
        return (fg: const Color(0xFF3ECF82), bg: const Color(0x1F3ECF82));
    }
  }

  // ── 删除确认弹窗 ──
  Future<void> _showDeleteConfirmation(PortfolioItem item) async {
    final confirmed = await showDialog<bool>(
      context: context,
      barrierDismissible: true,
      barrierColor: const Color(0x9E000000),
      builder: (dialogContext) => Center(
        child: Material(
          color: Colors.transparent,
          child: Container(
            width: 300,
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(18),
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: AppTheme.dialogGradient,
              ),
              border: Border.all(color: AppTheme.border),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppTheme.danger.withValues(alpha: 0.12),
                  ),
                  alignment: Alignment.center,
                  child: Icon(
                    Icons.delete_outline_rounded,
                    size: 24,
                    color: AppTheme.danger,
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  '确定要删除 ${item.displayName} 的持仓吗？\n此操作将清空该资产的所有持仓数据，且无法撤销。',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.dmSans(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: AppTheme.textPrimary,
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 20),
                Row(
                  children: [
                    Expanded(
                      child: GestureDetector(
                        onTap: () => Navigator.of(dialogContext).pop(false),
                        child: Container(
                          height: 40,
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: AppTheme.border),
                          ),
                          alignment: Alignment.center,
                          child: Text(
                            '取消',
                            style: GoogleFonts.dmSans(
                              fontSize: 14,
                              fontWeight: FontWeight.w500,
                              color: AppTheme.textSecondary,
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: GestureDetector(
                        onTap: () => Navigator.of(dialogContext).pop(true),
                        child: Container(
                          height: 40,
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(10),
                            color: AppTheme.danger,
                          ),
                          alignment: Alignment.center,
                          child: Text(
                            '确认删除',
                            style: GoogleFonts.dmSans(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              color: Colors.white,
                            ),
                          ),
                        ),
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

    if (confirmed == true && mounted) {
      final appState = context.read<AppState>();
      await appState.deleteInvestment(code: item.code);
      if (mounted) Navigator.of(context).pop();
    }
  }

  // ── 顶部导航栏 ──
  Widget _buildHeader(BuildContext context, PortfolioItem item) {
    final topPadding = defaultTargetPlatform == TargetPlatform.macOS ? 36.0 : 18.0;
    return Padding(
      padding: EdgeInsets.fromLTRB(18, topPadding, 18, 14),
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
                item.displayName,
                style: GoogleFonts.dmSans(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary,
                ),
              ),
            ),
          ),
          Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: () => _showDeleteConfirmation(item),
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
                child: Text(
                  '⋯',
                  style: GoogleFonts.dmSans(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                    color: AppTheme.textDim,
                    letterSpacing: 1,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ── P&L rate tag ──
  Widget _buildRateTag(double? rate) {
    if (rate == null) return const SizedBox.shrink();
    final isPositive = rate >= 0;
    final color = isPositive ? AppTheme.danger : AppTheme.success;
    final sign = isPositive ? '+' : '';
    final text = '$sign${rate.toStringAsFixed(2)}%';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(4),
        color: color.withValues(alpha: 0.08),
        border: Border.all(color: color, width: 1),
      ),
      child: Text(
        text,
        style: GoogleFonts.jetBrainsMono(
          fontSize: 9,
          fontWeight: FontWeight.w500,
          color: color,
        ),
      ),
    );
  }

  // ── Hero 卡片 ──
  Widget _buildHeroCard(BuildContext context, PortfolioItem item) {
    final isLight = AppTheme.isLight;
    final sym = _currencySymbol(item.curr);
    final marketValue = item.value ?? 0;
    final costPrice = item.displayCostPrice ?? item.price;
    final currentPrice = item.currentPrice ?? 0;
    final typeStyle = _assetTypeStyle(item.assetType);
    final displayCode = _formatDisplayCode(item.code);
    final displayQty = _formatDisplayQty(item.qty);

    return Container(
      width: double.infinity,
      decoration: AppTheme.heroDecoration,
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
                    const Color(
                      0xFF5B8DEF,
                    ).withValues(alpha: isLight ? 0.08 : 0.14),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),
          // 顶部高光线
          Positioned(
            top: 0,
            left: 20,
            right: 20,
            child: Container(
              height: 1,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    Colors.transparent,
                    const Color(0xFF5B8DEF).withValues(alpha: 0.3),
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
                // Row 1: name + market value
                Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Expanded(
                      child: Text(
                        item.displayName,
                        style: GoogleFonts.dmSans(
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                    ),
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.baseline,
                      textBaseline: TextBaseline.alphabetic,
                      children: [
                        Text(
                          '市值',
                          style: GoogleFonts.dmSans(
                            fontSize: 10,
                            color: AppTheme.heroLabelColor,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          '$sym${_formatAmount(marketValue, decimals: 0)}',
                          style: GoogleFonts.jetBrainsMono(
                            fontSize: 15,
                            fontWeight: FontWeight.w600,
                            color: AppTheme.heroValueColor,
                            letterSpacing: -0.3,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                // Row 2: asset type tag + code + qty
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 6,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(4),
                        color: typeStyle.bg,
                      ),
                      child: Text(
                        _assetTypeLabel(item.assetType),
                        style: GoogleFonts.dmSans(
                          fontSize: 9,
                          fontWeight: FontWeight.w600,
                          color: typeStyle.fg,
                          letterSpacing: 0.5,
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      displayCode,
                      style: GoogleFonts.jetBrainsMono(
                        fontSize: 10,
                        color: AppTheme.textDim,
                      ),
                    ),
                    const Spacer(),
                    Text(
                      '× $displayQty股',
                      style: GoogleFonts.jetBrainsMono(
                        fontSize: 10,
                        fontWeight: FontWeight.w500,
                        color: AppTheme.textMuted,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                // Divider
                Container(height: 1, color: AppTheme.borderSubtle),
                const SizedBox(height: 14),
                // 2×2 Metrics Grid
                _buildMetricsGrid(item, sym, currentPrice, costPrice),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ── 2×2 指标网格 ──
  Widget _buildMetricsGrid(
    PortfolioItem item,
    String sym,
    double currentPrice,
    double costPrice,
  ) {
    final dayPnl = item.dayPnl ?? 0;
    final totalPnl = item.totalPnl ?? 0;
    final currentPriceColor = dayPnl == 0
        ? AppTheme.textPrimary
        : (dayPnl > 0 ? AppTheme.danger : AppTheme.success);

    return IntrinsicHeight(
      child: Row(
        children: [
          // Left column
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildMetricItem(
                  label: '当日盈亏',
                  value: dayPnl,
                  sym: sym,
                  rate: item.dayPnlRate,
                  integer: true,
                  valueColor: dayPnl >= 0 ? AppTheme.danger : AppTheme.success,
                  alwaysShowSign: true,
                ),
                const SizedBox(height: 12),
                _buildMetricItem(
                  label: '累计盈亏',
                  value: totalPnl,
                  sym: sym,
                  rate: item.totalPnlRate,
                  integer: true,
                  valueColor: totalPnl >= 0
                      ? AppTheme.danger
                      : AppTheme.success,
                  alwaysShowSign: true,
                ),
              ],
            ),
          ),
          // Vertical divider
          Container(
            width: 1,
            margin: const EdgeInsets.symmetric(horizontal: 16),
            color: AppTheme.borderSubtle,
          ),
          // Right column
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildMetricItem(
                  label: '现价',
                  value: currentPrice,
                  sym: sym,
                  rate: null,
                  valueColor: currentPriceColor,
                  decimals: item.assetType.toLowerCase() == 'fund'
                      ? 4
                      : (currentPrice.abs() < 10 ? 3 : 2),
                  trimTrailingZeros: item.assetType.toLowerCase() == 'fund',
                ),
                const SizedBox(height: 12),
                _buildMetricItem(
                  label: '成本价',
                  value: costPrice,
                  sym: sym,
                  rate: null,
                  valueColor: AppTheme.textPrimary,
                  decimals: item.assetType.toLowerCase() == 'fund'
                      ? 4
                      : (costPrice.abs() < 10 ? 3 : 2),
                  trimTrailingZeros: item.assetType.toLowerCase() == 'fund',
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricItem({
    required String label,
    required double value,
    required String sym,
    required double? rate,
    required Color valueColor,
    bool alwaysShowSign = false,
    bool integer = false,
    int decimals = 2,
    bool trimTrailingZeros = false,
  }) {
    final displayDecimals = integer ? 0 : decimals;
    final sign = value < 0 ? '-' : (alwaysShowSign && value > 0 ? '+' : '');
    final valueStr =
        '$sign$sym${_formatAmount(value, decimals: displayDecimals, trimTrailingZeros: trimTrailingZeros)}';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: GoogleFonts.dmSans(
            fontSize: 10,
            color: AppTheme.heroLabelColor,
          ),
        ),
        const SizedBox(height: 2),
        Row(
          children: [
            Flexible(
              child: Text(
                valueStr,
                style: GoogleFonts.jetBrainsMono(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: valueColor,
                  letterSpacing: -0.3,
                ),
              ),
            ),
            if (rate != null) ...[
              const SizedBox(width: 6),
              _buildRateTag(rate),
            ],
          ],
        ),
      ],
    );
  }

  // ── 操作按钮 ──
  Widget _buildActionButtons(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _buildActionButton(
            label: '加仓',
            color: AppTheme.danger,
            onTap: () async {
              await showInvestTradeSheet(
                context: context,
                mode: 'buy',
                item: _currentItem,
                hostContext: context,
                onPortfolioChanged: _refreshData,
                presentation: InvestTradeDialogPresentation.centered,
              );
            },
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _buildActionButton(
            label: '减仓',
            color: AppTheme.success,
            onTap: () async {
              await showInvestTradeSheet(
                context: context,
                mode: 'sell',
                item: _currentItem,
                hostContext: context,
                onPortfolioChanged: _refreshData,
                presentation: InvestTradeDialogPresentation.centered,
              );
            },
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _buildActionButton(
            label: '修正',
            color: AppTheme.textSecondary,
            onTap: () async {
              await showInvestTradeSheet(
                context: context,
                mode: 'trade',
                item: _currentItem,
                hostContext: context,
                onPortfolioChanged: _refreshData,
                initialTradeMode: 'adjust',
                presentation: InvestTradeDialogPresentation.centered,
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildActionButton({
    required String label,
    required Color color,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 42,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(10),
          color: AppTheme.isLight
              ? Colors.white.withValues(alpha: 0.72)
              : const Color(0xFF14161F),
          border: Border.all(color: color.withValues(alpha: 0.25)),
        ),
        alignment: Alignment.center,
        child: Text(
          label,
          style: GoogleFonts.dmSans(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: color,
          ),
        ),
      ),
    );
  }

  // ── 交易记录区域 ──
  Widget _buildTransactionSection(String sym) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '交易记录',
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
            color: AppTheme.isLight ? AppTheme.bgCard : const Color(0xA81A1D25),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppTheme.border),
          ),
          child: !_transactionsLoaded
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
              : _transactions.isEmpty
              ? Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 28,
                  ),
                  child: Column(
                    children: [
                      Icon(
                        Icons.receipt_long_rounded,
                        size: 28,
                        color: AppTheme.textDim,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '暂无交易记录',
                        style: GoogleFonts.dmSans(
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '加仓或减仓后，记录会显示在这里',
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
                      for (var i = 0; i < _transactions.length; i++)
                        _buildTransactionItem(
                          _transactions[i],
                          sym,
                          i == _transactions.length - 1,
                        ),
                    ],
                  ),
                ),
        ),
      ],
    );
  }

  // ── 单条交易记录 ──
  Widget _buildTransactionItem(
    Map<String, dynamic> rec,
    String sym,
    bool isLast,
  ) {
    final rawType = (rec['type'] as String?) ?? '';
    final type = _resolveTransactionType(rawType, rec);
    final amount = ((rec['amount'] as num?) ?? 0).toDouble();
    final price = ((rec['price'] as num?) ?? 0).toDouble();
    final qty = ((rec['qty'] as num?) ?? 0).toDouble();
    final pnl = ((rec['pnl'] as num?) ?? 0).toDouble();
    final note = (rec['note'] as String?) ?? '';
    final timeStr = (rec['time'] as String?) ?? '';
    final time = DateTime.tryParse(timeStr) ?? DateTime.now();

    // 颜色规则
    Color dotColor;
    Color textColor;
    switch (type) {
      case '加仓':
        dotColor = AppTheme.danger;
        textColor = AppTheme.danger;
        break;
      case '减仓':
        dotColor = AppTheme.success;
        textColor = AppTheme.success;
        break;
      case '分红':
        dotColor = AppTheme.gold;
        textColor = AppTheme.gold;
        break;
      case '手续费':
      case '税金':
        dotColor = AppTheme.textTertiary;
        textColor = AppTheme.textTertiary;
        break;
      default:
        dotColor = AppTheme.accent;
        textColor = AppTheme.textSecondary;
    }

    // 详情
    String detail;
    if (type == '加仓' || type == '减仓') {
      final qtyStr = _formatDisplayQty(qty);
      final priceStr = _formatAmount(
        price,
        decimals: price.abs() < 10 ? 3 : 2,
        trimTrailingZeros: true,
      );
      detail = '$priceStr × $qtyStr股';
      if (type == '减仓' && pnl != 0) {
        detail =
            '$detail · 盈亏 ${_formatSignedAmount(pnl, sym, alwaysShowSign: true)}';
      }
    } else if (type == '成本修正') {
      final beforePrice = ((rec['before_price'] as num?) ?? 0).toDouble();
      final afterPrice = ((rec['after_price'] as num?) ?? 0).toDouble();
      if (beforePrice > 0 || afterPrice > 0) {
        detail = _buildCorrectionDetail(
          label: '成本价',
          beforeText: _formatAmount(
            beforePrice,
            decimals: beforePrice.abs() < 10 ? 3 : 2,
            trimTrailingZeros: true,
          ),
          afterText: _formatAmount(
            afterPrice,
            decimals: afterPrice.abs() < 10 ? 3 : 2,
            trimTrailingZeros: true,
          ),
          note: note,
        );
      } else {
        detail = note;
      }
    } else if (type == '数量修正') {
      final beforeQty = ((rec['before_qty'] as num?) ?? 0).toDouble();
      final afterQty = ((rec['after_qty'] as num?) ?? 0).toDouble();
      if (beforeQty > 0 || afterQty > 0) {
        detail = _buildCorrectionDetail(
          label: '持仓数量',
          beforeText: '${_formatDisplayQty(beforeQty)}股',
          afterText: '${_formatDisplayQty(afterQty)}股',
          note: note,
        );
      } else {
        detail = note;
      }
    } else if (type == '持仓修正') {
      final beforePrice = ((rec['before_price'] as num?) ?? 0).toDouble();
      final afterPrice = ((rec['after_price'] as num?) ?? 0).toDouble();
      final beforeQty = ((rec['before_qty'] as num?) ?? 0).toDouble();
      final afterQty = ((rec['after_qty'] as num?) ?? 0).toDouble();
      final parts = <String>[];
      if (beforePrice > 0 || afterPrice > 0) {
        parts.add(
          '成本价 ${_formatAmount(beforePrice, decimals: beforePrice.abs() < 10 ? 3 : 2, trimTrailingZeros: true)} -> '
          '${_formatAmount(afterPrice, decimals: afterPrice.abs() < 10 ? 3 : 2, trimTrailingZeros: true)}',
        );
      }
      if (beforeQty > 0 || afterQty > 0) {
        parts.add(
          '持仓数量 ${_formatDisplayQty(beforeQty)}股 -> ${_formatDisplayQty(afterQty)}股',
        );
      }
      detail = parts.join(' · ');
      if (note.trim().isNotEmpty) {
        detail = detail.isEmpty ? note.trim() : '$detail · ${note.trim()}';
      } else {
        detail = detail.isEmpty ? '持仓信息已修正' : detail;
      }
    } else {
      detail = note;
    }

    // 金额显示
    final amountStr = _formatTransactionAmount(type, amount, sym);

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
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 彩色圆点
          Container(
            width: 7,
            height: 7,
            margin: const EdgeInsets.only(top: 6),
            decoration: BoxDecoration(shape: BoxShape.circle, color: dotColor),
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
                        type,
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
                      amountStr,
                      style: GoogleFonts.jetBrainsMono(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: textColor,
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
                        detail,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: GoogleFonts.jetBrainsMono(
                          fontSize: 11,
                          color: type == '减仓' && pnl != 0
                              ? AppTheme.textTertiary
                              : AppTheme.textDim,
                        ),
                      ),
                    ),
                    Text(
                      _formatTime(time),
                      style: GoogleFonts.dmSans(
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

  String _resolveTransactionType(String rawType, Map<String, dynamic> rec) {
    if (rawType == '成本修正' || rawType == '数量修正' || rawType == '持仓修正') {
      return rawType;
    }
    final note = (rec['note'] as String? ?? '').trim();
    if (rawType == '手动调整') {
      if (note.contains('成本')) return '成本修正';
      if (note.contains('数量')) return '数量修正';
    }
    return rawType;
  }

  String _buildCorrectionDetail({
    required String label,
    required String beforeText,
    required String afterText,
    required String note,
  }) {
    final trimmedNote = note.trim();
    final base = '$label $beforeText -> $afterText';
    if (trimmedNote.isEmpty) return base;
    return '$base · $trimmedNote';
  }

  String _formatTransactionAmount(String type, double amount, String sym) {
    switch (type) {
      case '加仓':
        return _formatSignedAmount(amount.abs(), sym, alwaysShowSign: true);
      case '减仓':
        return _formatSignedAmount(-amount.abs(), sym);
      case '分红':
        return _formatSignedAmount(amount.abs(), sym, alwaysShowSign: true);
      case '手续费':
      case '税金':
        return _formatSignedAmount(-amount.abs(), sym);
      case '成本修正':
      case '数量修正':
      case '持仓修正':
      case '手动调整':
        return amount.abs() <= 1e-9
            ? '--'
            : _formatSignedAmount(amount, sym, alwaysShowSign: amount > 0);
      default:
        return _formatSignedAmount(amount, sym, alwaysShowSign: amount > 0);
    }
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
              final item = appState.portfolio.cast<PortfolioItem?>().firstWhere(
                (p) => p?.code == widget.item.code,
                orElse: () => null,
              );

              // 资产被删除时自动返回
              if (item == null) {
                WidgetsBinding.instance.addPostFrameCallback((_) {
                  if (context.mounted) Navigator.of(context).pop();
                });
                return const SizedBox.shrink();
              }

              final sym = _currencySymbol(item.curr);

              return Column(
                children: [
                  _buildHeader(context, item),
                  Expanded(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.fromLTRB(16, 4, 16, 48),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _buildHeroCard(context, item),
                          const SizedBox(height: 16),
                          _buildActionButtons(context),
                          const SizedBox(height: 22),
                          _buildTransactionSection(sym),
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
