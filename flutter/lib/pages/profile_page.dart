import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../config/theme.dart';
import '../models/app_version.dart';
import '../providers/app_state.dart';
import '../widgets/profile_icons.dart';
import 'about_page.dart';
import 'invite_acquire_page.dart';

/// 我的页面
typedef ProfileUrlOpener = Future<bool> Function(Uri uri, LaunchMode mode);
typedef ProfileVersionLoader = Future<String> Function();
typedef ProfileNowProvider = DateTime Function();

class ProfilePage extends StatefulWidget {
  final VoidCallback onLogout;
  final ProfileUrlOpener? externalUrlOpener;
  final ProfileVersionLoader? versionLoader;
  final ProfileNowProvider? nowProvider;

  const ProfilePage({
    super.key,
    required this.onLogout,
    this.externalUrlOpener,
    this.versionLoader,
    this.nowProvider,
  });

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  final ImagePicker _picker = ImagePicker();
  bool _profileLoaded = false;
  String _currentVersion = '';

  @override
  void initState() {
    super.initState();
    _loadVersion();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final appState = context.read<AppState>();
      if (appState.isLoggedIn && !_profileLoaded) {
        _profileLoaded = true;
        appState.fetchProfile();
      }
    });
  }

  Future<void> _loadVersion() async {
    final info = await PackageInfo.fromPlatform();
    if (mounted) {
      setState(() {
        _currentVersion = 'v${info.version.trim()}';
      });
    }
  }

  Future<bool> _openExternalUrl(Uri uri, LaunchMode mode) {
    if (widget.externalUrlOpener != null) {
      return widget.externalUrlOpener!(uri, mode);
    }
    return launchUrl(uri, mode: mode);
  }

  Future<void> _openUserGroupPage() async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) =>
            const InviteAcquirePage(scene: InviteAcquireScene.userGroup),
      ),
    );
  }

  Future<void> _checkUpdate() async {
    final messenger = ScaffoldMessenger.of(context);
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(child: CircularProgressIndicator()),
    );

    try {
      final apiService = context.read<AppState>().apiService;
      final latestVersion = await apiService.getAppVersion();
      final info = await PackageInfo.fromPlatform();
      final currentVersion = info.version.trim();

      if (!mounted) return;
      Navigator.of(context).pop();

      if (latestVersion == null) {
        messenger.showSnackBar(const SnackBar(content: Text('检查更新失败，请稍后重试')));
        return;
      }

      if (!_isNewerVersion(latestVersion.version, currentVersion)) {
        messenger.showSnackBar(const SnackBar(content: Text('当前已是最新版本')));
        return;
      }

      _showUpdateDialog(latestVersion);
    } catch (e) {
      if (!mounted) return;
      Navigator.of(context).pop();
      messenger.showSnackBar(SnackBar(content: Text('检查更新出错: $e')));
    }
  }

  bool _isNewerVersion(String latest, String current) {
    final latestParts = _parseVersion(latest);
    final currentParts = _parseVersion(current);
    final maxLen = latestParts.length > currentParts.length
        ? latestParts.length
        : currentParts.length;
    for (int i = 0; i < maxLen; i++) {
      final lv = i < latestParts.length ? latestParts[i] : 0;
      final cv = i < currentParts.length ? currentParts[i] : 0;
      if (lv > cv) return true;
      if (lv < cv) return false;
    }
    return false;
  }

  List<int> _parseVersion(String raw) {
    final value = raw.trim();
    if (value.isEmpty) return const <int>[0, 0, 0];
    return value
        .split('.')
        .map((part) {
          final match = RegExp(r'^\d+').firstMatch(part.trim());
          if (match == null) return 0;
          return int.tryParse(match.group(0) ?? '') ?? 0;
        })
        .toList(growable: false);
  }

  void _showUpdateDialog(AppVersion version) {
    showDialog(
      context: context,
      barrierDismissible: true,
      builder: (dialogContext) => Dialog(
        backgroundColor: Colors.transparent,
        insetPadding: const EdgeInsets.symmetric(horizontal: 28, vertical: 24),
        child: Container(
          constraints: const BoxConstraints(maxWidth: 420),
          decoration: BoxDecoration(
            color: AppTheme.bgElevated,
            borderRadius: BorderRadius.circular(20),
            boxShadow: const [
              BoxShadow(
                color: Color(0x332D1E70),
                blurRadius: 26,
                offset: Offset(0, 12),
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ClipRRect(
                borderRadius: const BorderRadius.vertical(
                  top: Radius.circular(20),
                ),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.fromLTRB(20, 18, 20, 14),
                  decoration: const BoxDecoration(
                    gradient: LinearGradient(
                      colors: [Color(0xFFFFD954), Color(0xFFFFC83D)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                  ),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.rocket_launch_rounded,
                        color: Colors.white,
                        size: 22,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          '发现新版本',
                          style: TextStyle(
                            color: AppTheme.textPrimary,
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                      Text(
                        'v${version.version}',
                        style: const TextStyle(
                          color: Color(0xFFE63946),
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 18, 20, 18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '更新内容',
                      style: TextStyle(
                        color: AppTheme.textPrimary,
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      version.releaseNotes.trim().isEmpty
                          ? '修复已知问题，优化使用体验。'
                          : version.releaseNotes,
                      style: TextStyle(
                        color: AppTheme.textSecondary,
                        fontSize: 14,
                        height: 1.6,
                      ),
                    ),
                    const SizedBox(height: 20),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFFC5B61),
                          foregroundColor: Colors.white,
                          elevation: 0,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(28),
                          ),
                        ),
                        onPressed: () async {
                          final urlText = version.downloadUrl.trim();
                          final uri = Uri.tryParse(urlText);
                          if (uri == null ||
                              uri.host.isEmpty ||
                              !(uri.scheme == 'http' ||
                                  uri.scheme == 'https')) {
                            if (!mounted) return;
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('下载链接不可用')),
                            );
                            return;
                          }
                          Navigator.of(dialogContext).pop();
                          final ok = await _openExternalUrl(
                            uri,
                            LaunchMode.externalApplication,
                          );
                          if (!ok && mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('无法打开下载链接')),
                            );
                          }
                        },
                        child: const Text(
                          '更新',
                          style: TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  DateTime? _parseCreatedAtAsBeijingDate(String? raw) {
    final text = raw?.trim() ?? '';
    if (text.isEmpty) return null;
    final noZonePattern = RegExp(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$');
    final normalized = noZonePattern.hasMatch(text)
        ? '${text.replaceFirst(' ', 'T')}Z'
        : text;
    final parsed = DateTime.tryParse(normalized);
    if (parsed == null) return null;
    final beijing = parsed.toUtc().add(const Duration(hours: 8));
    return DateTime(beijing.year, beijing.month, beijing.day);
  }

  int? _recordDaysTextValue(String? createdAtRaw) {
    final registeredDate = _parseCreatedAtAsBeijingDate(createdAtRaw);
    if (registeredDate == null) return null;
    final now = widget.nowProvider?.call() ?? DateTime.now();
    final nowBj = now.toUtc().add(const Duration(hours: 8));
    final todayBjDate = DateTime(nowBj.year, nowBj.month, nowBj.day);
    final days = todayBjDate.difference(registeredDate).inDays + 1;
    return days < 1 ? 1 : days;
  }

  // --- Avatar & Profile Editing ---
  Future<void> _pickAvatar(AppState appState) async {
    try {
      final file = await _picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 70,
        maxWidth: 360,
        maxHeight: 360,
      );
      if (file == null) return;
      final bytes = await file.readAsBytes();
      final base64Str = base64Encode(bytes);
      final ok = await appState.updateProfile(avatar: base64Str);
      if (!ok && mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('头像保存失败，请稍后重试')));
      }
    } catch (e) {
      debugPrint('选择头像失败: $e');
    }
  }

  Future<void> _removeAvatar(AppState appState) async {
    final ok = await appState.updateProfile(avatar: '');
    if (!ok && mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('头像移除失败，请稍后重试')));
    }
  }

  Future<void> _editNickname(AppState appState) async {
    final controller = TextEditingController(text: appState.nickname ?? '');
    final newName = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.bgElevated,
        title: Text('修改昵称', style: TextStyle(color: AppTheme.textPrimary)),
        content: TextField(
          controller: controller,
          autofocus: true,
          maxLength: 12,
          style: TextStyle(color: AppTheme.textPrimary),
          decoration: InputDecoration(
            hintText: '请输入昵称',
            hintStyle: TextStyle(color: AppTheme.textTertiary),
            counterText: '',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('取消', style: TextStyle(color: AppTheme.textSecondary)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, controller.text.trim()),
            child: Text('保存', style: TextStyle(color: AppTheme.accent)),
          ),
        ],
      ),
    );

    if (newName == null) return;
    final ok = await appState.updateProfile(nickname: newName);
    if (!ok && mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('昵称保存失败，请稍后重试')));
    }
  }

  // --- Settings Logic (Moved from AppSettingsPage) ---
  Future<void> _changePassword(AppState appState) async {
    final oldCtrl = TextEditingController();
    final newCtrl = TextEditingController();
    final confirmCtrl = TextEditingController();
    final submit = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.bgElevated,
        title: Text('修改密码', style: TextStyle(color: AppTheme.textPrimary)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: oldCtrl,
              obscureText: true,
              style: TextStyle(color: AppTheme.textPrimary),
              decoration: const InputDecoration(labelText: '原密码'),
            ),
            const SizedBox(height: Spacing.sm),
            TextField(
              controller: newCtrl,
              obscureText: true,
              style: TextStyle(color: AppTheme.textPrimary),
              decoration: const InputDecoration(labelText: '新密码'),
            ),
            const SizedBox(height: Spacing.sm),
            TextField(
              controller: confirmCtrl,
              obscureText: true,
              style: TextStyle(color: AppTheme.textPrimary),
              decoration: const InputDecoration(labelText: '确认新密码'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('取消', style: TextStyle(color: AppTheme.textSecondary)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text('提交', style: TextStyle(color: AppTheme.accent)),
          ),
        ],
      ),
    );
    if (submit != true) return;

    final oldPassword = oldCtrl.text;
    final newPassword = newCtrl.text;
    final confirm = confirmCtrl.text;
    if (newPassword != confirm) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('两次输入的新密码不一致')));
      return;
    }

    final ok = await appState.changePassword(
      oldPassword: oldPassword,
      newPassword: newPassword,
    );
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(ok ? '密码修改成功' : '密码修改失败，请检查原密码')));
  }

  // --- UI Builders ---
  Widget _buildAvatar(AppState appState) {
    final fallback =
        (appState.nickname?.isNotEmpty == true
                ? appState.nickname!.substring(0, 1)
                : (appState.username?.substring(0, 1).toUpperCase() ?? 'U'))
            .toUpperCase();

    Uint8List? avatarBytes;
    if (appState.avatar != null && appState.avatar!.isNotEmpty) {
      try {
        avatarBytes = base64Decode(appState.avatar!);
      } catch (_) {
        avatarBytes = null;
      }
    }

    final hasAvatar = avatarBytes != null;
    final avatarImage = avatarBytes == null ? null : MemoryImage(avatarBytes);

    return GestureDetector(
      onTap: () => _pickAvatar(appState),
      onLongPress: () => _removeAvatar(appState),
      child: Stack(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppTheme.accent,
              image: hasAvatar
                  ? DecorationImage(image: avatarImage!, fit: BoxFit.cover)
                  : null,
            ),
            alignment: Alignment.center,
            child: hasAvatar
                ? null
                : Text(
                    fallback,
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.textPrimary,
                    ),
                  ),
          ),
          Positioned(
            bottom: 0,
            right: 0,
            child: Container(
              width: 16,
              height: 16,
              decoration: BoxDecoration(
                color: appState.isLightTheme
                    ? const Color(0xFFF0F5FF)
                    : const Color(0xFF1F2A3D),
                shape: BoxShape.circle,
                border: Border.all(
                  color: appState.isLightTheme
                      ? Colors.white
                      : const Color(0xFF13151B),
                  width: 1.5,
                ),
              ),
              child: Icon(
                Icons.camera_alt,
                size: 8,
                color: AppTheme.textSecondary,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHero(AppState appState) {
    final days = _recordDaysTextValue(appState.createdAtRaw) ?? 1;
    final name = appState.nickname?.isNotEmpty == true
        ? appState.nickname!
        : (appState.username?.isNotEmpty == true
              ? appState.username!
              : 'Kona 用户');

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: appState.isLightTheme
              ? [const Color(0xFFDDE8FF), const Color(0xFFD0DCF5)]
              : [const Color(0xFF171C2E), const Color(0xFF101521)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: appState.isLightTheme
              ? const Color(0x2E5B8DEF)
              : const Color(0x2E5B8DEF),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              _buildAvatar(appState),
              const SizedBox(width: 14),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name,
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: appState.isLightTheme
                          ? const Color(0xFF1F2A3D)
                          : const Color(0xFFE6EBF7),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '已在咔咔记录 $days天',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                      color: appState.isLightTheme
                          ? const Color(0xFF55617B)
                          : const Color(0xFFECF1FB),
                    ),
                  ),
                ],
              ),
            ],
          ),
          GestureDetector(
            onTap: () => _editNickname(appState),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: appState.isLightTheme
                      ? const Color(0x24222C40)
                      : const Color(0x24FFFFFF),
                ),
                color: appState.isLightTheme
                    ? const Color(0x14222C40)
                    : const Color(0x12FFFFFF),
              ),
              child: Text(
                '修改昵称',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: appState.isLightTheme
                      ? const Color(0xFF1F2A3D)
                      : const Color(0xFFE6EBF7),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildListSection(AppState appState) {
    final isLight = appState.isLightTheme;
    return Container(
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: isLight ? const Color(0x1A222C40) : const Color(0x0EFFFFFF),
        ),
        boxShadow: [
          if (isLight)
            const BoxShadow(
              color: Color(0x12222C48),
              blurRadius: 14,
              offset: Offset(0, 4),
            ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _buildListItem(
            icon: ProfileIcons.themeIcon(),
            title: '切换主题',
            trailing: Switch(
              value: isLight,
              onChanged: (_) => appState.toggleTheme(),
              activeThumbColor: Colors.white,
              activeTrackColor: const Color(0xFF5B8DEF),
              inactiveThumbColor: const Color(0xFFD8DEEB),
              inactiveTrackColor: isLight
                  ? const Color(0x26222C40)
                  : const Color(0x29FFFFFF),
              materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
            isTop: true,
          ),
          _buildListDivider(isLight),
          _buildListItem(
            icon: ProfileIcons.passwordIcon(),
            title: '修改密码',
            onTap: () => _changePassword(appState),
          ),
          _buildListDivider(isLight),
          _buildListItem(
            icon: ProfileIcons.biometricsIcon(),
            title: '生物识别',
            trailing: Switch(
              value: appState.biometricEnabled,
              onChanged: (v) async {
                final ok = await appState.setBiometricEnabled(v);
                if (!ok && mounted) {
                  ScaffoldMessenger.of(
                    context,
                  ).showSnackBar(const SnackBar(content: Text('当前设备不可用生物识别')));
                }
              },
              activeThumbColor: Colors.white,
              activeTrackColor: const Color(0xFF5B8DEF),
              inactiveThumbColor: const Color(0xFFD8DEEB),
              inactiveTrackColor: isLight
                  ? const Color(0x26222C40)
                  : const Color(0x29FFFFFF),
              materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
          _buildListDivider(isLight),
          _buildListItem(
            icon: ProfileIcons.updateIcon(),
            title: '检查更新',
            trailingValue: _currentVersion,
            onTap: _checkUpdate,
          ),
          _buildListDivider(isLight),
          _buildListItem(
            icon: ProfileIcons.aboutIcon(),
            title: '关于我们',
            onTap: () => Navigator.of(
              context,
            ).push(MaterialPageRoute(builder: (_) => const AboutPage())),
          ),
          _buildListDivider(isLight),
          _buildListItem(
            icon: ProfileIcons.groupIcon(),
            title: '咔咔用户群',
            onTap: _openUserGroupPage,
            isBottom: true,
          ),
        ],
      ),
    );
  }

  Widget _buildListDivider(bool isLight) {
    return Container(
      height: 1,
      margin: const EdgeInsets.symmetric(horizontal: 16),
      color: isLight ? const Color(0x0A222C40) : const Color(0x0CFFFFFF),
    );
  }

  Widget _buildListItem({
    required Widget icon,
    required String title,
    String? trailingValue,
    Widget? trailing,
    VoidCallback? onTap,
    bool isTop = false,
    bool isBottom = false,
  }) {
    final appState = context.watch<AppState>();
    final isLight = appState.isLightTheme;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.vertical(
          top: isTop ? const Radius.circular(18) : Radius.zero,
          bottom: isBottom ? const Radius.circular(18) : Radius.zero,
        ),
        splashColor: isLight
            ? const Color(0x0A222C40)
            : const Color(0x0AFFFFFF),
        highlightColor: isLight
            ? const Color(0x0A222C40)
            : const Color(0x0AFFFFFF),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: [
              icon,
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  title,
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: isLight
                        ? const Color(0xFF1F2A3D)
                        : const Color(0xFFEDF1FA),
                  ),
                ),
              ),
              if (trailing != null) trailing,
              if (trailing == null) ...[
                if (trailingValue != null)
                  Padding(
                    padding: const EdgeInsets.only(right: 6),
                    child: Text(
                      trailingValue,
                      style: TextStyle(
                        fontFamily: 'JetBrains Mono',
                        fontSize: 13,
                        color: isLight
                            ? const Color(0xFF55617B)
                            : const Color(0xFFA8B2C9),
                      ),
                    ),
                  ),
                Icon(
                  Icons.arrow_forward_ios_rounded,
                  size: 14,
                  color: isLight
                      ? const Color(0xFF69758F)
                      : const Color(0xFF8F99AF),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLogoutButton(bool isLight) {
    return SizedBox(
      width: double.infinity,
      height: 46,
      child: OutlinedButton(
        onPressed: () {
          Navigator.of(
            context,
            rootNavigator: true,
          ).popUntil((route) => route.isFirst);
          widget.onLogout();
        },
        style: OutlinedButton.styleFrom(
          backgroundColor: isLight
              ? const Color(0x12F05A55)
              : const Color(0x12F05A55),
          side: BorderSide(
            color: isLight ? const Color(0x47F05A55) : const Color(0x47F05A55),
            width: 1,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          elevation: 0,
        ),
        child: Text(
          '退出登录',
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w700,
            color: const Color(0xFFF05A55), // var(--red)
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        return SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildHero(appState),
              const SizedBox(height: 24),
              Text(
                '通用设置',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: appState.isLightTheme
                      ? const Color(0xFF69758F)
                      : const Color(0xFF888FA0),
                ),
              ),
              const SizedBox(height: 8),
              _buildListSection(appState),
              const SizedBox(height: 32),
              _buildLogoutButton(appState.isLightTheme),
              const SizedBox(height: 48),
            ],
          ),
        );
      },
    );
  }
}
