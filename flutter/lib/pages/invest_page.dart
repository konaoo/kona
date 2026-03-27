import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../models/portfolio.dart';
import '../providers/app_state.dart';
import '../services/portfolio_metrics_service.dart';
import 'investment_detail_page.dart';
import 'ledger_management_page.dart';
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
  static final cardTag = GoogleFonts.dmSans(
    fontSize: 10,
    fontWeight: FontWeight.w600,
    letterSpacing: 0.03,
  );
  static final cardHoldNum = GoogleFonts.jetBrainsMono(fontSize: 11);
  static final cardPnlPending = GoogleFonts.dmSans(
    fontSize: 12,
    fontWeight: FontWeight.w600,
    letterSpacing: 0.01,
    height: 1.0,
  );
  static final cardNameCompact = GoogleFonts.dmSans(
    fontSize: 14,
    fontWeight: FontWeight.w700,
  );
  static final cardPriceSym = GoogleFonts.jetBrainsMono(
    fontSize: 11,
    fontWeight: FontWeight.w700,
  );
  static final cardPriceVal = GoogleFonts.jetBrainsMono(
    fontSize: 18,
    fontWeight: FontWeight.w700,
  );
  static final cardBadge = GoogleFonts.jetBrainsMono(
    fontSize: 10,
    fontWeight: FontWeight.w700,
  );
  static final cardMiniLabel = GoogleFonts.dmSans(
    fontSize: 10,
    fontWeight: FontWeight.w500,
  );
  static final cardMiniValue = GoogleFonts.jetBrainsMono(
    fontSize: 12.5,
    fontWeight: FontWeight.w600,
  );
  static final cardPositionLabel = GoogleFonts.dmSans(
    fontSize: 10,
    fontWeight: FontWeight.w500,
  );
  static final cardPositionValue = GoogleFonts.jetBrainsMono(
    fontSize: 12.5,
    fontWeight: FontWeight.w600,
  );
  // Ledger selector
  static final ledgerTrigger = GoogleFonts.dmSans(
    fontSize: 12,
    fontWeight: FontWeight.w700,
  );
  static final ledgerMenuName = GoogleFonts.dmSans(
    fontSize: 14,
    fontWeight: FontWeight.w600,
  );
  static final ledgerMenuMeta = GoogleFonts.dmSans(
    fontSize: 12,
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
  final LayerLink _ledgerLink = LayerLink();
  final GlobalKey _ledgerButtonKey = GlobalKey();
  bool _refreshInFlight = false;
  bool _ledgerDropdownOpen = false;
  OverlayEntry? _ledgerDropdownEntry;
  String? _lastAvatarString;
  MemoryImage? _cachedAvatarImage;

  @override
  void initState() {
    super.initState();
  }

  @override
  void dispose() {
    _hideLedgerDropdown(updateState: false);
    super.dispose();
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
    if (_ledgerDropdownOpen) {
      _hideLedgerDropdown();
    }
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
    const fabRegion = 10.0;
    return safeBottom + fabRegion;
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
    final intVal = (value.abs() + 1e-9).toStringAsFixed(0);
    final formatted = intVal.replaceAllMapped(
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

  String _fmtPnlNullable(double? value, String symbol) {
    if (value == null) return '--';
    return _fmtPnl(value, symbol);
  }

  String _fmtPctNullable(double? value) {
    if (value == null) return '--';
    return _fmtPct(value);
  }

  String? _readLatestNavDate(dynamic item) {
    if (item == null) return null;
    if (item is PortfolioItem) {
      final value = item.latestNavDate?.trim();
      return (value == null || value.isEmpty) ? null : value;
    }
    if (item is Map) {
      final value = (item['latest_nav_date'] ?? item['latestNavDate'])
          ?.toString()
          .trim();
      return (value == null || value.isEmpty) ? null : value;
    }
    return null;
  }

  String? _formatLatestNavDateText(String? value) {
    final text = (value ?? '').trim();
    if (text.isEmpty) return null;
    final match = RegExp(r'(\d{4})-(\d{2})-(\d{2})').firstMatch(text);
    if (match == null) return text;
    return '${match.group(2)}-${match.group(3)}';
  }

  bool _isDateToday(String? value) {
    final text = (value ?? '').trim();
    final match = RegExp(r'^(\d{4})-(\d{2})-(\d{2})').firstMatch(text);
    if (match == null) return false;
    final year = int.tryParse(match.group(1) ?? '');
    final month = int.tryParse(match.group(2) ?? '');
    final day = int.tryParse(match.group(3) ?? '');
    if (year == null || month == null || day == null) return false;
    final now = DateTime.now();
    return now.year == year && now.month == month && now.day == day;
  }

  double? _readPositionPct(dynamic item) {
    if (item == null) return null;
    if (item is PortfolioItem) return item.positionPct;
    if (item is Map) {
      const keys = [
        'position_pct',
        'positionPct',
        'pct',
        'holding_pct',
        'holdingPct',
        'portfolio_pct',
        'portfolioPct',
      ];
      for (final key in keys) {
        final raw = item[key];
        if (raw is num) return raw.toDouble();
        if (raw is String) {
          final parsed = double.tryParse(raw);
          if (parsed != null) return parsed;
        }
      }
    }
    return null;
  }

  String _formatPositionPctLabel(double? value) {
    if (value == null) return '--';
    return '${value.toStringAsFixed(2)}%';
  }

  Widget _buildRateBadge({
    required String label,
    required Color color,
    required bool muted,
  }) {
    if (label.isEmpty) return const SizedBox.shrink();
    final bg = muted
        ? (AppTheme.isLight ? const Color(0x08222C40) : const Color(0x14FFFFFF))
        : color.withValues(alpha: AppTheme.isLight ? 0.12 : 0.18);
    final fg = muted ? AppTheme.textMuted : color;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        label,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: _S.cardBadge.copyWith(color: fg),
      ),
    );
  }

  // ─── Ledger Selector ─────────────────────────────
  void _toggleLedgerDropdown(AppState appState) {
    if (_ledgerDropdownOpen) {
      _hideLedgerDropdown();
      return;
    }
    _showLedgerDropdown(appState);
  }

  void _showLedgerDropdown(AppState appState) {
    if (_ledgerDropdownEntry != null) return;
    final overlay = Overlay.of(context, rootOverlay: true);
    _ledgerDropdownEntry = OverlayEntry(
      builder: (_) {
        final triggerSize = _targetSize(_ledgerButtonKey);
        final width = (triggerSize.width + 74).clamp(164.0, 240.0);
        return Stack(
          children: [
            Positioned.fill(
              child: GestureDetector(
                behavior: HitTestBehavior.translucent,
                onTap: _hideLedgerDropdown,
                child: const SizedBox.expand(),
              ),
            ),
            CompositedTransformFollower(
              link: _ledgerLink,
              showWhenUnlinked: false,
              offset: Offset(0, triggerSize.height + 8),
              child: Material(
                color: Colors.transparent,
                child: SizedBox(
                  width: width,
                  child: _buildLedgerDropdownCard(appState),
                ),
              ),
            ),
          ],
        );
      },
    );
    overlay.insert(_ledgerDropdownEntry!);
    setState(() => _ledgerDropdownOpen = true);
  }

  void _hideLedgerDropdown({bool updateState = true}) {
    _ledgerDropdownEntry?.remove();
    _ledgerDropdownEntry = null;
    if (!mounted) return;
    if (updateState) {
      setState(() => _ledgerDropdownOpen = false);
    }
  }

  Size _targetSize(GlobalKey key) {
    final renderBox = key.currentContext?.findRenderObject() as RenderBox?;
    return renderBox?.size ?? Size.zero;
  }

  Widget _buildLedgerDropdownCard(AppState appState) {
    final ledgers = appState.ledgers;
    final currentId = appState.currentLedgerId;
    return TweenAnimationBuilder<double>(
      tween: Tween<double>(begin: 0, end: 1),
      duration: const Duration(milliseconds: 180),
      curve: Curves.easeOutBack,
      builder: (context, value, child) {
        final opacity = value.clamp(0.0, 1.0).toDouble();
        return Opacity(
          opacity: opacity,
          child: Transform.translate(
            offset: Offset(0, (1 - opacity) * -4),
            child: child,
          ),
        );
      },
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: AppTheme.isLight
                ? AppTheme.gold.withValues(alpha: 0.14)
                : AppTheme.gold.withValues(alpha: 0.36),
          ),
          color: AppTheme.isLight
              ? const Color(0xFFF9FAFF)
              : const Color(0xFA14171F),
          boxShadow: [
            BoxShadow(
              color: AppTheme.isLight
                  ? const Color(0x14222C48)
                  : Colors.black.withValues(alpha: 0.48),
              blurRadius: AppTheme.isLight ? 22 : 28,
              offset: AppTheme.isLight
                  ? const Offset(0, 10)
                  : const Offset(0, 16),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            for (final entry in ledgers.asMap().entries)
              _buildLedgerMenuItem(
                appState: appState,
                ledger: entry.value,
                isFirst: entry.key == 0,
                isLast: false,
                isActive: entry.value['id'] == currentId,
              ),
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 10),
              height: 1,
              color: AppTheme.isLight
                  ? const Color(0x0D222C40)
                  : Colors.white.withValues(alpha: 0.06),
            ),
            _buildManageLedgerItem(),
          ],
        ),
      ),
    );
  }

  Widget _buildLedgerMenuItem({
    required AppState appState,
    required Map<String, dynamic> ledger,
    required bool isFirst,
    required bool isLast,
    required bool isActive,
  }) {
    final title = (ledger['name'] as String?) ?? '账本';
    final isDefault = ledger['is_default'] == true || ledger['is_default'] == 1;
    final activeColor = AppTheme.isLight
        ? const Color(0xFFBC9552)
        : const Color(0xFFCDB47C);
    return InkWell(
      onTap: () {
        _hideLedgerDropdown();
        final ledgerId = ledger['id'] as int?;
        if (ledgerId != null) {
          appState.switchLedger(ledgerId);
        }
      },
      borderRadius: BorderRadius.vertical(
        top: isFirst ? const Radius.circular(14) : Radius.zero,
        bottom: isLast ? const Radius.circular(14) : Radius.zero,
      ),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: isActive
              ? activeColor.withValues(alpha: AppTheme.isLight ? 0.08 : 0.14)
              : Colors.transparent,
          borderRadius: BorderRadius.vertical(
            top: isFirst ? const Radius.circular(14) : Radius.zero,
            bottom: isLast ? const Radius.circular(14) : Radius.zero,
          ),
        ),
        child: Row(
          children: [
            Expanded(
              child: Row(
                children: [
                  Flexible(
                    child: Text(
                      title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: _S.ledgerMenuName.copyWith(
                        color: isActive ? activeColor : AppTheme.textPrimary,
                      ),
                    ),
                  ),
                  if (isDefault) ...[
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 7,
                        vertical: 3,
                      ),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(999),
                        border: Border.all(
                          color: activeColor.withValues(
                            alpha: AppTheme.isLight ? 0.26 : 0.4,
                          ),
                        ),
                        color: activeColor.withValues(
                          alpha: AppTheme.isLight ? 0.06 : 0.1,
                        ),
                      ),
                      child: Text(
                        '默认',
                        style: _S.ledgerMenuMeta.copyWith(color: activeColor),
                      ),
                    ),
                  ],
                ],
              ),
            ),
            if (isActive)
              Icon(Icons.check_rounded, size: 18, color: activeColor),
          ],
        ),
      ),
    );
  }

  Widget _buildManageLedgerItem() {
    return InkWell(
      onTap: () async {
        _hideLedgerDropdown();
        await Navigator.of(
          context,
        ).push(MaterialPageRoute(builder: (_) => const LedgerManagementPage()));
      },
      borderRadius: const BorderRadius.vertical(bottom: Radius.circular(14)),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
        decoration: const BoxDecoration(
          borderRadius: BorderRadius.vertical(bottom: Radius.circular(14)),
        ),
        child: Row(
          children: [
            Icon(Icons.tune_rounded, size: 18, color: AppTheme.textMuted),
            const SizedBox(width: 10),
            Text(
              '管理账本',
              style: _S.ledgerMenuName.copyWith(color: AppTheme.textPrimary),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLedgerAvatar(AppState appState) {
    final currentAvatarString = appState.avatar;
    if (currentAvatarString != _lastAvatarString) {
      _lastAvatarString = currentAvatarString;
      if (currentAvatarString != null && currentAvatarString.isNotEmpty) {
        try {
          _cachedAvatarImage = MemoryImage(base64Decode(currentAvatarString));
        } catch (_) {
          _cachedAvatarImage = null;
        }
      } else {
        _cachedAvatarImage = null;
      }
    }

    final hasAvatar = _cachedAvatarImage != null;
    final fallback =
        (appState.username?.isNotEmpty == true
                ? appState.username!.substring(0, 1)
                : 'U')
            .toUpperCase();

    return Container(
      width: 20,
      height: 20,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(
          color: AppTheme.isLight
              ? const Color(0x335B8DEF)
              : Colors.white.withValues(alpha: 0.16),
        ),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF5B8DEF), Color(0xFF4A7BE0)],
        ),
        image: hasAvatar
            ? DecorationImage(image: _cachedAvatarImage!, fit: BoxFit.cover)
            : null,
      ),
      alignment: Alignment.center,
      child: hasAvatar
          ? null
          : Text(
              fallback,
              style: const TextStyle(
                fontSize: 9,
                fontWeight: FontWeight.w700,
                color: Colors.white,
              ),
            ),
    );
  }

  Widget _buildLedgerSelector(AppState appState) {
    final ledgers = appState.ledgers;
    final currentId = appState.currentLedgerId;
    Map<String, dynamic>? currentLedger;
    for (final ledger in ledgers) {
      if (ledger['id'] == currentId) {
        currentLedger = ledger;
        break;
      }
    }
    currentLedger ??= ledgers.isNotEmpty
        ? Map<String, dynamic>.from(ledgers.first)
        : null;
    final currentName = (currentLedger?['name'] as String?) ?? '默认账本';
    final isDefaultLedger =
        currentLedger?['is_default'] == true ||
        currentLedger?['is_default'] == 1;
    final triggerColor = AppTheme.isLight
        ? const Color(0xFFBC9552)
        : const Color(0xFFCDB47C);
    final titleColor = AppTheme.isLight
        ? const Color(0xFF1E2430)
        : triggerColor;

    return Align(
      alignment: Alignment.centerLeft,
      child: Material(
        type: MaterialType.transparency,
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            CompositedTransformTarget(
              link: _ledgerLink,
              child: Container(
                key: _ledgerButtonKey,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(
                    color: AppTheme.isLight
                        ? AppTheme.gold.withValues(
                            alpha: _ledgerDropdownOpen ? 0.22 : 0.12,
                          )
                        : AppTheme.gold.withValues(
                            alpha: _ledgerDropdownOpen ? 0.42 : 0.26,
                          ),
                  ),
                  color: AppTheme.isLight
                      ? AppTheme.gold.withValues(
                          alpha: _ledgerDropdownOpen ? 0.06 : 0.01,
                        )
                      : AppTheme.gold.withValues(
                          alpha: _ledgerDropdownOpen ? 0.12 : 0.05,
                        ),
                ),
                child: InkWell(
                  onTap: () => _toggleLedgerDropdown(appState),
                  borderRadius: BorderRadius.circular(999),
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(12, 6, 10, 6),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        _buildLedgerAvatar(appState),
                        const SizedBox(width: 8),
                        ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 120),
                          child: Text(
                            currentName,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: _S.ledgerTrigger.copyWith(
                              color: titleColor,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 0.01,
                            ),
                          ),
                        ),
                        const SizedBox(width: 6),
                        AnimatedRotation(
                          turns: _ledgerDropdownOpen ? 0.5 : 0,
                          duration: const Duration(milliseconds: 180),
                          child: Icon(
                            Icons.expand_more_rounded,
                            size: 15,
                            color: triggerColor.withValues(
                              alpha: AppTheme.isLight ? 0.78 : 0.9,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            if (isDefaultLedger) ...[
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 7,
                  vertical: 2.5,
                ),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(
                    color: triggerColor.withValues(
                      alpha: AppTheme.isLight ? 0.16 : 0.3,
                    ),
                  ),
                  color: AppTheme.isLight
                      ? const Color(0xFFF8F1E5)
                      : triggerColor.withValues(alpha: 0.08),
                ),
                child: Text(
                  '默认账本',
                  style: _S.ledgerMenuMeta.copyWith(
                    fontSize: 10,
                    color: triggerColor.withValues(
                      alpha: AppTheme.isLight ? 0.88 : 1,
                    ),
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
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
                    _buildLedgerSelector(appState),
                    const SizedBox(height: 12),
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
    final realtimeToday = appState.realtimeToday;
    final realtimeTotals = realtimeToday['totals'] is Map
        ? Map<String, dynamic>.from(realtimeToday['totals'] as Map)
        : const <String, dynamic>{};
    final items = appState.portfolio;
    final totalValueCny = (realtimeTotals['total_asset'] as num?)?.toDouble();
    final dayPnlCny = (realtimeTotals['day_pnl'] as num?)?.toDouble();
    final holdPnlCny = PortfolioMetricsService.sumMetricOrNull(
      items,
      (item) => PortfolioMetricsService.resolveLiveFloatPnlCny(
        item,
        priceInfo: appState.resolvePriceInfo(item),
        fallbackRateToCny: appState.getCurrencyRate(item.curr),
      ),
    );
    final totalPnlCny = (realtimeTotals['total_pnl'] as num?)?.toDouble();
    final costAbsCny = PortfolioMetricsService.sumAbsMetricOrNull(
      items,
      (item) => PortfolioMetricsService.resolveCostCnyLive(
        item,
        fallbackRateToCny: appState.getCurrencyRate(item.curr),
      ),
    );
    final dayPnlRate = (realtimeTotals['day_pnl_rate'] as num?)?.toDouble();
    final holdPnlRate = PortfolioMetricsService.calcHoldingPnlRateNullable(
      holdPnlCny,
      costAbsCny,
    );
    final totalPnlRate = (realtimeTotals['total_pnl_rate'] as num?)?.toDouble();
    final dayColor = dayPnlCny == null
        ? AppTheme.textMuted
        : AppState.getPnlColor(dayPnlCny);
    final holdColor = holdPnlCny == null
        ? AppTheme.textMuted
        : AppState.getPnlColor(holdPnlCny);
    final totalColor = totalPnlCny == null
        ? AppTheme.textMuted
        : AppState.getPnlColor(totalPnlCny);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 14),
      decoration: AppTheme.heroDecoration,
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
                    '投资总资产',
                    style: _S.heroLabel.copyWith(
                      color: AppTheme.heroLabelColor,
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
                                  : (totalValueCny == null
                                        ? '--'
                                        : appState.formatAmount(
                                            totalValueCny,
                                            prefix: '',
                                          )),
                              style: _S.heroAmount.copyWith(
                                color: AppTheme.heroValueColor,
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
                          : (dayPnlCny == null
                                ? '--'
                                : appState.formatPnlInt(dayPnlCny)),
                      style: _S.heroDayVal.copyWith(color: dayColor),
                    ),
                    Text(
                      appState.amountHidden
                          ? ''
                          : (dayPnlRate == null
                                ? '--'
                                : appState.formatPct(dayPnlRate)),
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
            decoration: BoxDecoration(
              border: Border(top: BorderSide(color: AppTheme.dividerColor)),
            ),
            child: Row(
              children: [
                _statItem(
                  '持仓盈亏',
                  holdPnlCny == null ? '--' : appState.formatPnlInt(holdPnlCny),
                  holdColor,
                  true,
                ),
                _statItem(
                  '持仓盈亏率',
                  holdPnlRate == null ? '--' : appState.formatPct(holdPnlRate),
                  holdColor,
                  true,
                ),
                _statItem(
                  '累计盈亏',
                  totalPnlCny == null
                      ? '--'
                      : appState.formatPnlInt(totalPnlCny),
                  totalColor,
                  true,
                ),
                _statItem(
                  '累计盈亏率',
                  totalPnlRate == null
                      ? '--'
                      : appState.formatPct(totalPnlRate),
                  totalColor,
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
            ? BoxDecoration(
                border: Border(right: BorderSide(color: AppTheme.dividerColor)),
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
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: AppTheme.dividerColor)),
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
                        ? AppTheme.heroValueColor
                        : Colors.transparent,
                    width: 2,
                  ),
                ),
              ),
              child: Text(
                cat.$2,
                style: (isActive ? _S.tabTextActive : _S.tabText).copyWith(
                  color: isActive
                      ? AppTheme.heroValueColor
                      : AppTheme.heroLabelColor,
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

    final catDayPnl = PortfolioMetricsService.sumMetricWhenAny(
      filtered,
      (item) => PortfolioMetricsService.resolveCurrentDayPnlCny(
        item,
        priceInfo: appState.resolvePriceInfo(item),
        fallbackRateToCny: appState.getCurrencyRate(item.curr),
      ),
    );
    final catDayPnlBase = PortfolioMetricsService.sumMetricWhenAny(
      filtered,
      (item) => PortfolioMetricsService.resolveCurrentDayPnlBaseCny(
        item,
        priceInfo: appState.resolvePriceInfo(item),
        fallbackRateToCny: appState.getCurrencyRate(item.curr),
      ),
    );
    final catHoldPnl = PortfolioMetricsService.sumMetricOrNull(
      filtered,
      (item) => PortfolioMetricsService.resolveLiveTotalPnlCny(
        item,
        priceInfo: appState.resolvePriceInfo(item),
        fallbackRateToCny: appState.getCurrencyRate(item.curr),
      ),
    );
    final catCostAbs = PortfolioMetricsService.sumAbsMetricOrNull(
      filtered,
      (item) => PortfolioMetricsService.resolveCostCnyLive(
        item,
        fallbackRateToCny: appState.getCurrencyRate(item.curr),
      ),
    );
    final catDayPnlRate = PortfolioMetricsService.calcDayPnlRateNullable(
      catDayPnl,
      catDayPnlBase,
    );
    final catHoldPnlRate = PortfolioMetricsService.calcHoldingPnlRateNullable(
      catHoldPnl,
      catCostAbs,
    );

    final dayColor = catDayPnl == null
        ? AppTheme.textMuted
        : AppState.getPnlColor(catDayPnl);
    final holdColor = catHoldPnl == null
        ? AppTheme.textMuted
        : AppState.getPnlColor(catHoldPnl);

    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: AppTheme.isLight
              ? const Color(0x0A222C40)
              : AppTheme.dividerColor,
        ),
        color: AppTheme.isLight
            ? const Color(0x05222C40)
            : const Color(0x06FFFFFF),
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
                            : (catDayPnl == null
                                  ? '--'
                                  : appState.formatPnlIntWithCurrency(
                                      catDayPnl,
                                      '¥',
                                    )),
                        style: _S.sumVal.copyWith(color: dayColor),
                      ),
                      Text(
                        appState.amountHidden
                            ? ''
                            : _fmtPctNullable(catDayPnlRate),
                        style: _S.sumPct.copyWith(
                          color: dayColor.withValues(alpha: 0.85),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          // Divider
          Container(width: 1, height: 30, color: AppTheme.dividerColor),
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
                            : (catHoldPnl == null
                                  ? '--'
                                  : appState.formatPnlIntWithCurrency(
                                      catHoldPnl,
                                      '¥',
                                    )),
                        style: _S.sumVal.copyWith(color: holdColor),
                      ),
                      Text(
                        appState.amountHidden
                            ? ''
                            : _fmtPctNullable(catHoldPnlRate),
                        style: _S.sumPct.copyWith(
                          color: holdColor.withValues(alpha: 0.85),
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
    final List<PortfolioItem> filtered = List.from(appState.filteredPortfolio);

    // Sort by today's PnL descending
    filtered.sort((a, b) {
      final pnlA = PortfolioMetricsService.resolveCurrentDayPnlCny(
        a,
        priceInfo: appState.resolvePriceInfo(a),
        fallbackRateToCny: appState.getCurrencyRate(a.curr),
      );
      final pnlB = PortfolioMetricsService.resolveCurrentDayPnlCny(
        b,
        priceInfo: appState.resolvePriceInfo(b),
        fallbackRateToCny: appState.getCurrencyRate(b.curr),
      );
      if (pnlA == null && pnlB == null) return 0;
      if (pnlA == null) return 1;
      if (pnlB == null) return -1;
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
        return Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: RepaintBoundary(child: _buildStockCard(item, appState)),
        );
      }).toList(),
    );
  }

  // ─── Stock Card ────────────────────────────────
  Widget _buildStockCard(PortfolioItem item, AppState appState) {
    final priceInfo = appState.resolvePriceInfo(item);
    final fallbackRateToCny = appState.getCurrencyRate(item.curr);
    final qty = item.qty;
    final rawCostPrice = item.price;
    final displayCostPrice = item.displayCostPrice ?? rawCostPrice;

    final currentPrice = PortfolioMetricsService.resolveCurrentPrice(
      item,
      priceInfo: priceInfo,
    );
    final mv = PortfolioMetricsService.resolveLiveValue(item, priceInfo: priceInfo);
    final holdingPnl = PortfolioMetricsService.resolveLiveTotalPnl(
      item,
      priceInfo: priceInfo,
    );
    final holdingPnlPct = PortfolioMetricsService.resolveLiveTotalPnlRate(
      item,
      priceInfo: priceInfo,
      fallbackRateToCny: fallbackRateToCny,
    );

    final navUpdatePending = appState.isNavUpdatePendingAsset(item);
    final latestNavDate = _readLatestNavDate(item);
    final latestNavDateText = _formatLatestNavDateText(latestNavDate);
    final dayPnlEnabled = appState.isAssetDayPnlDisplayEnabled(
      item,
      priceInfo: priceInfo,
    );
    final dailyPnl = PortfolioMetricsService.resolveCurrentDayPnl(
      item,
      priceInfo: priceInfo,
    );
    final dailyPnlPct = PortfolioMetricsService.resolveCurrentDayPnlRate(
      item,
      priceInfo: priceInfo,
      fallbackRateToCny: fallbackRateToCny,
    );

    // Market type tag
    final marketType = (item.marketType as String? ?? 'a').toLowerCase();
    final tagColors = _tagColors[marketType] ?? _tagColors['a']!;
    final tagLabel = _tagLabels[marketType] ?? 'A股';

    // Currency symbol
    final sym = item.currencySymbol as String? ?? '¥';
    final isFund = _isFundAsset(item);
    final shouldShowFundDayPnlPlaceholder =
        isFund && latestNavDate != null && !_isDateToday(latestNavDate);
    final qtyUnit = isFund ? '份' : '股';
    final name = item.displayName.trim();
    final code = (item.code as String? ?? '').trim();
    final displayName = name.isNotEmpty ? name : _formatDisplayCode(code);

    final positionPct = _readPositionPct(item);
    final positionPctLabel = _formatPositionPctLabel(positionPct);
    final pctBase = positionPct ?? 0.0;
    final positionPctRatio = (pctBase.clamp(0.0, 100.0) / 100.0).toDouble();

    final mvLabel =
        '$sym${appState.formatAmount(mv, prefix: '').replaceFirst('¥', '')}';
    final currentPriceLabel = currentPrice > 0
        ? '$sym${_formatDisplayPrice(currentPrice, item: item)}'
        : '--';
    final costPriceLabel = displayCostPrice == 0
        ? '--'
        : '$sym${_formatDisplayPrice(displayCostPrice, item: item)}';

    final dailyValueColor =
        shouldShowFundDayPnlPlaceholder ||
            navUpdatePending ||
            !dayPnlEnabled ||
            dailyPnl == null
        ? AppTheme.textMuted
        : AppState.getPnlColor(dailyPnl);
    final holdingValueColor = AppState.getPnlColor(holdingPnl);

    final dayPnlValue = shouldShowFundDayPnlPlaceholder || navUpdatePending
        ? '--'
        : (dayPnlEnabled ? _fmtPnlNullable(dailyPnl, sym) : '--');
    final totalPnlValue = _fmtPnlNullable(holdingPnl, sym);
    final badgeLabel = shouldShowFundDayPnlPlaceholder || navUpdatePending
        ? null
        : (dayPnlEnabled ? _fmtPctNullable(dailyPnlPct) : '--');
    final badgeColor = navUpdatePending
        ? AppTheme.textMuted
        : (dailyPnl == null
              ? AppTheme.textMuted
              : AppState.getPnlColor(dailyPnl));
    final badgeBg = navUpdatePending
        ? (AppTheme.isLight ? const Color(0x08222C40) : const Color(0x14FFFFFF))
        : badgeColor.withValues(alpha: AppTheme.isLight ? 0.12 : 0.18);

    final accentColor = dailyPnl == null
        ? AppTheme.border
        : (dailyPnl >= 0 ? AppTheme.danger : AppTheme.success);

    String maskMoney(String value) {
      if (!appState.amountHidden) return value;
      if (value == '--' || value == '待净值更新') {
        return value;
      }
      return '****';
    }

    return GestureDetector(
      onTap: () async {
        final appState = context.read<AppState>();
        await Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => InvestmentDetailPage(item: item)),
        );
        appState.refreshPortfolio();
      },
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: AppTheme.isLight ? AppTheme.border : AppTheme.borderSubtle,
          ),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: AppTheme.cardGradient,
          ),
          boxShadow: AppTheme.cardShadow,
        ),
        clipBehavior: Clip.hardEdge,
        child: Stack(
          children: [
            Positioned(
              left: 0,
              right: 0,
              top: 0,
              height: 2,
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      Colors.transparent,
                      accentColor.withValues(
                        alpha: AppTheme.isLight ? 0.85 : 0.45,
                      ),
                      Colors.transparent,
                    ],
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── Header ──
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.baseline,
                              textBaseline: TextBaseline.alphabetic,
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Flexible(
                                  child: Text(
                                    displayName,
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: _S.cardNameCompact.copyWith(
                                      color: AppTheme.heroValueColor,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 4),
                                Text(
                                  'x ${_formatDisplayQty(qty)} $qtyUnit',
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: _S.cardHoldNum.copyWith(
                                    color: AppTheme.textMuted,
                                    fontSize: 10,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 6,
                                    vertical: 2,
                                  ),
                                  decoration: BoxDecoration(
                                    borderRadius: BorderRadius.circular(4),
                                    color: tagColors.$2,
                                  ),
                                  child: Text(
                                    tagLabel,
                                    style: _S.cardTag.copyWith(
                                      color: tagColors.$1,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 6),
                                Flexible(
                                  child: Text(
                                    maskMoney(mvLabel),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: _S.cardHoldNum.copyWith(
                                      color: AppTheme.textSecondary,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            '今日盈亏',
                            style: _S.cardMiniLabel.copyWith(
                              color: AppTheme.textMuted,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            maskMoney(dayPnlValue),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style:
                                (dayPnlValue == '待净值更新'
                                        ? _S.cardPnlPending
                                        : _S.cardMiniValue)
                                    .copyWith(color: dailyValueColor),
                          ),
                        ],
                      ),
                    ],
                  ),

                  const SizedBox(height: 12),

                  // ── Price + Badge ──
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      Expanded(
                        child: Row(
                          children: [
                            Flexible(
                              child: Builder(
                                builder: (context) {
                                  if (currentPrice <= 0) {
                                    return Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          navUpdatePending
                                              ? '最新净值'
                                              : currentPriceLabel,
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                          style: _S.cardPriceVal.copyWith(
                                            color: AppTheme.textMuted,
                                          ),
                                        ),
                                        if (latestNavDateText != null) ...[
                                          const SizedBox(height: 2),
                                          Text(
                                            '最新净值 $latestNavDateText',
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                            style: _S.cardMiniLabel.copyWith(
                                              color: AppTheme.textMuted,
                                            ),
                                          ),
                                        ],
                                      ],
                                    );
                                  }
                                  if (navUpdatePending) {
                                    return Row(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.baseline,
                                      textBaseline: TextBaseline.alphabetic,
                                      children: [
                                        if (appState.amountHidden)
                                          Text(
                                            '****',
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                            style: _S.cardPriceVal.copyWith(
                                              color: AppTheme.textPrimary,
                                            ),
                                          )
                                        else
                                          RichText(
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                            text: TextSpan(
                                              children: [
                                                TextSpan(
                                                  text: sym,
                                                  style: _S.cardPriceSym
                                                      .copyWith(
                                                        color: AppTheme
                                                            .textSecondary,
                                                      ),
                                                ),
                                                const TextSpan(text: ' '),
                                                TextSpan(
                                                  text: _formatDisplayPrice(
                                                    currentPrice,
                                                    item: item,
                                                  ),
                                                  style: _S.cardPriceVal
                                                      .copyWith(
                                                        color: AppTheme
                                                            .textPrimary,
                                                      ),
                                                ),
                                              ],
                                            ),
                                          ),
                                        if (latestNavDateText != null) ...[
                                          const SizedBox(width: 8),
                                          Flexible(
                                            child: Text(
                                              '最新净值 $latestNavDateText',
                                              maxLines: 1,
                                              overflow: TextOverflow.ellipsis,
                                              style: _S.cardMiniLabel.copyWith(
                                                color: AppTheme.textMuted,
                                              ),
                                            ),
                                          ),
                                        ],
                                      ],
                                    );
                                  }
                                  if (appState.amountHidden) {
                                    return Text(
                                      '****',
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: _S.cardPriceVal.copyWith(
                                        color: AppTheme.textPrimary,
                                      ),
                                    );
                                  }
                                  return RichText(
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    text: TextSpan(
                                      children: [
                                        TextSpan(
                                          text: sym,
                                          style: _S.cardPriceSym.copyWith(
                                            color: AppTheme.textSecondary,
                                          ),
                                        ),
                                        const TextSpan(text: ' '),
                                        TextSpan(
                                          text: _formatDisplayPrice(
                                            currentPrice,
                                            item: item,
                                          ),
                                          style: _S.cardPriceVal.copyWith(
                                            color: AppTheme.textPrimary,
                                          ),
                                        ),
                                      ],
                                    ),
                                  );
                                },
                              ),
                            ),
                            if (badgeLabel != null) ...[
                              const SizedBox(width: 8),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 6,
                                  vertical: 2,
                                ),
                                decoration: BoxDecoration(
                                  color: badgeBg,
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: Text(
                                  badgeLabel,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: _S.cardBadge.copyWith(
                                    color: badgeColor,
                                  ),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            '成本价',
                            style: _S.cardMiniLabel.copyWith(
                              color: AppTheme.textMuted,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            maskMoney(costPriceLabel),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: _S.cardHoldNum.copyWith(
                              color: AppTheme.textSecondary,
                              fontSize: 11,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),

                  const SizedBox(height: 8),
                  // ── Divider ──
                  Container(height: 1, color: AppTheme.dividerColor),

                  const SizedBox(height: 10),

                  // ── 盈亏 + 仓位 ──
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '累计盈亏',
                              style: _S.cardMiniLabel.copyWith(
                                color: AppTheme.textMuted,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Flexible(
                                  child: FittedBox(
                                    fit: BoxFit.scaleDown,
                                    alignment: Alignment.centerLeft,
                                    child: Text(
                                      maskMoney(totalPnlValue),
                                      style: _S.cardMiniValue.copyWith(
                                        color: holdingValueColor,
                                      ),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 4),
                                _buildRateBadge(
                                  label: appState.amountHidden
                                      ? ''
                                      : _fmtPctNullable(holdingPnlPct),
                                  color: holdingValueColor,
                                  muted: holdingPnlPct == null,
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      const SizedBox(width: 8),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '仓位占比',
                            style: _S.cardPositionLabel.copyWith(
                              color: AppTheme.textMuted,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.start,
                            children: [
                              SizedBox(
                                width: 50,
                                child: Container(
                                  height: 2,
                                  decoration: BoxDecoration(
                                    color: AppTheme.isLight
                                        ? const Color(0x0A222C40)
                                        : const Color(0x14FFFFFF),
                                    borderRadius: BorderRadius.circular(2),
                                  ),
                                  child: FractionallySizedBox(
                                    alignment: Alignment.centerLeft,
                                    widthFactor: positionPctRatio,
                                    child: Container(
                                      decoration: BoxDecoration(
                                        color: AppTheme.accent.withValues(
                                          alpha: 0.7,
                                        ),
                                        borderRadius: BorderRadius.circular(2),
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 6),
                              Text(
                                positionPctLabel,
                                style: _S.cardPositionValue.copyWith(
                                  color: AppTheme.accent,
                                  fontSize: 11,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class PnlProgressBar extends StatefulWidget {
  final double costPrice;
  final double currentPrice;
  final double maxRate;

  const PnlProgressBar({
    super.key,
    required this.costPrice,
    required this.currentPrice,
    this.maxRate = 0.30,
  });

  @override
  State<PnlProgressBar> createState() => _PnlProgressBarState();
}

class _PnlProgressBarState extends State<PnlProgressBar>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _anim = CurvedAnimation(parent: _ctrl, curve: Curves.easeOutCubic);
    _ctrl.forward();
  }

  @override
  void didUpdateWidget(PnlProgressBar oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.currentPrice != widget.currentPrice ||
        oldWidget.costPrice != widget.costPrice) {
      _ctrl.forward(from: 0.0);
    }
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.costPrice <= 0) return const SizedBox(height: 3);

    final changeRate =
        (widget.currentPrice - widget.costPrice) / widget.costPrice;
    final fillRatio = (changeRate.abs() / widget.maxRate).clamp(0.0, 1.0) * 0.5;
    final isProfit = changeRate > 0;
    final fillColor = isProfit
        ? const Color(0xFFF05A55)
        : const Color(0xFF2ECC8A);

    return SizedBox(
      height: 3,
      child: AnimatedBuilder(
        animation: _anim,
        builder: (_, child) => CustomPaint(
          size: Size.infinite,
          painter: _PnlBarPainter(
            fillRatio: fillRatio * _anim.value,
            isProfit: isProfit,
            fillColor: fillColor,
            hasChange: changeRate.abs() > 1e-9,
            isLight: AppTheme.isLight,
          ),
        ),
      ),
    );
  }
}

class _PnlBarPainter extends CustomPainter {
  final double fillRatio;
  final bool isProfit;
  final Color fillColor;
  final bool hasChange;
  final bool isLight;

  const _PnlBarPainter({
    required this.fillRatio,
    required this.isProfit,
    required this.fillColor,
    required this.hasChange,
    required this.isLight,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;
    final midX = w * 0.5;
    final radius = Radius.circular(h / 2);

    // 1. Track background
    canvas.drawRRect(
      RRect.fromLTRBR(0, 0, w, h, radius),
      Paint()
        ..color = isLight ? const Color(0x1A222C40) : const Color(0x14FFFFFF),
    );

    // 2. Fill bar
    if (hasChange && fillRatio > 0) {
      final fillW = w * fillRatio;
      final left = isProfit ? midX : midX - fillW;
      final right = isProfit ? midX + fillW : midX;

      final rrect = isProfit
          ? RRect.fromLTRBAndCorners(
              left,
              0,
              right,
              h,
              topRight: radius,
              bottomRight: radius,
            )
          : RRect.fromLTRBAndCorners(
              left,
              0,
              right,
              h,
              topLeft: radius,
              bottomLeft: radius,
            );

      canvas.drawRRect(rrect, Paint()..color = fillColor);
    }

    // 3. Center anchor line (Cost baseline)
    canvas.drawRect(
      Rect.fromLTWH(midX - 0.75, 0, 1.5, h),
      Paint()
        ..color = isLight ? const Color(0x33222C40) : const Color(0x66FFFFFF),
    );
  }

  @override
  bool shouldRepaint(_PnlBarPainter old) =>
      old.fillRatio != fillRatio || old.isProfit != isProfit;
}
