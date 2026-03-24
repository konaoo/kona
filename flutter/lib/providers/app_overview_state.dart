import 'package:flutter/foundation.dart';

class AppOverviewState extends ChangeNotifier {
  double _monthChange = 0;
  double _yearChange = 0;
  double _historyPeak = 0;
  bool _hasMonthBaseline = false;
  bool _hasYearBaseline = false;
  bool _overviewMilestonesReady = false;
  bool _monthFromFirst = false;
  bool _yearFromFirst = false;

  double get monthChange => _monthChange;
  double get yearChange => _yearChange;
  double get historyPeak => _historyPeak;
  bool get hasMonthBaseline => _hasMonthBaseline;
  bool get hasYearBaseline => _hasYearBaseline;
  bool get overviewMilestonesReady => _overviewMilestonesReady;
  bool get monthFromFirst => _monthFromFirst;
  bool get yearFromFirst => _yearFromFirst;

  void applyOverviewMilestones(
    Map<String, dynamic>? overview, {
    bool notify = true,
  }) {
    final data = overview ?? const <String, dynamic>{};
    final month = data['month'];
    final year = data['year'];

    double? extractPnl(dynamic node) {
      if (node is! Map) return null;
      final raw = node['pnl'];
      if (raw is num) return raw.toDouble();
      if (raw is String) return double.tryParse(raw.trim());
      return null;
    }

    final monthPnl = extractPnl(month);
    final yearPnl = extractPnl(year);
    _overviewMilestonesReady = monthPnl != null || yearPnl != null;
    debugPrint('分析概览覆盖: monthPnl=$monthPnl, yearPnl=$yearPnl, raw=$data');
    if (monthPnl != null) _monthChange = monthPnl;
    if (yearPnl != null) _yearChange = yearPnl;
    if (notify) {
      notifyListeners();
    }
  }

  void calculateHistoryStats(List<dynamic> history, {bool notify = true}) {
    _overviewMilestonesReady = false;
    if (history.isEmpty) {
      _monthChange = 0;
      _yearChange = 0;
      _historyPeak = 0;
      _hasMonthBaseline = false;
      _hasYearBaseline = false;
      _monthFromFirst = false;
      _yearFromFirst = false;
      if (notify) {
        notifyListeners();
      }
      return;
    }

    final now = DateTime.now();
    double? monthStart;
    double? yearStart;
    double peak = 0;
    double? firstNonZero;
    String? firstNonZeroDate;

    final sortedHistory = List<Map<String, dynamic>>.from(
      history.map((e) => e as Map<String, dynamic>),
    );
    sortedHistory.sort((a, b) => a['date'].compareTo(b['date']));

    final latestSnapshotAsset = sortedHistory.last['total_asset'] as num;
    final currentSnapshot = latestSnapshotAsset.toDouble();
    debugPrint(
      '历史数据计算: 当前日期=${now.toString().substring(0, 10)}, 快照总资产=$currentSnapshot',
    );
    debugPrint('历史数据条数: ${sortedHistory.length}');
    if (sortedHistory.isNotEmpty) {
      debugPrint(
        '最早记录: ${sortedHistory.first['date']}, 资产=${sortedHistory.first['total_asset']}',
      );
      debugPrint(
        '最新记录: ${sortedHistory.last['date']}, 资产=${sortedHistory.last['total_asset']}',
      );
    }

    for (final item in sortedHistory) {
      final date = DateTime.parse(item['date']);
      final totalAsset = (item['total_asset'] as num).toDouble();

      if (totalAsset > peak) peak = totalAsset;

      if (totalAsset != 0 && firstNonZero == null) {
        firstNonZero = totalAsset;
        firstNonZeroDate = item['date'];
      }

      if (date.year == now.year &&
          date.month == now.month &&
          monthStart == null &&
          totalAsset != 0) {
        monthStart = totalAsset;
        debugPrint('找到本月数据: ${item['date']}, 资产=$totalAsset');
      }

      if (date.year == now.year && yearStart == null && totalAsset != 0) {
        yearStart = totalAsset;
        debugPrint('找到今年数据: ${item['date']}, 资产=$totalAsset');
      }
    }

    if (monthStart == null && firstNonZero != null) {
      monthStart = firstNonZero;
      _monthFromFirst = true;
      debugPrint('使用首次记账作为本月起点: $firstNonZeroDate, 资产=$monthStart');
    } else {
      _monthFromFirst = false;
    }

    if (yearStart == null && firstNonZero != null) {
      yearStart = firstNonZero;
      _yearFromFirst = true;
      debugPrint('使用首次记账作为今年起点: $firstNonZeroDate, 资产=$yearStart');
    } else {
      _yearFromFirst = false;
    }

    _historyPeak = peak;
    _hasMonthBaseline = monthStart != null;
    _hasYearBaseline = yearStart != null;
    _monthChange = monthStart != null ? currentSnapshot - monthStart : 0;
    _yearChange = yearStart != null ? currentSnapshot - yearStart : 0;

    debugPrint(
      '计算结果: 本月变动=$_monthChange (基准=$monthStart), 今年变动=$_yearChange (基准=$yearStart)',
    );
    if (notify) {
      notifyListeners();
    }
  }
}
