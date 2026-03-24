import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/pages/analysis_page.dart';
import 'package:tool/providers/app_state.dart';


void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  Future<Map<String, dynamic>> overviewLoader(String _) async {
    return {
      'day': {'pnl': 0, 'pnl_rate': 0},
      'month': {'pnl': 0, 'pnl_rate': 0},
      'year': {'pnl': 0, 'pnl_rate': 0},
      'all': {'pnl': 0, 'pnl_rate': 0},
    };
  }

  Map<String, dynamic> calendarResponse({
    required String timeType,
    int? year,
    int? month,
    bool empty = false,
  }) {
    if (empty) {
      return {
        'items': <Map<String, dynamic>>[],
        'total_pnl': 0,
        'total_rate': 0,
        'title': '',
        'period': <String, dynamic>{},
        'selectable': {
          'day': {'years': <int>[], 'months_by_year': <String, dynamic>{}},
          'month': {'years': <int>[]},
        },
      };
    }

    if (timeType == 'month') {
      final y = year ?? 2025;
      return {
        'items': [
          {'label': '1月', 'pnl': 10.0},
        ],
        'total_pnl': 10,
        'total_rate': 1.0,
        'title': '$y年',
        'period': {'year': y},
        'selectable': {
          'day': {
            'years': [2025, 2026],
            'months_by_year': {
              '2025': [1],
              '2026': [2, 3],
            },
          },
          'month': {
            'years': [2025, 2026],
          },
        },
      };
    }

    final y = year ?? 2025;
    final m = month ?? 1;
    return {
      'items': [
        {'label': '1日', 'pnl': 10.0},
      ],
      'total_pnl': 10,
      'total_rate': 1.0,
      'title': '$y年$m月',
      'period': {'year': y, 'month': m},
      'selectable': {
        'day': {
          'years': [2025, 2026],
          'months_by_year': {
            '2025': [1],
            '2026': [2, 3],
          },
        },
        'month': {
          'years': [2025, 2026],
        },
      },
    };
  }

  Widget buildTestPage({
    required Future<Map<String, dynamic>> Function({
      required String timeType,
      int? year,
      int? month,
    })
    calendarLoader,
  }) {
    return ChangeNotifierProvider<AppState>(
      create: (_) => AppState(),
      child: MaterialApp(
        home: Scaffold(
          body: AnalysisPage(
            overviewLoader: overviewLoader,
            calendarLoader: calendarLoader,
          ),
        ),
      ),
    );
  }

  testWidgets('收益日历头部显示标题下方选择器并可打开滚轮弹层', (tester) async {
    await tester.pumpWidget(
      buildTestPage(
        calendarLoader: ({required timeType, year, month}) async =>
            calendarResponse(timeType: timeType, year: year, month: month),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('收益日历'), findsOneWidget);
    expect(
      find.byKey(const Key('calendar-header-controls-row')),
      findsOneWidget,
    );
    expect(find.byKey(const Key('calendar-period-button')), findsOneWidget);

    await tester.tap(find.byKey(const Key('calendar-period-button')));
    await tester.pumpAndSettle();

    expect(find.byKey(kCalendarYearWheelKey), findsOneWidget);
    expect(find.byKey(kCalendarMonthWheelKey), findsOneWidget);
  });

  testWidgets('日视图切换年份后月份会自动校正到可选项', (tester) async {
    await tester.pumpWidget(
      buildTestPage(
        calendarLoader: ({required timeType, year, month}) async =>
            calendarResponse(timeType: timeType, year: year, month: month),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('calendar-period-button')));
    await tester.pumpAndSettle();

    // Drag year wheel to select 2025 and tap on it to confirm (isFinal)
    await tester.drag(find.byKey(kCalendarYearWheelKey), const Offset(0, 120));
    await tester.pumpAndSettle();

    // Tap the year wheel to trigger isFinal=true and auto-close
    await tester.tap(find.byKey(kCalendarYearWheelKey));
    await tester.pumpAndSettle();

    expect(find.text('2025年01月'), findsOneWidget);
  });

  testWidgets('月视图仅显示年份滚轮', (tester) async {
    await tester.pumpWidget(
      buildTestPage(
        calendarLoader: ({required timeType, year, month}) async =>
            calendarResponse(timeType: timeType, year: year, month: month),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('月'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('calendar-period-button')));
    await tester.pumpAndSettle();

    expect(find.byKey(kCalendarYearWheelKey), findsOneWidget);
    expect(find.byKey(kCalendarMonthWheelKey), findsNothing);
  });

  testWidgets('无可选周期时日期按钮禁用', (tester) async {
    await tester.pumpWidget(
      buildTestPage(
        calendarLoader: ({required timeType, year, month}) async =>
            calendarResponse(
              timeType: timeType,
              year: year,
              month: month,
              empty: true,
            ),
      ),
    );
    await tester.pumpAndSettle();

    final periodButton = tester.widget<GestureDetector>(
      find.byKey(const Key('calendar-period-button')),
    );
    expect(periodButton.onTap, isNull);
  });

  // Test removed: '重置后完成会回到最近有数据周期并触发加载'
  // The Reset button was removed during the Date Picker UI refactoring
  // (replaced by inline DatePickerDropdown overlay).

  testWidgets('历史周期命中持久缓存后重建页面会后台回源刷新', (tester) async {
    int firstLoaderCalls = 0;
    final historical = {
      'items': [
        {'label': '1日', 'pnl': 12.0},
      ],
      'total_pnl': 12,
      'total_rate': 1.2,
      'title': '2001年1月',
      'period': {'year': 2001, 'month': 1},
      'selectable': {
        'day': {
          'years': [2001],
          'months_by_year': {
            '2001': [1],
          },
        },
        'month': {
          'years': [2001],
        },
      },
    };

    await tester.pumpWidget(
      buildTestPage(
        calendarLoader: ({required timeType, year, month}) async {
          firstLoaderCalls += 1;
          return historical;
        },
      ),
    );
    await tester.pumpAndSettle();
    expect(firstLoaderCalls, 1);
    expect(find.text('2001年01月'), findsOneWidget);

    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();

    int secondLoaderCalls = 0;
    await tester.pumpWidget(
      buildTestPage(
        calendarLoader: ({required timeType, year, month}) async {
          secondLoaderCalls += 1;
          return historical;
        },
      ),
    );
    await tester.pumpAndSettle();

    expect(secondLoaderCalls, 1);
    expect(find.text('2001年01月'), findsOneWidget);
  });

  testWidgets('分析页支持下拉刷新并触发概览与日历重拉', (tester) async {
    var overviewCalls = 0;
    var calendarCalls = 0;

    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>(
        create: (_) => AppState(),
        child: MaterialApp(
          home: Scaffold(
            body: AnalysisPage(
              overviewLoader: (_) async {
                overviewCalls += 1;
                return {
                  'day': {'pnl': 0, 'pnl_rate': 0},
                  'month': {'pnl': 0, 'pnl_rate': 0},
                  'year': {'pnl': 0, 'pnl_rate': 0},
                  'all': {'pnl': 0, 'pnl_rate': 0},
                };
              },
              calendarLoader: ({required timeType, year, month}) async {
                calendarCalls += 1;
                return calendarResponse(
                  timeType: timeType,
                  year: year,
                  month: month,
                );
              },
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(RefreshIndicator), findsOneWidget);
    expect(overviewCalls, 1);
    expect(calendarCalls, 1);

    final refresh = tester.widget<RefreshIndicator>(
      find.byType(RefreshIndicator),
    );
    await refresh.onRefresh();
    await tester.pump();

    expect(overviewCalls, greaterThanOrEqualTo(2));
    expect(calendarCalls, greaterThanOrEqualTo(2));
  });

  testWidgets('分析页下拉刷新时不显示中部大Loading', (tester) async {
    final refreshBlock = Completer<void>();
    var overviewCalls = 0;
    var calendarCalls = 0;

    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>(
        create: (_) => AppState(),
        child: MaterialApp(
          home: Scaffold(
            body: AnalysisPage(
              overviewLoader: (_) async {
                overviewCalls += 1;
                if (overviewCalls > 1) {
                  await refreshBlock.future;
                }
                return {
                  'day': {'pnl': 0, 'pnl_rate': 0},
                  'month': {'pnl': 0, 'pnl_rate': 0},
                  'year': {'pnl': 0, 'pnl_rate': 0},
                  'all': {'pnl': 0, 'pnl_rate': 0},
                };
              },
              calendarLoader: ({required timeType, year, month}) async {
                calendarCalls += 1;
                if (calendarCalls > 1) {
                  await refreshBlock.future;
                }
                return calendarResponse(
                  timeType: timeType,
                  year: year,
                  month: month,
                );
              },
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    final refresh = tester.widget<RefreshIndicator>(
      find.byType(RefreshIndicator),
    );
    final refreshFuture = refresh.onRefresh();
    await tester.pump();

    expect(find.byType(CircularProgressIndicator), findsNothing);

    refreshBlock.complete();
    await refreshFuture;
    await tester.pumpAndSettle();

    expect(overviewCalls, greaterThanOrEqualTo(2));
    expect(calendarCalls, greaterThanOrEqualTo(2));
  });
}
