import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'config/theme.dart';
import 'providers/app_state.dart';
import 'pages/login_page.dart';
import 'pages/home_page.dart';
import 'pages/invest_page.dart';
import 'pages/analysis_page.dart';
import 'pages/news_page.dart';
import 'pages/profile_page.dart';
import 'pages/asset_detail_page.dart';
import 'widgets/add_asset_dialog.dart';
import 'widgets/invest_trade_dialog.dart';

void main() {
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
  bool _isLoggedIn = false;

  @override
  void initState() {
    super.initState();
    // 临时自动登录 - 方便测试
    context.read<AppState>().hydrateFromCache();
    _autoLogin();
  }

  Future<void> _autoLogin() async {
    final appState = context.read<AppState>();
    // 自动登录已关闭，防止跳过验证码
    if (mounted) {
      setState(() => _isLoggedIn = false);
    }
  }

  void _onLoginSuccess() {
    setState(() => _isLoggedIn = true);
    context.read<AppState>().refreshAll();
  }

  void _onLogout() {
    context.read<AppState>().logout();
    setState(() => _isLoggedIn = false);
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoggedIn) {
      return MainApp(onLogout: _onLogout);
    } else {
      return LoginPage(onLoginSuccess: _onLoginSuccess);
    }
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

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _startPriceTimer();
  }

  @override
  void dispose() {
    _stopPriceTimer();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _startPriceTimer();
    } else if (state == AppLifecycleState.paused || state == AppLifecycleState.inactive) {
      _stopPriceTimer();
    }
  }

  void _startPriceTimer() {
    _priceTimer?.cancel();
    _priceTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      if (!mounted) return;
      context.read<AppState>().refreshPricesOnly();
    });
  }

  void _stopPriceTimer() {
    _priceTimer?.cancel();
    _priceTimer = null;
  }

  void _switchTab(int index) {
    setState(() => _currentIndex = index);
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
      barrierColor: Colors.black.withOpacity(0.5),
      builder: (context) => const AddAssetDialog(),
    );
  }

  void _showAddInvestment() {
    showDialog(
      context: context,
      barrierColor: Colors.black.withOpacity(0.5),
      builder: (context) => const InvestTradeDialog(mode: 'add'),
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
              onNavigate: _navigateTo,
              onSwitchTab: _switchTab,
            ),
            const InvestPage(),
            const AnalysisPage(),
            const NewsPage(),
            ProfilePage(onLogout: widget.onLogout),
          ],
        ),
      ),
      floatingActionButton: _currentIndex == 0 || _currentIndex == 1
          ? FloatingActionButton.small(
              heroTag: _currentIndex == 0 ? 'add_asset_home' : 'add_investment',
              onPressed: _currentIndex == 0 ? _showQuickAdd : _showAddInvestment,
              backgroundColor: AppTheme.accent,
              child: Icon(
                Icons.add,
                size: 20,
                color: AppTheme.isLight ? Colors.white : AppTheme.textPrimary,
              ),
            )
          : null,
      floatingActionButtonLocation: FloatingActionButtonLocation.endFloat,
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: AppTheme.navBg,
          border: Border(
            top: BorderSide(color: AppTheme.border.withOpacity(AppTheme.isLight ? 0.6 : 0.3), width: 1),
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
                _buildNavItem(1, Icons.business_center_outlined, Icons.business_center, '投资'),
                _buildNavItem(2, Icons.insert_chart_outlined, Icons.insert_chart, '分析'),
                _buildNavItem(3, Icons.flash_on_outlined, Icons.flash_on, '快讯'),
                _buildNavItem(4, Icons.person_outline, Icons.person, '我的'),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(int index, IconData icon, IconData activeIcon, String label) {
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
