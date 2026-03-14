import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tool/providers/app_preferences_state.dart';
import 'package:tool/services/cache_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  test('AppPreferencesState loads saved theme and toggles amount visibility', () async {
    SharedPreferences.setMockInitialValues({'theme_mode': 'light'});
    final state = AppPreferencesState(cache: CacheService());

    await state.loadTheme();
    expect(state.themeMode, ThemeMode.light);
    expect(state.isLightTheme, isTrue);

    expect(state.amountHidden, isFalse);
    state.toggleAmountHidden();
    expect(state.amountHidden, isTrue);

    state.setDisplayCurrency('USD');
    expect(state.displayCurrency, 'USD');
  });

  test('AppPreferencesState persists theme mode changes', () async {
    final state = AppPreferencesState(cache: CacheService());

    await state.setThemeMode(ThemeMode.light);

    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('theme_mode'), 'light');
  });
}
