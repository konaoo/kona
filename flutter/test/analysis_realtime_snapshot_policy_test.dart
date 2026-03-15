import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/pages/analysis_page.dart';
import 'package:tool/providers/app_state.dart';

class _RealtimeAppState extends AppState {
  _RealtimeAppState() : super(tokenLoader: () async => null);

  @override
  double get investDayPnl => 88;

  @override
  double get investDayPnlRate => 1.23;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  Future<Map<String, dynamic>> _overviewLoader(String _) async {
    return {
      'day': {'pnl': 999.0, 'pnl_rate': 9.99},
      'month': {'pnl': 222.0, 'pnl_rate': 2.22},
      'year': {'pnl': 333.0, 'pnl_rate': 3.33},
      'all': {'pnl': 444.0, 'pnl_rate': 4.44},
    };
  }

  Widget _buildPage({
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
            overviewLoader: _overviewLoader,
            calendarLoader: calendarLoader,
            rankLoader: ({String rankType = 'all', String market = 'all'}) async {
              return {'gain': [], 'loss': []};
            },
          ),
        ),
      ),
    );
  }

  Map<String, dynamic> _buildCalendarPayload({
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
        if (month != null) 'month': month,
      },
      'selectable': {
        'day': {
          'years': dayYears ?? [year],
          'months_by_year':
              monthsByYear ??
              <String, dynamic>{'$year': [if (month != null) month else 1]},
        },
        'month': {
          'years': monthYears ?? [year],
        },
      },
    };
  }

  testWidgets('顶部大卡只展示概览口径', (tester) async {
    final now = DateTime.now();
    await tester.pumpWidget(
      _buildPage(
        calendarLoader: ({required timeType, year, month}) async =>
            _buildCalendarPayload(
              timeType: timeType,
              year: year ?? now.year,
              month: month ?? now.month,
              items: const <Map<String, dynamic>>[],
            ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('当日盈亏'), findsOneWidget);
    expect(find.text('¥999'), findsOneWidget);
    expect(find.text('+9.99%'), findsOneWidget);

    await tester.tap(find.text('本年'));
    await tester.pumpAndSettle();

    expect(find.text('本年盈亏'), findsOneWidget);
    expect(find.text('¥333'), findsOneWidget);
    expect(find.text('+3.33%'), findsOneWidget);
  });

  testWidgets('当前月今天那格展示快照口径', (tester) async {
    final now = DateTime.now();
    final todayLabel = '${now.month}-${now.day}';
    await tester.pumpWidget(
      _buildPage(
        calendarLoader: ({required timeType, year, month}) async =>
            _buildCalendarPayload(
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

    expect(find.text('¥999'), findsOneWidget);
    expect(find.text('41'), findsWidgets);
  });

  testWidgets('非当前月今天那格保持快照，不会被实时值覆盖', (tester) async {
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
      _buildPage(
        calendarLoader: ({required timeType, year, month}) async =>
            _buildCalendarPayload(
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

    expect(find.text('¥999'), findsOneWidget);
    expect(find.text('41'), findsWidgets);
    expect(find.text('本月盈亏：'), findsOneWidget);
    expect(find.text('88'), findsNothing);
  });

  testWidgets('切换日历视图不影响顶部大卡当前周期', (tester) async {
    final now = DateTime.now();
    await tester.pumpWidget(
      _buildPage(
        calendarLoader: ({required timeType, year, month}) async {
          if (timeType == 'month') {
            return _buildCalendarPayload(
              timeType: 'month',
              year: year ?? now.year,
              items: const [
                {'label': '1月', 'pnl': 10.0},
              ],
              totalPnl: 10,
              totalRate: 0.1,
            );
          }
          return _buildCalendarPayload(
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
    expect(find.text('¥444'), findsOneWidget);

    await tester.tap(find.text('月'));
    await tester.pumpAndSettle();

    expect(find.text('累计盈亏'), findsOneWidget);
    expect(find.text('¥444'), findsOneWidget);
  });

  testWidgets('日历底部汇总优先使用接口 total_pnl，使用后端周期累计口径', (tester) async {
    final now = DateTime.now();
    await tester.pumpWidget(
      _buildPage(
        calendarLoader: ({required timeType, year, month}) async =>
            _buildCalendarPayload(
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

    expect(find.text('本月盈亏：'), findsOneWidget);
    expect(find.text('¥17118'), findsOneWidget);
    expect(find.text('+0.83%'), findsOneWidget);
  });
}
