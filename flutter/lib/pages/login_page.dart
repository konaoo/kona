import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../config/api_config.dart';
import '../config/theme.dart';
import '../providers/app_state.dart';

/// 登录/注册页面
class LoginPage extends StatefulWidget {
  final VoidCallback onLoginSuccess;

  const LoginPage({super.key, required this.onLoginSuccess});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  final _inviteController = TextEditingController();

  bool _isRegister = false;
  bool _submitting = false;
  String? _errorMessage;
  bool? _inviteValid;

  @override
  void initState() {
    super.initState();
    Future<void>.microtask(() {
      if (!mounted) return;
      context.read<AppState>().reloadBiometricPreference();
    });
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _confirmController.dispose();
    _inviteController.dispose();
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

  Future<void> _submit() async {
    FocusManager.instance.primaryFocus?.unfocus();
    final username = _usernameController.text.trim().toLowerCase();
    final password = _passwordController.text;
    final confirm = _confirmController.text;
    final invite = _inviteController.text.trim().toUpperCase();

    if (!_isRegister && (username.isEmpty || password.isEmpty)) {
      setState(() => _errorMessage = '请输入用户名和密码');
      return;
    }
    if (!_validUsername(username)) {
      setState(() => _errorMessage = '用户名格式不正确（4-24位，小写字母开头）');
      return;
    }
    if (!_validPassword(password)) {
      setState(() => _errorMessage = '密码需 8-64 位，且包含字母和数字');
      return;
    }
    if (_isRegister) {
      if (confirm != password) {
        setState(() => _errorMessage = '两次密码输入不一致');
        return;
      }
      if (invite.isEmpty) {
        setState(() => _errorMessage = '请输入邀请码');
        return;
      }
      if (_inviteValid == false) {
        setState(() => _errorMessage = '邀请码不可用');
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
      setState(() => _submitting = false);
      widget.onLoginSuccess();
      return;
    }

    final authError = context.read<AppState>().authErrorMessage;
    setState(() {
      _submitting = false;
      _errorMessage = authError?.trim().isNotEmpty == true
          ? authError!.trim()
          : (_isRegister ? '注册失败，请检查邀请码或用户名' : '登录失败，请检查用户名或密码');
    });
  }

  Future<void> _tryBiometricLogin() async {
    // 某些安卓机型在输入法弹出时会打断生物识别弹窗，先收起键盘再触发认证。
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
      setState(() => _submitting = false);
      widget.onLoginSuccess();
      return;
    }
    setState(() {
      _submitting = false;
      _errorMessage = '生物识别登录失败';
    });
  }

  Future<void> _openInviteAcquireLink() async {
    final uri = Uri.tryParse(ApiConfig.inviteAcquireUrl);
    if (uri == null || !uri.hasScheme) {
      if (!mounted) return;
      setState(() => _errorMessage = '邀请码获取链接配置无效');
      return;
    }
    final launched = await launchUrl(uri, mode: LaunchMode.externalApplication);
    if (!mounted || launched) return;
    setState(() => _errorMessage = '无法打开邀请码获取链接');
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
        body: Container(
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
                        _buildLogoHeader(isDark),
                        const SizedBox(height: Spacing.lg),
                        Text(
                          '咔咔记账',
                          style: TextStyle(
                            fontSize: FontSize.title,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                        const SizedBox(height: Spacing.sm),
                        Text(
                          _isRegister ? '创建账号' : '账号密码登录',
                          style: TextStyle(
                            fontSize: FontSize.lg,
                            color: AppTheme.textSecondary,
                          ),
                        ),
                        const SizedBox(height: Spacing.xl),

                        TextField(
                          controller: _usernameController,
                          keyboardType: TextInputType.text,
                          style: TextStyle(color: AppTheme.textPrimary),
                          decoration: const InputDecoration(labelText: '用户名'),
                          onChanged: (_) => _handleFieldChanged(),
                        ),

                        const SizedBox(height: Spacing.md),

                        TextField(
                          controller: _passwordController,
                          obscureText: true,
                          style: TextStyle(color: AppTheme.textPrimary),
                          decoration: const InputDecoration(labelText: '密码'),
                          onChanged: (_) => _handleFieldChanged(),
                        ),

                        if (_isRegister) ...[
                          const SizedBox(height: Spacing.md),
                          TextField(
                            controller: _confirmController,
                            obscureText: true,
                            style: TextStyle(color: AppTheme.textPrimary),
                            decoration: const InputDecoration(
                              labelText: '确认密码',
                            ),
                            onChanged: (_) => _handleFieldChanged(),
                          ),
                          const SizedBox(height: Spacing.md),
                          TextField(
                            controller: _inviteController,
                            style: TextStyle(color: AppTheme.textPrimary),
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
                                            ? Icons.check_circle
                                            : Icons.error),
                                  color: _inviteValid == null
                                      ? AppTheme.textSecondary
                                      : (_inviteValid!
                                            ? AppTheme.success
                                            : AppTheme.danger),
                                ),
                              ),
                            ),
                            onChanged: (_) {
                              _handleFieldChanged();
                              _checkInviteCode();
                            },
                          ),
                          const SizedBox(height: Spacing.sm),
                          Align(
                            alignment: Alignment.centerLeft,
                            child: TextButton(
                              onPressed: _submitting
                                  ? null
                                  : _openInviteAcquireLink,
                              style: TextButton.styleFrom(
                                minimumSize: const Size(0, 0),
                                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                padding: EdgeInsets.zero,
                                foregroundColor: AppTheme.accentLight,
                              ),
                              child: Text(
                                '没有邀请码，点我获取',
                                style: TextStyle(
                                  fontSize: FontSize.base,
                                  color: AppTheme.accentLight,
                                  decoration: TextDecoration.underline,
                                  decorationColor: AppTheme.accentLight,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ),
                        ],

                        if (_errorMessage != null)
                          Padding(
                            padding: const EdgeInsets.only(top: Spacing.sm),
                            child: Text(
                              _errorMessage!,
                              style: TextStyle(color: AppTheme.danger),
                            ),
                          ),

                        const SizedBox(height: Spacing.xl),

                        SizedBox(
                          key: const Key('login_primary_action'),
                          width: double.infinity,
                          height: 50,
                          child: ElevatedButton(
                            onPressed: _submitting ? null : _submit,
                            child: _submitting
                                ? SizedBox(
                                    width: 24,
                                    height: 24,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: AppTheme.textPrimary,
                                    ),
                                  )
                                : Text(
                                    _isRegister ? '注册并登录' : '登录',
                                    style: TextStyle(fontSize: FontSize.lg),
                                  ),
                          ),
                        ),

                        if (showBiometric) ...[
                          const SizedBox(height: Spacing.md),
                          Center(
                            child: Material(
                              color: Colors.transparent,
                              child: InkWell(
                                borderRadius: BorderRadius.circular(18),
                                onTap: _submitting ? null : _tryBiometricLogin,
                                child: Ink(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: Spacing.xl,
                                    vertical: Spacing.md,
                                  ),
                                  decoration: BoxDecoration(
                                    borderRadius: BorderRadius.circular(18),
                                    border: Border.all(
                                      color: AppTheme.accent.withValues(
                                        alpha: 0.45,
                                      ),
                                    ),
                                    gradient: LinearGradient(
                                      colors: [
                                        AppTheme.bgCard.withValues(
                                          alpha: isDark ? 0.95 : 0.98,
                                        ),
                                        AppTheme.bgElevated.withValues(
                                          alpha: isDark ? 0.88 : 0.94,
                                        ),
                                      ],
                                      begin: Alignment.topLeft,
                                      end: Alignment.bottomRight,
                                    ),
                                    boxShadow: [
                                      BoxShadow(
                                        color: AppTheme.accent.withValues(
                                          alpha: isDark ? 0.12 : 0.2,
                                        ),
                                        blurRadius: 16,
                                        spreadRadius: -2,
                                        offset: const Offset(0, 6),
                                      ),
                                    ],
                                  ),
                                  child: Column(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(
                                        Icons.fingerprint_rounded,
                                        size: 24,
                                        color: AppTheme.accentLight,
                                      ),
                                      const SizedBox(height: Spacing.xs),
                                      Text(
                                        '生物识别登录',
                                        style: TextStyle(
                                          fontSize: FontSize.base,
                                          color: AppTheme.textSecondary,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ],

                        const SizedBox(height: 48),
                        Row(
                          children: [
                            Expanded(
                              child: Divider(color: AppTheme.border, height: 1),
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
                              child: Divider(color: AppTheme.border, height: 1),
                            ),
                          ],
                        ),
                        const SizedBox(height: Spacing.sm),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(
                              _isRegister ? '已有账号？' : '还没有账号？',
                              style: TextStyle(
                                fontSize: FontSize.base,
                                color: AppTheme.textSecondary,
                              ),
                            ),
                            TextButton(
                              key: const Key('register_switch_action'),
                              onPressed: _submitting
                                  ? null
                                  : () {
                                      setState(() {
                                        _isRegister = !_isRegister;
                                        _errorMessage = null;
                                        _inviteValid = null;
                                      });
                                      context.read<AppState>().clearAuthError();
                                    },
                              style: TextButton.styleFrom(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: Spacing.sm,
                                ),
                                minimumSize: const Size(0, 0),
                                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                              ),
                              child: Text(
                                _isRegister ? '返回登录' : '立即注册',
                                style: TextStyle(
                                  fontSize: FontSize.base,
                                  color: AppTheme.accentLight,
                                  decoration: TextDecoration.underline,
                                  decorationColor: AppTheme.accentLight,
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
                );
              },
            ),
          ),
        ),
      ),
    );
  }
}
