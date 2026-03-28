import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/pages/analysis_page.dart';
import 'package:tool/providers/app_state.dart';

class _RealtimeAppState extends AppState {
  _RealtimeAppState() : super(tokenLoader: () async => null);

  @override
  Map<String, dynamic> get realtimeToday => {
    'effective_date': DateTime.now().toIso8601String().split('T').first,
    'totals': {
      'day_pnl': 88.0,
      'day_pnl_rate': 1.23,
    },
  };
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  Future<Map<String, dynamic>> overviewLoader(String _) async {
    return {
      'day': {'pnl': 999.0, 'pnl_rate': 9.99},
      'month': {'pnl': 222.0, 'pnl_rate': 2.22},
      'year': {'pnl': 333.0, 'pnl_rate': 3.33},
      'all': {'pnl': 444.0, 'pnl_rate': 4.44},
    };
  }

  Finder overviewAmountFinder(String text) {
    return find.descendant(
      of: find.byType(FittedBox).first,
      matching: find.text(text),
    );
  }

  Widget buildPage({
    bool isActive = true,
    Duration autoRefreshInterval = const Duration(minutes: 2),
    required Future<Map<String, dynamic>> Function({
      required String timeType,
      int? year,
      int? month,
    })
    calendarLoader,
  }) {
    return ChangeNotifierProvider<AppState>(
      create: (_) => _RealtimeAppState(),
      child: MaterialApp(
        home: Scaffold(
          body: AnalysisPage(
            isActive: isActive,
            autoRefreshInterval: autoRefreshInterval,
            overviewLoader: overviewLoader,
            calendarLoader: calendarLoader,
            rankLoader:
                ({String rankType = 'all', String market = 'all'}) async {
                  return {'gain': [], 'loss': []};
                },
          ),
        ),
      ),
    );
  }

  Map<String, dynamic> buildCalendarPayload({
    required String timeType,
    required int year,
    int? month,
    required List<Map<String, dynamic>> items,
    double totalPnl = 0,
    double totalRate = 0,
    List<int>? dayYears,
    Map<String, dynamic>? monthsByYear,
    List<int>? monthYears,
  }) {
    return {
      'items': items,
      'total_pnl': totalPnl,
      'total_rate': totalRate,
      'title': timeType == 'day' ? '$year年${month ?? 1}月累计' : '$year年累计',
      'period': {
        'time_type': timeType,
        'year': year,
        ...?switch (month) {
          final value? => {'month': value},
          null => null,
        },
      },
      'selectable': {
        'day': {
          'years': dayYears ?? [year],
          'months_by_year':
              monthsByYear ??
              <String, dynamic>{
                '$year': [if (month != null) month else 1],
              },
        },
        'month': {
          'years': monthYears ?? [year],
        },
      },
    };
  }

  testWidgets('顶部大卡当日优先展示实时投资口径，其他周期仍展示概览口径', (tester) async {
    final now = DateTime.now();
    await tester.pumpWidget(
      buildPage(
        calendarLoader: ({required timeType, year, month}) async =>
            buildCalendarPayload(
              timeType: timeType,
              year: year ?? now.year,
              month: month ?? now.month,
              items: const <Map<String, dynamic>>[],
            ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('当日盈亏'), findsOneWidget);
    expect(overviewAmountFinder('¥88'), findsOneWidget);
    expect(find.text('+1.23%'), findsOneWidget);

    await tester.tap(find.text('本年'));
    await tester.pumpAndSettle();

    expect(find.text('本年盈亏'), findsOneWidget);
    expect(overviewAmountFinder('¥333'), findsOneWidget);
    expect(find.text('+3.33%'), findsOneWidget);
  });

  testWidgets('当前月今天那格展示 realtime today 口径', (tester) async {
    final now = DateTime.now();
    final todayLabel = '${now.month}-${now.day}';
    await tester.pumpWidget(
      buildPage(
        calendarLoader: ({required timeType, year, month}) async =>
            buildCalendarPayload(
              timeType: 'day',
              year: now.year,
              month: now.month,
              items: [
                {'label': todayLabel, 'pnl': 41.0},
              ],
              totalPnl: 41,
              totalRate: 0.41,
            ),
      ),
    );
    await tester.pumpAndSettle();

    expect(overviewAmountFinder('¥88'), findsOneWidget);
    expect(find.text('88'), findsWidgets);
  });

  testWidgets('非当前月历史格子保持快照，不会被 realtime today 覆盖', (tester) async {
    final now = DateTime.now();
    final previousMonth = now.month == 1
        ? DateTime(now.year - 1, 12, 1)
        : DateTime(now.year, now.month - 1, 1);
    final lastDayOfPreviousMonth = DateTime(
      previousMonth.year,
      previousMonth.month + 1,
      0,
    ).day;
    final safeDay = now.day > lastDayOfPreviousMonth
        ? lastDayOfPreviousMonth
        : now.day;
    await tester.pumpWidget(
      buildPage(
        calendarLoader: ({required timeType, year, month}) async =>
            buildCalendarPayload(
              timeType: 'day',
              year: previousMonth.year,
              month: previousMonth.month,
              items: [
                {'label': '${previousMonth.month}-$safeDay', 'pnl': 41.0},
              ],
              totalPnl: 41,
              totalRate: 0.41,
              dayYears: [previousMonth.year],
              monthsByYear: <String, dynamic>{
                '${previousMonth.year}': [previousMonth.month],
              },
              monthYears: [previousMonth.year],
            ),
      ),
    );
    await tester.pumpAndSettle();

    expect(overviewAmountFinder('¥88'), findsOneWidget);
    expect(find.text('41'), findsWidgets);
    expect(find.text('本月盈亏'), findsOneWidget);
    expect(find.text('88'), findsNothing);
  });

  testWidgets('切换日历视图不影响顶部大卡当前周期', (tester) async {
    final now = DateTime.now();
    await tester.pumpWidget(
      buildPage(
        calendarLoader: ({required timeType, year, month}) async {
          if (timeType == 'month') {
            return buildCalendarPayload(
              timeType: 'month',
              year: year ?? now.year,
              items: const [
                {'label': '1月', 'pnl': 10.0},
              ],
              totalPnl: 10,
              totalRate: 0.1,
            );
          }
          return buildCalendarPayload(
            timeType: 'day',
            year: year ?? now.year,
            month: month ?? now.month,
            items: const <Map<String, dynamic>>[],
          );
        },
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('全部'));
    await tester.pumpAndSettle();
    expect(find.text('累计盈亏'), findsOneWidget);
    expect(overviewAmountFinder('¥444'), findsOneWidget);

    await tester.tap(find.text('月'));
    await tester.pumpAndSettle();

    expect(find.text('累计盈亏'), findsOneWidget);
    expect(overviewAmountFinder('¥444'), findsOneWidget);
  });

  testWidgets('日历底部汇总会和今天格子保持同一口径', (tester) async {
    final now = DateTime.now();
    await tester.pumpWidget(
      buildPage(
        calendarLoader: ({required timeType, year, month}) async =>
            buildCalendarPayload(
              timeType: 'day',
              year: now.year,
              month: now.month,
              items: const [
                {'label': '3-2', 'pnl': 5550.0},
                {'label': '3-3', 'pnl': 3054.0},
                {'label': '3-4', 'pnl': -6336.0},
                {'label': '3-6', 'pnl': 5088.0},
                {'label': '3-9', 'pnl': -5774.0},
                {'label': '3-10', 'pnl': 2266.0},
                {'label': '3-11', 'pnl': 10000.0},
                {'label': '3-12', 'pnl': 2678.0},
              ],
              totalPnl: 17118,
              totalRate: 0.83,
            ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('本月盈亏'), findsOneWidget);
    expect(find.text('¥17206'), findsOneWidget);
    expect(find.text('+0.83%'), findsOneWidget);
  });

  testWidgets('分析页激活时会静默自动刷新', (tester) async {
    final now = DateTime.now();
    var overviewCallCount = 0;
    var calendarCallCount = 0;
    var rankCallCount = 0;

    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>(
        create: (_) => _RealtimeAppState(),
        child: MaterialApp(
          home: Scaffold(
            body: AnalysisPage(
              isActive: true,
              autoRefreshInterval: const Duration(milliseconds: 50),
              overviewLoader: (_) async {
                overviewCallCount += 1;
                return {
                  'day': {'pnl': overviewCallCount.toDouble(), 'pnl_rate': 1.0},
                  'month': {'pnl': 2.0, 'pnl_rate': 2.0},
                  'year': {'pnl': 3.0, 'pnl_rate': 3.0},
                  'all': {'pnl': 4.0, 'pnl_rate': 4.0},
                };
              },
              calendarLoader: ({required timeType, year, month}) async {
                calendarCallCount += 1;
                return buildCalendarPayload(
                  timeType: timeType,
                  year: year ?? now.year,
                  month: month ?? now.month,
                  items: const <Map<String, dynamic>>[],
                );
              },
              rankLoader:
                  ({String rankType = 'all', String market = 'all'}) async {
                    rankCallCount += 1;
                    return {'gain': [], 'loss': []};
                  },
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    final initialOverviewCalls = overviewCallCount;
    final initialCalendarCalls = calendarCallCount;
    final initialRankCalls = rankCallCount;

    await tester.pump(const Duration(milliseconds: 80));
    await tester.pumpAndSettle();

    expect(overviewCallCount, greaterThan(initialOverviewCalls));
    expect(calendarCallCount, greaterThan(initialCalendarCalls));
    expect(rankCallCount, greaterThan(initialRankCalls));
  });
}
