import 'dart:async';

import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../config/theme.dart';
import '../providers/app_overview_state.dart';
import '../providers/app_state.dart';
import '../services/api_service.dart';

class AssetHistoryPage extends StatefulWidget {
  const AssetHistoryPage({super.key});

  @override
  State<AssetHistoryPage> createState() => _AssetHistoryPageState();
}

class _AssetHistoryPageState extends State<AssetHistoryPage> {
  List<dynamic> _allHistory = [];
  // 预计算缓存，避免每次 build 重排
  List<dynamic> _sortedAsc = [];   // 旧→新，用于折线图
  List<dynamic> _sortedDesc = [];  // 新→旧，用于近期变动
  List<dynamic> _filteredHistory = []; // 当前 period 的切片

  bool _loading = true;
  String _chartMode = 'asset'; // 'asset' | 'pnl'
  String _period = '1Y'; // '1M' | '3M' | '6M' | '1Y' | 'ALL'
  int? _touchedIndex;
  int? _touchedDonutIndex;

  static const _periods = [
    ('1M', '近1月'),
    ('3M', '近3月'),
    ('6M', '近半年'),
    ('1Y', '近1年'),
    ('ALL', '全部'),
  ];

  static final bool _isDesktop = defaultTargetPlatform == TargetPlatform.macOS ||
      defaultTargetPlatform == TargetPlatform.windows ||
      defaultTargetPlatform == TargetPlatform.linux;

  double _monthChange = 0;
  double _yearChange = 0;
  double _historyPeak = 0;

  @override
  void initState() {
    super.initState();
    _hydrateHistory();
  }

  Future<void> _hydrateHistory() async {
    final appState = context.read<AppState>();
    final cached = await appState.loadCachedHistory();
    if (!mounted) return;
    if (cached.isNotEmpty) {
      _applyHistory(cached);
      Future<void>(() async {
        await _refreshHistory();
      });
      return;
    }
    await _refreshHistory();
  }

  Future<void> _refreshHistory() async {
    try {
      final list = await ApiService().getHistory();
      if (!mounted) return;
      _applyHistory(list);
    } catch (_) {
      if (!mounted) return;
      if (_allHistory.isEmpty) {
        setState(() => _loading = false);
      }
    }
  }

  void _applyHistory(List<dynamic> list) {
    final stats = AppOverviewState();
    stats.calculateHistoryStats(list, notify: false);
    setState(() {
      _allHistory = list;
      _monthChange = stats.monthChange;
      _yearChange = stats.yearChange;
      _historyPeak = stats.historyPeak;
      _loading = false;
      _rebuildCache();
    });
  }

  // 排序 + 过滤只在数据变化或 period 切换时执行一次
  void _rebuildCache() {
    if (_allHistory.isEmpty) {
      _sortedAsc = [];
      _sortedDesc = [];
      _filteredHistory = [];
      return;
    }
    final asc = [..._allHistory]
      ..sort((a, b) => (a['date'] as String).compareTo(b['date'] as String));
    _sortedAsc = asc;
    _sortedDesc = asc.reversed.toList();
    _filteredHistory = _applyPeriodFilter(asc);
  }

  List<dynamic> _applyPeriodFilter(List<dynamic> asc) {
    final now = DateTime.now();
    final cutoff = switch (_period) {
      '1M' => now.subtract(const Duration(days: 30)),
      '3M' => now.subtract(const Duration(days: 90)),
      '6M' => now.subtract(const Duration(days: 180)),
      '1Y' => now.subtract(const Duration(days: 365)),
      _ => DateTime(2000),
    };
    return asc.where((r) {
      final d = DateTime.tryParse(r['date'] as String);
      return d != null && !d.isBefore(cutoff);
    }).toList();
  }

  String _fmt(double value, {bool showSign = false}) {
    if (value == 0) return '--';
    final sign = showSign && value > 0 ? '+' : '';
    final abs = value.abs().toInt();
    final formatted = abs.toString().replaceAllMapped(
      RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
      (m) => '${m[1]},',
    );
    return '${value < 0 ? '-' : sign}$formatted';
  }

  Color _pnlColor(double value) {
    if (value > 0) return AppTheme.success;
    if (value < 0) return AppTheme.danger;
    return AppTheme.textMuted;
  }

  // ─────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPrimary,
      appBar: AppBar(
        backgroundColor: AppTheme.bgPrimary,
        elevation: 0,
        leading: GestureDetector(
          onTap: () => Navigator.of(context).pop(),
          child: Icon(
            Icons.arrow_back_ios_new_rounded,
            size: 18,
            color: AppTheme.textPrimary,
          ),
        ),
        title: Text(
          '资产历史',
          style: GoogleFonts.dmSans(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            color: AppTheme.textPrimary,
          ),
        ),
        centerTitle: true,
      ),
      body: _loading
          ? Center(child: CircularProgressIndicator(color: AppTheme.accent))
          : SingleChildScrollView(
              padding: EdgeInsets.fromLTRB(
                16,
                8,
                16,
                MediaQuery.of(context).padding.bottom + 24,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildModeTab(),
                  const SizedBox(height: 20),
                  _buildMilestones(),
                  const SizedBox(height: 20),
                  _buildChartCard(),
                  const SizedBox(height: 20),
                  // 只有资产构成需要 AppState，Consumer 收窄到这一块
                  Consumer<AppState>(
                    builder: (context, appState, child) => _buildComposition(appState),
                  ),
                  const SizedBox(height: 20),
                  _buildRecentChanges(),
                ],
              ),
            ),
    );
  }

  // ── 模式切换 Tab ──────────────────────────────────
  Widget _buildModeTab() {
    return Container(
      height: 40,
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        color: AppTheme.isLight ? const Color(0xFFF3F6FB) : AppTheme.surface2,
        border: Border.all(
          color: AppTheme.isLight
              ? const Color(0x14222C40)
              : Colors.white.withValues(alpha: 0.06),
          width: 0.8,
        ),
        boxShadow: AppTheme.isLight
            ? [
                BoxShadow(
                  color: const Color(0x0A222C40),
                  blurRadius: 10,
                  offset: const Offset(0, 3),
                ),
              ]
            : null,
      ),
      child: Row(
        children: [
          _modeTabItem('asset', '总资产趋势'),
          _modeTabItem('pnl', '盈亏趋势'),
        ],
      ),
    );
  }

  Widget _modeTabItem(String mode, String label) {
    final active = _chartMode == mode;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() {
          _chartMode = mode;
          _touchedIndex = null;
        }),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(9),
            color: active
                ? AppTheme.accent
                : (AppTheme.isLight ? Colors.white.withValues(alpha: 0.55) : Colors.transparent),
            border: active
                ? null
                : Border.all(
                    color: AppTheme.isLight
                        ? const Color(0x10222C40)
                        : Colors.transparent,
                    width: 0.6,
                  ),
            boxShadow: active && AppTheme.isLight
                ? [
                    BoxShadow(
                      color: AppTheme.accent.withValues(alpha: 0.18),
                      blurRadius: 12,
                      offset: const Offset(0, 4),
                    ),
                  ]
                : null,
          ),
          alignment: Alignment.center,
          child: Text(
            label,
            style: GoogleFonts.dmSans(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: active ? Colors.white : AppTheme.textSecondary,
            ),
          ),
        ),
      ),
    );
  }

  // ── 里程碑 3 格 ──────────────────────────────────
  Widget _buildMilestones() {
    return Row(
      children: [
        _milestoneCard('历史最高', _fmt(_historyPeak), AppTheme.gold),
        const SizedBox(width: 8),
        _milestoneCard('本月变化', _fmt(_monthChange, showSign: true), _pnlColor(_monthChange)),
        const SizedBox(width: 8),
        _milestoneCard('今年变化', _fmt(_yearChange, showSign: true), _pnlColor(_yearChange)),
      ],
    );
  }

  Widget _milestoneCard(String label, String value, Color valueColor) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: AppTheme.isLight
                ? const Color(0x0A222C40)
                : Colors.white.withValues(alpha: 0.06),
          ),
          color: AppTheme.isLight ? Colors.white : AppTheme.surface2,
          boxShadow: AppTheme.cardShadow,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: GoogleFonts.dmSans(fontSize: 10, color: AppTheme.textMuted),
            ),
            const SizedBox(height: 4),
            Text(
              value,
              style: GoogleFonts.jetBrainsMono(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: valueColor,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
      ),
    );
  }

  // ── 折线图卡片 ───────────────────────────────────
  Widget _buildChartCard() {
    final filtered = _filteredHistory;
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 14, 12, 12),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.isLight
              ? const Color(0x0A222C40)
              : Colors.white.withValues(alpha: 0.06),
        ),
        color: AppTheme.isLight ? Colors.white : AppTheme.surface2,
        boxShadow: AppTheme.cardShadow,
      ),
      child: Column(
        children: [
          _buildPeriodSelector(),
          const SizedBox(height: 12),
          SizedBox(
            height: 180,
            child: filtered.isEmpty
                ? Center(
                    child: Text(
                      '暂无数据',
                      style: GoogleFonts.dmSans(
                        color: AppTheme.textMuted,
                        fontSize: 13,
                      ),
                    ),
                  )
                : _buildLineChart(filtered),
          ),
          if (_touchedIndex != null &&
              _touchedIndex! >= 0 &&
              _touchedIndex! < filtered.length)
            _buildTouchInfo(filtered[_touchedIndex!], filtered),
        ],
      ),
    );
  }

  Widget _buildPeriodSelector() {
    return Row(
      children: _periods.map(((String, String) p) {
        final key = p.$1;
        final label = p.$2;
        final active = _period == key;
        return Padding(
          padding: const EdgeInsets.only(right: 4),
          child: GestureDetector(
            onTap: () => setState(() {
              _period = key;
              _touchedIndex = null;
              _filteredHistory = _applyPeriodFilter(_sortedAsc);
            }),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 150),
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(6),
                color: active
                    ? AppTheme.accent.withValues(alpha: 0.15)
                    : Colors.transparent,
              ),
              child: Text(
                label,
                style: GoogleFonts.dmSans(
                  fontSize: 12,
                  fontWeight: active ? FontWeight.w600 : FontWeight.w400,
                  color: active ? AppTheme.accent : AppTheme.textMuted,
                ),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildLineChart(List<dynamic> data) {
    final isAsset = _chartMode == 'asset';
    final spots = <FlSpot>[];
    for (var i = 0; i < data.length; i++) {
      final y = isAsset
          ? (data[i]['total_asset'] as num).toDouble()
          : (data[i]['total_pnl'] as num).toDouble();
      spots.add(FlSpot(i.toDouble(), y));
    }
    if (spots.isEmpty) return const SizedBox();

    final ys = spots.map((s) => s.y).toList();
    final minY = ys.reduce((a, b) => a < b ? a : b);
    final maxY = ys.reduce((a, b) => a > b ? a : b);
    final yRange = (maxY - minY).abs();
    final yPad = yRange == 0 ? 1000.0 : yRange * 0.12;

    final lastY = spots.last.y;
    final lineColor = isAsset
        ? AppTheme.accent
        : (lastY >= 0 ? AppTheme.success : AppTheme.danger);

    return LineChart(
      LineChartData(
        minX: 0,
        maxX: (spots.length - 1).toDouble(),
        minY: minY - yPad,
        maxY: maxY + yPad,
        gridData: const FlGridData(show: false),
        borderData: FlBorderData(show: false),
        titlesData: const FlTitlesData(show: false),
        lineTouchData: _isDesktop
            ? const LineTouchData(enabled: false)
            : LineTouchData(
                enabled: true,
                touchCallback: (event, response) {
                  if (event is FlTapUpEvent ||
                      event is FlPanEndEvent ||
                      event is FlPointerExitEvent) {
                    if (_touchedIndex != null) {
                      setState(() => _touchedIndex = null);
                    }
                    return;
                  }
                  final idx =
                      response?.lineBarSpots?.firstOrNull?.spotIndex;
                  if (idx != _touchedIndex) {
                    setState(() => _touchedIndex = idx);
                  }
                },
                getTouchedSpotIndicator: (_, spotIndexes) => spotIndexes
                    .map(
                      (_) => TouchedSpotIndicatorData(
                        FlLine(
                          color: lineColor.withValues(alpha: 0.45),
                          strokeWidth: 1,
                          dashArray: [4, 4],
                        ),
                        FlDotData(
                          show: true,
                          getDotPainter: (spot, xPercentage, bar, index) =>
                              FlDotCirclePainter(
                            radius: 4,
                            color: lineColor,
                            strokeWidth: 2,
                            strokeColor: AppTheme.bgPrimary,
                          ),
                        ),
                      ),
                    )
                    .toList(),
                touchTooltipData: const LineTouchTooltipData(
                  tooltipBgColor: Colors.transparent,
                  tooltipPadding: EdgeInsets.zero,
                ),
              ),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            curveSmoothness: 0.3,
            color: lineColor,
            barWidth: 2,
            isStrokeCapRound: true,
            dotData: const FlDotData(show: false),
            belowBarData: BarAreaData(
              show: true,
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  lineColor.withValues(alpha: 0.22),
                  lineColor.withValues(alpha: 0.0),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTouchInfo(dynamic item, List<dynamic> filtered) {
    final isAsset = _chartMode == 'asset';
    final date = item['date'] as String;
    final value = isAsset
        ? (item['total_asset'] as num).toDouble()
        : (item['total_pnl'] as num).toDouble();
    final color = isAsset ? AppTheme.accent : _pnlColor(value);
    return Padding(
      padding: const EdgeInsets.only(top: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            date,
            style: GoogleFonts.dmSans(fontSize: 11, color: AppTheme.textMuted),
          ),
          const SizedBox(width: 8),
          Text(
            '¥${_fmt(value, showSign: !isAsset)}',
            style: GoogleFonts.jetBrainsMono(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  // ── 资产构成（环形图） ────────────────────────────
  Widget _buildComposition(AppState appState) {
    final items = [
      ('投资', appState.totalInvest, AppTheme.accent),
      ('现金', appState.totalCash, AppTheme.success),
      ('其他', appState.totalOther, AppTheme.gold),
      ('负债', appState.totalLiability, AppTheme.danger),
    ];
    final total = items.fold(0.0, (sum, e) => sum + e.$2.abs());

    // 只把有值的条目放进饼图，保留原始 index 用于 touch 高亮
    final pieItems = items.asMap().entries
        .where((e) => e.value.$2.abs() > 0)
        .toList();

    // 最大占比条目（显示在圆心）
    final dominant = pieItems.isNotEmpty
        ? pieItems.reduce((a, b) => a.value.$2.abs() > b.value.$2.abs() ? a : b)
        : null;

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.isLight
              ? const Color(0x0A222C40)
              : Colors.white.withValues(alpha: 0.06),
        ),
        color: AppTheme.isLight ? Colors.white : AppTheme.surface2,
        boxShadow: AppTheme.cardShadow,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '资产构成',
            style: GoogleFonts.dmSans(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: AppTheme.textPrimary,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // 环形图 + 圆心文字
              SizedBox(
                width: 108,
                height: 108,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    total == 0
                        ? Center(
                            child: Text(
                              '--',
                              style: GoogleFonts.dmSans(
                                color: AppTheme.textMuted,
                              ),
                            ),
                          )
                        : PieChart(
                            PieChartData(
                              sections: pieItems.map((entry) {
                                final origIdx = entry.key;
                                final item = entry.value;
                                final isTouched = _touchedDonutIndex == origIdx;
                                return PieChartSectionData(
                                  value: item.$2.abs(),
                                  color: item.$3,
                                  radius: isTouched ? 26 : 20,
                                  title: '',
                                  borderSide: isTouched
                                      ? BorderSide(color: item.$3, width: 2)
                                      : const BorderSide(
                                          color: Colors.transparent,
                                          width: 0,
                                        ),
                                );
                              }).toList(),
                              centerSpaceRadius: 30,
                              sectionsSpace: 2,
                              pieTouchData: _isDesktop
                                  ? PieTouchData(enabled: false)
                                  : PieTouchData(
                                      touchCallback: (event, response) {
                                        if (event is FlPointerExitEvent) {
                                          return; // 不清除，保持选中
                                        }
                                        if (event is FlTapUpEvent) {
                                          final sectionIdx = response
                                              ?.touchedSection
                                              ?.touchedSectionIndex;
                                          final origIdx =
                                              (sectionIdx != null &&
                                                      sectionIdx >= 0 &&
                                                      sectionIdx <
                                                          pieItems.length)
                                                  ? pieItems[sectionIdx].key
                                                  : null;
                                          // 点同一个则取消，点不同的则切换
                                          final newIdx =
                                              origIdx == _touchedDonutIndex
                                                  ? null
                                                  : origIdx;
                                          if (newIdx != _touchedDonutIndex) {
                                            setState(() =>
                                                _touchedDonutIndex = newIdx);
                                          }
                                          return;
                                        }
                                      },
                                    ),
                            ),
                          ),
                    // 圆心：选中项 or 最大占比
                    Builder(builder: (_) {
                      // 优先显示被触摸选中的分类
                      final activeIdx = _touchedDonutIndex;
                      final active = activeIdx != null &&
                              activeIdx < items.length
                          ? items[activeIdx]
                          : dominant?.value;
                      if (active == null || total == 0) {
                        return const SizedBox.shrink();
                      }
                      final pct =
                          '${(active.$2.abs() / total * 100).toStringAsFixed(0)}%';
                      return Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            pct,
                            style: GoogleFonts.jetBrainsMono(
                              fontSize: 13,
                              fontWeight: FontWeight.w700,
                              color: active.$3,
                              height: 1.1,
                            ),
                          ),
                          Text(
                            active.$1,
                            style: GoogleFonts.dmSans(
                              fontSize: 9,
                              color: AppTheme.textMuted,
                              height: 1.2,
                            ),
                          ),
                        ],
                      );
                    }),
                  ],
                ),
              ),

              const SizedBox(width: 18),

              // 图例：严格三列对齐
              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: items.asMap().entries.map((entry) {
                    final idx = entry.key;
                    final item = entry.value;
                    final hasValue = item.$2.abs() > 0;
                    final pct = total > 0 ? item.$2.abs() / total : 0.0;
                    final highlighted = _touchedDonutIndex == idx;

                    return AnimatedContainer(
                      duration: const Duration(milliseconds: 150),
                      margin: const EdgeInsets.only(bottom: 5),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 6,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(6),
                        color: highlighted
                            ? item.$3.withValues(
                                alpha: AppTheme.isLight ? 0.08 : 0.12,
                              )
                            : Colors.transparent,
                      ),
                      child: Row(
                        children: [
                          // 色块
                          Container(
                            width: 7,
                            height: 7,
                            decoration: BoxDecoration(
                              color: hasValue
                                  ? item.$3
                                  : item.$3.withValues(alpha: 0.25),
                              borderRadius: BorderRadius.circular(2),
                            ),
                          ),
                          const SizedBox(width: 6),
                          // 分类名（固定宽度）
                          SizedBox(
                            width: 28,
                            child: Text(
                              item.$1,
                              maxLines: 1,
                              style: GoogleFonts.dmSans(
                                fontSize: 12,
                                color: hasValue
                                    ? (highlighted
                                        ? AppTheme.textPrimary
                                        : AppTheme.textSecondary)
                                    : AppTheme.textDim,
                                fontWeight: highlighted
                                    ? FontWeight.w600
                                    : FontWeight.w400,
                              ),
                            ),
                          ),
                          // 金额（右对齐固定宽度）
                          Expanded(
                            child: Text(
                              hasValue ? '¥${_fmt(item.$2)}' : '--',
                              textAlign: TextAlign.right,
                              style: GoogleFonts.jetBrainsMono(
                                fontSize: 11,
                                color: hasValue
                                    ? (highlighted
                                        ? AppTheme.textPrimary
                                        : AppTheme.textSecondary)
                                    : AppTheme.textDim,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(width: 8),
                          // 百分比（固定宽度右对齐）
                          SizedBox(
                            width: 36,
                            child: Text(
                              hasValue
                                  ? '${(pct * 100).toStringAsFixed(1)}%'
                                  : '--',
                              textAlign: TextAlign.right,
                              style: GoogleFonts.dmSans(
                                fontSize: 10,
                                color: hasValue
                                    ? (highlighted
                                        ? item.$3
                                        : AppTheme.textMuted)
                                    : AppTheme.textDim,
                                fontWeight: highlighted
                                    ? FontWeight.w600
                                    : FontWeight.w400,
                              ),
                            ),
                          ),
                        ],
                      ),
                    );
                  }).toList(),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ── 近期日变动 ───────────────────────────────────
  static const _weekdays = ['一', '二', '三', '四', '五', '六', '日'];

  Widget _buildRecentChanges() {
    if (_sortedDesc.isEmpty) return const SizedBox();
    final recent = _sortedDesc.take(30).toList();
    final maxAbsPnl = recent
        .map((e) => ((e['day_pnl'] as num? ?? 0).toDouble()).abs())
        .fold(0.0, (a, b) => a > b ? a : b);

    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.isLight
              ? const Color(0x0A222C40)
              : Colors.white.withValues(alpha: 0.06),
        ),
        color: AppTheme.isLight ? Colors.white : AppTheme.surface2,
        boxShadow: AppTheme.cardShadow,
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 10),
              child: Row(
                children: [
                  Text(
                    '近期日变动',
                    style: GoogleFonts.dmSans(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  const Spacer(),
                  Text(
                    '最近 ${recent.length} 天',
                    style: GoogleFonts.dmSans(
                      fontSize: 11,
                      color: AppTheme.textMuted,
                    ),
                  ),
                ],
              ),
            ),
            ...recent.asMap().entries.map((entry) {
              return _recentRow(
                entry.value,
                maxAbsPnl: maxAbsPnl,
                isLast: entry.key == recent.length - 1,
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _recentRow(
    dynamic item, {
    required double maxAbsPnl,
    required bool isLast,
  }) {
    final date = item['date'] as String;
    final parts = date.split('-');
    final month = parts.length == 3 ? '${int.tryParse(parts[1]) ?? parts[1]}月' : '';
    final day = parts.length == 3 ? parts[2] : date;

    // 星期
    String weekday = '';
    try {
      final dt = DateTime.parse(date);
      weekday = '周${_weekdays[dt.weekday - 1]}';
    } catch (_) {}

    final dayPnl = (item['day_pnl'] as num? ?? 0).toDouble();
    final totalAsset = (item['total_asset'] as num).toDouble();
    final isPositive = dayPnl > 0;
    final isNegative = dayPnl < 0;
    final pnlColor = _pnlColor(dayPnl);
    final pnlSign = isPositive ? '+' : '';
    final barRatio = maxAbsPnl > 0 ? (dayPnl.abs() / maxAbsPnl).clamp(0.0, 1.0) : 0.0;
    final accentColor = isPositive
        ? AppTheme.success
        : isNegative
            ? AppTheme.danger
            : AppTheme.textMuted;

    return Container(
      decoration: BoxDecoration(
        border: Border(
          left: BorderSide(color: accentColor.withValues(alpha: 0.7), width: 3),
          bottom: isLast
              ? BorderSide.none
              : BorderSide(
                  color: AppTheme.isLight
                      ? const Color(0x07222C40)
                      : Colors.white.withValues(alpha: 0.04),
                ),
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(13, 10, 16, 10),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // 日期列
            SizedBox(
              width: 42,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    day,
                    style: GoogleFonts.jetBrainsMono(
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                      color: AppTheme.textPrimary,
                      height: 1.0,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '$month $weekday',
                    style: GoogleFonts.dmSans(
                      fontSize: 9,
                      color: AppTheme.textMuted,
                      height: 1.0,
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(width: 12),

            // 涨跌 + 相对进度条
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    dayPnl == 0
                        ? '持平'
                        : '¥$pnlSign${_fmt(dayPnl)}',
                    style: GoogleFonts.jetBrainsMono(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: dayPnl == 0 ? AppTheme.textMuted : pnlColor,
                      height: 1.2,
                    ),
                  ),
                  const SizedBox(height: 5),
                  // 相对变化进度条
                  LayoutBuilder(
                    builder: (ctx, bc) => Stack(
                      children: [
                        Container(
                          height: 2,
                          width: bc.maxWidth,
                          decoration: BoxDecoration(
                            color: accentColor.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(1),
                          ),
                        ),
                        Container(
                          height: 2,
                          width: bc.maxWidth * barRatio,
                          decoration: BoxDecoration(
                            color: accentColor.withValues(alpha: 0.55),
                            borderRadius: BorderRadius.circular(1),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(width: 14),

            // 总资产
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '¥${_fmt(totalAsset)}',
                  style: GoogleFonts.jetBrainsMono(
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                    color: AppTheme.textSecondary,
                    height: 1.2,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  '总资产',
                  style: GoogleFonts.dmSans(
                    fontSize: 9,
                    color: AppTheme.textMuted,
                    height: 1.0,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
