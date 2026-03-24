import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/models/asset_action_result.dart';
import 'package:tool/pages/analysis_page.dart';
import 'package:tool/providers/app_state.dart';
import 'package:tool/services/api_service.dart';

class _NoRefreshAppState extends AppState {
  _NoRefreshAppState({required ApiService api})
    : super(api: api, tokenLoader: () async => null);

  @override
  Future<void> refreshHomeData({int? ledgerId}) async {}
}

class _FakeApiService implements ApiService {
  void Function()? _onAuthExpired;

  @override
  void Function()? get onAuthExpired => _onAuthExpired;

  @override
  set onAuthExpired(void Function()? value) {
    _onAuthExpired = value;
  }

  @override
  void setToken(String token) {}

  @override
  void clearToken() {}

  @override
  Future<AssetActionResult> addPortfolioAsset(
    String code,
    String name,
    double price,
    double qty, {
    String? curr,
    String? assetType,
    String? requestId,
    int? ledgerId,
  }) async {
    return const AssetActionResult.success(data: {'status': 'ok'});
  }

  @override
  Future<AssetActionResult> modifyPortfolioAsset(
    String code,
    double qty,
    double price, {
    String? note,
    String? requestId,
    int? ledgerId,
  }) async {
    return const AssetActionResult.success(data: {'status': 'ok'});
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

Future<Map<String, dynamic>> _overviewLoader(String _) async {
  return {
    'day': {'pnl': 0, 'pnl_rate': 0},
    'month': {'pnl': 0, 'pnl_rate': 0},
    'year': {'pnl': 0, 'pnl_rate': 0},
    'all': {'pnl': 0, 'pnl_rate': 0},
  };
}

Future<Map<String, dynamic>> _calendarLoader({
  required String timeType,
  int? year,
  int? month,
}) async {
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

Future<Map<String, dynamic>> _rankLoader({
  String rankType = 'all',
  String market = 'all',
}) async {
  return {
    'gain': [
      {
        'code': 'gb_tsla',
        'name': 'Tesla',
        'pnl': 200,
        'pnl_rate': 100.0,
        'curr': 'USD',
      },
    ],
    'loss': [],
  };
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('Analysis rank uses abs(cost) for negative-cost holding', (
    WidgetTester tester,
  ) async {
    final api = _FakeApiService();
    final state = _NoRefreshAppState(api: api);
    final addResult = await state.addInvestment(
      code: 'gb_tsla',
      name: 'Tesla',
      price: 2,
      qty: 10,
      curr: 'USD',
      assetType: 'us',
      awaitRefresh: false,
    );
    expect(addResult.ok, isTrue);
    final modifyResult = await state.modifyInvestment(
      code: 'gb_tsla',
      qty: 10,
      price: -2,
      awaitRefresh: false,
    );
    expect(modifyResult.ok, isTrue);

    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: state,
        child: MaterialApp(
          home: Scaffold(
            body: AnalysisPage(
              overviewLoader: _overviewLoader,
              calendarLoader: _calendarLoader,
              rankLoader: _rankLoader,
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('盈亏排行'), findsOneWidget);
    expect(find.text('+100.00%'), findsWidgets);
  });
}
