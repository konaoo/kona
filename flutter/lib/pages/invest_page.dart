import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../providers/app_state.dart';
import '../widgets/invest_trade_dialog.dart';
import '../widgets/fab_scroll_visibility_controller.dart';

// ══════════════════════════════════════════════════
// Cached text styles
// ══════════════════════════════════════════════════
class _S {
  _S._();
  // Hero
  static final heroLabel = GoogleFonts.dmSans(
    fontSize: 12,
    fontWeight: FontWeight.w600,
    letterSpacing: 0.01,
  );
  static final heroCurrSym = GoogleFonts.dmSans(
    fontSize: 18,
    fontWeight: FontWeight.w300,
  );
  static final heroAmount = GoogleFonts.jetBrainsMono(
    fontSize: 30,
    fontWeight: FontWeight.w600,
    letterSpacing: -0.03,
    height: 1.06,
  );
  static final heroDayLabel = GoogleFonts.dmSans(fontSize: 10);
  static final heroDayVal = GoogleFonts.jetBrainsMono(
    fontSize: 15,
    fontWeight: FontWeight.w600,
  );
  static final heroDayPct = GoogleFonts.dmSans(fontSize: 11);
  static final heroStatLabel = GoogleFonts.dmSans(fontSize: 9);
  static final heroStatVal = GoogleFonts.jetBrainsMono(
    fontSize: 12,
    fontWeight: FontWeight.w600,
  );
  static final heroMeta = GoogleFonts.dmSans(fontSize: 11);
  // Tabs
  static final tabText = GoogleFonts.dmSans(
    fontSize: 13,
    fontWeight: FontWeight.w500,
  );
  static final tabTextActive = GoogleFonts.dmSans(
    fontSize: 13,
    fontWeight: FontWeight.w600,
  );
  // Summary bar
  static final sumLabel = GoogleFonts.dmSans(fontSize: 11);
  static final sumVal = GoogleFonts.jetBrainsMono(
    fontSize: 13,
    fontWeight: FontWeight.w600,
  );
  static final sumPct = GoogleFonts.dmSans(
    fontSize: 10,
    fontWeight: FontWeight.w500,
  );
  // Card
  static final cardName = GoogleFonts.dmSans(
    fontSize: 16,
    fontWeight: FontWeight.w600,
  );
  static final cardTag = GoogleFonts.dmSans(
    fontSize: 10,
    fontWeight: FontWeight.w600,
    letterSpacing: 0.03,
  );
  static final cardCode = GoogleFonts.jetBrainsMono(fontSize: 11);
  static final cardMktVal = GoogleFonts.jetBrainsMono(
    fontSize: 15,
    fontWeight: FontWeight.w600,
  );
  static final cardHoldNum = GoogleFonts.jetBrainsMono(fontSize: 11);
  static final cardProgressLabel = GoogleFonts.jetBrainsMono(fontSize: 9);
  static final cardPnlLabel = GoogleFonts.dmSans(fontSize: 10);
  static final cardPnlVal = GoogleFonts.jetBrainsMono(
    fontSize: 15,
    fontWeight: FontWeight.w600,
  );
  static final cardPnlPct = GoogleFonts.dmSans(
    fontSize: 11,
    fontWeight: FontWeight.w500,
  );
}

// Market tag colours
const _tagColors = <String, (Color, Color)>{
  'a': (Color(0xFF3ECF82), Color(0x1E3ECF82)),
  'hk': (Color(0xFFE06B3A), Color(0x1EE06B3A)),
  'us': (Color(0xFF5B8DEF), Color(0x1E5B8DEF)),
  'fund': (Color(0xFFB57ADB), Color(0x1EB57ADB)),
};

const _tagLabels = <String, String>{
  'a': 'A股',
  'us': '美股',
  'hk': '港股',
  'fund': '基金',
};

/// 投资页面 - 持仓列表
class InvestPage extends StatefulWidget {
  final ValueChanged<bool>? onFabVisibilityChanged;

  const InvestPage({super.key, this.onFabVisibilityChanged});

  @override
  State<InvestPage> createState() => InvestPageState();
}

class InvestPageState extends State<InvestPage> {
  final FabScrollVisibilityController _fabVisibilityController =
      FabScrollVisibilityController();
  bool _refreshInFlight = false;

  @override
  void initState() {
    super.initState();
  }

  Future<void> _loadData() async {
    if (_refreshInFlight) return;
    _refreshInFlight = true;
    try {
      await context.read<AppState>().refreshHomeData();
    } finally {
      _refreshInFlight = false;
    }
  }

  void resetFabVisibilityController() {
    _fabVisibilityController.resetVisible();
    widget.onFabVisibilityChanged?.call(true);
  }

  bool _onScrollNotification(ScrollNotification notification) {
    final callback = widget.onFabVisibilityChanged;
    if (callback == null) return false;
    if (notification.depth != 0) return false;

    if (notification is ScrollUpdateNotification) {
      final delta = notification.scrollDelta;
      if (delta != null) {
        final next = _fabVisibilityController.onScrollUpdate(delta);
        if (next != null) callback(next);
      }
      return false;
    }

    if (notification is UserScrollNotification &&
        notification.direction == ScrollDirection.idle) {
      _fabVisibilityController.onScrollIdle();
    }
    return false;
  }

  double _bottomContentPadding(BuildContext context) {
    final safeBottom = MediaQuery.of(context).padding.bottom;
    const navBarHeight = 60.0;
    const fabRegion = 76.0;
    return navBarHeight + safeBottom + fabRegion;
  }

  // ─── Format helpers ──────────────────────────────
  bool _isFundAsset(dynamic item) {
    if (item == null) return false;
    final mt = (item.marketType as String? ?? '').trim().toLowerCase();
    if (mt == 'fund') return true;
    final code = (item.code as String? ?? '').trim().toLowerCase();
    return code.startsWith('f_') || code.startsWith('ft_');
  }

  String _formatDisplayPrice(double value, {dynamic item}) {
    if (_isFundAsset(item)) {
      return value.toStringAsFixed(4).replaceFirst(RegExp(r'\.?0+$'), '');
    }
    return value.toStringAsFixed(value.abs() < 10 ? 3 : 2);
  }

  String _formatDisplayQty(double value) {
    return value.toStringAsFixed(2).replaceFirst(RegExp(r'\.?0+$'), '');
  }

  String _formatDisplayCode(String code) {
    const customMap = {'ft_LU1116320737': 'BLK'};
    if (customMap.containsKey(code)) return customMap[code]!;
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
    if (c.toUpperCase().endsWith('.HK')) c = c.substring(0, c.length - 3);
    return c;
  }

  String _fmtPnl(double value, String symbol) {
    if (value == 0) return '--';
    final prefix = value > 0 ? '+' : '-';
    final intVal = value.toInt().abs();
    final formatted = intVal.toString().replaceAllMapped(
      RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
      (m) => '${m[1]},',
    );
    return '$prefix$symbol$formatted';
  }

  String _fmtPct(double value) {
    if (value == 0) return '--';
    final prefix = value > 0 ? '+' : ''; // value < 0 handled by toStringAsFixed
    return '$prefix${value.toStringAsFixed(2)}%';
  }

  // ─── Build ───────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        return RefreshIndicator(
          onRefresh: _loadData,
          color: AppTheme.accent,
          child: NotificationListener<ScrollNotification>(
            onNotification: _onScrollNotification,
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: EdgeInsets.fromLTRB(
                0,
                0,
                0,
                _bottomContentPadding(context),
              ),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 14),
                child: Column(
                  children: [
                    const SizedBox(height: 10),
                    _buildHeroCard(appState),
                    const SizedBox(height: 12),
                    _buildCategoryTabs(appState),
                    const SizedBox(height: 10),
                    _buildSummaryBar(appState),
                    const SizedBox(height: 10),
                    _buildPortfolioList(appState),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  // ─── Hero Card ─────────────────────────────────
  Widget _buildHeroCard(AppState appState) {
    final dayPnl = appState.investDayPnl;
    final dayPnlRate = appState.investDayPnlRate;
    final dayColor = AppState.getPnlColor(dayPnl);
    final holdPnl = appState.investHoldingPnl;
    final holdPnlRate = appState.investHoldingPnlRate;
    final holdColor = AppState.getPnlColor(holdPnl);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 14),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0x265B8DEF)),
        gradient: const LinearGradient(
          begin: Alignment(-0.6, -1),
          end: Alignment(1, 1),
          colors: [Color(0xFF171C2E), Color(0xFF111520), Color(0xFF0F1219)],
          stops: [0.0, 0.6, 1.0],
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.35),
            blurRadius: 26,
            offset: const Offset(0, 12),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Stack(
            clipBehavior: Clip.none,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '投资总市值',
                    style: _S.heroLabel.copyWith(
                      color: const Color(0xFF9AA3B7),
                    ),
                  ),
                  const SizedBox(height: 12),
                  // Left: total market value + Sync Time underneath
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.baseline,
                        textBaseline: TextBaseline.alphabetic,
                        children: [
                          Text(
                            '¥',
                            style: _S.heroCurrSym.copyWith(
                              color: const Color(0xFF9AA3B7),
                            ),
                          ),
                          const SizedBox(width: 5),
                          FittedBox(
                            fit: BoxFit.scaleDown,
                            alignment: Alignment.centerLeft,
                            child: Text(
                              appState.amountHidden
                                  ? '****'
                                  : appState.formatAmount(
                                      appState.investTotalMV,
                                      prefix: '',
                                    ),
                              style: _S.heroAmount.copyWith(
                                color: const Color(0xFFF0F4FF),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      // Sync text aligned to the left edge of the market value
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          '同步于 刚刚',
                          style: _S.heroMeta.copyWith(
                            color: AppTheme.textMuted,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              // Right: today PnL (aligned with '投资总市值')
              Positioned(
                top: 0,
                right: 0,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      '今日盈亏',
                      style: _S.heroDayLabel.copyWith(
                        color: AppTheme.textMuted,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      appState.amountHidden
                          ? '****'
                          : appState.formatPnlInt(dayPnl),
                      style: _S.heroDayVal.copyWith(color: dayColor),
                    ),
                    Text(
                      appState.amountHidden
                          ? ''
                          : appState.formatPct(dayPnlRate),
                      style: _S.heroDayPct.copyWith(color: dayColor),
                    ),
                  ],
                ),
              ),
            ],
          ),

          const SizedBox(height: 12),

          // Stats grid: 4 columns
          Container(
            padding: const EdgeInsets.only(top: 10),
            decoration: const BoxDecoration(
              border: Border(top: BorderSide(color: Color(0x1AFFFFFF))),
            ),
            child: Row(
              children: [
                _statItem(
                  '持仓盈亏',
                  appState.formatPnlInt(holdPnl),
                  holdColor,
                  true,
                ),
                _statItem(
                  '持仓盈亏率',
                  appState.formatPct(holdPnlRate),
                  holdColor,
                  true,
                ),
                _statItem(
                  '累计盈亏',
                  appState.formatPnlInt(holdPnl),
                  holdColor,
                  true,
                ),
                _statItem(
                  '累计盈亏率',
                  appState.formatPct(holdPnlRate),
                  holdColor,
                  false,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _statItem(String label, String value, Color color, bool hasDivider) {
    return Expanded(
      child: Container(
        decoration: hasDivider
            ? const BoxDecoration(
                border: Border(right: BorderSide(color: Color(0x1AFFFFFF))),
              )
            : null,
        child: Column(
          children: [
            Text(
              label,
              style: _S.heroStatLabel.copyWith(color: AppTheme.textMuted),
            ),
            const SizedBox(height: 3),
            Text(value, style: _S.heroStatVal.copyWith(color: color)),
          ],
        ),
      ),
    );
  }

  // ─── Category Tabs ─────────────────────────────
  Widget _buildCategoryTabs(AppState appState) {
    const categories = [
      ('all', '全部'),
      ('a', 'A股'),
      ('us', '美股'),
      ('hk', '港股'),
      ('fund', '基金'),
    ];
    return Container(
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: Color(0x1AFFFFFF))),
      ),
      child: Row(
        children: categories.map((cat) {
          final isActive = appState.currentCategory == cat.$1;
          return GestureDetector(
            onTap: () => appState.setCategory(cat.$1),
            child: Container(
              padding: const EdgeInsets.fromLTRB(14, 8, 14, 10),
              decoration: BoxDecoration(
                border: Border(
                  bottom: BorderSide(
                    color: isActive
                        ? const Color(0xFFF0F4FF)
                        : Colors.transparent,
                    width: 2,
                  ),
                ),
              ),
              child: Text(
                cat.$2,
                style: (isActive ? _S.tabTextActive : _S.tabText).copyWith(
                  color: isActive
                      ? const Color(0xFFF0F4FF)
                      : const Color(0xFF9AA3B7),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  // ─── Summary Bar ───────────────────────────────
  Widget _buildSummaryBar(AppState appState) {
    if (appState.currentCategory == 'all') return const SizedBox.shrink();

    final filtered = appState.filteredPortfolio;
    if (filtered.isEmpty) return const SizedBox.shrink();

    // Calculate category-level PnL from filtered list
    double catDayPnl = 0, catDayBase = 0;
    double catHoldPnl = 0, catCostAbs = 0;

    for (final item in filtered) {
      final priceInfo = appState.resolvePriceInfoByCode(
        item.code,
        preferred: appState.prices[item.code],
      );
      final hasValidPrice = priceInfo != null && priceInfo.price > 0;
      final price = hasValidPrice
          ? priceInfo.price
          : (item.price > 0 ? item.price : 0.0);
      final rate = appState.getCurrencyRate(item.curr);
      final mv = price * item.qty * rate;
      final cost = item.price * item.qty * rate;
      catHoldPnl += mv - cost + item.adjustment * rate;
      catCostAbs += cost.abs();

      if (appState.isAssetDayPnlEnabled(item, priceInfo: priceInfo) &&
          hasValidPrice) {
        catDayPnl += priceInfo.change * item.qty * rate;
        final yclose = priceInfo.yclose > 0 ? priceInfo.yclose : item.price;
        catDayBase += yclose * item.qty * rate;
      }
    }

    final catDayPnlRate = catDayBase > 0 ? (catDayPnl / catDayBase * 100) : 0.0;
    final catHoldPnlRate = catCostAbs > 0
        ? (catHoldPnl / catCostAbs * 100)
        : 0.0;

    final dayColor = AppState.getPnlColor(catDayPnl);
    final holdColor = AppState.getPnlColor(catHoldPnl);

    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0x1AFFFFFF)),
        color: const Color(0x06FFFFFF),
      ),
      child: Row(
        children: [
          // Day PnL
          Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '当日盈亏',
                    style: _S.sumLabel.copyWith(color: AppTheme.textMuted),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        appState.amountHidden
                            ? '****'
                            : appState.formatPnlInt(catDayPnl),
                        style: _S.sumVal.copyWith(color: dayColor),
                      ),
                      Text(
                        appState.amountHidden ? '' : _fmtPct(catDayPnlRate),
                        style: _S.sumPct.copyWith(
                          color: dayColor.withOpacity(0.85),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          // Divider
          Container(width: 1, height: 30, color: const Color(0x1AFFFFFF)),
          // Hold PnL
          Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '累计盈亏',
                    style: _S.sumLabel.copyWith(color: AppTheme.textMuted),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        appState.amountHidden
                            ? '****'
                            : appState.formatPnlInt(catHoldPnl),
                        style: _S.sumVal.copyWith(color: holdColor),
                      ),
                      Text(
                        appState.amountHidden ? '' : _fmtPct(catHoldPnlRate),
                        style: _S.sumPct.copyWith(
                          color: holdColor.withOpacity(0.85),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ─── Portfolio List ────────────────────────────
  Widget _buildPortfolioList(AppState appState) {
    final List<dynamic> filtered = List.from(appState.filteredPortfolio);

    // Sort by today's PnL descending
    filtered.sort((a, b) {
      final priceInfoA = appState.resolvePriceInfoByCode(
        a.code,
        preferred: appState.prices[a.code],
      );
      final priceInfoB = appState.resolvePriceInfoByCode(
        b.code,
        preferred: appState.prices[b.code],
      );

      final rateA = appState.getCurrencyRate(a.curr);
      final rateB = appState.getCurrencyRate(b.curr);

      double pnlA = 0;
      if (appState.isAssetDayPnlEnabled(a, priceInfo: priceInfoA) &&
          priceInfoA != null &&
          priceInfoA.price > 0) {
        pnlA = priceInfoA.change * a.qty * rateA;
      }

      double pnlB = 0;
      if (appState.isAssetDayPnlEnabled(b, priceInfo: priceInfoB) &&
          priceInfoB != null &&
          priceInfoB.price > 0) {
        pnlB = priceInfoB.change * b.qty * rateB;
      }

      return pnlB.compareTo(pnlA); // Descending
    });

    if (filtered.isEmpty) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 60),
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.business_center,
                size: 48,
                color: AppTheme.textTertiary,
              ),
              const SizedBox(height: 12),
              Text('暂无持仓', style: TextStyle(color: AppTheme.textSecondary)),
            ],
          ),
        ),
      );
    }

    return Column(
      children: filtered.map((item) {
        final priceInfo = appState.resolvePriceInfoByCode(
          item.code,
          preferred: appState.prices[item.code],
        );
        return Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: RepaintBoundary(
            child: _buildStockCard(item, priceInfo, appState),
          ),
        );
      }).toList(),
    );
  }

  // ─── Stock Card ────────────────────────────────
  Widget _buildStockCard(dynamic item, dynamic priceInfo, AppState appState) {
    final qty = (item.qty as num?)?.toDouble() ?? 0.0;
    final rawCostPrice = (item.price as num?)?.toDouble() ?? 0.0;
    final adjustment = (item.adjustment as num?)?.toDouble() ?? 0.0;
    final displayCostPrice = qty.abs() > 1e-9
        ? ((rawCostPrice * qty) - adjustment) / qty
        : rawCostPrice;

    final hasValidPrice = priceInfo != null && priceInfo.price > 0;
    final currentPrice = hasValidPrice
        ? priceInfo.price
        : (rawCostPrice > 0 ? rawCostPrice : 0.0);

    final mv = currentPrice * qty;
    final costTotal = rawCostPrice * qty;
    final holdingPnl = mv - costTotal + adjustment;
    final holdingPnlPct = costTotal.abs() > 0
        ? (holdingPnl / costTotal.abs() * 100)
        : 0.0;
    final pnlColor = AppState.getPnlColor(holdingPnl);

    final rate = appState.getCurrencyRate(item.curr);
    final dayPnlEnabled = appState.isAssetDayPnlDisplayEnabled(
      item,
      priceInfo: priceInfo,
    );
    final dailyPnl = (dayPnlEnabled && hasValidPrice)
        ? priceInfo.change * qty * rate
        : 0.0;
    final dailyBase = (dayPnlEnabled && hasValidPrice && priceInfo.yclose > 0)
        ? priceInfo.yclose * qty * rate
        : 0.0;
    final dailyPnlPct = dailyBase > 0 ? (dailyPnl / dailyBase * 100) : 0.0;
    final dailyColor = AppState.getPnlColor(dailyPnl);

    // Market type tag
    final marketType = (item.marketType as String? ?? 'a').toLowerCase();
    final tagColors = _tagColors[marketType] ?? _tagColors['a']!;
    final tagLabel = _tagLabels[marketType] ?? 'A股';

    // Progress bar calculation
    final isProfit = currentPrice >= displayCostPrice;
    final maxPrice = max(currentPrice, displayCostPrice);
    final progressRatio = maxPrice > 0
        ? (isProfit ? displayCostPrice / maxPrice : currentPrice / maxPrice)
        : 0.5;
    final priceDiffPct = displayCostPrice > 0
        ? ((currentPrice - displayCostPrice) / displayCostPrice * 100)
        : 0.0;

    // Currency symbol
    final sym = item.currencySymbol as String? ?? '¥';
    final isFund = _isFundAsset(item);
    final qtyUnit = isFund ? '份' : '股';

    return GestureDetector(
      onTap: () => showInvestTradeSheet(
        context: context,
        mode: 'trade',
        item: item,
        hostContext: context,
        presentation: InvestTradeDialogPresentation.centered,
      ),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0x0FFFFFFF)),
          color: AppTheme.surface2,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.18),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          children: [
            // ── Head row: name/tag/code | mktval/holding ──
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Left
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item.name.length > 20
                            ? '${item.name.substring(0, 20)}...'
                            : item.name,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: _S.cardName.copyWith(
                          color: const Color(0xFFF0F4FF),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 6,
                              vertical: 1,
                            ),
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(4),
                              color: tagColors.$2,
                            ),
                            child: Text(
                              tagLabel,
                              style: _S.cardTag.copyWith(color: tagColors.$1),
                            ),
                          ),
                          const SizedBox(width: 6),
                          Text(
                            _formatDisplayCode(item.code),
                            style: _S.cardCode.copyWith(
                              color: AppTheme.textMuted,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                // Right
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      appState.amountHidden
                          ? '****'
                          : '$sym${appState.formatAmount(mv, prefix: '').replaceFirst('¥', '')}',
                      style: _S.cardMktVal.copyWith(
                        color: const Color(0xFFF0F4FF),
                      ),
                    ),
                    const SizedBox(height: 3),
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 3,
                          height: 3,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: AppTheme.textMuted.withOpacity(0.5),
                          ),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '${_formatDisplayQty(qty)} $qtyUnit',
                          style: _S.cardHoldNum.copyWith(
                            color: AppTheme.textMuted,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ],
            ),

            const SizedBox(height: 10),

            // ── Progress bar (Center-anchored at Cost Price) ──
            Column(
              children: [
                Builder(
                  builder: (context) {
                    // Maximum change rate for 50% width is 30% (0.3)
                    const double maxRate = 0.3;
                    double costPrice = item.price;

                    // We can derive current price from market value and quantity
                    double currentPrice = costPrice;
                    if (qty > 0) {
                      currentPrice = mv / qty;
                    }

                    double changeRate = costPrice > 0
                        ? (currentPrice - costPrice) / costPrice
                        : 0.0;
                    double fillRatio =
                        (changeRate.abs() / maxRate).clamp(0.0, 1.0) * 0.5;

                    bool isUp = changeRate >= 0;

                    return Container(
                      height: 3,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(2),
                        color: const Color(0x0FFFFFFF), // Empty track
                      ),
                      child: Stack(
                        children: [
                          // Center anchor point (50%)
                          Positioned(
                            left: 0,
                            right: 0,
                            top: 0,
                            bottom: 0,
                            child: Row(
                              children: [
                                // Left side (Down / Green)
                                Expanded(
                                  child: Align(
                                    alignment: Alignment.centerRight,
                                    child: FractionallySizedBox(
                                      widthFactor: isUp
                                          ? 0.0
                                          : fillRatio *
                                                2, // Multiply by 2 because it's in a 50% expanded box
                                      child: Container(
                                        decoration: BoxDecoration(
                                          borderRadius: BorderRadius.circular(
                                            2,
                                          ),
                                          gradient: const LinearGradient(
                                            colors: [
                                              Color(0x662ECC8A),
                                              Color(0xFF2ECC8A),
                                            ],
                                          ),
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                                // Right side (Up / Red)
                                Expanded(
                                  child: Align(
                                    alignment: Alignment.centerLeft,
                                    child: FractionallySizedBox(
                                      widthFactor: isUp ? fillRatio * 2 : 0.0,
                                      child: Container(
                                        decoration: BoxDecoration(
                                          borderRadius: BorderRadius.circular(
                                            2,
                                          ),
                                          gradient: const LinearGradient(
                                            colors: [
                                              Color(0x66F05A55),
                                              Color(0xFFF05A55),
                                            ],
                                          ),
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
                const SizedBox(height: 6),
                // Labels
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '成本 $sym${_formatDisplayPrice(displayCostPrice, item: item)}',
                      style: _S.cardProgressLabel.copyWith(
                        color: const Color(0xFFF0F4FF),
                      ),
                    ),
                    RichText(
                      text: TextSpan(
                        children: [
                          TextSpan(
                            text:
                                '现价 $sym${_formatDisplayPrice(currentPrice, item: item)} ',
                            style: _S.cardProgressLabel.copyWith(
                              color: const Color(0xFFF0F4FF),
                            ),
                          ),
                          TextSpan(
                            text:
                                '${isProfit ? '↑' : '↓'}${priceDiffPct.abs().toStringAsFixed(2)}%',
                            style: _S.cardProgressLabel.copyWith(
                              color: isProfit
                                  ? AppTheme.danger
                                  : AppTheme.success,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),

            const SizedBox(height: 10),

            // ── PnL boxes: day | cumulative ──
            Row(
              children: [
                Expanded(
                  child: _pnlBox(
                    label: '当日盈亏',
                    value: _fmtPnl(dailyPnl, '¥'),
                    pct: _fmtPct(dailyPnlPct),
                    color: dailyColor,
                    hidden: appState.amountHidden,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _pnlBox(
                    label: '累计盈亏',
                    value: _fmtPnl(holdingPnl, sym),
                    pct: _fmtPct(holdingPnlPct),
                    color: pnlColor,
                    hidden: appState.amountHidden,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _pnlBox({
    required String label,
    required String value,
    required String pct,
    required Color color,
    required bool hidden,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0x1AFFFFFF)),
        color: AppTheme.surface2,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: _S.cardPnlLabel.copyWith(color: AppTheme.textMuted),
          ),
          const SizedBox(height: 5),
          Text(
            hidden ? '****' : value,
            style: _S.cardPnlVal.copyWith(color: color),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 2),
          Text(hidden ? '' : pct, style: _S.cardPnlPct.copyWith(color: color)),
        ],
      ),
    );
  }
}
