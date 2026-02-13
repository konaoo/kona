import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

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

  Future<void> _submit() async {
    final username = _usernameController.text.trim().toLowerCase();
    final password = _passwordController.text;
    final confirm = _confirmController.text;
    final invite = _inviteController.text.trim().toUpperCase();

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

    setState(() {
      _submitting = false;
      _errorMessage = _isRegister ? '注册失败，请检查邀请码或用户名' : '登录失败，请检查用户名或密码';
    });
  }

  Future<void> _tryBiometricLogin() async {
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

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();
    final showBiometric = !_isRegister && appState.biometricEnabled;

    return Scaffold(
      backgroundColor: AppTheme.bgPrimary,
      body: SafeArea(
        minimum: const EdgeInsets.only(top: 8),
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: Spacing.xl),
          child: Column(
            children: [
              const SizedBox(height: 72),
              Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  color: AppTheme.bgCard,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Icon(
                  Icons.lock_person,
                  size: 50,
                  color: AppTheme.accent,
                ),
              ),
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
                _isRegister ? '邀请码注册新账号' : '账号密码登录',
                style: TextStyle(
                  fontSize: FontSize.lg,
                  color: AppTheme.textSecondary,
                ),
              ),
              const SizedBox(height: Spacing.xl),

              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: _submitting
                          ? null
                          : () {
                              setState(() {
                                _isRegister = false;
                                _errorMessage = null;
                              });
                            },
                      style: OutlinedButton.styleFrom(
                        backgroundColor: _isRegister ? AppTheme.bgCard : AppTheme.accent,
                        side: BorderSide(color: AppTheme.bgElevated),
                      ),
                      child: Text(
                        '登录',
                        style: TextStyle(color: AppTheme.textPrimary),
                      ),
                    ),
                  ),
                  const SizedBox(width: Spacing.sm),
                  Expanded(
                    child: OutlinedButton(
                      onPressed: _submitting
                          ? null
                          : () {
                              setState(() {
                                _isRegister = true;
                                _errorMessage = null;
                              });
                            },
                      style: OutlinedButton.styleFrom(
                        backgroundColor: _isRegister ? AppTheme.accent : AppTheme.bgCard,
                        side: BorderSide(color: AppTheme.bgElevated),
                      ),
                      child: Text(
                        '注册',
                        style: TextStyle(color: AppTheme.textPrimary),
                      ),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: Spacing.lg),

              TextField(
                controller: _usernameController,
                keyboardType: TextInputType.text,
                style: TextStyle(color: AppTheme.textPrimary),
                decoration: const InputDecoration(
                  labelText: '用户名',
                  hintText: '例如 kona_user',
                ),
              ),

              const SizedBox(height: Spacing.md),

              TextField(
                controller: _passwordController,
                obscureText: true,
                style: TextStyle(color: AppTheme.textPrimary),
                decoration: const InputDecoration(
                  labelText: '密码',
                  hintText: '8-64位，字母+数字',
                ),
              ),

              if (_isRegister) ...[
                const SizedBox(height: Spacing.md),
                TextField(
                  controller: _confirmController,
                  obscureText: true,
                  style: TextStyle(color: AppTheme.textPrimary),
                  decoration: const InputDecoration(
                    labelText: '确认密码',
                    hintText: '请再次输入密码',
                  ),
                ),
                const SizedBox(height: Spacing.md),
                TextField(
                  controller: _inviteController,
                  style: TextStyle(color: AppTheme.textPrimary),
                  decoration: InputDecoration(
                    labelText: '邀请码',
                    hintText: '请输入邀请码',
                    suffixIcon: IconButton(
                      onPressed: _submitting ? null : _checkInviteCode,
                      icon: Icon(
                        _inviteValid == null
                            ? Icons.help_outline
                            : (_inviteValid! ? Icons.check_circle : Icons.error),
                        color: _inviteValid == null
                            ? AppTheme.textSecondary
                            : (_inviteValid! ? AppTheme.success : AppTheme.danger),
                      ),
                    ),
                  ),
                  onChanged: (_) => _checkInviteCode(),
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
                      : Text(_isRegister ? '注册并登录' : '登录', style: TextStyle(fontSize: FontSize.lg)),
                ),
              ),

              if (showBiometric) ...[
                const SizedBox(height: Spacing.md),
                SizedBox(
                  width: double.infinity,
                  height: 46,
                  child: OutlinedButton.icon(
                    onPressed: _submitting ? null : _tryBiometricLogin,
                    icon: const Icon(Icons.fingerprint),
                    label: const Text('使用生物识别登录'),
                  ),
                ),
              ],

              const SizedBox(height: 80),
              Text(
                '登录即表示同意服务条款和隐私政策',
                style: TextStyle(
                  fontSize: FontSize.sm,
                  color: AppTheme.textTertiary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
