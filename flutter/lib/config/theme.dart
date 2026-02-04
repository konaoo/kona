import 'package:flutter/material.dart';

class AppPalette {
  final Color bgPrimary;
  final Color bgCard;
  final Color bgElevated;
  final Color navBg;
  final Color accent;
  final Color accentLight;
  final Color textPrimary;
  final Color textSecondary;
  final Color textTertiary;
  final Color success;
  final Color danger;
  final Color border;
  final List<Color> cardGradient;

  const AppPalette({
    required this.bgPrimary,
    required this.bgCard,
    required this.bgElevated,
    required this.navBg,
    required this.accent,
    required this.accentLight,
    required this.textPrimary,
    required this.textSecondary,
    required this.textTertiary,
    required this.success,
    required this.danger,
    required this.border,
    required this.cardGradient,
  });

  static const dark = AppPalette(
    bgPrimary: Color(0xFF0A0E1A),
    bgCard: Color(0xFF1A2332),
    bgElevated: Color(0xFF1F2937),
    navBg: Color(0xFF0F172A),
    accent: Color(0xFF3B82F6),
    accentLight: Color(0xFF60A5FA),
    textPrimary: Color(0xFFFFFFFF),
    textSecondary: Color(0xFF94A3B8),
    textTertiary: Color(0xFF64748B),
    success: Color(0xFF10B981),
    danger: Color(0xFFEF4444),
    border: Color(0xFF1F2937),
    cardGradient: [Color(0xFF1A2744), Color(0xFF0F1829)],
  );

  // 轻浅文艺风：柔和米白 + 低饱和蓝绿
  static const light = AppPalette(
    bgPrimary: Color(0xFFF5F2ED),
    bgCard: Color(0xFFFFFFFF),
    bgElevated: Color(0xFFEFF2F7),
    navBg: Color(0xFFF1EEE8),
    accent: Color(0xFF4B86F0),
    accentLight: Color(0xFF8CB5FF),
    textPrimary: Color(0xFF1F2A37),
    textSecondary: Color(0xFF6B7280),
    textTertiary: Color(0xFF9AA3B2),
    success: Color(0xFF16A34A),
    danger: Color(0xFFE45656),
    border: Color(0xFFDCE3EE),
    cardGradient: [Color(0xFFE3EDFF), Color(0xFFF7FAFF)],
  );
}

/// 主题配置
class AppTheme {
  static AppPalette _palette = AppPalette.dark;

  static void setMode(ThemeMode mode) {
    _palette = mode == ThemeMode.light ? AppPalette.light : AppPalette.dark;
  }

  static AppPalette get palette => _palette;
  static bool get isLight => _palette == AppPalette.light;

  // 背景色
  static Color get bgPrimary => _palette.bgPrimary;
  static Color get bgCard => _palette.bgCard;
  static Color get bgElevated => _palette.bgElevated;
  static Color get navBg => _palette.navBg;

  // 强调色
  static Color get accent => _palette.accent;
  static Color get accentLight => _palette.accentLight;

  // 文字色
  static Color get textPrimary => _palette.textPrimary;
  static Color get textSecondary => _palette.textSecondary;
  static Color get textTertiary => _palette.textTertiary;

  // 状态色
  static Color get success => _palette.success;
  static Color get danger => _palette.danger;

  // 边框
  static Color get border => _palette.border;

  // 渐变色
  static List<Color> get cardGradient => _palette.cardGradient;

  static List<BoxShadow> get cardShadow {
    if (!isLight) return [];
    return [
      BoxShadow(
        color: Color(0x14000000),
        blurRadius: 16,
        offset: Offset(0, 6),
      ),
    ];
  }

  static List<BoxShadow> get navShadow {
    if (!isLight) return [];
    return [
      BoxShadow(
        color: Color(0x22000000),
        blurRadius: 12,
        offset: Offset(0, -2),
      ),
    ];
  }

  static List<Color> get dialogGradient {
    return isLight
        ? [Color(0xFFFDFEFF), Color(0xFFF1F5FB)]
        : [Color(0xCC1A2744), Color(0xB30F1829)];
  }

  static ThemeData buildTheme(AppPalette p, Brightness brightness) {
    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      scaffoldBackgroundColor: p.bgPrimary,
      primaryColor: p.accent,
      colorScheme: ColorScheme(
        brightness: brightness,
        primary: p.accent,
        onPrimary: p.textPrimary,
        secondary: p.accentLight,
        onSecondary: p.textPrimary,
        error: p.danger,
        onError: p.textPrimary,
        surface: p.bgCard,
        onSurface: p.textPrimary,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: p.bgPrimary,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          color: p.textPrimary,
          fontSize: 18,
          fontWeight: FontWeight.bold,
        ),
        iconTheme: IconThemeData(color: p.textPrimary),
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: p.navBg,
        selectedItemColor: p.accent,
        unselectedItemColor: p.textTertiary,
        type: BottomNavigationBarType.fixed,
        elevation: 0,
      ),
      cardTheme: CardThemeData(
        color: p.bgCard,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: p.bgCard,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(color: p.border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(color: p.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(color: p.accent),
        ),
        labelStyle: TextStyle(color: p.textSecondary),
        hintStyle: TextStyle(color: p.textTertiary),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: p.accent,
          foregroundColor: p.textPrimary,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
        ),
      ),
      textTheme: TextTheme(
        headlineLarge: TextStyle(color: p.textPrimary, fontWeight: FontWeight.bold),
        headlineMedium: TextStyle(color: p.textPrimary, fontWeight: FontWeight.bold),
        headlineSmall: TextStyle(color: p.textPrimary, fontWeight: FontWeight.bold),
        bodyLarge: TextStyle(color: p.textPrimary),
        bodyMedium: TextStyle(color: p.textSecondary),
        bodySmall: TextStyle(color: p.textTertiary),
      ),
    );
  }

  static ThemeData get darkTheme => buildTheme(AppPalette.dark, Brightness.dark);
  static ThemeData get lightTheme => buildTheme(AppPalette.light, Brightness.light);
}

/// 间距常量
class Spacing {
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;
  static const double xl = 20;
  static const double xxl = 24;
}

/// 字体大小
class FontSize {
  static const double xs = 9;
  static const double sm = 10;
  static const double md = 11;
  static const double base = 12;
  static const double lg = 14;
  static const double xl = 16;
  static const double xxl = 20;
  static const double title = 24;
  static const double hero = 28;
}

/// 圆角大小
class AppRadius {
  static const double sm = 6;
  static const double md = 10;
  static const double lg = 12;
  static const double xl = 16;
  static const double xxl = 20;
}
