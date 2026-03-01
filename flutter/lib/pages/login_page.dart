import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:provider/provider.dart';

import '../config/theme.dart';
import 'invite_acquire_page.dart';
import '../providers/app_state.dart';

/// 登录/注册页面
class LoginPage extends StatefulWidget {
  final VoidCallback onLoginSuccess;

  const LoginPage({super.key, required this.onLoginSuccess});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> with TickerProviderStateMixin {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  final _inviteController = TextEditingController();

  // Focus nodes for keyboard chaining (A5)
  final _usernameFocus = FocusNode();
  final _passwordFocus = FocusNode();
  final _confirmFocus = FocusNode();
  final _inviteFocus = FocusNode();

  bool _isRegister = false;
  bool _submitting = false;
  String? _errorMessage;
  bool? _inviteValid;

  // A2: 密码显示/隐藏
  bool _passwordVisible = false;
  bool _confirmVisible = false;

  // A8: 记住用户名
  bool _rememberUsername = false;
  bool _rememberLoaded = false;

  // A6: 邀请码防抖
  Timer? _inviteDebounce;

  // A7: 成功状态动画
  bool _showSuccess = false;

  // ─── Animation controllers ────────────────────────────────
  // A1: 入场动画
  late final AnimationController _entranceController;
  late final Animation<double> _logoFade;
  late final Animation<Offset> _logoSlide;
  late final Animation<double> _formFade;
  late final Animation<Offset> _formSlide;

  // A3: Shake 动画
  late final AnimationController _shakeController;
  late final Animation<double> _shakeAnimation;

  // A7: 成功动画
  late final AnimationController _successController;
  late final Animation<double> _successScale;
  late final Animation<double> _successOpacity;

  @override
  void initState() {
    super.initState();

    // A1: entrance animation
    _entranceController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _logoFade = CurvedAnimation(
      parent: _entranceController,
      curve: const Interval(0.0, 0.6, curve: Curves.easeOut),
    );
    _logoSlide = Tween<Offset>(begin: const Offset(0, -0.3), end: Offset.zero)
        .animate(
          CurvedAnimation(
            parent: _entranceController,
            curve: const Interval(0.0, 0.6, curve: Curves.easeOutCubic),
          ),
        );
    _formFade = CurvedAnimation(
      parent: _entranceController,
      curve: const Interval(0.35, 1.0, curve: Curves.easeOut),
    );
    _formSlide = Tween<Offset>(begin: const Offset(0, 0.15), end: Offset.zero)
        .animate(
          CurvedAnimation(
            parent: _entranceController,
            curve: const Interval(0.35, 1.0, curve: Curves.easeOutCubic),
          ),
        );

    // A3: shake animation
    _shakeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 480),
    );
    _shakeAnimation =
        TweenSequence<double>([
          TweenSequenceItem(tween: Tween(begin: 0, end: -8), weight: 1),
          TweenSequenceItem(tween: Tween(begin: -8, end: 8), weight: 2),
          TweenSequenceItem(tween: Tween(begin: 8, end: -6), weight: 2),
          TweenSequenceItem(tween: Tween(begin: -6, end: 6), weight: 2),
          TweenSequenceItem(tween: Tween(begin: 6, end: -3), weight: 2),
          TweenSequenceItem(tween: Tween(begin: -3, end: 0), weight: 1),
        ]).animate(
          CurvedAnimation(parent: _shakeController, curve: Curves.easeInOut),
        );

    // A7: success animation
    _successController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _successScale = Tween<double>(begin: 0.5, end: 1.0).animate(
      CurvedAnimation(
        parent: _successController,
        curve: const Interval(0.0, 0.7, curve: Curves.elasticOut),
      ),
    );
    _successOpacity = CurvedAnimation(
      parent: _successController,
      curve: const Interval(0.0, 0.4, curve: Curves.easeIn),
    );

    // start entrance
    _entranceController.forward();

    // load saved username & remember flag
    Future<void>.microtask(() async {
      if (!mounted) return;
      context.read<AppState>().reloadBiometricPreference();
      await _loadRememberedUsername();
    });
  }

  Future<void> _loadRememberedUsername() async {
    if (!mounted) return;
    final appState = context.read<AppState>();
    // AppState exposes _secureStorage indirectly via username getter after restoreSession.
    // We read stored username directly from SecureStorage through AppState helper.
    final savedUsername = appState.username ?? '';
    if (savedUsername.isNotEmpty) {
      _usernameController.text = savedUsername;
      setState(() {
        _rememberUsername = true;
        _rememberLoaded = true;
      });
    } else {
      setState(() => _rememberLoaded = true);
    }
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _confirmController.dispose();
    _inviteController.dispose();
    _usernameFocus.dispose();
    _passwordFocus.dispose();
    _confirmFocus.dispose();
    _inviteFocus.dispose();
    _inviteDebounce?.cancel();
    _entranceController.dispose();
    _shakeController.dispose();
    _successController.dispose();
    super.dispose();
  }

  bool _validUsername(String username) {
    return RegExp(r'^[a-z][a-z0-9_]{3,23}$').hasMatch(username);
  }

  bool _validPassword(String password) {
    if (password.length < 8 || password.length > 64) return false;
    final hasLetter = RegExp(r'[A-Za-z]').hasMatch(password);
    final hasDigit = RegExp(r'\d').hasMatch(password);
    return hasLetter && hasDigit;
  }

  // A6: 邀请码防抖
  void _checkInviteCodeDebounced() {
    _inviteDebounce?.cancel();
    _inviteDebounce = Timer(const Duration(milliseconds: 500), () {
      if (mounted) _checkInviteCode();
    });
  }

  Future<void> _checkInviteCode() async {
    final code = _inviteController.text.trim().toUpperCase();
    if (code.length < 8) {
      setState(() => _inviteValid = null);
      return;
    }
    final ok = await context.read<AppState>().validateInviteCode(code);
    if (!mounted) return;
    setState(() => _inviteValid = ok);
  }

  void _handleFieldChanged() {
    context.read<AppState>().clearAuthError();
    if (_errorMessage == null) return;
    setState(() => _errorMessage = null);
  }

  // A3: 触发 shake 动画并显示错误
  void _setError(String msg) {
    setState(() => _errorMessage = msg);
    _shakeController.forward(from: 0);
  }

  Future<void> _submit() async {
    FocusManager.instance.primaryFocus?.unfocus();
    final username = _usernameController.text.trim().toLowerCase();
    final password = _passwordController.text;
    final confirm = _confirmController.text;
    final invite = _inviteController.text.trim().toUpperCase();

    if (!_isRegister && (username.isEmpty || password.isEmpty)) {
      _setError('请输入用户名和密码');
      return;
    }
    if (!_validUsername(username)) {
      _setError('用户名格式不正确（4-24位，小写字母开头）');
      return;
    }
    if (!_validPassword(password)) {
      _setError('密码需 8-64 位，且包含字母和数字');
      return;
    }
    if (_isRegister) {
      if (confirm != password) {
        _setError('两次密码输入不一致');
        return;
      }
      if (invite.isEmpty) {
        _setError('请输入邀请码');
        return;
      }
      if (_inviteValid == false) {
        _setError('邀请码不可用');
        return;
      }
    }

    setState(() {
      _submitting = true;
      _errorMessage = null;
    });

    bool success = false;
    if (_isRegister) {
      success = await context.read<AppState>().register(
        username: username,
        password: password,
        inviteCode: invite,
      );
    } else {
      success = await context.read<AppState>().login(
        username: username,
        password: password,
      );
    }

    if (!mounted) return;

    if (success) {
      // A7: 成功动画
      setState(() {
        _submitting = false;
        _showSuccess = true;
      });
      await _successController.forward();
      await Future<void>.delayed(const Duration(milliseconds: 400));
      if (!mounted) return;
      widget.onLoginSuccess();
      return;
    }

    final authError = context.read<AppState>().authErrorMessage;
    final errMsg = authError?.trim().isNotEmpty == true
        ? authError!.trim()
        : (_isRegister ? '注册失败，请检查邀请码或用户名' : '登录失败，请检查用户名或密码');
    setState(() => _submitting = false);
    _setError(errMsg);
  }

  Future<void> _tryBiometricLogin() async {
    FocusManager.instance.primaryFocus?.unfocus();
    await Future<void>.delayed(const Duration(milliseconds: 180));
    if (!mounted) return;
    setState(() {
      _submitting = true;
      _errorMessage = null;
    });
    final ok = await context.read<AppState>().tryBiometricLogin();
    if (!mounted) return;
    if (ok) {
      setState(() {
        _submitting = false;
        _showSuccess = true;
      });
      await _successController.forward();
      await Future<void>.delayed(const Duration(milliseconds: 400));
      if (!mounted) return;
      widget.onLoginSuccess();
      return;
    }
    setState(() => _submitting = false);
    _setError('生物识别登录失败');
  }

  Future<void> _openInviteAcquireLink() async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) =>
            const InviteAcquirePage(scene: InviteAcquireScene.invite),
      ),
    );
  }

  SystemUiOverlayStyle _overlayStyle(bool isDark) {
    if (isDark) {
      return const SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: Brightness.light,
        statusBarBrightness: Brightness.dark,
        systemNavigationBarColor: Colors.transparent,
        systemNavigationBarIconBrightness: Brightness.light,
        systemNavigationBarDividerColor: Colors.transparent,
      );
    }
    return const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
      statusBarBrightness: Brightness.light,
      systemNavigationBarColor: Colors.transparent,
      systemNavigationBarIconBrightness: Brightness.dark,
      systemNavigationBarDividerColor: Colors.transparent,
    );
  }

  Widget _buildLogoHeader(bool isDark) {
    final mark = SvgPicture.asset(
      'assets/images/login_logo_mark.svg',
      key: const Key('login_logo_mark'),
      width: 70,
      height: 70,
    );

    if (isDark) {
      return Container(
        key: const Key('login_logo_shell'),
        width: 108,
        height: 108,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: AppTheme.accent.withValues(alpha: 0.16)),
          gradient: const LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0x220B2452), Color(0x1108162F)],
          ),
          boxShadow: [
            BoxShadow(
              color: AppTheme.accent.withValues(alpha: 0.18),
              blurRadius: 26,
              spreadRadius: -6,
              offset: const Offset(0, 12),
            ),
          ],
        ),
        child: mark,
      );
    }

    return Container(
      key: const Key('login_logo_shell'),
      width: 104,
      height: 104,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: AppTheme.bgCard.withValues(alpha: 0.9),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: AppTheme.border.withValues(alpha: 0.85)),
        boxShadow: [
          BoxShadow(
            color: AppTheme.accent.withValues(alpha: 0.12),
            blurRadius: 18,
            spreadRadius: -3,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: mark,
    );
  }

  // A7: 成功覆盖层
  Widget _buildSuccessOverlay() {
    return AnimatedBuilder(
      animation: _successController,
      builder: (context, _) => Opacity(
        opacity: _successOpacity.value,
        child: ScaleTransition(
          scale: _successScale,
          child: Container(
            width: 72,
            height: 72,
            decoration: BoxDecoration(
              color: AppTheme.success,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: AppTheme.success.withValues(alpha: 0.35),
                  blurRadius: 20,
                  spreadRadius: -2,
                ),
              ],
            ),
            child: const Icon(
              Icons.check_rounded,
              color: Colors.white,
              size: 38,
            ),
          ),
        ),
      ),
    );
  }

  // A3: 错误提示（带图标）
  Widget _buildErrorBanner(String message) {
    return AnimatedBuilder(
      animation: _shakeAnimation,
      builder: (context, child) => Transform.translate(
        offset: Offset(_shakeAnimation.value, 0),
        child: child,
      ),
      child: Container(
        margin: const EdgeInsets.only(top: Spacing.sm),
        padding: const EdgeInsets.symmetric(
          horizontal: Spacing.md,
          vertical: Spacing.sm,
        ),
        decoration: BoxDecoration(
          color: AppTheme.danger.withValues(alpha: 0.10),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppTheme.danger.withValues(alpha: 0.28)),
        ),
        child: Row(
          children: [
            Icon(Icons.error_outline_rounded, size: 16, color: AppTheme.danger),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                message,
                style: TextStyle(
                  color: AppTheme.danger,
                  fontSize: FontSize.base,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // A2: 密码输入框
  Widget _buildPasswordField({
    required TextEditingController controller,
    required String label,
    required bool visible,
    required VoidCallback onToggle,
    required FocusNode focusNode,
    TextInputAction textInputAction = TextInputAction.next,
    VoidCallback? onSubmitted,
  }) {
    return TextField(
      controller: controller,
      obscureText: !visible,
      focusNode: focusNode,
      textInputAction: textInputAction,
      onSubmitted: (_) => onSubmitted?.call(),
      style: TextStyle(color: AppTheme.textPrimary),
      decoration: InputDecoration(
        labelText: label,
        suffixIcon: IconButton(
          key: Key('toggle_${label}_visibility'),
          onPressed: onToggle,
          icon: Icon(
            visible ? Icons.visibility_outlined : Icons.visibility_off_outlined,
            size: 20,
            color: AppTheme.textSecondary,
          ),
        ),
      ),
      onChanged: (_) => _handleFieldChanged(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();
    final showBiometric = !_isRegister && appState.biometricEnabled;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bottomInset = MediaQuery.of(context).padding.bottom;

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: _overlayStyle(isDark),
      child: Scaffold(
        backgroundColor: Colors.transparent,
        extendBody: true,
        body: Stack(
          children: [
            // 背景 + 主体
            Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  stops: const [0.0, 0.34, 0.76, 1.0],
                  colors: isDark
                      ? const [
                          Color(0xFF08122D),
                          Color(0xFF0C1D45),
                          Color(0xFF102650),
                          Color(0xFF0A1635),
                        ]
                      : [
                          AppTheme.bgPrimary,
                          AppTheme.bgElevated.withValues(alpha: 0.92),
                          AppTheme.bgPrimary,
                          AppTheme.bgPrimary,
                        ],
                ),
              ),
              child: SafeArea(
                top: true,
                bottom: false,
                minimum: const EdgeInsets.only(top: 8),
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    return SingleChildScrollView(
                      padding: EdgeInsets.fromLTRB(
                        Spacing.xl,
                        0,
                        Spacing.xl,
                        24 + bottomInset,
                      ),
                      child: ConstrainedBox(
                        constraints: BoxConstraints(
                          minHeight: constraints.maxHeight,
                        ),
                        child: Column(
                          children: [
                            const SizedBox(height: 72),

                            // A1: Logo 入场动画
                            SlideTransition(
                              position: _logoSlide,
                              child: FadeTransition(
                                opacity: _logoFade,
                                child: _buildLogoHeader(isDark),
                              ),
                            ),

                            FadeTransition(
                              opacity: _formFade,
                              child: SlideTransition(
                                position: _formSlide,
                                child: Column(
                                  crossAxisAlignment:
                                      CrossAxisAlignment.stretch,
                                  children: [
                                    const SizedBox(height: Spacing.lg),
                                    Text(
                                      '咔咔记账',
                                      textAlign: TextAlign.center,
                                      style: TextStyle(
                                        fontSize: FontSize.title,
                                        fontWeight: FontWeight.bold,
                                        color: AppTheme.textPrimary,
                                      ),
                                    ),
                                    const SizedBox(height: Spacing.sm),
                                    // A4: 切换文字平滑动画
                                    AnimatedSwitcher(
                                      duration: const Duration(
                                        milliseconds: 250,
                                      ),
                                      transitionBuilder: (child, animation) =>
                                          FadeTransition(
                                            opacity: animation,
                                            child: child,
                                          ),
                                      child: Text(
                                        _isRegister ? '创建账号' : '账号密码登录',
                                        key: ValueKey(_isRegister),
                                        textAlign: TextAlign.center,
                                        style: TextStyle(
                                          fontSize: FontSize.lg,
                                          color: AppTheme.textSecondary,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(height: Spacing.xl),

                                    // A5: 用户名框，textInputAction 跳转到密码
                                    TextField(
                                      controller: _usernameController,
                                      focusNode: _usernameFocus,
                                      keyboardType: TextInputType.text,
                                      textInputAction: TextInputAction.next,
                                      onSubmitted: (_) =>
                                          _passwordFocus.requestFocus(),
                                      style: TextStyle(
                                        color: AppTheme.textPrimary,
                                      ),
                                      decoration: const InputDecoration(
                                        labelText: '用户名',
                                      ),
                                      onChanged: (_) => _handleFieldChanged(),
                                    ),

                                    const SizedBox(height: Spacing.md),

                                    // A2 + A5: 密码框
                                    _buildPasswordField(
                                      controller: _passwordController,
                                      label: '密码',
                                      visible: _passwordVisible,
                                      onToggle: () => setState(
                                        () => _passwordVisible =
                                            !_passwordVisible,
                                      ),
                                      focusNode: _passwordFocus,
                                      textInputAction: _isRegister
                                          ? TextInputAction.next
                                          : TextInputAction.done,
                                      onSubmitted: _isRegister
                                          ? () => _confirmFocus.requestFocus()
                                          : _submit,
                                    ),

                                    // A4: 注册模式额外字段，AnimatedSize 平滑展开
                                    AnimatedSize(
                                      duration: const Duration(
                                        milliseconds: 300,
                                      ),
                                      curve: Curves.easeInOut,
                                      child: _isRegister
                                          ? Column(
                                              crossAxisAlignment:
                                                  CrossAxisAlignment.stretch,
                                              children: [
                                                const SizedBox(
                                                  height: Spacing.md,
                                                ),
                                                // A2: 确认密码 + 眼睛
                                                _buildPasswordField(
                                                  controller:
                                                      _confirmController,
                                                  label: '确认密码',
                                                  visible: _confirmVisible,
                                                  onToggle: () => setState(
                                                    () => _confirmVisible =
                                                        !_confirmVisible,
                                                  ),
                                                  focusNode: _confirmFocus,
                                                  textInputAction:
                                                      TextInputAction.next,
                                                  onSubmitted: () =>
                                                      _inviteFocus
                                                          .requestFocus(),
                                                ),
                                                const SizedBox(
                                                  height: Spacing.md,
                                                ),
                                                // A6: 邀请码防抖
                                                TextField(
                                                  controller: _inviteController,
                                                  focusNode: _inviteFocus,
                                                  textInputAction:
                                                      TextInputAction.done,
                                                  onSubmitted: (_) => _submit(),
                                                  style: TextStyle(
                                                    color: AppTheme.textPrimary,
                                                  ),
                                                  decoration: InputDecoration(
                                                    labelText: '邀请码',
                                                    hintText: '请输入邀请码',
                                                    suffixIcon: IconButton(
                                                      onPressed: _submitting
                                                          ? null
                                                          : _checkInviteCode,
                                                      icon: Icon(
                                                        _inviteValid == null
                                                            ? Icons.help_outline
                                                            : (_inviteValid!
                                                                  ? Icons
                                                                        .check_circle
                                                                  : Icons
                                                                        .error),
                                                        color:
                                                            _inviteValid == null
                                                            ? AppTheme
                                                                  .textSecondary
                                                            : (_inviteValid!
                                                                  ? AppTheme
                                                                        .success
                                                                  : AppTheme
                                                                        .danger),
                                                      ),
                                                    ),
                                                  ),
                                                  onChanged: (_) {
                                                    _handleFieldChanged();
                                                    // A6 debounce
                                                    _checkInviteCodeDebounced();
                                                  },
                                                ),
                                                const SizedBox(
                                                  height: Spacing.sm,
                                                ),
                                                Align(
                                                  alignment:
                                                      Alignment.centerLeft,
                                                  child: TextButton(
                                                    onPressed: _submitting
                                                        ? null
                                                        : _openInviteAcquireLink,
                                                    style: TextButton.styleFrom(
                                                      minimumSize: const Size(
                                                        0,
                                                        0,
                                                      ),
                                                      tapTargetSize:
                                                          MaterialTapTargetSize
                                                              .shrinkWrap,
                                                      padding: EdgeInsets.zero,
                                                      foregroundColor:
                                                          AppTheme.accentLight,
                                                    ),
                                                    child: Text(
                                                      '没有邀请码，点我获取',
                                                      style: TextStyle(
                                                        fontSize: FontSize.base,
                                                        color: AppTheme
                                                            .accentLight,
                                                        decoration:
                                                            TextDecoration
                                                                .underline,
                                                        decorationColor:
                                                            AppTheme
                                                                .accentLight,
                                                        fontWeight:
                                                            FontWeight.w600,
                                                      ),
                                                    ),
                                                  ),
                                                ),
                                              ],
                                            )
                                          : const SizedBox.shrink(),
                                    ),

                                    // A8+生物识别: 密码框下方紧凑行
                                    if (!_isRegister && _rememberLoaded)
                                      Padding(
                                        padding: const EdgeInsets.only(
                                          top: Spacing.sm,
                                        ),
                                        child: Row(
                                          children: [
                                            GestureDetector(
                                              behavior: HitTestBehavior.opaque,
                                              onTap: _submitting
                                                  ? null
                                                  : () => setState(
                                                      () => _rememberUsername =
                                                          !_rememberUsername,
                                                    ),
                                              child: Row(
                                                mainAxisSize: MainAxisSize.min,
                                                children: [
                                                  SizedBox(
                                                    width: 20,
                                                    height: 20,
                                                    child: Checkbox(
                                                      key: const Key(
                                                        'remember_username_checkbox',
                                                      ),
                                                      value: _rememberUsername,
                                                      onChanged: _submitting
                                                          ? null
                                                          : (v) => setState(
                                                              () =>
                                                                  _rememberUsername =
                                                                      v ??
                                                                      false,
                                                            ),
                                                      activeColor:
                                                          AppTheme.accent,
                                                      shape: RoundedRectangleBorder(
                                                        borderRadius:
                                                            BorderRadius.circular(
                                                              4,
                                                            ),
                                                      ),
                                                      materialTapTargetSize:
                                                          MaterialTapTargetSize
                                                              .shrinkWrap,
                                                      visualDensity:
                                                          VisualDensity.compact,
                                                    ),
                                                  ),
                                                  const SizedBox(width: 6),
                                                  Text(
                                                    '记住用户名',
                                                    style: TextStyle(
                                                      fontSize: FontSize.sm,
                                                      color: AppTheme
                                                          .textSecondary,
                                                    ),
                                                  ),
                                                ],
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),

                                    // A3: 错误提示，带 shake 动画
                                    if (_errorMessage != null)
                                      _buildErrorBanner(_errorMessage!),

                                    const SizedBox(height: Spacing.xl),

                                    // A7: 提交按钮，成功时显示打勾
                                    SizedBox(
                                      key: const Key('login_primary_action'),
                                      width: double.infinity,
                                      height: 50,
                                      child: _showSuccess
                                          ? Center(
                                              child: _buildSuccessOverlay(),
                                            )
                                          : ElevatedButton(
                                              onPressed: _submitting
                                                  ? null
                                                  : _submit,
                                              child: _submitting
                                                  ? SizedBox(
                                                      width: 24,
                                                      height: 24,
                                                      child:
                                                          CircularProgressIndicator(
                                                            strokeWidth: 2,
                                                            color: AppTheme
                                                                .textPrimary,
                                                          ),
                                                    )
                                                  : Text(
                                                      _isRegister
                                                          ? '注册并登录'
                                                          : '登录',
                                                      style: TextStyle(
                                                        fontSize: FontSize.lg,
                                                      ),
                                                    ),
                                            ),
                                    ),

                                    // 生物识别文字链接
                                    if (showBiometric) ...[
                                      const SizedBox(
                                        height: Spacing.xl,
                                      ), // 从 lg 加大到 xl
                                      GestureDetector(
                                        key: const Key('biometric_text_button'),
                                        onTap: _submitting
                                            ? null
                                            : _tryBiometricLogin,
                                        child: Center(
                                          child: Opacity(
                                            opacity: _submitting ? 0.4 : 1.0,
                                            child: Row(
                                              mainAxisSize: MainAxisSize.min,
                                              children: [
                                                Icon(
                                                  Icons.fingerprint_rounded,
                                                  size: 26, // 图标进一步加大
                                                  color: AppTheme.textSecondary,
                                                ),
                                                const SizedBox(width: 8),
                                                Text(
                                                  '使用 Face ID / 指纹登录',
                                                  style: TextStyle(
                                                    fontSize: 18, // 进一步明确字号增大
                                                    color:
                                                        AppTheme.textSecondary,
                                                  ),
                                                ),
                                              ],
                                            ),
                                          ),
                                        ),
                                      ),
                                      const SizedBox(
                                        height: Spacing.md,
                                      ), // 底部间距从 sm 加大到 md
                                    ],

                                    const SizedBox(height: Spacing.xl),
                                    Row(
                                      children: [
                                        Expanded(
                                          child: Divider(
                                            color: AppTheme.border,
                                            height: 1,
                                          ),
                                        ),
                                        Padding(
                                          padding: const EdgeInsets.symmetric(
                                            horizontal: Spacing.sm,
                                          ),
                                          child: Icon(
                                            Icons.diamond_outlined,
                                            size: 14,
                                            color: AppTheme.textTertiary,
                                          ),
                                        ),
                                        Expanded(
                                          child: Divider(
                                            color: AppTheme.border,
                                            height: 1,
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: Spacing.sm),
                                    Row(
                                      mainAxisAlignment:
                                          MainAxisAlignment.center,
                                      children: [
                                        Text(
                                          _isRegister ? '已有账号？' : '还没有账号？',
                                          style: TextStyle(
                                            fontSize: FontSize.base,
                                            color: AppTheme.textSecondary,
                                          ),
                                        ),
                                        // A4: 切换登录/注册
                                        TextButton(
                                          key: const Key(
                                            'register_switch_action',
                                          ),
                                          onPressed: _submitting
                                              ? null
                                              : () {
                                                  setState(() {
                                                    _isRegister = !_isRegister;
                                                    _errorMessage = null;
                                                    _inviteValid = null;
                                                    _passwordVisible = false;
                                                    _confirmVisible = false;
                                                  });
                                                  context
                                                      .read<AppState>()
                                                      .clearAuthError();
                                                },
                                          style: TextButton.styleFrom(
                                            padding: const EdgeInsets.symmetric(
                                              horizontal: Spacing.sm,
                                            ),
                                            minimumSize: const Size(0, 0),
                                            tapTargetSize: MaterialTapTargetSize
                                                .shrinkWrap,
                                          ),
                                          child: Text(
                                            _isRegister ? '返回登录' : '立即注册',
                                            style: TextStyle(
                                              fontSize: FontSize.base,
                                              color: AppTheme.accentLight,
                                              decoration:
                                                  TextDecoration.underline,
                                              decorationColor:
                                                  AppTheme.accentLight,
                                              fontWeight: FontWeight.w600,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: Spacing.lg),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
