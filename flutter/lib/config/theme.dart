import 'package:flutter/material.dart';

class AppPalette {
  final Color bgPrimary;
  final Color bgCard;
  final Color bgElevated;
  final Color navBg;
  final Color surface2;
  final Color surface3;
  final Color accent;
  final Color accentLight;
  final Color gold;
  final Color goldDim;
  final Color textPrimary;
  final Color textSecondary;
  final Color textTertiary;
  final Color textDim;
  final Color textMuted;
  final Color success;
  final Color danger;
  final Color border;
  final Color borderSubtle;
  final Color borderDivider;
  final List<Color> cardGradient;

  const AppPalette({
    required this.bgPrimary,
    required this.bgCard,
    required this.bgElevated,
    required this.navBg,
    required this.surface2,
    required this.surface3,
    required this.accent,
    required this.accentLight,
    required this.gold,
    required this.goldDim,
    required this.textPrimary,
    required this.textSecondary,
    required this.textTertiary,
    required this.textDim,
    required this.textMuted,
    required this.success,
    required this.danger,
    required this.border,
    required this.borderSubtle,
    required this.borderDivider,
    required this.cardGradient,
  });

  static const dark = AppPalette(
    bgPrimary: Color(0xFF0C0D11),
    bgCard: Color(0xFF13151C),
    bgElevated: Color(0xFF181B23),
    navBg: Color(0xFF0F1118),
    surface2: Color(0xFF1A1D25),
    surface3: Color(0xFF20242E),
    accent: Color(0xFF5B8DEF),
    accentLight: Color(0xFF60A5FA),
    gold: Color(0xFFD4AF64),
    goldDim: Color(0x1FD4AF64),
    textPrimary: Color(0xFFE8EAF0),
    textSecondary: Color(0xFF8B909F),
    textTertiary: Color(0xFF64748B),
    textDim: Color(0xFF4E5464),
    textMuted: Color(0xFF575D6E),
    success: Color(0xFF2ECC8A),
    danger: Color(0xFFF05A55),
    border: Color(0x1FFFFFFF),
    borderSubtle: Color(0x0CFFFFFF),
    borderDivider: Color(0x0FFFFFFF),
    cardGradient: [Color(0xFF1A2744), Color(0xFF0F1829)],
  );

  // 轻浅文艺风：柔和米白 + 低饱和蓝绿
  static const light = AppPalette(
    bgPrimary: Color(0xFFEEF2F8),
    bgCard: Color(0xFFF8FAFF),
    bgElevated: Color(0xFFEFF3FB),
    navBg: Color(0xFFE6EDFA),
    surface2: Color(0xFFEFF3FB),
    surface3: Color(0xFFE5EBF7),
    accent: Color(0xFF4B86F0),
    accentLight: Color(0xFF8CB5FF),
    gold: Color(0xFFB8942D),
    goldDim: Color(0x1FB8942D),
    textPrimary: Color(0xFF1F2A3D),
    textSecondary: Color(0xFF55617B),
    textTertiary: Color(0xFF69758F),
    textDim: Color(0xFF8A94AB),
    textMuted: Color(0xFF69758F),
    success: Color(0xFF16A34A),
    danger: Color(0xFFE45656),
    border: Color(0x1A222C40),
    borderSubtle: Color(0x17222C40),
    borderDivider: Color(0x14222C40),
    cardGradient: [Color(0xFFFFFFFF), Color(0xFFF5F8FF)],
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
  static Color get surface2 => _palette.surface2;
  static Color get surface3 => _palette.surface3;

  // 强调色
  static Color get accent => _palette.accent;
  static Color get accentLight => _palette.accentLight;
  static Color get gold => _palette.gold;
  static Color get goldDim => _palette.goldDim;

  // 文字色
  static Color get textPrimary => _palette.textPrimary;
  static Color get textSecondary => _palette.textSecondary;
  static Color get textTertiary => _palette.textTertiary;
  static Color get textMuted => _palette.textMuted;
  static Color get textDim => _palette.textDim;

  // 状态色
  static Color get success => _palette.success;
  static Color get danger => _palette.danger;

  // 边框
  static Color get border => _palette.border;
  static Color get borderSubtle => _palette.borderSubtle;
  static Color get borderDivider => _palette.borderDivider;

  // 渐变色
  static List<Color> get cardGradient => _palette.cardGradient;

  // ── 分割线颜色 ──
  static Color get dividerColor =>
      isLight ? const Color(0x1A222C40) : const Color(0x1AFFFFFF);

  // ── Hero 卡片装饰 ──
  static BoxDecoration get heroDecoration => BoxDecoration(
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: isLight
              ? const Color(0x2E5B8DEF) // rgba(91,141,239,0.18)
              : Colors.white.withValues(alpha: 0.06),
        ),
        gradient: LinearGradient(
          begin: const Alignment(-0.6, -1),
          end: const Alignment(1, 1),
          colors: isLight
              ? [const Color(0xFFDDE8FF), const Color(0xFFCFDAF5), const Color(0xFFC8D5F0)]
              : [const Color(0x335B8DEF), const Color(0x0F4A7BE0), const Color(0xF0191C25)],
          stops: const [0.0, 0.6, 1.0],
        ),
        boxShadow: [
          BoxShadow(
            color: isLight
                ? const Color(0x1A222C48) // rgba(34,44,72,0.10)
                : Colors.black.withValues(alpha: 0.35),
            blurRadius: isLight ? 20 : 26,
            offset: isLight ? const Offset(0, 8) : const Offset(0, 12),
          ),
        ],
      );

  // ── Hero 卡片内部的文字颜色 ──
  static Color get heroLabelColor =>
      isLight ? const Color(0xFF55617B) : const Color(0xFF9AA3B7);

  static Color get heroValueColor =>
      isLight ? const Color(0xFF111C2E) : const Color(0xFFF0F4FF);

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
