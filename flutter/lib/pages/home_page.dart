import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../providers/app_state.dart';
import '../widgets/fab_scroll_visibility_controller.dart';

// ──────────────────────────────────────────────────
// Cached TextStyles – created once, reused every build
// ──────────────────────────────────────────────────
class _S {
  _S._();
  // Brand header
  static final brandTitle = GoogleFonts.dmSans(
    fontSize: 15, fontWeight: FontWeight.w700, height: 1.1,
  );
  static final brandSub = GoogleFonts.dmSans(fontSize: 11);
  // Hero
  static final heroLabel = GoogleFonts.dmSans(
    fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 0.012,
  );
  static final heroValue = GoogleFonts.jetBrainsMono(
    fontSize: 30, fontWeight: FontWeight.w600, letterSpacing: 0.02, height: 1.06,
  );
  static final heroCurrCode = GoogleFonts.jetBrainsMono(
    fontSize: 10, fontWeight: FontWeight.w500, letterSpacing: 0.015,
  );
  static final heroMetaText = GoogleFonts.dmSans(fontSize: 11);
  static final heroMarketPill = GoogleFonts.dmSans(
    fontSize: 11, fontWeight: FontWeight.w600, height: 1,
  );
  // Currency dropdown
  static final currItemName = GoogleFonts.dmSans(fontSize: 12);
  static final currItemCode = GoogleFonts.jetBrainsMono(
    fontSize: 11, letterSpacing: 0.04,
  );
  // Cards
  static final cardName = GoogleFonts.dmSans(
    fontSize: 14, fontWeight: FontWeight.w700, height: 1.2,
  );
  static final cardSub = GoogleFonts.dmSans(
    fontSize: 10, letterSpacing: 0.02,
  );
  static final cardValue = GoogleFonts.jetBrainsMono(
    fontSize: 15, fontWeight: FontWeight.w600,
  );
}

/// 首页 - 资产总览
class HomePage extends StatefulWidget {
  final Function(String) onNavigate;
  final Function(int) onSwitchTab;
  final ValueChanged<bool>? onFabVisibilityChanged;

  const HomePage({
    super.key,
    required this.onNavigate,
    required this.onSwitchTab,
    this.onFabVisibilityChanged,
  });

  @override
  State<HomePage> createState() => HomePageState();
}

class HomePageState extends State<HomePage> {
  final FabScrollVisibilityController _fabVisibilityController =
      FabScrollVisibilityController();
  bool _refreshInFlight = false;

  // Currency dropdown open state
  bool _currDropdownOpen = false;

  static const _currencies = [
    {'code': 'CNY', 'name': '人民币', 'flag': '🇨🇳', 'symbol': '¥'},
    {'code': 'USD', 'name': '美元', 'flag': '🇺🇸', 'symbol': r'$'},
    {'code': 'HKD', 'name': '港币', 'flag': '🇭🇰', 'symbol': 'HK\$'},
  ];

  @override
  void initState() {
    super.initState();
  }

  Future<void> _refreshData() async {
    if (_refreshInFlight) return;
    _refreshInFlight = true;
    final appState = context.read<AppState>();
    try {
      await appState.refreshAll(force: true);
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

    if (notification is ScrollUpdateNotification) {
      final delta = notification.scrollDelta;
      if (delta != null) {
        final next = _fabVisibilityController.onScrollUpdate(delta);
        if (next != null) {
          callback(next);
        }
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

  String _fmt(double value, bool hidden) {
    if (hidden) return '****';
    if (value == 0) return '--';
    final intVal = value.toInt();
    return intVal.toString().replaceAllMapped(
      RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
      (m) => '${m[1]},',
    );
  }

  int _accountCount(AppState s, String type) {
    switch (type) {
      case 'cash':
        return s.cashAssets.length;
      case 'other':
        return s.otherAssets.length;
      case 'liability':
        return s.liabilities.length;
      default:
        return 0;
    }
  }

  /// Determine market status text from A/HK/US open status
  String _marketStatusText(AppState appState) {
    final aOpen = appState.isMarketOpen('a');
    final hkOpen = appState.isMarketOpen('hk');
    final usOpen = appState.isMarketOpen('us');
    if (aOpen || hkOpen || usOpen) {
      final parts = <String>[];
      if (aOpen) parts.add('A股');
      if (hkOpen) parts.add('港股');
      if (usOpen) parts.add('美股');
      return '${parts.join('·')} 交易中';
    }
    return '市场休市中';
  }

  bool _isAnyMarketOpen(AppState appState) {
    return appState.isMarketOpen('a') ||
        appState.isMarketOpen('hk') ||
        appState.isMarketOpen('us');
  }

  // ─── Build ───────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        return RefreshIndicator(
          onRefresh: _refreshData,
          color: AppTheme.accent,
          child: NotificationListener<ScrollNotification>(
            onNotification: _onScrollNotification,
            child: GestureDetector(
              onTap: () {
                if (_currDropdownOpen) {
                  setState(() => _currDropdownOpen = false);
                }
              },
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: EdgeInsets.fromLTRB(
                  0, 0, 0, _bottomContentPadding(context),
                ),
                child: Column(
                  children: [
                    // ── Brand header ──────────────────
                    _buildBrandHeader(appState),

                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 14),
                      child: Column(
                        children: [
                          // ── Hero Card ─────────────────────
                          _buildHeroCard(appState),

                          const SizedBox(height: 12),

                          // ── Asset category cards ──────────
                          _buildCategoryCard(
                            icon: Icons.account_balance_wallet_outlined,
                            name: '现金资产',
                            subtitle: '${_accountCount(appState, "cash")}个账户',
                            amount: _fmt(
                              appState.convertDisplayAmount(appState.totalCash),
                              appState.amountHidden,
                            ),
                            onTap: () => widget.onNavigate('cash_detail'),
                          ),
                          const SizedBox(height: 10),
                          _buildCategoryCard(
                            icon: Icons.trending_up,
                            name: '投资资产',
                            subtitle: '${appState.portfolio.length}个持仓',
                            amount: _fmt(
                              appState.convertDisplayAmount(appState.totalInvest),
                              appState.amountHidden,
                            ),
                            onTap: () => widget.onSwitchTab(1),
                          ),
                          const SizedBox(height: 10),
                          _buildCategoryCard(
                            icon: Icons.dataset_outlined,
                            name: '其他资产',
                            subtitle: '${_accountCount(appState, "other")}个账户',
                            amount: _fmt(
                              appState.convertDisplayAmount(appState.totalOther),
                              appState.amountHidden,
                            ),
                            onTap: () => widget.onNavigate('other_detail'),
                          ),
                          const SizedBox(height: 10),
                          _buildCategoryCard(
                            icon: Icons.credit_card_outlined,
                            name: '我的负债',
                            subtitle:
                                '${_accountCount(appState, "liability")}个账户',
                            amount: _fmt(
                              appState.convertDisplayAmount(appState.totalLiability),
                              appState.amountHidden,
                            ),
                            onTap: () => widget.onNavigate('liability_detail'),
                          ),

                          const SizedBox(height: 20),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  // ─── Brand Header ──────────────────────────────
  Widget _buildBrandHeader(AppState appState) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(color: Colors.white.withValues(alpha: 0.04)),
        ),
      ),
      child: Row(
        children: [
          // Brand mark
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: Colors.white.withValues(alpha: 0.16)),
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF5B8DEF), Color(0xFF4A7BE0)],
              ),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF4A7BE0).withValues(alpha: 0.32),
                  blurRadius: 20,
                  offset: const Offset(0, 10),
                ),
              ],
            ),
            alignment: Alignment.center,
            child: const Text(
              'K',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w700,
                color: Colors.white,
              ),
            ),
          ),
          const SizedBox(width: 10),

          // Brand text
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '咔咔记账',
                  style: _S.brandTitle.copyWith(color: AppTheme.textPrimary),
                ),
                const SizedBox(height: 2),
                Text(
                  (appState.nickname ?? '').isNotEmpty
                      ? '你好，${appState.nickname}'
                      : '你好，欢迎回来',
                  style: _S.brandSub.copyWith(color: AppTheme.textMuted),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),


        ],
      ),
    );
  }

  // ─── Hero Card ─────────────────────────────────
  Widget _buildHeroCard(AppState appState) {
    final anyOpen = _isAnyMarketOpen(appState);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 15),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.white.withValues(alpha: 0.06)),
        gradient: const LinearGradient(
          begin: Alignment(-0.6, -1),
          end: Alignment(1, 1),
          colors: [
            Color(0x335B8DEF),
            Color(0x0F4A7BE0),
            Color(0xF0191C25),
          ],
          stops: [0.0, 0.35, 1.0],
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.35),
            blurRadius: 26,
            offset: const Offset(0, 12),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Top row: label + CNY dropdown + eye button
          Row(
            children: [
              Text(
                '总资产估值',
                style: _S.heroLabel.copyWith(color: const Color(0xFF9AA3B7)),
              ),
              const SizedBox(width: 6),
              // Currency selector button
              _buildCurrencyButton(appState),
              const Spacer(),
              // Privacy toggle
              _heroIconBtn(
                icon: appState.amountHidden
                    ? Icons.visibility_off_outlined
                    : Icons.visibility_outlined,
                onTap: () => appState.toggleAmountHidden(),
              ),
            ],
          ),

          const SizedBox(height: 8),

          // Total value
          LayoutBuilder(
            builder: (context, constraints) {
              final displayTotal = appState.convertDisplayAmount(appState.totalAsset);
              return SizedBox(
                width: constraints.maxWidth,
                child: FittedBox(
                  fit: BoxFit.scaleDown,
                  alignment: Alignment.centerLeft,
                  child: Text(
                    appState.amountHidden
                        ? '****'
                        : _fmt(displayTotal, false),
                    style: _S.heroValue.copyWith(
                      color: const Color(0xFFF0F4FF),
                    ),
                  ),
                ),
              );
            },
          ),

          const SizedBox(height: 10),

          // Meta row: sync text + market pill
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '同步于刚刚',
                style: _S.heroMetaText.copyWith(color: AppTheme.textMuted),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(
                    color: anyOpen
                        ? AppTheme.danger.withValues(alpha: 0.3)
                        : AppTheme.success.withValues(alpha: 0.3),
                  ),
                  color: anyOpen
                      ? AppTheme.danger.withValues(alpha: 0.08)
                      : AppTheme.success.withValues(alpha: 0.08),
                ),
                child: Text(
                  _marketStatusText(appState),
                  style: _S.heroMarketPill.copyWith(
                    color: anyOpen ? AppTheme.danger : AppTheme.success,
                  ),
                ),
              ),
            ],
          ),

          // Currency dropdown (shown/hidden by state)
          if (_currDropdownOpen) _buildCurrencyDropdown(appState),
        ],
      ),
    );
  }

  // ─── Currency Selector ─────────────────────────
  Widget _buildCurrencyButton(AppState appState) {
    return GestureDetector(
      onTap: () {
        setState(() => _currDropdownOpen = !_currDropdownOpen);
      },
      child: Container(
        height: 20,
        padding: const EdgeInsets.symmetric(horizontal: 7),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(999),
          border: Border.all(
            color: AppTheme.gold.withValues(alpha: _currDropdownOpen ? 0.4 : 0.26),
          ),
          color: AppTheme.gold.withValues(alpha: _currDropdownOpen ? 0.1 : 0.05),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              appState.displayCurrency,
              style: _S.heroCurrCode.copyWith(color: const Color(0xFFCDB47C)),
            ),
            const SizedBox(width: 4),
            AnimatedRotation(
              turns: _currDropdownOpen ? 0.5 : 0,
              duration: const Duration(milliseconds: 180),
              child: Icon(
                Icons.expand_more,
                size: 9,
                color: const Color(0xFFCDB47C),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCurrencyDropdown(AppState appState) {
    return Container(
      margin: const EdgeInsets.only(top: 10),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.gold.withValues(alpha: 0.42)),
        color: const Color(0xFA14171F),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.5),
            blurRadius: 32,
            offset: const Offset(0, 16),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: _currencies.asMap().entries.map((entry) {
          final idx = entry.key;
          final c = entry.value;
          final code = c['code']!;
          final isActive = code == appState.displayCurrency;
          final isLast = idx == _currencies.length - 1;
          return GestureDetector(
            onTap: () {
              appState.setDisplayCurrency(code);
              setState(() {
                _currDropdownOpen = false;
              });
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
              decoration: BoxDecoration(
                color: isActive
                    ? AppTheme.gold.withValues(alpha: 0.14)
                    : Colors.transparent,
                border: isLast
                    ? null
                    : Border(
                        bottom: BorderSide(
                          color: Colors.white.withValues(alpha: 0.06),
                        ),
                      ),
                borderRadius: isLast
                    ? const BorderRadius.vertical(
                        bottom: Radius.circular(10),
                      )
                    : (idx == 0
                        ? const BorderRadius.vertical(
                            top: Radius.circular(10),
                          )
                        : null),
              ),
              child: Row(
                children: [
                  Text(
                    code,
                    style: _S.currItemCode.copyWith(
                      color: const Color(0xFFD7BD83),
                    ),
                  ),
                  const Spacer(),
                  Text(
                    c['name']!,
                    style: _S.currItemName.copyWith(
                      color: isActive
                          ? const Color(0xFFEFD8A7)
                          : AppTheme.textMuted,
                    ),
                  ),
                  if (isActive) ...[
                    const SizedBox(width: 8),
                    Icon(
                      Icons.check,
                      size: 12,
                      color: const Color(0xFFD7BD83),
                    ),
                  ],
                ],
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _heroIconBtn({
    required IconData icon,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 30,
        height: 30,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(9),
          border: Border.all(color: Colors.white.withValues(alpha: 0.07)),
          color: AppTheme.surface2,
        ),
        child: Icon(icon, size: 15, color: AppTheme.textSecondary),
      ),
    );
  }

  // ─── Category Card ─────────────────────────────
  Widget _buildCategoryCard({
    required IconData icon,
    required String name,
    required String subtitle,
    required String amount,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: Colors.white.withValues(alpha: 0.055)),
          gradient: const LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              Color(0xF51A1D25),
              Color(0xFA171A22),
            ],
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.28),
              blurRadius: 18,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: Row(
          children: [
            // Icon container
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(11),
                gradient: const LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    Color(0x235B8DEF),
                    Color(0x0F4A7BE0),
                  ],
                ),
                border: Border.all(
                  color: const Color(0x295B8DEF),
                ),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x145B8DEF),
                    blurRadius: 10,
                    spreadRadius: -2,
                  ),
                ],
              ),
              child: Icon(icon, size: 18, color: const Color(0xFF739BF0)),
            ),
            const SizedBox(width: 10),

            // Name + subtitle
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name,
                    style: _S.cardName.copyWith(color: const Color(0xFFEDF1FA)),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    style: _S.cardSub.copyWith(color: AppTheme.textMuted),
                  ),
                ],
              ),
            ),

            // Value
            Text(
              amount,
              style: _S.cardValue.copyWith(color: const Color(0xFFE3E9F7)),
            ),
            const SizedBox(width: 8),

            // Arrow
            Icon(
              Icons.chevron_right_rounded,
              size: 14,
              color: AppTheme.textSecondary,
            ),
          ],
        ),
      ),
    );
  }
}
