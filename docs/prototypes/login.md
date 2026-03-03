# 咔咔记账登录页 Flutter 1:1 还原指南

> 将此文档连同 `login.html` 文件一起提供给 Claude Code，并附上下方指令。

---

## ✅ 给 Claude Code 的完整指令

```
请根据我提供的 login.html 文件，用 Flutter 1:1 还原这个登录页面。
下面是所有设计细节和实现要求，请严格遵照执行。
```

---

## 一、整体页面结构

页面从上到下分为三块，全部垂直居中对齐：

```
SafeArea
└── SingleChildScrollView
    └── Center
        └── ConstrainedBox(maxWidth: 380)
            └── Padding(horizontal: 20, vertical: 24)
                └── Column
                    ├── 品牌区（Logo + 名称 + 副标题）
                    ├── SizedBox(height: 36)
                    ├── 卡片区（Tab 切换 + 表单）
                    └── 底部法律声明
```

**页面背景色：** `Color(0xFF0C0D11)`

**背景装饰（Stack 底层）：**
- 左上角径向渐变光晕：500×500，颜色 `Color(0xFF5B8DEF).withOpacity(0.07)`，位置 top: -120, 水平居中，用 `RadialGradient` + `BoxDecoration`
- 右下角径向渐变光晕：320×320，颜色 `Color(0xFFF05A55).withOpacity(0.05)`，位置 bottom: -80, right: -60
- 两个光晕用 `Positioned` + `IgnorePointer` 放在 Stack 最底层

**入场动画（整体）：** 页面加载时 opacity 0→1 + translateY 16→0，duration 400ms，curve: `Curves.easeOutCubic`，用 `AnimationController` + `FadeTransition` + `SlideTransition` 实现

---

## 二、颜色 Token（全局常量）

```dart
class AppColors {
  // 背景
  static const bg    = Color(0xFF0C0D11);
  static const card  = Color(0xFF13151C);
  static const card2 = Color(0xFF181B23);

  // 描边
  static const border      = Color(0x0FFFFFFF); // rgba(255,255,255,0.06)
  static const borderFocus = Color(0x805B8DEF); // rgba(91,141,239,0.5)
  static const borderErr   = Color(0x8DF05A55); // rgba(240,90,85,0.55)

  // 文字
  static const text    = Color(0xFFE8EAF0);
  static const textSub = Color(0xFF8B909F);
  static const textDim = Color(0xFF4E5464);

  // 功能色
  static const up   = Color(0xFFF05A55); // 错误/上涨红
  static const down = Color(0xFF2ECC8A); // 成功/下跌绿
  static const blue  = Color(0xFF5B8DEF); // 主色调
  static const blue2 = Color(0xFF4A7BE0); // 蓝色渐变终点
  static const gold  = Color(0xFFD4AF64); // 邀请码金色
}
```

---

## 三、字体

使用 **DM Sans**（Google Fonts）作为主字体：
```yaml
# pubspec.yaml
dependencies:
  google_fonts: ^6.x
```
```dart
// 全局设置
theme: ThemeData(
  fontFamily: GoogleFonts.dmSans().fontFamily,
)
```

密码输入框等宽字体使用 **JetBrains Mono**（`GoogleFonts.jetBrainsMono()`），仅邀请码输入框和密码输入框使用。

---

## 四、品牌区

```dart
Column(
  children: [
    // Logo 图标
    Container(
      width: 76, height: 76,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(22),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFF7B54), Color(0xFFFF4F7B), Color(0xFFFF1493)],
          stops: [0.0, 0.5, 1.0],
        ),
        boxShadow: [BoxShadow(
          color: Color(0xFFFF4F7B).withOpacity(0.25),
          blurRadius: 32, offset: Offset(0, 8),
        )],
      ),
      child: CustomPaint(painter: LogoMPainter()), // 见下方 M 形折线说明
    ),
    SizedBox(height: 14),

    // 应用名
    Text('咔咔记账', style: TextStyle(
      fontSize: 22, fontWeight: FontWeight.w700,
      color: AppColors.text, letterSpacing: -0.3,
    )),
    SizedBox(height: 4),

    // 副标题
    Text('一站式管理全市场资产', style: TextStyle(
      fontSize: 11, color: AppColors.textDim, letterSpacing: 1.1,
    )),
  ],
)
```

**Logo M 形折线（CustomPainter）：**
```dart
class LogoMPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withOpacity(0.95)
      ..strokeWidth = 90 / 1024 * size.width  // 按比例缩放
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round
      ..style = PaintingStyle.stroke;

    // 原始 SVG 坐标基于 1024×1024，需缩放到实际 size
    final scaleX = size.width / 1024;
    final scaleY = size.height / 1024;
    final path = Path();
    // points: 222,648 → 312,376 → 410,648 → 512,376 → 614,648 → 712,376 → 802,648
    final points = [
      Offset(222 * scaleX, 648 * scaleY),
      Offset(312 * scaleX, 376 * scaleY),
      Offset(410 * scaleX, 648 * scaleY),
      Offset(512 * scaleX, 376 * scaleY),
      Offset(614 * scaleX, 648 * scaleY),
      Offset(712 * scaleX, 376 * scaleY),
      Offset(802 * scaleX, 648 * scaleY),
    ];
    path.moveTo(points[0].dx, points[0].dy);
    for (final p in points.skip(1)) path.lineTo(p.dx, p.dy);
    canvas.drawPath(path, paint);
  }
  @override
  bool shouldRepaint(_) => false;
}
```

---

## 五、卡片区

```dart
Container(
  decoration: BoxDecoration(
    color: AppColors.card,
    borderRadius: BorderRadius.circular(20),
    border: Border.all(color: AppColors.border),
    boxShadow: [BoxShadow(
      color: Colors.black.withOpacity(0.4),
      blurRadius: 60, offset: Offset(0, 24),
    )],
  ),
  padding: EdgeInsets.fromLTRB(24, 28, 24, 24),
  child: Column(children: [
    _buildTabSwitcher(),
    _buildLoginPanel(),   // or _buildRegisterPanel()
  ]),
)
```

**卡片顶部高光线：**
在卡片 Stack 顶部叠加一个 `Positioned` Container：
```dart
Positioned(
  top: 0, left: 20, right: 20, height: 1,
  child: Container(
    decoration: BoxDecoration(
      gradient: LinearGradient(colors: [
        Colors.transparent,
        Colors.white.withOpacity(0.08),
        Colors.transparent,
      ]),
    ),
  ),
)
```

---

## 六、Tab 切换器

```dart
Container(
  padding: EdgeInsets.all(3),
  decoration: BoxDecoration(
    color: Colors.black.withOpacity(0.35),
    border: Border.all(color: Colors.white.withOpacity(0.08)),
    borderRadius: BorderRadius.circular(10),
  ),
  child: Row(children: [
    _buildTab('登录',    isActive: currentTab == 'login',    onTap: () => switchTab('login')),
    SizedBox(width: 2),
    _buildTab('注册',   isActive: currentTab == 'register', onTap: () => switchTab('register')),
  ]),
)
```

**单个 Tab：**
```dart
Widget _buildTab(String label, {required bool isActive, required VoidCallback onTap}) {
  return Expanded(
    child: GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: Duration(milliseconds: 180),
        padding: EdgeInsets.symmetric(vertical: 9),
        decoration: BoxDecoration(
          color: isActive ? Colors.white.withOpacity(0.10) : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
          boxShadow: isActive ? [BoxShadow(
            color: Colors.black.withOpacity(0.5),
            blurRadius: 8, offset: Offset(0, 2),
          )] : [],
        ),
        child: Text(label,
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 13,
            fontWeight: isActive ? FontWeight.w600 : FontWeight.w500,
            color: isActive
              ? AppColors.text
              : Colors.white.withOpacity(0.4),
          ),
        ),
      ),
    ),
  );
}
```

**切换逻辑：** 用 `setState` + `AnimatedSwitcher` 切换面板，切换时调用 `clearErrors()`。

---

## 七、表单公共组件

### 7.1 字段容器

```dart
Column(
  crossAxisAlignment: CrossAxisAlignment.start,
  children: [
    // 标签（注册页带蓝点前缀）
    Row(children: [
      if (showDot) ...[
        Container(width: 4, height: 4,
          decoration: BoxDecoration(color: AppColors.blue, shape: BoxShape.circle)),
        SizedBox(width: 4),
      ],
      Text(label, style: TextStyle(
        fontSize: 11, fontWeight: FontWeight.w500,
        color: AppColors.textSub, letterSpacing: 0.3,
      )),
    ]),
    SizedBox(height: 6),
    // 输入框
    _buildInputWrap(...),
    // 错误提示
    if (errorText != null) Padding(
      padding: EdgeInsets.only(top: 4, left: 2),
      child: Text(errorText!, style: TextStyle(fontSize: 10, color: AppColors.up)),
    ),
  ],
)
```

### 7.2 输入框容器

```dart
// 用 FocusNode 监听聚焦状态
AnimatedContainer(
  duration: Duration(milliseconds: 180),
  decoration: BoxDecoration(
    color: AppColors.card2,
    borderRadius: BorderRadius.circular(10),
    border: Border.all(
      color: hasError
        ? AppColors.borderErr
        : isFocused ? AppColors.borderFocus : AppColors.border,
      width: 1,
    ),
    boxShadow: hasError
      ? [BoxShadow(color: Color(0xFFF05A55).withOpacity(0.07), blurRadius: 0, spreadRadius: 3)]
      : isFocused
        ? [BoxShadow(color: Color(0xFF5B8DEF).withOpacity(0.08), blurRadius: 0, spreadRadius: 3)]
        : [],
  ),
  child: Row(children: [
    // 左侧图标
    Padding(
      padding: EdgeInsets.only(left: 14, right: 10),
      child: Icon(iconData, size: 15,
        color: isFocused ? AppColors.blue : AppColors.textDim),
    ),
    // 输入框
    Expanded(child: TextField(
      controller: controller,
      focusNode: focusNode,
      obscureText: obscure,
      style: TextStyle(fontSize: 14, color: AppColors.text),
      decoration: InputDecoration(
        border: InputBorder.none,
        hintText: placeholder,
        hintStyle: TextStyle(fontSize: 13, color: AppColors.textDim),
        contentPadding: EdgeInsets.symmetric(vertical: 13),
        isDense: true,
      ),
    )),
    // 右侧操作按钮（密码显示/隐藏）
    if (onToggleObscure != null)
      GestureDetector(
        onTap: onToggleObscure,
        child: Padding(
          padding: EdgeInsets.symmetric(horizontal: 14),
          child: Icon(obscure ? Icons.visibility_off_outlined : Icons.visibility_outlined,
            size: 15, color: obscure ? AppColors.textDim : AppColors.blue),
        ),
      ),
  ]),
)
```

**图标对应关系：**
- 账号字段：人像图标（`Icons.person_outline`）
- 密码字段：锁图标（`Icons.lock_outline`）
- 邀请码字段：五角星图标（`Icons.star_outline`）

---

## 八、登录表单

包含以下元素（`Column`，`gap: 14`）：

### 8.1 账号输入框
- label: `账号`，placeholder: `请输入用户名`
- 无蓝点前缀
- 图标：人像

### 8.2 密码输入框
- label: `密码`，placeholder: `请输入密码`
- 图标：锁，右侧有显示/隐藏按钮
- 密码字体：JetBrains Mono，字号 14px

### 8.3 记住用户名 + 忘记密码行

```dart
// margin-top: 4, margin-bottom: 4
Row(
  mainAxisAlignment: MainAxisAlignment.spaceBetween,
  children: [
    // 左：记住用户名勾选
    GestureDetector(
      onTap: toggleRemember,
      child: Row(children: [
        AnimatedContainer(
          duration: Duration(milliseconds: 150),
          width: 16, height: 16,
          decoration: BoxDecoration(
            color: rememberEnabled ? AppColors.blue : AppColors.card2,
            border: Border.all(
              color: rememberEnabled ? AppColors.blue : AppColors.border),
            borderRadius: BorderRadius.circular(4),
          ),
          child: rememberEnabled
            ? Icon(Icons.check, size: 10, color: Colors.white)
            : null,
        ),
        SizedBox(width: 7),
        Text('记住用户名', style: TextStyle(fontSize: 12, color: AppColors.textDim)),
      ]),
    ),
    // 右：忘记密码
    GestureDetector(
      onTap: () { /* TODO */ },
      child: Text('忘记密码？', style: TextStyle(fontSize: 12, color: AppColors.textDim)),
    ),
  ],
)
```

**记住用户名逻辑：** 勾选后用 `shared_preferences` 保存用户名，页面初始化时读取并填入输入框。

### 8.4 登录按钮

```dart
SizedBox(
  width: double.infinity,
  child: ElevatedButton(
    onPressed: isLoading ? null : handleLogin,
    style: ElevatedButton.styleFrom(
      padding: EdgeInsets.symmetric(vertical: 13),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      elevation: 0,
      backgroundColor: Colors.transparent,
      shadowColor: Colors.transparent,
    ),
    child: Ink(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: isSuccess
            ? [Color(0xFF2ECC8A), Color(0xFF25B377)]
            : [AppColors.blue, AppColors.blue2],
          begin: Alignment.topLeft, end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(10),
        boxShadow: [BoxShadow(
          color: (isSuccess ? Color(0xFF2ECC8A) : AppColors.blue).withOpacity(0.35),
          blurRadius: 16, offset: Offset(0, 4),
        )],
      ),
      child: Container(
        alignment: Alignment.center,
        padding: EdgeInsets.symmetric(vertical: 13),
        child: isLoading
          ? SizedBox(width: 16, height: 16,
              child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
          : Text(isSuccess ? '✓ 登录成功' : '登录',
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: Colors.white)),
      ),
    ),
  ),
)
```

**按钮状态机：**
- `idle` → 点击 → `loading`（文字变「登录中…」，1200ms）→ `success`（变绿，文字「✓ 登录成功」）→ 2000ms 后回到 `idle`

---

## 九、注册表单

包含以下元素（`Column`，`gap: 14`）：

### 9.1 邀请码提示条

```dart
Container(
  padding: EdgeInsets.symmetric(horizontal: 13, vertical: 10),
  decoration: BoxDecoration(
    color: Color(0xFFD4AF64).withOpacity(0.07),
    border: Border.all(color: Color(0xFFD4AF64).withOpacity(0.2)),
    borderRadius: BorderRadius.circular(10),
  ),
  child: Row(children: [
    Text('🔑', style: TextStyle(fontSize: 16)),
    SizedBox(width: 9),
    Expanded(child: RichText(text: TextSpan(
      style: TextStyle(fontSize: 11, color: AppColors.gold, height: 1.5),
      children: [
        TextSpan(text: '当前注册仅限受邀用户，'),
        TextSpan(
          text: '获取邀请码',
          style: TextStyle(
            fontWeight: FontWeight.w500,
            decoration: TextDecoration.underline,
            decorationColor: AppColors.gold.withOpacity(0.35),
          ),
          recognizer: TapGestureRecognizer()..onTap = openInviteModal,
        ),
      ],
    ))),
  ]),
)
```

### 9.2 邀请码输入框
- label: `邀请码`（带蓝点前缀），placeholder: `输入邀请码`
- 输入字体：JetBrains Mono，字号 15px，字间距 0.12em，**自动转大写**
- 最大长度：8 位
- 图标：星形（`Icons.star_outline`）

### 9.3 用户名输入框
- label: `用户名 / 账号`（带蓝点），placeholder: `请输入用户名`
- 图标：人像

### 9.4 设置密码输入框
- label: `设置密码`（带蓝点），placeholder: `至少 8 位，含字母和数字`
- 图标：锁，右侧显示/隐藏按钮
- 密码字体：JetBrains Mono

**密码强度条（输入时显示）：**
```dart
// 紧跟在密码输入框下方，初始隐藏
Column(children: [
  Row(children: [
    _buildPwBar(score >= 1, color),   // 弱：红 #F05A55
    SizedBox(width: 3),
    _buildPwBar(score >= 2, color),   // 中：橙 #E09030
    SizedBox(width: 3),
    _buildPwBar(score >= 3, color),   // 强：绿 #2ECC8A
  ]),
  SizedBox(height: 3),
  Text(label, style: TextStyle(fontSize: 10, color: AppColors.textDim)),
])

// 每条：flex:1, 高度 3px, 圆角 2px
// 评分规则：
// +1 长度 >= 8
// +1 含字母且含数字
// +1 含特殊字符或长度 >= 12
```

### 9.5 确认密码输入框
- label: `确认密码`（带蓝点），placeholder: `再次输入密码`
- 图标：锁，右侧显示/隐藏按钮

### 9.6 创建账户按钮
- 同登录按钮样式
- 状态机：`idle` → `loading`（1400ms）→ `success`（「✓ 注册成功」）→ 1800ms 后跳回登录 Tab

**注册校验规则：**
- 邀请码：非空且长度 >= 4
- 用户名：非空
- 密码：长度 >= 8
- 确认密码：与密码一致

---

## 十、底部法律声明

```dart
// 在卡片外部，margin-top: 20
RichText(
  textAlign: TextAlign.center,
  text: TextSpan(
    style: TextStyle(fontSize: 11, color: AppColors.textDim, height: 1.6),
    children: [
      TextSpan(text: '登录或注册即代表您同意 '),
      TextSpan(
        text: '用户协议',
        style: TextStyle(
          color: AppColors.textSub,
          decoration: TextDecoration.underline,
          decorationColor: AppColors.textSub.withOpacity(0.25),
        ),
        recognizer: TapGestureRecognizer()..onTap = openUserAgreement,
      ),
      TextSpan(text: ' 和 '),
      TextSpan(
        text: '隐私政策',
        style: TextStyle(
          color: AppColors.textSub,
          decoration: TextDecoration.underline,
          decorationColor: AppColors.textSub.withOpacity(0.25),
        ),
        recognizer: TapGestureRecognizer()..onTap = openPrivacyPolicy,
      ),
    ],
  ),
)
```

---

## 十一、获取邀请码弹窗

点击「获取邀请码」弹出底部弹窗（`showModalBottomSheet` 或 `showDialog`）。

**弹窗样式：**
```dart
// 用 showDialog + 自定义 Dialog
Container(
  width: 320,
  padding: EdgeInsets.all(24),
  decoration: BoxDecoration(
    color: AppColors.card,
    borderRadius: BorderRadius.circular(20),
    border: Border.all(color: AppColors.border),
    boxShadow: [BoxShadow(
      color: Colors.black.withOpacity(0.6), blurRadius: 64, offset: Offset(0, 24))],
  ),
  child: Column(children: [
    // 关闭按钮（右上角）
    Align(alignment: Alignment.topRight,
      child: GestureDetector(
        onTap: () => Navigator.pop(context),
        child: Container(
          width: 28, height: 28,
          decoration: BoxDecoration(
            color: AppColors.card2, border: Border.all(color: AppColors.border),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(Icons.close, size: 12, color: AppColors.textDim),
        ),
      ),
    ),

    // 标题
    Text('联系我们获取邀请码', style: TextStyle(
      fontSize: 15, fontWeight: FontWeight.w600, color: AppColors.text)),
    SizedBox(height: 6),

    // 描述
    Text('扫描下方微信二维码，添加好友后发送「咔咔记账邀请码」即可获取，仅限内测用户。',
      style: TextStyle(fontSize: 12, color: AppColors.textDim, height: 1.6)),
    SizedBox(height: 16),

    // 二维码图片区域（白色背景，1:1 比例）
    Container(
      width: double.infinity,
      height: 260,   // 正方形
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Image.asset('assets/images/wechat_qr.png', fit: BoxFit.contain),
      // 替换为实际微信二维码图片
    ),
    SizedBox(height: 14),

    // 保存按钮
    GestureDetector(
      onTap: saveQrCode,
      child: Container(
        width: double.infinity,
        padding: EdgeInsets.symmetric(vertical: 11),
        decoration: BoxDecoration(
          color: AppColors.card2,
          border: Border.all(color: AppColors.border),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          Icon(Icons.download_outlined, size: 14, color: AppColors.textSub),
          SizedBox(width: 6),
          Text('保存二维码', style: TextStyle(
            fontSize: 13, fontWeight: FontWeight.w500, color: AppColors.textSub)),
        ]),
      ),
    ),
  ]),
)
```

**弹窗背景遮罩：** `barrierColor: Colors.black.withOpacity(0.7)`，点击背景关闭。

**保存二维码：** 使用 `image_gallery_saver` 或 `gallery_saver` package 将图片保存到相册。

---

## 十二、状态管理建议

用 `StatefulWidget` + 本地 state 即可，无需全局状态管理。

```dart
class _LoginPageState extends State<LoginPage> with TickerProviderStateMixin {
  // Tab
  String currentTab = 'login';   // 'login' | 'register'

  // 登录
  final loginAccCtrl = TextEditingController();
  final loginPwCtrl  = TextEditingController();
  bool loginPwObscure = true;
  bool rememberEnabled = false;
  bool loginLoading = false;
  bool loginSuccess = false;

  // 注册
  final regInvCtrl  = TextEditingController();
  final regAccCtrl  = TextEditingController();
  final regPwCtrl   = TextEditingController();
  final regPw2Ctrl  = TextEditingController();
  bool regPwObscure  = true;
  bool regPw2Obscure = true;
  int  pwScore = 0;
  bool regLoading = false;
  bool regSuccess = false;

  // 错误状态
  Map<String, String?> errors = {};

  void clearErrors() => setState(() => errors = {});
  void setError(String field, String msg) => setState(() => errors[field] = msg);
}
```

---

## 十三、动画细节

| 元素 | 动画类型 | Duration | Curve |
|------|---------|----------|-------|
| 整体页面入场 | fadeUp (opacity + translateY 16→0) | 400ms | easeOutCubic |
| 品牌区 | 同上，delay 0ms | 500ms | ease |
| 卡片 | 同上，delay 80ms | 500ms | ease |
| 法律声明 | 同上，delay 200ms | 500ms | ease |
| 表单面板切换 | fadeUp (translateY 6→0) | 220ms | ease |
| Tab 激活背景 | AnimatedContainer | 180ms | linear |
| 输入框聚焦描边 | AnimatedContainer | 180ms | linear |
| 记住勾选框 | AnimatedContainer (color) | 150ms | linear |
| 按钮按下 | scale 1→0.98 | 150ms | linear |
| 弹窗遮罩 | opacity 0→1 | 200ms | linear |
| 弹窗内容 | translateY 10→0 | 250ms | ease |

---

## 十四、依赖包

```yaml
dependencies:
  google_fonts: ^6.2.1          # DM Sans + JetBrains Mono
  shared_preferences: ^2.3.x    # 记住用户名
  image_gallery_saver: ^2.0.x   # 保存二维码到相册（弹窗内）
```

---

## 十五、注意事项

1. **不要用 `AppBar`**，这是全屏沉浸式页面，背景延伸到状态栏
2. **密码输入框字体** 必须切换到 JetBrains Mono，普通文字仍用 DM Sans
3. **邀请码输入** 需要强制大写：`TextCapitalization.characters` + `onChanged` 转大写
4. **所有颜色** 使用上方 `AppColors` 常量，不要硬编码十六进制
5. **错误状态** 是字段级的（每个输入框独立），不是表单级的
6. **按钮渐变** 必须用 `Ink + BoxDecoration`，不能用 `ElevatedButton` 默认样式
7. **弹窗的二维码图片** 替换为实际微信二维码，路径：`assets/images/wechat_qr.png`
8. **iOS SafeArea** 要正确处理，顶部和底部都要有安全区域

---

*将本文档与 `login.html` 一起提供给 Claude Code，可实现精确的 1:1 还原。*
