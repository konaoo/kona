import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../services/api_service.dart';
import '../providers/app_state.dart';

/// 分析页面 - 盈亏分析
class AnalysisPage extends StatefulWidget {
  const AnalysisPage({super.key});

  @override
  State<AnalysisPage> createState() => _AnalysisPageState();
}

class _AnalysisPageState extends State<AnalysisPage> {
  final ApiService _api = ApiService();
  String _currentPeriod = 'day';
  Map<String, dynamic> _overview = {};
  bool _loading = true;
  bool _overviewLoaded = false;

  // 收益日历相关
  String _calendarTimeType = 'day';
  Map<String, dynamic> _calendarData = {};
  bool _calendarLoading = false;
  final Map<String, Map<String, dynamic>> _calendarCache = {};

  // 盈亏排行相关
  String _rankType = 'profit'; // 'profit' 或 'loss'

  @override
  void initState() {
    super.initState();
    _loadData();
    _loadCalendar();
  }

  Future<void> _loadData({bool force = false}) async {
    if (_overviewLoaded && !force) return;
    setState(() => _loading = true);
    try {
      final data = await _api.getAnalysisOverview(period: 'all');
      setState(() {
        _overview = data;
        _loading = false;
        _overviewLoaded = true;
      });
    } catch (e) {
      debugPrint('加载分析数据失败: $e');
      setState(() => _loading = false);
    }
  }

  Future<void> _loadCalendar({bool force = false}) async {
    if (_calendarCache.containsKey(_calendarTimeType) && !force) {
      setState(() {
        _calendarData = _calendarCache[_calendarTimeType] ?? {};
        _calendarLoading = false;
      });
      return;
    }
    setState(() => _calendarLoading = true);
    try {
      final data = await _api.getAnalysisCalendar(timeType: _calendarTimeType);
      debugPrint('收益日历数据: $data');
      setState(() {
        _calendarData = data;
        _calendarCache[_calendarTimeType] = data;
        _calendarLoading = false;
      });
    } catch (e) {
      debugPrint('加载收益日历失败: $e');
      setState(() => _calendarLoading = false);
    }
  }

  void _changePeriod(String period) {
    setState(() => _currentPeriod = period);
  }

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();
    return SingleChildScrollView(
      padding: const EdgeInsets.all(Spacing.xl),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 盈亏概览卡片
          _buildOverviewCard(appState),
          const SizedBox(height: Spacing.xl),
          // 收益日历
          _buildCalendarSection(appState),
          const SizedBox(height: Spacing.xl),
          // 盈亏排行
          _buildRankSection(appState),
        ],
      ),
    );
  }

  Widget _buildOverviewCard(AppState appState) {
    final periodData = _overview[_currentPeriod] ?? {};
    final apiPnl = (periodData['pnl'] as num?)?.toDouble();
    final apiRate = (periodData['pnl_rate'] as num?)?.toDouble();
    final isDay = _currentPeriod == 'day';
    final pnl = isDay ? appState.investDayPnl : (apiPnl ?? 0);
    final pnlRate = isDay ? appState.investDayPnlRate : (apiRate ?? 0);
    final pnlColor = pnl >= 0 ? const Color(0xFFEF4444) : const Color(0xFF10B981);
    final showLoading = _loading && !_overviewLoaded && !isDay;

    return Container(
      padding: const EdgeInsets.all(Spacing.xl),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: AppTheme.cardGradient,
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(AppRadius.xl),
      ),
      child: Column(
        children: [
          Text(
            _getPeriodTitle(_currentPeriod),
            style: const TextStyle(fontSize: FontSize.sm, color: AppTheme.textSecondary),
          ),
          const SizedBox(height: 4),
          Text(
            showLoading ? '加载中...' : '¥${pnl.toStringAsFixed(0)}',
            style: TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.bold,
              color: showLoading ? AppTheme.textPrimary : pnlColor,
            ),
          ),
          const SizedBox(height: 4),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                pnl >= 0 ? Icons.trending_up : Icons.trending_down,
                size: 16,
                color: showLoading ? AppTheme.textTertiary : pnlColor,
              ),
              const SizedBox(width: 4),
              Text(
                showLoading ? '--' : '收益率 ${pnlRate.toStringAsFixed(2)}%',
                style: TextStyle(fontSize: FontSize.sm, color: showLoading ? AppTheme.textTertiary : pnlColor),
              ),
            ],
          ),
          const SizedBox(height: Spacing.lg),
          // 周期切换
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _buildPeriodTab('当日', 'day'),
              _buildPeriodTab('本月', 'month'),
              _buildPeriodTab('今年', 'year'),
              _buildPeriodTab('全部', 'all'),
            ],
          ),
        ],
      ),
    );
  }

  String _getPeriodTitle(String period) {
    switch (period) {
      case 'day':
        return '今日盈亏';
      case 'month':
        return '本月盈亏';
      case 'year':
        return '今年盈亏';
      case 'all':
        return '累计盈亏';
      default:
        return '盈亏';
    }
  }

  Widget _buildPeriodTab(String label, String value) {
    final isSelected = _currentPeriod == value;
    return GestureDetector(
      onTap: () => _changePeriod(value),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.accent : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: FontSize.sm,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            color: isSelected ? AppTheme.textPrimary : AppTheme.textTertiary,
          ),
        ),
      ),
    );
  }

  Widget _buildCalendarSection(AppState appState) {
    // 根据时间类型生成日期网格数据
    final now = DateTime.now();
    List<Map<String, dynamic>> calendarGrid = [];

    if (_calendarTimeType == 'day') {
      // 显示本月每天，以日历网格形式
      final firstDayOfMonth = DateTime(now.year, now.month, 1);
      final lastDayOfMonth = DateTime(now.year, now.month + 1, 0);
      final daysInMonth = lastDayOfMonth.day;

      // 生成本月所有日期
      for (int i = 1; i <= daysInMonth; i++) {
        final date = DateTime(now.year, now.month, i);
        final dateStr = '${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
        calendarGrid.add({
          'day': i,
          'date': dateStr,
          'pnl': null,
        });
      }
    } else if (_calendarTimeType == 'month') {
      // 显示今年12个月
      for (int i = 1; i <= 12; i++) {
        calendarGrid.add({
          'day': i,
          'date': '${i}月',
          'pnl': null,
        });
      }
    } else {
      // 显示最近5年
      for (int i = 0; i < 5; i++) {
        final year = now.year - 4 + i;
        calendarGrid.add({
          'day': year,
          'date': '${year}年',
          'pnl': null,
        });
      }
    }

    // 如果有实际数据，填充到网格中（用精确匹配）
    final items = _calendarData['items'] as List<dynamic>? ?? [];
    final pnlMap = <int, double>{};
    for (var item in items) {
      final label = item['label'] ?? '';
      final pnl = (item['pnl'] as num?)?.toDouble();
      final key = _parseLabelKey(label.toString());
      if (key != null && pnl != null) {
        pnlMap[key] = pnl;
      }
    }
    // 当天数据始终用实时日盈亏，确保与“今日盈亏”一致
    if (_calendarTimeType == 'day') {
      final todayKey = DateTime.now().day;
      pnlMap[todayKey] = appState.investDayPnl;
    }

    for (var gridItem in calendarGrid) {
      final key = gridItem['day'] as int;
      if (pnlMap.containsKey(key)) {
        gridItem['pnl'] = pnlMap[key];
      }
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              '收益日历',
              style: TextStyle(
                fontSize: FontSize.xl,
                fontWeight: FontWeight.bold,
                color: AppTheme.textPrimary,
              ),
            ),
            Container(
              padding: const EdgeInsets.all(2),
              decoration: BoxDecoration(
                color: AppTheme.bgCard,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  _buildToggle('日', _calendarTimeType == 'day', () {
                    setState(() => _calendarTimeType = 'day');
                    _loadCalendar();
                  }),
                  _buildToggle('月', _calendarTimeType == 'month', () {
                    setState(() => _calendarTimeType = 'month');
                    _loadCalendar();
                  }),
                  _buildToggle('年', _calendarTimeType == 'year', () {
                    setState(() => _calendarTimeType = 'year');
                    _loadCalendar();
                  }),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: Spacing.md),
        Container(
          padding: const EdgeInsets.all(Spacing.lg),
          decoration: BoxDecoration(
            color: AppTheme.bgCard,
            borderRadius: BorderRadius.circular(AppRadius.lg),
          ),
          child: _calendarLoading
              ? const Center(
                  child: CircularProgressIndicator(color: AppTheme.accent),
                )
              : GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: _calendarTimeType == 'day' ? 7 : (_calendarTimeType == 'month' ? 4 : 5),
                    childAspectRatio: _calendarTimeType == 'day' ? 0.85 : 1.0,
                    crossAxisSpacing: 8,
                    mainAxisSpacing: 8,
                  ),
                  itemCount: calendarGrid.length,
                  itemBuilder: (context, index) {
                    final item = calendarGrid[index];
                    final day = item['day'];
                    final pnl = item['pnl'] as double?;

                    Color backgroundColor;
                    Color textColor;

                    if (pnl != null) {
                      if (pnl > 0) {
                        backgroundColor = const Color(0xFFEF4444).withOpacity(0.15);
                        textColor = const Color(0xFFEF4444);
                      } else if (pnl < 0) {
                        backgroundColor = const Color(0xFF10B981).withOpacity(0.15);
                        textColor = const Color(0xFF10B981);
                      } else {
                        backgroundColor = AppTheme.bgElevated;
                        textColor = AppTheme.textSecondary;
                      }
                    } else {
                      backgroundColor = AppTheme.bgElevated;
                      textColor = AppTheme.textTertiary;
                    }

                    return Container(
                      decoration: BoxDecoration(
                        color: backgroundColor,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            _calendarTimeType == 'day'
                                ? day.toString()
                                : (_calendarTimeType == 'month' ? '${day}月' : day.toString()),
                            style: TextStyle(
                              fontSize: FontSize.sm,
                              color: textColor,
                              fontWeight: pnl != null ? FontWeight.bold : FontWeight.normal,
                            ),
                          ),
                          if (pnl != null) ...[
                            const SizedBox(height: 2),
                            Text(
                              _formatCalendarPnl(pnl),
                              style: TextStyle(
                                fontSize: 11,
                                color: textColor,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ] else ...[
                            const SizedBox(height: 2),
                            Text(
                              '-',
                              style: TextStyle(
                                fontSize: 11,
                                color: textColor,
                              ),
                            ),
                          ],
                        ],
                      ),
                    );
                  },
                ),
        ),
        const SizedBox(height: Spacing.md),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: Spacing.lg, vertical: Spacing.sm),
          decoration: BoxDecoration(
            color: AppTheme.bgElevated,
            borderRadius: BorderRadius.circular(AppRadius.lg),
          ),
          child: Align(
            alignment: Alignment.centerLeft,
            child: Text(
              _calendarSummaryText(),
              style: const TextStyle(fontSize: FontSize.sm, color: AppTheme.textSecondary),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildToggle(String text, bool isSelected, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.accent : Colors.transparent,
          borderRadius: BorderRadius.circular(6),
        ),
        child: Text(
          text,
          style: TextStyle(
            fontSize: FontSize.sm,
            color: isSelected ? AppTheme.textPrimary : AppTheme.textSecondary,
          ),
        ),
      ),
    );
  }

  Widget _buildRankSection(AppState appState) {
    final rankItems = _buildRankItems(appState);
    final rankList =
        _rankType == 'profit' ? rankItems.where((x) => x.pnl > 0).toList() : rankItems.where((x) => x.pnl < 0).toList();
    if (_rankType == 'profit') {
      rankList.sort((a, b) => b.pnl.compareTo(a.pnl));
    } else {
      rankList.sort((a, b) => a.pnl.compareTo(b.pnl));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          '盈亏排行',
          style: TextStyle(
            fontSize: FontSize.xl,
            fontWeight: FontWeight.bold,
            color: AppTheme.textPrimary,
          ),
        ),
        const SizedBox(height: Spacing.md),
        Row(
          children: [
            _buildRankTab('盈利榜', _rankType == 'profit', () {
              setState(() => _rankType = 'profit');
            }),
            const SizedBox(width: Spacing.sm),
            _buildRankTab('亏损榜', _rankType == 'loss', () {
              setState(() => _rankType = 'loss');
            }),
            const Spacer(),
            GestureDetector(
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => AnalysisRankAllPage(rankType: _rankType)),
                );
              },
              child: const Text(
                '查看全部 >',
                style: TextStyle(fontSize: FontSize.base, color: AppTheme.accentLight),
              ),
            ),
          ],
        ),
        const SizedBox(height: Spacing.md),
        if (rankList.isEmpty)
          Container(
            padding: const EdgeInsets.all(Spacing.lg),
            decoration: BoxDecoration(
              color: AppTheme.bgCard,
              borderRadius: BorderRadius.circular(AppRadius.lg),
            ),
            child: const Center(
              child: Padding(
                padding: EdgeInsets.all(24.0),
                child: Text(
                  '暂无数据',
                  style: TextStyle(color: AppTheme.textTertiary),
                ),
              ),
            ),
          )
        else
          Column(
            children: rankList.take(5).toList().asMap().entries.map((entry) {
              final idx = entry.key;
              final item = entry.value;
              return _buildRankCard(item, appState, idx + 1);
            }).toList(),
          ),
      ],
    );
  }

  Widget _buildRankTab(String text, bool isSelected, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: Spacing.md, vertical: Spacing.sm),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.accent : Colors.transparent,
          borderRadius: BorderRadius.circular(AppRadius.md),
        ),
        child: Text(
          text,
          style: TextStyle(
            fontSize: FontSize.lg,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            color: isSelected ? AppTheme.textPrimary : AppTheme.textTertiary,
          ),
        ),
      ),
    );
  }

  List<_RankItem> _buildRankItems(AppState appState) {
    final items = <_RankItem>[];
    for (final item in appState.portfolio) {
      final priceInfo = appState.prices[item.code];
      final hasValidPrice = priceInfo != null && priceInfo.price > 0;
      final currentPrice = hasValidPrice ? priceInfo.price : item.price;
      final mv = currentPrice * item.qty;
      final cost = item.price * item.qty;
      final pnl = mv - cost + item.adjustment;
      final pnlRate = cost > 0 ? (pnl / cost * 100) : 0.0;
      items.add(_RankItem(
        code: item.code,
        name: item.name,
        pnl: pnl,
        pnlRate: pnlRate,
        currencySymbol: item.currencySymbol,
      ));
    }
    return items;
  }

  Widget _buildRankCard(_RankItem item, AppState appState, int rank) {
    final pnlColor = AppState.getPnlColor(item.pnl);
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 6),
      padding: const EdgeInsets.all(Spacing.md),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(AppRadius.md),
      ),
      child: Row(
        children: [
          _rankBadge(rank),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.name,
                  style: const TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: FontSize.base,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  _formatDisplayCode(item.code),
                  style: const TextStyle(color: AppTheme.textTertiary, fontSize: FontSize.sm),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                appState.formatPnlIntWithCurrency(item.pnl, item.currencySymbol),
                style: TextStyle(color: pnlColor, fontSize: FontSize.base, fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 2),
              Text(
                appState.formatPct(item.pnlRate),
                style: TextStyle(color: pnlColor, fontSize: FontSize.sm),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _formatDisplayCode(String code) {
    const customMap = {
      'ft_LU1116320737': 'BLK',
    };
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
    if (c.toUpperCase().endsWith('.HK')) {
      c = c.substring(0, c.length - 3);
    }
    return c;
  }

  int? _parseLabelKey(String label) {
    final match = RegExp(r'\d+').allMatches(label).toList();
    if (match.isEmpty) return null;
    final last = match.last.group(0);
    if (last == null) return null;
    return int.tryParse(last);
  }

  String _formatCalendarPnl(double pnl) {
    final absVal = pnl.abs().toStringAsFixed(0);
    if (pnl > 0) return '+$absVal';
    if (pnl < 0) return '-$absVal';
    return '0';
  }

  String _calendarSummaryText() {
    final totalPnl = (_calendarData['total_pnl'] as num?)?.toDouble() ?? 0.0;
    final totalRate = (_calendarData['total_rate'] as num?)?.toDouble() ?? 0.0;
    final label = _calendarTimeType == 'day'
        ? '本月累计'
        : (_calendarTimeType == 'month' ? '当年累计' : '历史累计');
    final sign = totalPnl > 0 ? '+' : (totalPnl < 0 ? '-' : '');
    final amount = totalPnl.abs().toStringAsFixed(0).replaceAllMapped(
      RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
      (Match m) => '${m[1]},',
    );
    final rateSign = totalRate >= 0 ? '+' : '';
    return '$label  ${sign}$amount   收益率 ${rateSign}${totalRate.toStringAsFixed(2)}%';
  }

  Widget _rankBadge(int rank) {
    if (rank <= 3) {
      final gradients = [
        const [Color(0xFFFDE68A), Color(0xFFF59E0B)], // gold
        const [Color(0xFFE5E7EB), Color(0xFF94A3B8)], // silver
        const [Color(0xFFFED7AA), Color(0xFFEA580C)], // bronze
      ];
      final g = gradients[rank - 1];
      return SizedBox(
        width: 32,
        height: 32,
        child: Stack(
          alignment: Alignment.center,
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                gradient: LinearGradient(colors: g, begin: Alignment.topLeft, end: Alignment.bottomRight),
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: g[1].withOpacity(0.25),
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
            ),
            const Icon(Icons.military_tech, size: 16, color: Color(0xFF0F172A)),
            Positioned(
              bottom: 2,
              child: Text(
                '$rank',
                style: const TextStyle(fontSize: 10, color: Color(0xFF0F172A), fontWeight: FontWeight.w800),
              ),
            ),
          ],
        ),
      );
    }
    return Container(
      width: 24,
      height: 24,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: AppTheme.bgElevated,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        '$rank',
        style: const TextStyle(fontSize: 11, color: AppTheme.textTertiary, fontWeight: FontWeight.w600),
      ),
    );
  }
}

class AnalysisRankAllPage extends StatelessWidget {
  final String rankType; // profit / loss
  const AnalysisRankAllPage({super.key, required this.rankType});

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();
    final items = _buildRankItems(appState);
    final list = rankType == 'profit'
        ? items.where((x) => x.pnl > 0).toList()
        : items.where((x) => x.pnl < 0).toList();
    if (rankType == 'profit') {
      list.sort((a, b) => b.pnl.compareTo(a.pnl));
    } else {
      list.sort((a, b) => a.pnl.compareTo(b.pnl));
    }

    return Scaffold(
      backgroundColor: AppTheme.bgPrimary,
      appBar: AppBar(
        backgroundColor: AppTheme.bgPrimary,
        elevation: 0,
        title: Text(rankType == 'profit' ? '盈利榜' : '亏损榜', style: const TextStyle(color: AppTheme.textPrimary)),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppTheme.textPrimary),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(Spacing.xl),
        itemCount: list.length,
        itemBuilder: (context, index) {
          final item = list[index];
          final pnlColor = AppState.getPnlColor(item.pnl);
          return Container(
            margin: const EdgeInsets.symmetric(vertical: 6),
            padding: const EdgeInsets.all(Spacing.md),
            decoration: BoxDecoration(
              color: AppTheme.bgCard,
              borderRadius: BorderRadius.circular(AppRadius.md),
            ),
            child: Row(
              children: [
                _rankBadge(index + 1),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item.name,
                        style: const TextStyle(
                          color: AppTheme.textPrimary,
                          fontSize: FontSize.base,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        _formatDisplayCode(item.code),
                        style: const TextStyle(color: AppTheme.textTertiary, fontSize: FontSize.sm),
                      ),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      appState.formatPnlIntWithCurrency(item.pnl, item.currencySymbol),
                      style: TextStyle(color: pnlColor, fontSize: FontSize.base, fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      appState.formatPct(item.pnlRate),
                      style: TextStyle(color: pnlColor, fontSize: FontSize.sm),
                    ),
                  ],
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  List<_RankItem> _buildRankItems(AppState appState) {
    final items = <_RankItem>[];
    for (final item in appState.portfolio) {
      final priceInfo = appState.prices[item.code];
      final hasValidPrice = priceInfo != null && priceInfo.price > 0;
      final currentPrice = hasValidPrice ? priceInfo.price : item.price;
      final mv = currentPrice * item.qty;
      final cost = item.price * item.qty;
      final pnl = mv - cost + item.adjustment;
      final pnlRate = cost > 0 ? (pnl / cost * 100) : 0.0;
      items.add(_RankItem(
        code: item.code,
        name: item.name,
        pnl: pnl,
        pnlRate: pnlRate,
        currencySymbol: item.currencySymbol,
      ));
    }
    return items;
  }

  String _formatDisplayCode(String code) {
    const customMap = {
      'ft_LU1116320737': 'BLK',
    };
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
    if (c.toUpperCase().endsWith('.HK')) {
      c = c.substring(0, c.length - 3);
    }
    return c;
  }

  Widget _rankBadge(int rank) {
    if (rank <= 3) {
      final gradients = [
        const [Color(0xFFFDE68A), Color(0xFFF59E0B)],
        const [Color(0xFFE5E7EB), Color(0xFF94A3B8)],
        const [Color(0xFFFED7AA), Color(0xFFEA580C)],
      ];
      final g = gradients[rank - 1];
      return SizedBox(
        width: 32,
        height: 32,
        child: Stack(
          alignment: Alignment.center,
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                gradient: LinearGradient(colors: g, begin: Alignment.topLeft, end: Alignment.bottomRight),
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: g[1].withOpacity(0.25),
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
            ),
            const Icon(Icons.military_tech, size: 16, color: Color(0xFF0F172A)),
            Positioned(
              bottom: 2,
              child: Text(
                '$rank',
                style: const TextStyle(fontSize: 10, color: Color(0xFF0F172A), fontWeight: FontWeight.w800),
              ),
            ),
          ],
        ),
      );
    }
    return Container(
      width: 24,
      height: 24,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: AppTheme.bgElevated,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        '$rank',
        style: const TextStyle(fontSize: 11, color: AppTheme.textTertiary, fontWeight: FontWeight.w600),
      ),
    );
  }
}

class _RankItem {
  final String code;
  final String name;
  final double pnl;
  final double pnlRate;
  final String currencySymbol;

  _RankItem({
    required this.code,
    required this.name,
    required this.pnl,
    required this.pnlRate,
    required this.currencySymbol,
  });
}
