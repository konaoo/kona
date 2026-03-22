import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';

import 'config/theme.dart';
import 'providers/app_state.dart';
import 'pages/login_page.dart';
import 'pages/home_page.dart';
import 'pages/invest_page.dart';
import 'pages/analysis_page.dart';
import 'pages/news_page.dart';
import 'pages/profile_page.dart';
import 'pages/asset_detail_page.dart';
import 'pages/portfolio_screenshot_import_page.dart';
import 'widgets/add_asset_dialog.dart';
import 'widgets/invest_trade_dialog.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      systemNavigationBarColor: Colors.transparent,
      systemNavigationBarDividerColor: Colors.transparent,
    ),
  );
  // 预加载登录页所需字体，避免渲染时首帧卡顿
  GoogleFonts.pendingFonts([
    GoogleFonts.dmSans(),
    GoogleFonts.jetBrainsMono(),
  ]);
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AppState(),
      child: Consumer<AppState>(
        builder: (context, appState, child) {
          return MaterialApp(
            title: '咔咔记账',
            debugShowCheckedModeBanner: false,
            theme: AppTheme.lightTheme,
            darkTheme: AppTheme.darkTheme,
            themeMode: appState.themeMode,
            home: const AuthWrapper(),
          );
        },
      ),
    );
  }
}

/// 认证包装器 - 根据登录状态显示不同页面
class AuthWrapper extends StatefulWidget {
  const AuthWrapper({super.key});

  @override
  State<AuthWrapper> createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  @override
  void initState() {
    super.initState();
    // 先加载缓存，登录态由 AppState 持久化恢复结果决定
    context.read<AppState>().hydrateFromCache();
  }

  void _onLoginSuccess() {
    context.read<AppState>().refreshAll();
  }

  void _onLogout() {
    context.read<AppState>().logout();
  }

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();
    switch (appState.sessionBootState) {
      case SessionBootState.initializing:
        return const StartupSplashPage();
      case SessionBootState.authenticated:
        // B1/B2: 包裹 AppLockOverlay
        return AppLockOverlay(child: MainApp(onLogout: _onLogout));
      case SessionBootState.unauthenticated:
        return LoginPage(onLoginSuccess: _onLoginSuccess);
    }
  }
}

class StartupSplashPage extends StatelessWidget {
  const StartupSplashPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        width: double.infinity,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              AppTheme.accent.withValues(alpha: 0.9),
              AppTheme.accent.withValues(alpha: 0.65),
            ],
          ),
        ),
        child: SafeArea(
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(
                  Icons.account_balance_wallet,
                  size: 56,
                  color: Colors.white,
                ),
                const SizedBox(height: 12),
                const Text(
                  '咔咔记账',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 26,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.2,
                  ),
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: 22,
                  height: 22,
                  child: CircularProgressIndicator(
                    strokeWidth: 2.5,
                    valueColor: const AlwaysStoppedAnimation<Color>(
                      Colors.white,
                    ),
                    backgroundColor: Colors.white.withValues(alpha: 0.3),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────
// B1: AppLockOverlay - 全屏锁屏遮罩
// ─────────────────────────────────────────────
class AppLockOverlay extends StatefulWidget {
  final Widget child;

  const AppLockOverlay({super.key, required this.child});

  @override
  State<AppLockOverlay> createState() => _AppLockOverlayState();
}

class _AppLockOverlayState extends State<AppLockOverlay>
    with WidgetsBindingObserver {
  bool _unlocking = false;
  bool _cancelled = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  // B2: 回到前台时触发锁定逻辑已应要求移除
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      // 由 _MainAppState 处理数据刷新；此处不再强制执行 appState.lockApp()
    }
  }

  Future<void> _tryUnlock() async {
    if (_unlocking) return;
    setState(() {
      _unlocking = true;
      _cancelled = false;
    });
    final ok = await context.read<AppState>().tryBiometricLogin();
    if (!mounted) return;
    if (ok) {
      context.read<AppState>().unlockApp();
    } else {
      setState(() {
        _unlocking = false;
        _cancelled = true;
      });
    }
  }

  // B4: 取消后可重试
  void _retryUnlock() {
    setState(() {
      _unlocking = false;
      _cancelled = false;
    });
    _tryUnlock();
  }

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();
    final isDark = Theme.of(context).brightness == Brightness.dark;

    // B4: isAppLocked 决定是否显示遮罩
    if (!appState.isAppLocked) {
      return widget.child;
    }

    return Stack(
      children: [
        widget.child,
        // 遮罩层
        Material(
          color: Colors.transparent,
          child: Container(
            color: isDark
                ? Colors.black.withValues(alpha: 0.88)
                : Colors.white.withValues(alpha: 0.92),
            child: SafeArea(
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 40),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // 图标
                      Container(
                        width: 80,
                        height: 80,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: AppTheme.accent.withValues(alpha: 0.12),
                          border: Border.all(
                            color: AppTheme.accent.withValues(alpha: 0.35),
                            width: 1.5,
                          ),
                        ),
                        child: Icon(
                          Icons.lock_outline_rounded,
                          size: 36,
                          color: AppTheme.accentLight,
                        ),
                      ),
                      const SizedBox(height: 24),
                      Text(
                        '应用已锁定',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.textPrimary,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '请通过生物识别解锁应用',
                        style: TextStyle(
                          fontSize: FontSize.base,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 40),
                      if (_unlocking)
                        Column(
                          children: [
                            SizedBox(
                              width: 32,
                              height: 32,
                              child: CircularProgressIndicator(
                                strokeWidth: 2.5,
                                color: AppTheme.accent,
                              ),
                            ),
                            const SizedBox(height: 12),
                            Text(
                              '正在验证身份…',
                              style: TextStyle(
                                fontSize: FontSize.base,
                                color: AppTheme.textSecondary,
                              ),
                            ),
                          ],
                        )
                      else ...[
                        // 解锁按钮
                        SizedBox(
                          width: double.infinity,
                          height: 50,
                          child: ElevatedButton.icon(
                            key: const Key('app_lock_biometric_button'),
                            onPressed: _tryUnlock,
                            icon: const Icon(Icons.fingerprint_rounded),
                            label: const Text('生物识别解锁'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.accent,
                              foregroundColor: Colors.white,
                              textStyle: TextStyle(
                                fontSize: FontSize.lg,
                                fontWeight: FontWeight.w600,
                              ),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(14),
                              ),
                            ),
                          ),
                        ),
                        if (_cancelled) ...[
                          const SizedBox(height: 16),
                          Text(
                            '验证失败，请重试',
                            style: TextStyle(
                              color: AppTheme.danger,
                              fontSize: FontSize.base,
                            ),
                          ),
                          const SizedBox(height: 8),
                          TextButton(
                            key: const Key('app_lock_retry_button'),
                            onPressed: _retryUnlock,
                            child: Text(
                              '重新验证',
                              style: TextStyle(color: AppTheme.accentLight),
                            ),
                          ),
                        ],
                      ],
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

/// 主应用 - 带底部导航栏
class MainApp extends StatefulWidget {
  final VoidCallback onLogout;

  const MainApp({super.key, required this.onLogout});

  @override
  State<MainApp> createState() => _MainAppState();
}

class _MainAppState extends State<MainApp> with WidgetsBindingObserver {
  int _currentIndex = 0;
  Timer? _priceTimer;
  Timer? _syncTimer;
  DateTime? _lastResumeAt;
  DateTime? _lastPausedAt;
  bool _fabVisible = true;
  bool _investFabExpanded = false;
  final GlobalKey<HomePageState> _homePageKey = GlobalKey<HomePageState>();
  final GlobalKey<InvestPageState> _investPageKey =
      GlobalKey<InvestPageState>();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _startPriceTimer();
    _startSyncTimer(immediate: true);
  }

  @override
  void dispose() {
    _stopPriceTimer();
    _stopSyncTimer();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      final now = DateTime.now();
      final shouldImmediate =
          _lastResumeAt == null ||
          now.difference(_lastResumeAt!) > const Duration(seconds: 15);
      _lastResumeAt = now;
      _startPriceTimer(immediate: shouldImmediate);
      _startSyncTimer(
        immediate: false,
      ); // Resume triggers manual check below, timer starts for future

      final pausedAt = _lastPausedAt;
      if (pausedAt != null) {
        final awayDuration = now.difference(pausedAt);
        final appState = context.read<AppState>();
        if (awayDuration > const Duration(minutes: 30)) {
          unawaited(appState.refreshAll());
        } else if (awayDuration > const Duration(minutes: 5)) {
          unawaited(
            appState.refreshByVersion(force: false, refreshQuotes: false),
          );
        }
      }
    } else if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.inactive) {
      _lastPausedAt = DateTime.now();
      _stopPriceTimer();
      _stopSyncTimer();
    }
  }

  Future<void> _runPriceRefresh() async {
    if (!mounted) return;
    await context.read<AppState>().refreshPricesOnly();
  }

  void _scheduleNextPriceRefresh() {
    if (!mounted) return;
    final intervalSeconds = context
        .read<AppState>()
        .quoteRefreshIntervalSeconds;
    _priceTimer = Timer(Duration(seconds: intervalSeconds), () {
      if (!mounted) return;
      unawaited(() async {
        await _runPriceRefresh();
        _scheduleNextPriceRefresh();
      }());
    });
  }

  void _startPriceTimer({bool immediate = true}) {
    _priceTimer?.cancel();
    if (immediate) {
      unawaited(_runPriceRefresh());
    }
    _scheduleNextPriceRefresh();
  }

  void _stopPriceTimer() {
    _priceTimer?.cancel();
    _priceTimer = null;
  }

  Future<void> _runDataSync() async {
    if (!mounted) return;
    // 静默增量刷新核心业务数据（不强制拉行情以免和 priceTimer 冲突）
    await context.read<AppState>().refreshByVersion(
      force: false,
      refreshQuotes: false,
    );
  }

  void _scheduleNextSyncTimer() {
    if (!mounted) return;
    // 每 2 分钟执行一次前台静默同步
    const intervalSeconds = 120;
    _syncTimer = Timer(const Duration(seconds: intervalSeconds), () {
      if (!mounted) return;
      unawaited(() async {
        await _runDataSync();
        _scheduleNextSyncTimer();
      }());
    });
  }

  void _startSyncTimer({bool immediate = false}) {
    _syncTimer?.cancel();
    if (immediate) {
      unawaited(_runDataSync());
    }
    _scheduleNextSyncTimer();
  }

  void _stopSyncTimer() {
    _syncTimer?.cancel();
    _syncTimer = null;
  }

  void _switchTab(int index) {
    if (_currentIndex != index) {
      // 切换 Tab 时触发一次静默增量刷新（SWR）
      unawaited(_runDataSync());
    }
    setState(() {
      _currentIndex = index;
      _fabVisible = true;
      _investFabExpanded = false;
    });
    _homePageKey.currentState?.resetFabVisibilityController();
    _investPageKey.currentState?.resetFabVisibilityController();
  }

  void _onPrimaryScrollVisibilityChanged(bool visible) {
    if (_fabVisible == visible) return;
    setState(() {
      _fabVisible = visible;
      if (!visible) {
        _investFabExpanded = false;
      }
    });
  }

  void _navigateTo(String pageName) {
    String assetType = '';

    switch (pageName) {
      case 'cash_detail':
        assetType = 'cash';
        break;
      case 'other_detail':
        assetType = 'other';
        break;
      case 'liability_detail':
        assetType = 'liability';
        break;
      default:
        debugPrint('Navigate to: $pageName');
        return;
    }

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => AssetDetailPage(assetType: assetType),
      ),
    );
  }

  void _showQuickAdd() {
    showDialog(
      context: context,
      barrierDismissible: false,
      barrierColor: Colors.black.withValues(alpha: 0.5),
      builder: (dialogContext) => AddAssetDialog(hostContext: context),
    );
  }

  void _showAddInvestment() {
    showInvestTradeSheet(
      context: context,
      mode: 'add',
      hostContext: context,
      presentation: InvestTradeDialogPresentation.centered,
    );
  }

  void _toggleInvestFab() {
    setState(() => _investFabExpanded = !_investFabExpanded);
  }

  Future<void> _openManualInvestment() async {
    setState(() => _investFabExpanded = false);
    _showAddInvestment();
  }

  Future<void> _openScreenshotInvestment() async {
    setState(() => _investFabExpanded = false);
    await Navigator.of(context).push(
      MaterialPageRoute<bool>(
        builder: (_) => const PortfolioScreenshotImportPage(),
        fullscreenDialog: true,
      ),
    );
  }

  static const Color _investFabForeground = Color(0xFF22304D);

  Widget _buildInvestFabOption({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
    required Color backgroundColor,
    required double right,
    required double bottom,
  }) {
    final visible = _investFabExpanded && _fabVisible && _currentIndex == 1;
    return AnimatedPositioned(
      duration: const Duration(milliseconds: 220),
      curve: Curves.easeOutBack,
      right: visible ? right : 10,
      bottom: visible ? bottom : 10,
      child: AnimatedScale(
        scale: visible ? 1 : 0.72,
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOutBack,
        child: AnimatedOpacity(
          opacity: visible ? 1 : 0,
          duration: const Duration(milliseconds: 140),
          child: IgnorePointer(
            ignoring: !visible,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
                  decoration: BoxDecoration(
                    color: backgroundColor.withValues(alpha: 0.94),
                    borderRadius: BorderRadius.circular(999),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.12),
                        blurRadius: 18,
                        offset: const Offset(0, 8),
                      ),
                    ],
                  ),
                  child: Text(
                    label,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      color: _investFabForeground,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                DecoratedBox(
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.18),
                        blurRadius: 24,
                        offset: const Offset(0, 10),
                      ),
                    ],
                  ),
                  child: FloatingActionButton.small(
                    heroTag: '${icon.codePoint}_${right}_$bottom',
                    onPressed: onTap,
                    backgroundColor: backgroundColor,
                    child: Icon(icon, size: 20, color: _investFabForeground),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildInvestFabGroup() {
    return SizedBox(
      width: 240,
      height: 220,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          _buildInvestFabOption(
            icon: Icons.edit_note_rounded,
            label: '手动录入',
            onTap: _openManualInvestment,
            backgroundColor: const Color(0xFFE7C8FF),
            right: 66,
            bottom: 12,
          ),
          _buildInvestFabOption(
            icon: Icons.photo_camera_outlined,
            label: '截图识别',
            onTap: _openScreenshotInvestment,
            backgroundColor: const Color(0xFFC9DBFF),
            right: 18,
            bottom: 84,
          ),
          Positioned(
            right: 0,
            bottom: 0,
            child: DecoratedBox(
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.24),
                    blurRadius: 28,
                    offset: const Offset(0, 12),
                  ),
                ],
              ),
              child: FloatingActionButton.small(
                heroTag: 'add_investment_main',
                onPressed: _toggleInvestFab,
                backgroundColor: const Color(0xFF52679E),
                child: AnimatedRotation(
                  turns: _investFabExpanded ? 0.125 : 0,
                  duration: const Duration(milliseconds: 220),
                  curve: Curves.easeOutCubic,
                  child: Icon(
                    _investFabExpanded ? Icons.close : Icons.add,
                    size: 20,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    // Rebuild on theme changes so bottom bar updates immediately
    context.watch<AppState>();
    return Scaffold(
      body: SafeArea(
        bottom: false,
        minimum: const EdgeInsets.only(top: 8),
        child: IndexedStack(
          index: _currentIndex,
          children: [
            HomePage(
              key: _homePageKey,
              onNavigate: _navigateTo,
              onSwitchTab: _switchTab,
              onFabVisibilityChanged: _onPrimaryScrollVisibilityChanged,
            ),
            InvestPage(
              key: _investPageKey,
              onFabVisibilityChanged: _onPrimaryScrollVisibilityChanged,
            ),
            const AnalysisPage(),
            const NewsPage(),
            ProfilePage(onLogout: widget.onLogout),
          ],
        ),
      ),
      floatingActionButton: _currentIndex == 0 || _currentIndex == 1
          ? AnimatedSlide(
              offset: _fabVisible ? Offset.zero : const Offset(0, 2.2),
              duration: const Duration(milliseconds: 180),
              curve: Curves.easeOutCubic,
              child: AnimatedOpacity(
                opacity: _fabVisible ? 1 : 0,
                duration: const Duration(milliseconds: 140),
                child: IgnorePointer(
                  ignoring: !_fabVisible,
                  child: _currentIndex == 0
                      ? FloatingActionButton.small(
                          heroTag: 'add_asset_home',
                          onPressed: _showQuickAdd,
                          backgroundColor: AppTheme.accent,
                          child: Icon(
                            Icons.add,
                            size: 20,
                            color: AppTheme.isLight
                                ? Colors.white
                                : AppTheme.textPrimary,
                          ),
                        )
                      : _buildInvestFabGroup(),
                ),
              ),
            )
          : null,
      floatingActionButtonLocation: FloatingActionButtonLocation.endFloat,
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: AppTheme.navBg,
          border: Border(
            top: BorderSide(
              color: AppTheme.isLight
                  ? const Color(0x0F000000)
                  : Colors.transparent,
              width: AppTheme.isLight ? 1 : 0,
            ),
          ),
          boxShadow: AppTheme.navShadow,
        ),
        child: SafeArea(
          child: SizedBox(
            height: 60,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildNavItem(0, Icons.home_outlined, Icons.home, '首页'),
                _buildNavItem(
                  1,
                  Icons.business_center_outlined,
                  Icons.business_center,
                  '投资',
                ),
                _buildNavItem(
                  2,
                  Icons.insert_chart_outlined,
                  Icons.insert_chart,
                  '分析',
                ),
                _buildNavItem(3, Icons.flash_on_outlined, Icons.flash_on, '快讯'),
                _buildNavItem(4, Icons.person_outline, Icons.person, '我的'),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(
    int index,
    IconData icon,
    IconData activeIcon,
    String label,
  ) {
    final isSelected = _currentIndex == index;
    return Expanded(
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => _switchTab(index),
          child: Container(
            height: 60,
            alignment: Alignment.center,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  isSelected ? activeIcon : icon,
                  color: isSelected ? AppTheme.accent : AppTheme.textTertiary,
                  size: 24,
                ),
                const SizedBox(height: 4),
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 11,
                    color: isSelected ? AppTheme.accent : AppTheme.textTertiary,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
