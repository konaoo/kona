import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../providers/app_state.dart';

/// 登录页面
class LoginPage extends StatefulWidget {
  final VoidCallback onLoginSuccess;

  const LoginPage({super.key, required this.onLoginSuccess});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _emailController = TextEditingController();
  final _codeController = TextEditingController();
  
  bool _codeSent = false;
  bool _sendingCode = false;
  bool _loggingIn = false;
  int _countdown = 0;
  String? _errorMessage;

  @override
  void dispose() {
    _emailController.dispose();
    _codeController.dispose();
    super.dispose();
  }

  bool _isValidEmail(String email) {
    return RegExp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$').hasMatch(email);
  }

  Future<void> _sendCode() async {
    final email = _emailController.text.trim();
    
    if (email.isEmpty) {
      setState(() => _errorMessage = '请输入邮箱地址');
      return;
    }
    
    if (!_isValidEmail(email)) {
      setState(() => _errorMessage = '请输入有效的邮箱地址');
      return;
    }

    setState(() {
      _sendingCode = true;
      _errorMessage = null;
    });

    final ok = await context.read<AppState>().sendLoginCode(email);
    if (!ok) {
      setState(() {
        _sendingCode = false;
        _errorMessage = '发送失败，请稍后重试';
      });
      return;
    }

    setState(() {
      _sendingCode = false;
      _codeSent = true;
      _countdown = 60;
    });

    _startCountdown();
  }

  void _startCountdown() async {
    while (_countdown > 0) {
      await Future.delayed(const Duration(seconds: 1));
      if (mounted) {
        setState(() => _countdown--);
      }
    }
  }

  Future<void> _login() async {
    final code = _codeController.text.trim();
    final email = _emailController.text.trim();

    if (code.isEmpty || code.length != 6) {
      setState(() => _errorMessage = '请输入6位验证码');
      return;
    }

    setState(() {
      _loggingIn = true;
      _errorMessage = null;
    });

    try {
      // 生成用户ID（简化版：使用邮箱作为user_id）
      final userId = email;

      // 调用登录API
      final appState = context.read<AppState>();
      final success = await appState.login(userId, email, code);

      if (success) {
        setState(() => _loggingIn = false);
        widget.onLoginSuccess();
      } else {
        setState(() {
          _loggingIn = false;
          _errorMessage = '登录失败，请重试';
        });
      }
    } catch (e) {
      setState(() {
        _loggingIn = false;
        _errorMessage = '登录失败: $e';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPrimary,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: Spacing.xl),
          child: Column(
            children: [
              const SizedBox(height: 80),
              
              // Logo
              Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  color: AppTheme.bgCard,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Icon(
                  Icons.account_balance_wallet,
                  size: 50,
                  color: AppTheme.accent,
                ),
              ),
              
              const SizedBox(height: Spacing.lg),
              
              // 标题
              const Text(
                '咔咔记账',
                style: TextStyle(
                  fontSize: FontSize.title,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textPrimary,
                ),
              ),
              
              const SizedBox(height: Spacing.sm),
              
              const Text(
                '轻松管理你的投资',
                style: TextStyle(
                  fontSize: FontSize.lg,
                  color: AppTheme.textSecondary,
                ),
              ),
              
              const SizedBox(height: 50),
              
              // 邮箱 + 发送按钮
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                      style: const TextStyle(color: AppTheme.textPrimary),
                      decoration: const InputDecoration(
                        labelText: '邮箱地址',
                        hintText: 'example@email.com',
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  SizedBox(
                    width: 110,
                    height: 56,
                    child: ElevatedButton(
                      onPressed: _sendingCode || _countdown > 0 ? null : _sendCode,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: _countdown > 0 ? AppTheme.bgElevated : AppTheme.accent,
                      ),
                      child: _sendingCode
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: AppTheme.textPrimary,
                              ),
                            )
                          : Text(
                              _countdown > 0 ? '重新发送($_countdown)' : '发送验证码',
                              style: const TextStyle(fontSize: 13),
                            ),
                    ),
                  ),
                ],
              ),
              
              const SizedBox(height: Spacing.lg),
              
              // 验证码
              TextField(
                controller: _codeController,
                keyboardType: TextInputType.number,
                maxLength: 6,
                style: const TextStyle(color: AppTheme.textPrimary),
                decoration: const InputDecoration(
                  labelText: '验证码',
                  hintText: '请输入6位数字验证码',
                  counterText: '',
                ),
                onChanged: (_) {
                  if (_codeController.text.length == 6) {
                    setState(() {});
                  }
                },
              ),
              
              // 错误提示
              if (_errorMessage != null)
                Padding(
                  padding: const EdgeInsets.only(top: Spacing.sm),
                  child: Text(
                    _errorMessage!,
                    style: const TextStyle(color: AppTheme.danger),
                  ),
                ),
              
              const SizedBox(height: Spacing.xl),
              
              // 登录按钮
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: _codeController.text.length == 6 && !_loggingIn
                      ? _login
                      : null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _codeController.text.length == 6
                        ? AppTheme.accent
                        : AppTheme.bgElevated,
                  ),
                  child: _loggingIn
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: AppTheme.textPrimary,
                          ),
                        )
                      : const Text(
                          '登录',
                          style: TextStyle(fontSize: FontSize.lg),
                        ),
                ),
              ),
              
              const SizedBox(height: 100),
              
              // 底部说明
              const Text(
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
