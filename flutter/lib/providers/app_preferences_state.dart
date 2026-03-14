import 'package:flutter/material.dart';

import '../config/theme.dart';
import '../services/cache_service.dart';

class AppPreferencesState extends ChangeNotifier {
  final CacheService _cache;

  bool _amountHidden = false;
  String _displayCurrency = 'CNY';
  ThemeMode _themeMode = ThemeMode.dark;

  AppPreferencesState({required CacheService cache}) : _cache = cache;

  bool get amountHidden => _amountHidden;
  String get displayCurrency => _displayCurrency;
  ThemeMode get themeMode => _themeMode;
  bool get isLightTheme => _themeMode == ThemeMode.light;

  Future<void> loadTheme() async {
    final saved = await _cache.getString('theme_mode');
    if (saved == 'light') {
      await setThemeMode(ThemeMode.light, save: false);
    } else if (saved == 'dark') {
      await setThemeMode(ThemeMode.dark, save: false);
    }
  }

  Future<void> setThemeMode(ThemeMode mode, {bool save = true}) async {
    final changed = _themeMode != mode;
    _themeMode = mode;
    AppTheme.setMode(mode);
    if (save) {
      await _cache.setString(
        'theme_mode',
        mode == ThemeMode.light ? 'light' : 'dark',
      );
    }
    if (changed) {
      notifyListeners();
    }
  }

  void toggleTheme() {
    setThemeMode(isLightTheme ? ThemeMode.dark : ThemeMode.light);
  }

  void toggleAmountHidden() {
    _amountHidden = !_amountHidden;
    notifyListeners();
  }

  void setDisplayCurrency(String currency) {
    if (_displayCurrency == currency) return;
    _displayCurrency = currency;
    notifyListeners();
  }
}
