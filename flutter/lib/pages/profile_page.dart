import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../config/api_config.dart';
import '../config/theme.dart';
import 'app_settings_page.dart';
import '../providers/app_state.dart';

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
  late final Future<String> _appVersionFuture = _loadAppVersion();

  Future<String> _loadAppVersion() async {
    if (widget.versionLoader != null) return widget.versionLoader!();
    final info = await PackageInfo.fromPlatform();
    final version = info.version.trim();
    final build = info.buildNumber.trim();
    if (version.isEmpty) return '未知版本';
    if (build.isEmpty) return 'v$version';
    return 'v$version+$build';
  }

  Future<bool> _openExternalUrl(Uri uri, LaunchMode mode) {
    if (widget.externalUrlOpener != null) {
      return widget.externalUrlOpener!(uri, mode);
    }
    return launchUrl(uri, mode: mode);
  }

  Future<void> _openFeedback() async {
    final uri = Uri.tryParse(ApiConfig.feedbackUrl);
    if (uri == null || !uri.hasScheme) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('反馈链接配置无效')));
      return;
    }
    final ok = await _openExternalUrl(uri, LaunchMode.externalApplication);
    if (!mounted || ok) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('无法打开反馈链接')));
  }

  Future<void> _checkUpdate() async {
    final messenger = ScaffoldMessenger.of(context);
    final uri = Uri.parse(ApiConfig.apkDownloadUrl);
    var ok = await _openExternalUrl(uri, LaunchMode.inAppBrowserView);
    if (!ok) {
      ok = await _openExternalUrl(uri, LaunchMode.externalApplication);
    }
    if (!mounted) return;
    messenger.showSnackBar(
      SnackBar(content: Text(ok ? '已打开应用内下载页面，请按提示完成安装' : '无法打开下载链接，请稍后再试')),
    );
  }

  void _showAboutDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.bgElevated,
        title: Text('关于我们', style: TextStyle(color: AppTheme.textPrimary)),
        content: FutureBuilder<String>(
          future: _appVersionFuture,
          builder: (context, snapshot) {
            final versionText = snapshot.data ?? '读取版本中...';
            return Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 54,
                      height: 54,
                      decoration: BoxDecoration(
                        color: AppTheme.bgCard,
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Icon(
                        Icons.account_balance_wallet,
                        size: 28,
                        color: AppTheme.accent,
                      ),
                    ),
                    const SizedBox(width: Spacing.md),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '咔咔记账',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.textPrimary,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '当前版本：$versionText',
                            style: TextStyle(color: AppTheme.textSecondary),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: Spacing.md),
                Text(
                  '咔咔记账是一个面向长期投资者的资产记录工具，帮助你把银行卡、A股/港股/美股、基金、房产和负债放到一个页面里统一管理。',
                  style: TextStyle(color: AppTheme.textSecondary, height: 1.4),
                ),
                const SizedBox(height: Spacing.sm),
                Text(
                  '官网：kakawallet.fun',
                  style: TextStyle(color: AppTheme.textSecondary),
                ),
                const SizedBox(height: 6),
                Text(
                  '© 2026 KakaWallet',
                  style: TextStyle(fontSize: 12, color: AppTheme.textTertiary),
                ),
              ],
            );
          },
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('我知道了', style: TextStyle(color: AppTheme.accent)),
          ),
        ],
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
              _buildSettingItem(Icons.feedback_outlined, '问题反馈', _openFeedback),
              const SizedBox(height: Spacing.sm),
              _buildSettingItem(
                Icons.system_update_outlined,
                '检查更新',
                _checkUpdate,
              ),
              const SizedBox(height: Spacing.sm),
              _buildSettingItem(Icons.info_outline, '关于我们', _showAboutDialog),
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
