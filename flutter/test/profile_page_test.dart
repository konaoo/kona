import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/config/api_config.dart';
import 'package:tool/pages/profile_page.dart';
import 'package:tool/providers/app_state.dart';
import 'package:url_launcher/url_launcher.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('Profile page shows menu order and profile info', (
    WidgetTester tester,
  ) async {
    final appState = AppState(tokenLoader: () async => null);
    await appState.setLoggedIn(
      token: 't',
      refreshToken: 'r',
      username: 'kona',
      userId: 'uid-1',
      nickname: 'kona',
      createdAtRaw: '2026-02-27 00:00:00',
    );

    Uri? openedUri;
    LaunchMode? openedMode;
    await tester.pumpWidget(
      ChangeNotifierProvider<AppState>.value(
        value: appState,
        child: MaterialApp(
          home: Scaffold(
            body: ProfilePage(
              onLogout: () {},
              versionLoader: () async => 'v1.0.17+17',
              nowProvider: () => DateTime.utc(2026, 3, 1, 0, 0, 0),
              externalUrlOpener: (uri, mode) async {
                openedUri = uri;
                openedMode = mode;
                return true;
              },
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('kona'), findsOneWidget);
    expect(find.text('已在咔咔记录 3 天'), findsOneWidget);
    expect(find.text('个人设置'), findsOneWidget);
    expect(find.text('问题反馈'), findsOneWidget);
    expect(find.text('检查更新'), findsOneWidget);
    expect(find.text('关于我们'), findsOneWidget);
    expect(find.text('修改密码'), findsNothing);
    expect(find.text('生物识别登录'), findsNothing);
    expect(find.text('退出登录'), findsNothing);

    final settingTexts = find.byType(Text);
    final personalSettingIndex = tester
        .widgetList<Text>(settingTexts)
        .toList()
        .indexWhere((w) => w.data == '个人设置');
    final feedbackIndex = tester
        .widgetList<Text>(settingTexts)
        .toList()
        .indexWhere((w) => w.data == '问题反馈');
    final updateIndex = tester
        .widgetList<Text>(settingTexts)
        .toList()
        .indexWhere((w) => w.data == '检查更新');
    final aboutIndex = tester
        .widgetList<Text>(settingTexts)
        .toList()
        .indexWhere((w) => w.data == '关于我们');
    expect(personalSettingIndex, lessThan(feedbackIndex));
    expect(feedbackIndex, lessThan(updateIndex));
    expect(updateIndex, lessThan(aboutIndex));

    await tester.tap(find.text('问题反馈'));
    await tester.pumpAndSettle();
    expect(openedUri?.toString(), ApiConfig.feedbackUrl);
    expect(openedMode, LaunchMode.externalApplication);

    await tester.tap(find.text('检查更新'));
    await tester.pumpAndSettle();
    expect(openedUri?.toString(), ApiConfig.apkDownloadUrl);
    expect(openedMode, LaunchMode.inAppBrowserView);

    await tester.tap(find.text('关于我们'));
    await tester.pumpAndSettle();
    expect(find.text('当前版本：v1.0.17+17'), findsOneWidget);
    expect(find.text('我知道了'), findsOneWidget);
  });
}
