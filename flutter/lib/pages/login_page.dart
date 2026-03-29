import 'dart:async';
import 'dart:io';

import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import 'package:gal/gal.dart';
import 'package:provider/provider.dart';

import '../services/api_service.dart';
import '../providers/app_state.dart';

// ───────────────────────────────────────────
// 登录页专用色板（仅本文件使用）
// ───────────────────────────────────────────
class _C {
  final bool isLight;
  final Color bg;
  final Color card;
  final Color card2;
  final Color border;
  final Color borderIdle;
  final Color borderFocus;
  final Color borderErr;
  final Color text;
  final Color textSub;
  final Color textDim;
  final Color textSoft;
  final Color up;
  final Color down;
  final Color blue;
  final Color blue2;
  final Color gold;
  final Color tabShellBg;
  final Color tabShellBorder;
  final Color tabActiveBg;
  final Color topHighlight;
  final Color glowBlue;
  final Color glowRed;
  final Color cardShadow;
  final Color dialogBackdrop;

  const _C({
    required this.isLight,
    required this.bg,
    required this.card,
    required this.card2,
    required this.border,
    required this.borderIdle,
    required this.borderFocus,
    required this.borderErr,
    required this.text,
    required this.textSub,
    required this.textDim,
    required this.textSoft,
    required this.up,
    required this.down,
    required this.blue,
    required this.blue2,
    required this.gold,
    required this.tabShellBg,
    required this.tabShellBorder,
    required this.tabActiveBg,
    required this.topHighlight,
    required this.glowBlue,
    required this.glowRed,
    required this.cardShadow,
    required this.dialogBackdrop,
  });

  static const dark = _C(
    isLight: false,
    bg: Color(0xFF0C0D11),
    card: Color(0xFF13151C),
    card2: Color(0xFF181B23),
    border: Color(0x0FFFFFFF),
    borderIdle: Color(0x1FFFFFFF),
    borderFocus: Color(0x805B8DEF),
    borderErr: Color(0x8DF05A55),
    text: Color(0xFFE8EAF0),
    textSub: Color(0xFF8B909F),
    textDim: Color(0xFF4E5464),
    textSoft: Color(0x66FFFFFF),
    up: Color(0xFFF05A55),
    down: Color(0xFF2ECC8A),
    blue: Color(0xFF5B8DEF),
    blue2: Color(0xFF4A7BE0),
    gold: Color(0xFFD4AF64),
    tabShellBg: Color(0x59000000),
    tabShellBorder: Color(0x14FFFFFF),
    tabActiveBg: Color(0x1AFFFFFF),
    topHighlight: Color(0x14FFFFFF),
    glowBlue: Color(0x125B8DEF),
    glowRed: Color(0x0DF05A55),
    cardShadow: Color(0x66000000),
    dialogBackdrop: Color(0xB3000000),
  );

  static const light = _C(
    isLight: true,
    bg: Color(0xFFF2F5FB),
    card: Color(0xFFFFFFFF),
    card2: Color(0xFFF6F8FD),
    border: Color(0x1F22304A),
    borderIdle: Color(0x1A33415E),
    borderFocus: Color(0x804B86F0),
    borderErr: Color(0x80E45656),
    text: Color(0xFF1D2738),
    textSub: Color(0xFF5D6B83),
    textDim: Color(0xFF94A0B5),
    textSoft: Color(0x99586784),
    up: Color(0xFFE45656),
    down: Color(0xFF16A34A),
    blue: Color(0xFF4B86F0),
    blue2: Color(0xFF6A9CF7),
    gold: Color(0xFFB8942D),
    tabShellBg: Color(0xFFF0F4FC),
    tabShellBorder: Color(0x1F22304A),
    tabActiveBg: Color(0xFFDEE8FB),
    topHighlight: Color(0x3DFFFFFF),
    glowBlue: Color(0x184B86F0),
    glowRed: Color(0x12E45656),
    cardShadow: Color(0x1A22304A),
    dialogBackdrop: Color(0x66161B28),
  );
}

// ───────────────────────────────────────────
// 缓存 TextStyle（避免 GoogleFonts 每次 build 重复解析）
// ───────────────────────────────────────────
class _S {
  late final TextStyle brandName;
  late final TextStyle brandSub;
  late final TextStyle tabActive;
  late final TextStyle tabInactive;
  late final TextStyle fieldLabel;
  late final TextStyle fieldError;
  late final TextStyle rememberTxt;
  late final TextStyle btn;
  late final TextStyle strengthLabel;
  late final TextStyle badgeTxt;
  late final TextStyle legalBase;
  late final TextStyle inputText;
  late final TextStyle inputHint;
  late final TextStyle snackTxt;
  late final TextStyle dialogDesc;
  late final TextStyle saveBtn;
  late final TextStyle monoInput;
  late final TextStyle monoUpper;

  _S(_C c) {
    brandName = GoogleFonts.dmSans(
      fontSize: 20,
      fontWeight: FontWeight.w700,
      color: c.text,
      letterSpacing: -0.3,
    );
    brandSub = GoogleFonts.dmSans(
      fontSize: 15,
      color: c.isLight ? c.textDim : c.textSub,
      letterSpacing: 1.1,
    );
    tabActive = GoogleFonts.dmSans(
      fontSize: 13,
      fontWeight: FontWeight.w600,
      color: c.text,
    );
    tabInactive = GoogleFonts.dmSans(
      fontSize: 13,
      fontWeight: FontWeight.w500,
      color: c.textSoft,
    );
    fieldLabel = GoogleFonts.dmSans(
      fontSize: 11,
      fontWeight: FontWeight.w500,
      color: c.textSub,
      letterSpacing: 0.3,
    );
    fieldError = GoogleFonts.dmSans(fontSize: 10, color: c.up);
    rememberTxt = GoogleFonts.dmSans(
      fontSize: 12,
      color: c.textDim,
    );
    btn = GoogleFonts.dmSans(
      fontSize: 15,
      fontWeight: FontWeight.w600,
      color: Colors.white,
    );
    strengthLabel = GoogleFonts.dmSans(
      fontSize: 10,
      color: c.textDim,
    );
    badgeTxt = GoogleFonts.dmSans(
      fontSize: 11,
      color: c.gold,
      height: 1.5,
    );
    legalBase = GoogleFonts.dmSans(
      fontSize: 11,
      color: c.textDim,
      height: 1.6,
    );
    inputText = GoogleFonts.dmSans(fontSize: 14, color: c.text);
    inputHint = GoogleFonts.dmSans(fontSize: 13, color: c.textDim);
    snackTxt = GoogleFonts.dmSans(color: Colors.white);
    dialogDesc = GoogleFonts.dmSans(
      fontSize: 12,
      color: c.textDim,
      height: 1.6,
    );
    saveBtn = GoogleFonts.dmSans(
      fontSize: 13,
      fontWeight: FontWeight.w500,
      color: c.textSub,
    );
    monoInput = GoogleFonts.jetBrainsMono(
      fontSize: 14,
      color: c.text,
    );
    monoUpper = GoogleFonts.jetBrainsMono(
      fontSize: 15,
      color: c.text,
      letterSpacing: 1.5,
    );
  }
}

/// 登录/注册页面
class LoginPage extends StatefulWidget {
  final VoidCallback onLoginSuccess;

  const LoginPage({super.key, required this.onLoginSuccess});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> with TickerProviderStateMixin {
  // ── Controllers ──
  final _loginAccCtrl = TextEditingController();
  final _loginPwCtrl = TextEditingController();
  final _regInvCtrl = TextEditingController();
  final _regAccCtrl = TextEditingController();
  final _regPwCtrl = TextEditingController();
  final _regPw2Ctrl = TextEditingController();

  // ── Focus Nodes ──
  final _loginAccFocus = FocusNode();
  final _loginPwFocus = FocusNode();
  final _regInvFocus = FocusNode();
  final _regAccFocus = FocusNode();
  final _regPwFocus = FocusNode();
  final _regPw2Focus = FocusNode();

  // ── State ──
  String _currentTab = 'login'; // 'login' | 'register'
  bool _loginPwObscure = true;
  bool _regPwObscure = true;
  bool _regPw2Obscure = true;
  bool _rememberEnabled = false;
  bool _rememberLoaded = false;
  int _pwScore = 0;

  // 按钮状态: idle / loading / success
  String _loginBtnState = 'idle';
  String _regBtnState = 'idle';

  // 字段级错误
  final Map<String, String?> _errors = {};

  // 邀请码防抖
  Timer? _inviteDebounce;
  bool? _inviteValid;

  // ── Animations ──
  late final AnimationController _entranceCtrl;
  late final Animation<double> _cardFade;
  late final Animation<Offset> _cardSlide;
  late final Animation<double> _footerFade;
  late final Animation<Offset> _footerSlide;

  _C get _colors => Theme.of(context).brightness == Brightness.light ? _C.light : _C.dark;
  _S get _styles => _S(_colors);

  @override
  void initState() {
    super.initState();

    // 入场动画
    _entranceCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );

    _cardFade = CurvedAnimation(
      parent: _entranceCtrl,
      curve: const Interval(0.13, 0.83, curve: Curves.ease),
    );
    _cardSlide = Tween<Offset>(begin: const Offset(0, 0.06), end: Offset.zero)
        .animate(
          CurvedAnimation(
            parent: _entranceCtrl,
            curve: const Interval(0.13, 0.83, curve: Curves.ease),
          ),
        );

    _footerFade = CurvedAnimation(
      parent: _entranceCtrl,
      curve: const Interval(0.33, 1.0, curve: Curves.ease),
    );
    _footerSlide = Tween<Offset>(begin: const Offset(0, 0.06), end: Offset.zero)
        .animate(
          CurvedAnimation(
            parent: _entranceCtrl,
            curve: const Interval(0.33, 1.0, curve: Curves.ease),
          ),
        );

    _entranceCtrl.forward();

    // 加载保存的用户名
    Future<void>.microtask(() async {
      if (!mounted) return;
      context.read<AppState>().reloadBiometricPreference();
      await _loadRememberedUsername();
    });
  }

  Future<void> _loadRememberedUsername() async {
    if (!mounted) return;
    final appState = context.read<AppState>();
    final savedUsername = appState.username ?? '';
    if (savedUsername.isNotEmpty) {
      _loginAccCtrl.text = savedUsername;
      setState(() {
        _rememberEnabled = true;
        _rememberLoaded = true;
      });
    } else {
      setState(() => _rememberLoaded = true);
    }
  }

  @override
  void dispose() {
    _loginAccCtrl.dispose();
    _loginPwCtrl.dispose();
    _regInvCtrl.dispose();
    _regAccCtrl.dispose();
    _regPwCtrl.dispose();
    _regPw2Ctrl.dispose();
    _loginAccFocus.dispose();
    _loginPwFocus.dispose();
    _regInvFocus.dispose();
    _regAccFocus.dispose();
    _regPwFocus.dispose();
    _regPw2Focus.dispose();
    _inviteDebounce?.cancel();
    _entranceCtrl.dispose();
    super.dispose();
  }

  // ───────────────────────────────────────────
  // 业务逻辑（保留原有实现）
  // ───────────────────────────────────────────

  bool _validUsername(String username) {
    return RegExp(r'^[a-z][a-z0-9_]{3,23}$').hasMatch(username);
  }

  bool _validPassword(String password) {
    if (password.length < 8 || password.length > 64) return false;
    final hasLetter = RegExp(r'[A-Za-z]').hasMatch(password);
    final hasDigit = RegExp(r'\d').hasMatch(password);
    return hasLetter && hasDigit;
  }

  void _clearErrors() => setState(() => _errors.clear());

  void _setFieldError(String field, String msg) {
    setState(() => _errors[field] = msg);
  }

  void _handleFieldChanged() {
    context.read<AppState>().clearAuthError();
    if (_errors.isNotEmpty) _clearErrors();
  }

  // 邀请码防抖
  void _checkInviteCodeDebounced() {
    _inviteDebounce?.cancel();
    _inviteDebounce = Timer(const Duration(milliseconds: 500), () {
      if (mounted) _checkInviteCode();
    });
  }

  Future<void> _checkInviteCode() async {
    final code = _regInvCtrl.text.trim().toUpperCase();
    if (code.length < 10) {
      setState(() => _inviteValid = null);
      return;
    }
    final ok = await context.read<AppState>().validateInviteCode(code);
    if (!mounted) return;
    setState(() => _inviteValid = ok);
  }

  int _calcPwScore(String v) {
    if (v.isEmpty) return 0;
    int s = 0;
    if (v.length >= 8) s++;
    if (RegExp(r'[A-Za-z]').hasMatch(v) && RegExp(r'[0-9]').hasMatch(v)) s++;
    if (RegExp(r'[^A-Za-z0-9]').hasMatch(v) || v.length >= 12) s++;
    return s;
  }

  Future<void> _handleLogin() async {
    if (_loginBtnState == 'loading') return;
    FocusManager.instance.primaryFocus?.unfocus();
    _clearErrors();

    final acc = _loginAccCtrl.text.trim().toLowerCase();
    final pw = _loginPwCtrl.text;
    bool ok = true;

    if (acc.isEmpty) {
      _setFieldError('loginAcc', '请输入用户名');
      ok = false;
    } else if (!_validUsername(acc)) {
      _setFieldError('loginAcc', '用户名格式不正确（4-24位，小写字母开头）');
      ok = false;
    }
    if (pw.isEmpty) {
      _setFieldError('loginPw', '请输入密码');
      ok = false;
    } else if (!_validPassword(pw)) {
      _setFieldError('loginPw', '密码需 8-64 位，且包含字母和数字');
      ok = false;
    }
    if (!ok) return;

    if (_rememberEnabled && acc.isNotEmpty) {
      // saved via AppState on success
    }

    setState(() => _loginBtnState = 'loading');

    final success = await context.read<AppState>().login(
      username: acc,
      password: pw,
    );

    if (!mounted) return;

    if (success) {
      setState(() => _loginBtnState = 'success');
      await Future<void>.delayed(const Duration(milliseconds: 800));
      if (!mounted) return;
      widget.onLoginSuccess();
      return;
    }

    final authError = context.read<AppState>().authErrorMessage;
    final errMsg = authError?.trim().isNotEmpty == true
        ? authError!.trim()
        : '用户名/密码错误，请重试';
    setState(() => _loginBtnState = 'idle');
    _setFieldError('loginPw', errMsg);
  }

  Future<void> _handleRegister() async {
    FocusManager.instance.primaryFocus?.unfocus();
    _clearErrors();

    final inv = _regInvCtrl.text.trim().toUpperCase();
    final acc = _regAccCtrl.text.trim().toLowerCase();
    final pw = _regPwCtrl.text;
    final pw2 = _regPw2Ctrl.text;
    bool ok = true;

    if (inv.isEmpty || inv.length < 4) {
      _setFieldError('regInv', '邀请码格式不正确');
      ok = false;
    }
    if (acc.isEmpty) {
      _setFieldError('regAcc', '请输入用户名');
      ok = false;
    } else if (!_validUsername(acc)) {
      _setFieldError('regAcc', '用户名格式不正确（4-24位，小写字母开头）');
      ok = false;
    }
    if (pw.isEmpty || pw.length < 8) {
      _setFieldError('regPw', '密码至少 8 位');
      ok = false;
    } else if (!_validPassword(pw)) {
      _setFieldError('regPw', '密码需包含字母和数字');
      ok = false;
    } else if (pw != pw2) {
      _setFieldError('regPw2', '两次密码不一致');
      ok = false;
    }
    if (!ok) return;

    if (_inviteValid == false) {
      _setFieldError('regInv', '邀请码不可用');
      return;
    }

    setState(() => _regBtnState = 'loading');

    final success = await context.read<AppState>().register(
      username: acc,
      password: pw,
      inviteCode: inv,
    );

    if (!mounted) return;

    if (success) {
      setState(() => _regBtnState = 'success');
      await Future<void>.delayed(const Duration(milliseconds: 1200));
      if (!mounted) return;
      widget.onLoginSuccess();
      return;
    }

    final authError = context.read<AppState>().authErrorMessage;
    final errMsg = authError?.trim().isNotEmpty == true
        ? authError!.trim()
        : '注册失败，请检查邀请码或用户名';
    setState(() => _regBtnState = 'idle');
    _setFieldError('regAcc', errMsg);
  }

  void _switchTab(String tab) {
    if (tab == _currentTab) return;
    setState(() {
      _currentTab = tab;
      _errors.clear();
      _loginBtnState = 'idle';
      _regBtnState = 'idle';
      _pwScore = 0;
      _inviteValid = null;
    });
    context.read<AppState>().clearAuthError();
  }

  void _showInviteCodeDialog() {
    final p = _colors;
    showDialog(
      context: context,
      barrierDismissible: true,
      barrierColor: p.dialogBackdrop,
      builder: (ctx) => _InviteCodeDialog(),
    );
  }

  // ───────────────────────────────────────────
  // 构建 UI ──────────────────────────────────
  // ───────────────────────────────────────────

  Widget _buildTabSwitcher() {
    final p = _colors;
    return Center(
      child: Container(
        width: 240,
        decoration: BoxDecoration(
          border: Border(
            bottom: BorderSide(color: p.border.withValues(alpha: 0.85)),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildTab(
              '登录',
              isActive: _currentTab == 'login',
              onTap: () => _switchTab('login'),
            ),
            _buildTab(
              '注册',
              isActive: _currentTab == 'register',
              onTap: () => _switchTab('register'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTab(
    String label, {
    required bool isActive,
    required VoidCallback onTap,
  }) {
    final p = _colors;
    final s = _styles;
    return SizedBox(
      width: 120,
      child: GestureDetector(
        onTap: onTap,
        behavior: HitTestBehavior.opaque,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.only(bottom: 12),
          decoration: BoxDecoration(
            border: Border(
              bottom: BorderSide(
                color: isActive ? p.blue : Colors.transparent,
                width: 2,
              ),
            ),
          ),
          child: Text(
            label,
            textAlign: TextAlign.center,
            style: isActive ? s.tabActive : s.tabInactive,
          ),
        ),
      ),
    );
  }

  Widget _buildFieldContainer({
    required String label,
    required Widget input,
    String? errorKey,
    bool showDot = false,
  }) {
    final p = _colors;
    final s = _styles;
    final err = errorKey != null ? _errors[errorKey] : null;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            if (showDot) ...[
              Container(
                width: 4,
                height: 4,
                decoration: BoxDecoration(
                  color: p.blue,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 4),
            ],
            Text(label, style: s.fieldLabel),
          ],
        ),
        const SizedBox(height: 6),
        input,
        if (err != null)
          Padding(
            padding: const EdgeInsets.only(top: 4, left: 2),
            child: Text(err, style: s.fieldError),
          ),
      ],
    );
  }

  Widget _buildInputWrap({
    required TextEditingController controller,
    required FocusNode focusNode,
    required IconData icon,
    String? placeholder,
    bool obscure = false,
    VoidCallback? onToggleObscure,
    bool isObscured = true,
    TextInputAction textInputAction = TextInputAction.next,
    VoidCallback? onSubmitted,
    ValueChanged<String>? onChanged,
    bool isMono = false,
    bool forceUppercase = false,
    int? maxLength,
    String? errorKey,
  }) {
    final hasError = errorKey != null && _errors[errorKey] != null;

    return _InputWrap(
      controller: controller,
      focusNode: focusNode,
      icon: icon,
      placeholder: placeholder,
      obscure: obscure,
      onToggleObscure: onToggleObscure,
      isObscured: isObscured,
      textInputAction: textInputAction,
      onSubmitted: onSubmitted,
      onChanged: (v) {
        _handleFieldChanged();
        onChanged?.call(v);
      },
      isMono: isMono,
      forceUppercase: forceUppercase,
      maxLength: maxLength,
      hasError: hasError,
    );
  }

  Widget _buildRememberForgotRow() {
    final p = _colors;
    final s = _styles;
    if (!_rememberLoaded) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // 记住用户名
          GestureDetector(
            onTap: () => setState(() => _rememberEnabled = !_rememberEnabled),
            child: Row(
              children: [
                AnimatedContainer(
                  duration: const Duration(milliseconds: 150),
                  width: 16,
                  height: 16,
                  decoration: BoxDecoration(
                    color: _rememberEnabled ? p.blue : p.card2,
                    border: Border.all(
                      color: _rememberEnabled ? p.blue : p.border,
                    ),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: _rememberEnabled
                      ? const Icon(Icons.check, size: 10, color: Colors.white)
                      : null,
                ),
                const SizedBox(width: 7),
                Text('记住用户名', style: s.rememberTxt),
              ],
            ),
          ),
          // 忘记密码
          GestureDetector(
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('功能开发中', style: s.snackTxt),
                  duration: const Duration(seconds: 2),
                  backgroundColor: p.card2,
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
            child: Text('忘记密码？', style: s.rememberTxt),
          ),
        ],
      ),
    );
  }

  Widget _buildGradientButton({
    required String label,
    required String successLabel,
    required String btnState,
    required VoidCallback onPressed,
  }) {
    final p = _colors;
    final s = _styles;
    final isLoading = btnState == 'loading';
    final isSuccess = btnState == 'success';

    return GestureDetector(
      onTap: isLoading || isSuccess ? null : onPressed,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 13),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: isSuccess
                ? [const Color(0xFF2ECC8A), const Color(0xFF25B377)]
                : [p.blue, p.blue2],
          ),
          borderRadius: BorderRadius.circular(10),
          boxShadow: [
            BoxShadow(
              color: (isSuccess ? const Color(0xFF2ECC8A) : p.blue).withValues(
                alpha: 0.35,
              ),
              blurRadius: 16,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Center(
          child: isLoading
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(
                    color: Colors.white,
                    strokeWidth: 2,
                  ),
                )
              : Text(isSuccess ? successLabel : label, style: s.btn),
        ),
      ),
    );
  }

  Widget _buildPasswordStrength() {
    final p = _colors;
    final s = _styles;
    if (_pwScore == 0) return const SizedBox.shrink();

    Color barColor;
    String label;
    if (_pwScore >= 3) {
      barColor = p.down;
      label = '强度：强';
    } else if (_pwScore >= 2) {
      barColor = const Color(0xFFE09030);
      label = '强度：中';
    } else {
      barColor = p.up;
      label = '强度：弱';
    }

    return Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: List.generate(3, (i) {
              return Expanded(
                child: Container(
                  height: 3,
                  margin: EdgeInsets.only(right: i < 2 ? 3 : 0),
                  decoration: BoxDecoration(
                    color: i < _pwScore ? barColor : p.border,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              );
            }),
          ),
          const SizedBox(height: 3),
          Text(label, style: s.strengthLabel),
        ],
      ),
    );
  }

  Widget _buildInviteBadge() {
    final p = _colors;
    final s = _styles;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 10),
      decoration: BoxDecoration(
        color: p.gold.withValues(alpha: p.isLight ? 0.10 : 0.07),
        border: Border.all(color: p.gold.withValues(alpha: p.isLight ? 0.28 : 0.2)),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          const Text('🔑', style: TextStyle(fontSize: 16)),
          const SizedBox(width: 9),
          Expanded(
            child: RichText(
              text: TextSpan(
                style: s.badgeTxt,
                children: [
                  const TextSpan(text: '当前注册仅限受邀用户，'),
                  TextSpan(
                    text: '获取邀请码',
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      color: p.isLight ? p.text : Colors.white,
                      decoration: TextDecoration.underline,
                      decorationColor: (p.isLight ? p.text : Colors.white).withValues(alpha: 0.35),
                    ),
                    recognizer: TapGestureRecognizer()
                      ..onTap = _showInviteCodeDialog,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoginPanel() {
    return Column(
      children: [
        // 账号
        _buildFieldContainer(
          label: '账号',
          errorKey: 'loginAcc',
          input: _buildInputWrap(
            controller: _loginAccCtrl,
            focusNode: _loginAccFocus,
            icon: Icons.person_outline,
            placeholder: '请输入用户名',
            textInputAction: TextInputAction.next,
            onSubmitted: () => _loginPwFocus.requestFocus(),
            errorKey: 'loginAcc',
          ),
        ),
        const SizedBox(height: 14),
        // 密码
        _buildFieldContainer(
          label: '密码',
          errorKey: 'loginPw',
          input: _buildInputWrap(
            controller: _loginPwCtrl,
            focusNode: _loginPwFocus,
            icon: Icons.lock_outline,
            placeholder: '请输入密码',
            obscure: true,
            isObscured: _loginPwObscure,
            onToggleObscure: () =>
                setState(() => _loginPwObscure = !_loginPwObscure),
            textInputAction: TextInputAction.done,
            onSubmitted: () => _handleLogin(),
            isMono: true,
            errorKey: 'loginPw',
          ),
        ),
        const SizedBox(height: 12),
        // 记住/忘记
        _buildRememberForgotRow(),
        const SizedBox(height: 8),
        // 登录按钮
        KeyedSubtree(
          key: const Key('login_primary_action'),
          child: _buildGradientButton(
            label: '登录',
            successLabel: '✓ 登录成功',
            btnState: _loginBtnState,
            onPressed: _handleLogin,
          ),
        ),
      ],
    );
  }

  Widget _buildRegisterPanel() {
    return Column(
      children: [
        // 邀请码提示条
        _buildInviteBadge(),
        const SizedBox(height: 14),
        // 邀请码
        _buildFieldContainer(
          label: '邀请码',
          showDot: true,
          errorKey: 'regInv',
          input: _buildInputWrap(
            controller: _regInvCtrl,
            focusNode: _regInvFocus,
            icon: Icons.star_outline,
            placeholder: '输入邀请码',
            textInputAction: TextInputAction.next,
            onSubmitted: () => _regAccFocus.requestFocus(),
            isMono: true,
            forceUppercase: true,
            maxLength: 10,
            errorKey: 'regInv',
            onChanged: (_) => _checkInviteCodeDebounced(),
          ),
        ),
        const SizedBox(height: 14),
        // 用户名
        _buildFieldContainer(
          label: '用户名 / 账号',
          showDot: true,
          errorKey: 'regAcc',
          input: _buildInputWrap(
            controller: _regAccCtrl,
            focusNode: _regAccFocus,
            icon: Icons.person_outline,
            placeholder: '请输入用户名',
            textInputAction: TextInputAction.next,
            onSubmitted: () => _regPwFocus.requestFocus(),
            errorKey: 'regAcc',
          ),
        ),
        const SizedBox(height: 14),
        // 设置密码
        _buildFieldContainer(
          label: '设置密码',
          showDot: true,
          errorKey: 'regPw',
          input: Column(
            children: [
              _buildInputWrap(
                controller: _regPwCtrl,
                focusNode: _regPwFocus,
                icon: Icons.lock_outline,
                placeholder: '至少 8 位，含字母和数字',
                obscure: true,
                isObscured: _regPwObscure,
                onToggleObscure: () =>
                    setState(() => _regPwObscure = !_regPwObscure),
                textInputAction: TextInputAction.next,
                onSubmitted: () => _regPw2Focus.requestFocus(),
                isMono: true,
                errorKey: 'regPw',
                onChanged: (v) {
                  setState(() => _pwScore = _calcPwScore(v));
                },
              ),
              _buildPasswordStrength(),
            ],
          ),
        ),
        const SizedBox(height: 14),
        // 确认密码
        _buildFieldContainer(
          label: '确认密码',
          showDot: true,
          errorKey: 'regPw2',
          input: _buildInputWrap(
            controller: _regPw2Ctrl,
            focusNode: _regPw2Focus,
            icon: Icons.lock_outline,
            placeholder: '再次输入密码',
            obscure: true,
            isObscured: _regPw2Obscure,
            onToggleObscure: () =>
                setState(() => _regPw2Obscure = !_regPw2Obscure),
            textInputAction: TextInputAction.done,
            onSubmitted: () => _handleRegister(),
            isMono: true,
            errorKey: 'regPw2',
          ),
        ),
        const SizedBox(height: 14),
        // 立即注册按钮
        _buildGradientButton(
          label: '立即注册',
          successLabel: '✓ 注册成功',
          btnState: _regBtnState,
          onPressed: _handleRegister,
        ),
      ],
    );
  }

  Widget _buildLegalFooter() {
    final p = _colors;
    final s = _styles;
    return Padding(
      padding: const EdgeInsets.only(top: 20, bottom: 8),
      child: RichText(
        textAlign: TextAlign.center,
        text: TextSpan(
          style: s.legalBase,
          children: [
            const TextSpan(text: '登录或注册即代表您同意 '),
            TextSpan(
              text: '用户协议',
              style: TextStyle(
                color: p.textSub,
                decoration: TextDecoration.underline,
                decorationColor: p.textSub.withValues(alpha: 0.25),
              ),
              recognizer: TapGestureRecognizer()..onTap = () {},
            ),
            const TextSpan(text: ' 和 '),
            TextSpan(
              text: '隐私政策',
              style: TextStyle(
                color: p.textSub,
                decoration: TextDecoration.underline,
                decorationColor: p.textSub.withValues(alpha: 0.25),
              ),
              recognizer: TapGestureRecognizer()..onTap = () {},
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final p = _colors;
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: p.isLight ? Brightness.dark : Brightness.light,
        statusBarBrightness: p.isLight ? Brightness.light : Brightness.dark,
        systemNavigationBarColor: Colors.transparent,
        systemNavigationBarIconBrightness: p.isLight ? Brightness.dark : Brightness.light,
        systemNavigationBarDividerColor: Colors.transparent,
      ),
      child: Scaffold(
        backgroundColor: p.bg,
        body: Stack(
          children: [
            Positioned.fill(
              child: IgnorePointer(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: p.isLight
                          ? const [
                              Color(0xFFF7FAFF),
                              Color(0xFFF0F4FC),
                              Color(0xFFE9EEF8),
                            ]
                          : const [
                              Color(0xFF0B0D13),
                              Color(0xFF10141D),
                              Color(0xFF0C1018),
                            ],
                      stops: const [0.0, 0.52, 1.0],
                    ),
                  ),
                ),
              ),
            ),
            Positioned(
              top: -180,
              right: -120,
              child: IgnorePointer(
                child: Container(
                  width: 420,
                  height: 420,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(
                      colors: p.isLight
                          ? const [
                              Color(0x1EFFF5D9),
                              Color(0x0AFFF5D9),
                              Colors.transparent,
                            ]
                          : const [
                              Color(0x18F6D997),
                              Color(0x08F6D997),
                              Colors.transparent,
                            ],
                      stops: const [0.0, 0.42, 1.0],
                    ),
                  ),
                ),
              ),
            ),
            // 背景光晕 - 左上蓝
            Positioned(
              top: -120,
              left: MediaQuery.of(context).size.width / 2 - 250,
              child: IgnorePointer(
                child: Container(
                  width: 500,
                  height: 500,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(
                      colors: [
                        p.glowBlue,
                        Colors.transparent,
                      ],
                      stops: const [0.0, 0.65],
                    ),
                  ),
                ),
              ),
            ),
            // 背景光晕 - 右下红
            Positioned(
              bottom: -80,
              right: -60,
              child: IgnorePointer(
                child: Container(
                  width: 320,
                  height: 320,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(
                      colors: [
                        p.glowRed,
                        Colors.transparent,
                      ],
                      stops: const [0.0, 0.65],
                    ),
                  ),
                ),
              ),
            ),
            Positioned(
              top: 0,
              left: 0,
              right: 0,
              child: IgnorePointer(
                child: SizedBox(
                  height: p.isLight ? 150 : 96,
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: p.isLight
                            ? const [
                                Color(0x52F7FAFF),
                                Color(0x30EEF4FF),
                                Color(0x18DCE7FF),
                                Color(0x00DCE7FF),
                              ]
                            : const [
                                Color(0x104B86F0),
                                Color(0x063B5D96),
                                Color(0x02283D61),
                                Color(0x00283D61),
                              ],
                        stops: const [0.0, 0.34, 0.72, 1.0],
                      ),
                    ),
                  ),
                ),
              ),
            ),
            // 主体内容
            SafeArea(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  const brandAreaTop = 56.0;
                  const brandAreaReservedHeight = 84.0;
                  final contentLeft =
                      ((constraints.maxWidth - 380) / 2).clamp(28.0, double.infinity).toDouble();

                  return Stack(
                    children: [
                      Positioned(
                        top: brandAreaTop,
                        left: contentLeft,
                        child: FadeTransition(
                          opacity: _cardFade,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                '咔咔记账',
                                style: _styles.brandName,
                              ),
                              const SizedBox(height: 6),
                              Text(
                                '很高兴见到你。',
                                style: _styles.brandSub,
                              ),
                            ],
                          ),
                        ),
                      ),
                      SingleChildScrollView(
                        child: ConstrainedBox(
                          constraints: BoxConstraints(minHeight: constraints.maxHeight),
                          child: IntrinsicHeight(
                            child: Center(
                              child: ConstrainedBox(
                                constraints: const BoxConstraints(maxWidth: 380),
                                child: Padding(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 20,
                                    vertical: 24,
                                  ),
                                  child: Column(
                                    children: [
                                      Expanded(
                                        child: Align(
                                          alignment: Alignment.center,
                                          child: SlideTransition(
                                            position: _cardSlide,
                                            child: FadeTransition(
                                              opacity: _cardFade,
                                              child: Padding(
                                                padding: const EdgeInsets.fromLTRB(
                                                  8,
                                                  brandAreaReservedHeight,
                                                  8,
                                                  0,
                                                ),
                                                child: Column(
                                                  mainAxisSize: MainAxisSize.min,
                                                  children: [
                                                    _buildTabSwitcher(),
                                                    const SizedBox(height: 24),
                                                    AnimatedSwitcher(
                                                      duration: const Duration(
                                                        milliseconds: 220,
                                                      ),
                                                      transitionBuilder: (child, anim) {
                                                        return FadeTransition(
                                                          opacity: anim,
                                                          child: SlideTransition(
                                                            position: Tween<Offset>(
                                                              begin: const Offset(0, 0.02),
                                                              end: Offset.zero,
                                                            ).animate(anim),
                                                            child: child,
                                                          ),
                                                        );
                                                      },
                                                      child: _currentTab == 'login'
                                                          ? KeyedSubtree(
                                                              key: const ValueKey('login'),
                                                              child: _buildLoginPanel(),
                                                            )
                                                          : KeyedSubtree(
                                                              key: const ValueKey(
                                                                'register',
                                                              ),
                                                              child: _buildRegisterPanel(),
                                                            ),
                                                    ),
                                                  ],
                                                ),
                                              ),
                                            ),
                                          ),
                                        ),
                                      ),
                                      SlideTransition(
                                        position: _footerSlide,
                                        child: FadeTransition(
                                          opacity: _footerFade,
                                          child: _buildLegalFooter(),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// 自定义输入框组件（有自己的聚焦状态管理）
// ─────────────────────────────────────────────────
class _InputWrap extends StatefulWidget {
  final TextEditingController controller;
  final FocusNode focusNode;
  final IconData icon;
  final String? placeholder;
  final bool obscure;
  final VoidCallback? onToggleObscure;
  final bool isObscured;
  final TextInputAction textInputAction;
  final VoidCallback? onSubmitted;
  final ValueChanged<String>? onChanged;
  final bool isMono;
  final bool forceUppercase;
  final int? maxLength;
  final bool hasError;

  const _InputWrap({
    required this.controller,
    required this.focusNode,
    required this.icon,
    this.placeholder,
    this.obscure = false,
    this.onToggleObscure,
    this.isObscured = true,
    this.textInputAction = TextInputAction.next,
    this.onSubmitted,
    this.onChanged,
    this.isMono = false,
    this.forceUppercase = false,
    this.maxLength,
    this.hasError = false,
  });

  @override
  State<_InputWrap> createState() => _InputWrapState();
}

class _InputWrapState extends State<_InputWrap> {
  bool _focused = false;

  _C get _colors => Theme.of(context).brightness == Brightness.light ? _C.light : _C.dark;
  _S get _styles => _S(_colors);

  @override
  void initState() {
    super.initState();
    widget.focusNode.addListener(_onFocusChange);
  }

  @override
  void dispose() {
    widget.focusNode.removeListener(_onFocusChange);
    super.dispose();
  }

  void _onFocusChange() {
    setState(() => _focused = widget.focusNode.hasFocus);
  }

  @override
  Widget build(BuildContext context) {
    final p = _colors;
    final s = _styles;
    final isObscuredText = widget.obscure && widget.isObscured;

    return AnimatedContainer(
      duration: const Duration(milliseconds: 180),
      decoration: BoxDecoration(
        color: p.card2,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: widget.hasError
              ? p.borderErr
              : _focused
              ? p.borderFocus
              : p.borderIdle,
          width: 1,
        ),
        boxShadow: widget.hasError
            ? [
                BoxShadow(
                  color: p.up.withValues(alpha: p.isLight ? 0.10 : 0.07),
                  blurRadius: 0,
                  spreadRadius: 3,
                ),
              ]
            : _focused
            ? [
                BoxShadow(
                  color: p.blue.withValues(alpha: p.isLight ? 0.12 : 0.08),
                  blurRadius: 0,
                  spreadRadius: 3,
                ),
              ]
            : [],
      ),
      child: Row(
        children: [
          Padding(
            padding: const EdgeInsets.only(left: 14, right: 10),
            child: Icon(
              widget.icon,
              size: 15,
              color: _focused ? p.blue : p.textDim,
            ),
          ),
          Expanded(
            child: TextField(
              controller: widget.controller,
              focusNode: widget.focusNode,
              obscureText: isObscuredText,
              textInputAction: widget.textInputAction,
              textCapitalization: widget.forceUppercase
                  ? TextCapitalization.characters
                  : TextCapitalization.none,
              maxLength: widget.maxLength,
              onSubmitted: (_) => widget.onSubmitted?.call(),
              onChanged: (v) {
                if (widget.forceUppercase) {
                  final upper = v.toUpperCase();
                  if (upper != v) {
                    widget.controller.value = TextEditingValue(
                      text: upper,
                      selection: TextSelection.collapsed(offset: upper.length),
                    );
                  }
                }
                widget.onChanged?.call(v);
              },
              style: widget.isMono
                  ? (widget.forceUppercase ? s.monoUpper : s.monoInput)
                  : s.inputText,
              decoration: InputDecoration(
                border: InputBorder.none,
                enabledBorder: InputBorder.none,
                focusedBorder: InputBorder.none,
                disabledBorder: InputBorder.none,
                errorBorder: InputBorder.none,
                focusedErrorBorder: InputBorder.none,
                filled: true,
                fillColor: Colors.transparent,
                hoverColor: Colors.transparent,
                hintText: widget.placeholder,
                hintStyle: s.inputHint,
                contentPadding: const EdgeInsets.symmetric(vertical: 13),
                isDense: true,
                counterText: '',
              ),
            ),
          ),
          if (widget.onToggleObscure != null)
            GestureDetector(
              onTap: widget.onToggleObscure,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 14),
                child: Icon(
                  widget.isObscured
                      ? Icons.visibility_off_outlined
                      : Icons.visibility_outlined,
                  size: 15,
                  color: widget.isObscured ? p.textDim : p.blue,
                ),
              ),
            ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────
// 邀请码弹窗
// ─────────────────────────────────────────────────
class _InviteCodeDialog extends StatefulWidget {
  @override
  State<_InviteCodeDialog> createState() => _InviteCodeDialogState();
}

class _InviteCodeDialogState extends State<_InviteCodeDialog> {
  final ApiService _api = ApiService();
  String _imageUrl = '';
  String _text = '';
  bool _loading = true;
  bool _saving = false;

  static const String _defaultText = '扫描下方微信二维码，添加好友后发送「咔咔记账邀请码」即可获取，仅限内测用户。';

  @override
  void initState() {
    super.initState();
    _text = _defaultText;
    _loadConfig();
  }

  Future<void> _loadConfig() async {
    final payload = await _api.getWebConfig();
    if (!mounted) return;
    setState(() {
      _loading = false;
      _imageUrl = payload?['invite_acquire_image_url']?.toString().trim() ?? '';
      final serverText =
          payload?['invite_acquire_text']?.toString().trim() ?? '';
      if (serverText.isNotEmpty) _text = serverText;
    });
  }

  Future<void> _saveImage() async {
    if (_imageUrl.isEmpty || _saving) return;
    setState(() => _saving = true);
    try {
      final response = await http.get(Uri.parse(_imageUrl));
      if (response.statusCode == 200) {
        // Write to temp file then save to gallery
        final tempDir = await Directory.systemTemp.createTemp('kaka_invite');
        final file = File(
          '${tempDir.path}/kaka_invite_${DateTime.now().millisecondsSinceEpoch}.jpg',
        );
        await file.writeAsBytes(response.bodyBytes);
        await Gal.putImage(file.path);
        // Clean up temp file
        try {
          await tempDir.delete(recursive: true);
        } catch (_) {}
        if (!mounted) return;
        final p = Theme.of(context).brightness == Brightness.light ? _C.light : _C.dark;
        final s = _S(p);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('已保存到相册', style: s.snackTxt),
            duration: const Duration(seconds: 2),
            backgroundColor: p.down,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      if (!mounted) return;
      final p = Theme.of(context).brightness == Brightness.light ? _C.light : _C.dark;
      final s = _S(p);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('保存失败', style: s.snackTxt),
          duration: const Duration(seconds: 2),
          backgroundColor: p.up,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = Theme.of(context).brightness == Brightness.light ? _C.light : _C.dark;
    final s = _S(p);
    return Dialog(
      backgroundColor: Colors.transparent,
      child: Container(
        width: 320,
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: p.card,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: p.border),
          boxShadow: [
            BoxShadow(
              color: p.cardShadow,
              blurRadius: p.isLight ? 36 : 64,
              offset: p.isLight ? const Offset(0, 18) : const Offset(0, 24),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // 标题
            Text(
              '获取邀请码',
              style: GoogleFonts.dmSans(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: p.text,
              ),
            ),
            const SizedBox(height: 16),
            // 描述
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                _text,
                textAlign: TextAlign.start,
                style: s.dialogDesc,
              ),
            ),
            const SizedBox(height: 16),
            // 二维码
            Container(
              width: 200,
              height: 200,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
              ),
              child: _loading
                  ? const Center(
                      child: CircularProgressIndicator(
                        color: Color(0xFF5B8DEF),
                        strokeWidth: 2,
                      ),
                    )
                  : _imageUrl.isNotEmpty
                  ? ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Image.network(
                        _imageUrl,
                        fit: BoxFit.contain,
                        errorBuilder: (context, error, stackTrace) =>
                            _buildQrPlaceholder(),
                      ),
                    )
                  : _buildQrPlaceholder(),
            ),
            const SizedBox(height: 14),
            // 保存按钮
            GestureDetector(
              onTap: _saveImage,
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 11),
                decoration: BoxDecoration(
                  color: p.card2,
                  border: Border.all(color: p.border),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _saving
                        ? SizedBox(
                            width: 14,
                            height: 14,
                            child: CircularProgressIndicator(
                              color: p.textSub,
                              strokeWidth: 1.5,
                            ),
                          )
                        : Icon(
                            Icons.download_outlined,
                            size: 14,
                            color: p.textSub,
                          ),
                    const SizedBox(width: 6),
                    Text(_saving ? '保存中...' : '保存图片', style: s.saveBtn),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQrPlaceholder() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.qr_code_2, size: 80, color: Colors.grey[300]),
          const SizedBox(height: 8),
          Text(
            '二维码加载失败',
            style: GoogleFonts.dmSans(
              fontSize: 12,
              color: Colors.grey[400],
            ), // placeholder, no cache needed
          ),
        ],
      ),
    );
  }
}
