import 'package:flutter_test/flutter_test.dart';
import 'package:tool/providers/app_overview_state.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('AppOverviewState applies overview milestones', () {
    final state = AppOverviewState();

    state.applyOverviewMilestones(<String, dynamic>{
      'month': <String, dynamic>{'pnl': 88.5},
      'year': <String, dynamic>{'pnl': '-12.0'},
    }, notify: false);

    expect(state.monthChange, 88.5);
    expect(state.yearChange, -12.0);
    expect(state.overviewMilestonesReady, isTrue);
  });

  test(
    'AppOverviewState calculates history stats with first-entry fallback',
    () {
      final state = AppOverviewState();

      state.calculateHistoryStats(<dynamic>[
        <String, dynamic>{'date': '2024-12-31', 'total_asset': 1000},
      ], notify: false);

      expect(state.historyPeak, 1000);
      expect(state.hasMonthBaseline, isTrue);
      expect(state.hasYearBaseline, isTrue);
      expect(state.monthChange, 0);
      expect(state.yearChange, 0);
      expect(state.monthFromFirst, isTrue);
      expect(state.yearFromFirst, isTrue);
    },
  );
}
