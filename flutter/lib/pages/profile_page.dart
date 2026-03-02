import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../config/theme.dart';
import '../models/app_version.dart';
import 'app_settings_page.dart';
import '../providers/app_state.dart';
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

    // 显示 Loading
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
      // 隐藏 Loading
      Navigator.of(context).pop();

      if (latestVersion == null) {
        messenger.showSnackBar(const SnackBar(content: Text('检查更新失败，请稍后重试')));
        return;
      }

      if (!_isNewerVersion(latestVersion.version, currentVersion)) {
        messenger.showSnackBar(const SnackBar(content: Text('当前已是最新版本')));
        return;
      }

      // 有新版本，弹窗提示
      _showUpdateDialog(latestVersion);
    } catch (e) {
      if (!mounted) return;
      // 隐藏 Loading
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
                borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
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
                      const Icon(Icons.rocket_launch_rounded, color: Colors.white, size: 22),
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
                              !(uri.scheme == 'http' || uri.scheme == 'https')) {
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
                          style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
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

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final appState = context.read<AppState>();
      if (appState.isLoggedIn && !_profileLoaded) {
        _profileLoaded = true;
        appState.fetchProfile();
      }
    });
  }

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
          CircleAvatar(
            radius: 35,
            backgroundColor: AppTheme.accent,
            backgroundImage: avatarImage,
            child: hasAvatar
                ? null
                : Text(
                    fallback,
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.textPrimary,
                    ),
                  ),
          ),
          Positioned(
            bottom: 0,
            right: 0,
            child: Container(
              width: 20,
              height: 20,
              decoration: BoxDecoration(
                color: AppTheme.bgElevated,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(
                Icons.camera_alt,
                size: 12,
                color: AppTheme.textSecondary,
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        return SingleChildScrollView(
          padding: const EdgeInsets.all(Spacing.xl),
          child: Column(
            children: [
              const SizedBox(height: Spacing.xl),
              // 用户信息卡片
              Container(
                padding: const EdgeInsets.all(Spacing.lg),
                decoration: BoxDecoration(
                  color: AppTheme.bgCard,
                  borderRadius: BorderRadius.circular(AppRadius.lg),
                ),
                child: Row(
                  children: [
                    _buildAvatar(appState),
                    const SizedBox(width: Spacing.lg),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            appState.nickname?.isNotEmpty == true
                                ? appState.nickname!
                                : (appState.username?.isNotEmpty == true
                                      ? appState.username!
                                      : '用户'),
                            style: TextStyle(
                              fontSize: FontSize.xl,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.textPrimary,
                            ),
                          ),
                          Builder(
                            builder: (context) {
                              final days = _recordDaysTextValue(
                                appState.createdAtRaw,
                              );
                              if (days == null) return const SizedBox.shrink();
                              return Padding(
                                padding: const EdgeInsets.only(top: 4),
                                child: Text(
                                  '已在咔咔记录 $days 天',
                                  style: TextStyle(
                                    fontSize: 13,
                                    color: AppTheme.textSecondary,
                                  ),
                                ),
                              );
                            },
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: Icon(Icons.edit, color: AppTheme.textTertiary),
                      onPressed: () => _editNickname(appState),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: Spacing.lg),

              // 设置项
              _buildSettingItem(Icons.settings, '个人设置', () {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (context) =>
                        AppSettingsPage(onLogout: widget.onLogout),
                  ),
                );
              }),
              const SizedBox(height: Spacing.sm),
              _buildSettingItem(
                Icons.system_update_outlined,
                '检查更新',
                _checkUpdate,
              ),
              const SizedBox(height: Spacing.sm),
              _buildSettingItem(Icons.info_outline, '关于我们', () {
                Navigator.of(context).push(
                  MaterialPageRoute(builder: (context) => const AboutPage()),
                );
              }),
              const SizedBox(height: Spacing.sm),
              _buildSettingItem(
                Icons.groups_outlined,
                '咔咔用户群',
                _openUserGroupPage,
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildSettingItem(IconData icon, String title, VoidCallback onTap) {
    return Material(
      color: AppTheme.bgCard,
      borderRadius: BorderRadius.circular(AppRadius.lg),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        child: Padding(
          padding: const EdgeInsets.all(Spacing.lg),
          child: Row(
            children: [
              Icon(icon, size: 20, color: AppTheme.accentLight),
              const SizedBox(width: Spacing.md),
              Expanded(
                child: Text(
                  title,
                  style: TextStyle(fontSize: 15, color: AppTheme.textPrimary),
                ),
              ),
              Icon(Icons.chevron_right, size: 20, color: AppTheme.textTertiary),
            ],
          ),
        ),
      ),
    );
  }
}
