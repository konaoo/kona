import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../services/api_service.dart';

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

  // 收益日历相关
  String _calendarTimeType = 'day';
  Map<String, dynamic> _calendarData = {};
  bool _calendarLoading = false;

  // 盈亏排行相关
  String _rankType = 'profit'; // 'profit' 或 'loss'
  Map<String, dynamic> _rankData = {};
  bool _rankLoading = false;

  @override
  void initState() {
    super.initState();
    _loadData();
    _loadCalendar();
    _loadRank();
  }

  Future<void> _loadData() async {
    setState(() => _loading = true);
    try {
      final data = await _api.getAnalysisOverview(period: _currentPeriod);
      setState(() {
        _overview = data;
        _loading = false;
      });
    } catch (e) {
      debugPrint('加载分析数据失败: $e');
      setState(() => _loading = false);
    }
  }

  Future<void> _loadCalendar() async {
    setState(() => _calendarLoading = true);
    try {
      final data = await _api.getAnalysisCalendar(timeType: _calendarTimeType);
      debugPrint('收益日历数据: $data');
      setState(() {
        _calendarData = data;
        _calendarLoading = false;
      });
    } catch (e) {
      debugPrint('加载收益日历失败: $e');
      setState(() => _calendarLoading = false);
    }
  }

  Future<void> _loadRank() async {
    setState(() => _rankLoading = true);
    try {
      final data = await _api.getAnalysisRank(rankType: _rankType);
      debugPrint('盈亏排行数据: $data');
      setState(() {
        _rankData = data;
        _rankLoading = false;
      });
    } catch (e) {
      debugPrint('加载盈亏排行失败: $e');
      setState(() => _rankLoading = false);
    }
  }

  void _changePeriod(String period) {
    setState(() => _currentPeriod = period);
    _loadData();
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(Spacing.xl),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 盈亏概览卡片
          _buildOverviewCard(),
          const SizedBox(height: Spacing.xl),
          // 收益日历
          _buildCalendarSection(),
          const SizedBox(height: Spacing.xl),
          // 盈亏排行
          _buildRankSection(),
        ],
      ),
    );
  }

  Widget _buildOverviewCard() {
    final periodData = _overview[_currentPeriod] ?? {};
    final pnl = (periodData['pnl'] as num?)?.toDouble() ?? 0.0;
    final pnlRate = (periodData['pnl_rate'] as num?)?.toDouble() ?? 0.0;
    final pnlColor = pnl >= 0 ? const Color(0xFFEF4444) : const Color(0xFF10B981);

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
            style: const TextStyle(fontSize: FontSize.base, color: AppTheme.textSecondary),
          ),
          const SizedBox(height: 4),
          Text(
            _loading ? '加载中...' : '¥${pnl.toStringAsFixed(2)}',
            style: TextStyle(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: _loading ? AppTheme.textPrimary : pnlColor,
            ),
          ),
          const SizedBox(height: 4),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                pnl >= 0 ? Icons.trending_up : Icons.trending_down,
                size: 16,
                color: _loading ? AppTheme.textTertiary : pnlColor,
              ),
              const SizedBox(width: 4),
              Text(
                _loading ? '--' : '收益率 ${pnlRate.toStringAsFixed(2)}%',
                style: TextStyle(color: _loading ? AppTheme.textTertiary : pnlColor),
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
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.accent : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: FontSize.base,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            color: isSelected ? AppTheme.textPrimary : AppTheme.textTertiary,
          ),
        ),
      ),
    );
  }

  Widget _buildCalendarSection() {
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

    // 如果有实际数据，填充到网格中
    final items = _calendarData['items'] as List<dynamic>? ?? [];
    for (var item in items) {
      final label = item['label'] ?? '';
      final pnl = (item['pnl'] as num?)?.toDouble();
      // 查找并更新对应的网格项
      for (var gridItem in calendarGrid) {
        if (gridItem['date'].toString().contains(label.toString())) {
          gridItem['pnl'] = pnl;
          break;
        }
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
                    childAspectRatio: 1.0,
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
                              pnl >= 0 ? '+${pnl.toStringAsFixed(0)}' : pnl.toStringAsFixed(0),
                              style: TextStyle(
                                fontSize: 10,
                                color: textColor,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ] else ...[
                            const SizedBox(height: 2),
                            Text(
                              '-',
                              style: TextStyle(
                                fontSize: 10,
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
            fontSize: FontSize.base,
            color: isSelected ? AppTheme.textPrimary : AppTheme.textSecondary,
          ),
        ),
      ),
    );
  }

  Widget _buildRankSection() {
    // 根据rankType选择盈利榜或亏损榜
    final rankList = _rankType == 'profit'
        ? (_rankData['gain'] as List<dynamic>? ?? [])
        : (_rankData['loss'] as List<dynamic>? ?? []);

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
              _loadRank();
            }),
            const SizedBox(width: Spacing.sm),
            _buildRankTab('亏损榜', _rankType == 'loss', () {
              setState(() => _rankType = 'loss');
              _loadRank();
            }),
            const Spacer(),
            GestureDetector(
              onTap: () {
                // 显示提示信息
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('完整盈亏排行功能开发中...'),
                    duration: Duration(seconds: 2),
                    backgroundColor: AppTheme.accent,
                  ),
                );
                debugPrint('查看全部盈亏排行');
              },
              child: const Text(
                '查看全部 >',
                style: TextStyle(fontSize: FontSize.base, color: AppTheme.accentLight),
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
          child: _rankLoading
              ? const Center(
                  child: CircularProgressIndicator(color: AppTheme.accent),
                )
              : rankList.isEmpty
                  ? const Center(
                      child: Padding(
                        padding: EdgeInsets.all(24.0),
                        child: Text(
                          '暂无数据',
                          style: TextStyle(color: AppTheme.textTertiary),
                        ),
                      ),
                    )
                  : Column(
                      children: rankList.map((item) {
                        final code = item['code'] ?? '';
                        final name = item['name'] ?? '';
                        final pnl = (item['pnl'] as num?)?.toDouble() ?? 0.0;
                        final pnlRate = (item['pnl_rate'] as num?)?.toDouble() ?? 0.0;
                        final pnlColor = pnl >= 0 ? const Color(0xFFEF4444) : const Color(0xFF10B981);

                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          child: Row(
                            children: [
                              Expanded(
                                flex: 2,
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      name,
                                      style: const TextStyle(
                                        color: AppTheme.textPrimary,
                                        fontSize: FontSize.base,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                    Text(
                                      code,
                                      style: const TextStyle(
                                        color: AppTheme.textTertiary,
                                        fontSize: FontSize.sm,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Text(
                                      '¥${pnl.toStringAsFixed(2)}',
                                      style: TextStyle(
                                        color: pnlColor,
                                        fontSize: FontSize.base,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                    Text(
                                      '${pnlRate >= 0 ? '+' : ''}${pnlRate.toStringAsFixed(2)}%',
                                      style: TextStyle(
                                        color: pnlColor,
                                        fontSize: FontSize.sm,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        );
                      }).toList(),
                    ),
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
}
