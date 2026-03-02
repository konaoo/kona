import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:tool/models/app_version.dart';
import 'package:tool/pages/profile_page.dart';
import 'package:tool/providers/app_state.dart';
import 'package:tool/services/api_service.dart';
import 'package:url_launcher/url_launcher.dart';

class MockApiService implements ApiService {
  MockApiService({
    this.appVersion = const AppVersion(
      version: '1.0.2',
      buildNumber: 2,
      releaseNotes: 'test notes',
      downloadUrl: 'http://test.com/app.apk',
      forceUpdate: false,
    ),
  });

  final AppVersion appVersion;

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
  @override
  Future<AppVersion?> getAppVersion() async {
    return appVersion;
  }

  @override
  set onAuthExpired(void Function()? callback) {}

  @override
  void setToken(String token) {}

  @override
  void clearToken() {}

  @override
  Future<Map<String, dynamic>?> getProfile() async => null;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
    PackageInfo.setMockInitialValues(
      appName: 'tool',
      packageName: 'com.example.tool',
      version: '1.0.1',
      buildNumber: '1',
      buildSignature: 'sign',
    );
  });

  testWidgets('Profile page shows menu order and profile info', (
    WidgetTester tester,
  ) async {
    final mockApi = MockApiService();
    final openCalls = <LaunchMode>[];
    final appState = AppState(tokenLoader: () async => null, api: mockApi);
    await appState.setLoggedIn(
      token: 't',
      refreshToken: 'r',
      username: 'kona',
      userId: 'uid-1',
      nickname: 'kona',
      createdAtRaw: '2026-02-27 00:00:00',
    );

    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: MaterialApp(
          home: Scaffold(
            body: ProfilePage(
              onLogout: () {},
              externalUrlOpener: (uri, mode) async {
                openCalls.add(mode);
                return true;
              },
              versionLoader: () async => 'v1.0.17+17',
              nowProvider: () => DateTime.utc(2026, 3, 1, 0, 0, 0),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('kona'), findsOneWidget);
    expect(find.text('已在咔咔记录 3 天'), findsOneWidget);
    expect(find.text('个人设置'), findsOneWidget);
    expect(find.text('检查更新'), findsOneWidget);
    expect(find.text('关于我们'), findsOneWidget);
    expect(find.text('咔咔用户群'), findsOneWidget);
    expect(find.text('修改密码'), findsNothing);
    expect(find.text('生物识别登录'), findsNothing);
    expect(find.text('退出登录'), findsNothing);

    final settingTexts = find.byType(Text);
    final personalSettingIndex = tester
        .widgetList<Text>(settingTexts)
        .toList()
        .indexWhere((w) => w.data == '个人设置');
    final updateIndex = tester
        .widgetList<Text>(settingTexts)
        .toList()
        .indexWhere((w) => w.data == '检查更新');
    final aboutIndex = tester
        .widgetList<Text>(settingTexts)
        .toList()
        .indexWhere((w) => w.data == '关于我们');
    final userGroupIndex = tester
        .widgetList<Text>(settingTexts)
        .toList()
        .indexWhere((w) => w.data == '咔咔用户群');
    expect(personalSettingIndex, lessThan(updateIndex));
    expect(updateIndex, lessThan(aboutIndex));
    expect(aboutIndex, lessThan(userGroupIndex));

    await tester.tap(find.text('检查更新'));
    await tester.pumpAndSettle();
    expect(find.text('发现新版本'), findsOneWidget);
    expect(find.text('v1.0.2'), findsOneWidget);
    expect(find.text('test notes'), findsOneWidget);
    expect(find.text('暂不更新'), findsNothing);
    expect(find.text('更新'), findsOneWidget);

    await tester.tap(find.text('更新'));
    await tester.pumpAndSettle();
    expect(find.text('发现新版本'), findsNothing);
    expect(openCalls, isNotEmpty);
    expect(openCalls.single, LaunchMode.externalApplication);

    await tester.tap(find.text('关于我们'));
    await tester.pumpAndSettle();
    expect(find.text('隐私协议'), findsOneWidget);
    expect(find.text('《第三方信息共享清单》'), findsOneWidget);

    await tester.pageBack();
    await tester.pumpAndSettle();
    await tester.tap(find.text('咔咔用户群'));
    await tester.pumpAndSettle();
    expect(find.text('咔咔用户群'), findsOneWidget);
  });

  testWidgets('Check update shows latest message when version is up-to-date', (
    WidgetTester tester,
  ) async {
    final mockApi = MockApiService(
      appVersion: const AppVersion(
        version: '1.0.1',
        buildNumber: 1,
        releaseNotes: 'latest',
        downloadUrl: 'http://test.com/app.apk',
        forceUpdate: false,
      ),
    );
    final appState = AppState(tokenLoader: () async => null, api: mockApi);
    await appState.setLoggedIn(
      token: 't',
      refreshToken: 'r',
      username: 'kona',
      userId: 'uid-2',
      nickname: 'kona',
      createdAtRaw: '2026-02-27 00:00:00',
    );

    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: MaterialApp(
          home: Scaffold(body: ProfilePage(onLogout: _noop)),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('检查更新'));
    await tester.pumpAndSettle();
    expect(find.text('当前已是最新版本'), findsOneWidget);
  });
}

void _noop() {}
