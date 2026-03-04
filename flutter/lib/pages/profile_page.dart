import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:gal/gal.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:path_provider/path_provider.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../config/theme.dart';
import '../models/app_version.dart';
import '../providers/app_state.dart';
import '../widgets/profile_custom_dialog.dart';
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
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(child: CircularProgressIndicator()),
    );

    try {
      final appState = context.read<AppState>();
      final config = await appState.apiService.getWebConfig();
      if (!mounted) return;
      Navigator.of(context).pop();

      final opsText = config?['user_group_text']?.toString().trim() ?? '';
      final imageUrl = config?['user_group_image_url']?.toString().trim() ?? '';

      showDialog(
        context: context,
        builder: (context) => ProfileCustomDialog(
          title: '咔咔用户群',
          subTitle: '',
          showClose: false,
          showDivider: true,
          primaryText: '保存二维码',
          onPrimary: imageUrl.isEmpty ? null : () async {
            final scaffoldMessenger = ScaffoldMessenger.of(context);
            try {
              final response = await http.get(Uri.parse(imageUrl)).timeout(const Duration(seconds: 15));
              if (response.statusCode == 200) {
                // 先保存到本地临时文件，再保存到相册，增加兼容性
                final tempDir = await getTemporaryDirectory();
                final tempFile = File('${tempDir.path}/kaka_qr_${DateTime.now().millisecondsSinceEpoch}.png');
                await tempFile.writeAsBytes(response.bodyBytes);
                
                await Gal.putImage(tempFile.path);
                
                scaffoldMessenger.showSnackBar(
                  const SnackBar(content: Text('二维码已保存至相册')),
                );
              } else {
                scaffoldMessenger.showSnackBar(
                  SnackBar(content: Text('下载失败: HTTP ${response.statusCode}')),
                );
              }
            } catch (e) {
              debugPrint('保存图片失败: $e');
              scaffoldMessenger.showSnackBar(
                SnackBar(content: Text('保存失败: $e')),
              );
            }
          },
          body: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: appState.isLightTheme
                  ? Colors.white
                  : const Color(0xFF1F2A3D),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: appState.isLightTheme
                    ? const Color.fromRGBO(91, 141, 239, 0.20)
                    : const Color.fromRGBO(34, 44, 64, 0.10),
              ),
              boxShadow: appState.isLightTheme
                  ? const [
                      BoxShadow(
                        color: Color.fromRGBO(34, 44, 72, 0.10),
                        blurRadius: 20,
                        offset: Offset(0, 8),
                      ),
                    ]
                  : const [
                      BoxShadow(
                        color: Color.fromRGBO(0, 0, 0, 0.26),
                        blurRadius: 22,
                        offset: Offset(0, 10),
                      ),
                    ],
            ),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
              decoration: BoxDecoration(
                color: appState.isLightTheme
                    ? const Color.fromRGBO(34, 44, 64, 0.05)
                    : const Color.fromRGBO(255, 255, 255, 0.02),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: appState.isLightTheme
                      ? const Color.fromRGBO(34, 44, 64, 0.10)
                      : const Color.fromRGBO(255, 255, 255, 0.05),
                ),
              ),
              child: Row(
                children: [
                  // 二维码区域
                  Container(
                    width: 104,
                    height: 104,
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: const Color.fromRGBO(255, 255, 255, 0.2),
                      ),
                    ),
                    alignment: Alignment.center,
                    child: imageUrl.isNotEmpty
                        ? ClipRRect(
                            borderRadius: BorderRadius.circular(4),
                            child: Image.network(
                              imageUrl,
                              width: 92,
                              height: 92,
                              fit: BoxFit.contain,
                              errorBuilder: (_, __, ___) => const Icon(
                                Icons.qr_code_2,
                                size: 80,
                                color: Colors.black,
                              ),
                            ),
                          )
                        : const Icon(
                            Icons.qr_code_2,
                            size: 80,
                            color: Colors.black,
                          ),
                  ),
                  const SizedBox(width: 16),
                  // 文案区域
                  Expanded(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (opsText.isNotEmpty)
                          Text(
                            opsText,
                            style: TextStyle(
                              fontSize: 11,
                              color: AppTheme.textSecondary,
                              height: 1.45,
                              fontWeight: FontWeight.w400,
                            ),
                          ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('获取运营配置失败: $e')),
      );
    }
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
      builder: (dialogContext) => ProfileCustomDialog(
        title: '发现新版本 v${version.version}',
        subTitle: '本次升级包含以下优化内容',
        ghostText: '稍后再说',
        onGhost: () => Navigator.of(dialogContext).pop(),
        primaryText: '立即升级',
        onPrimary: () async {
          final urlText = version.downloadUrl.trim();
          final uri = Uri.tryParse(urlText);
          if (uri == null ||
              uri.host.isEmpty ||
              !(uri.scheme == 'http' || uri.scheme == 'https')) {
            if (!mounted) return;
            ScaffoldMessenger.of(
              context,
            ).showSnackBar(const SnackBar(content: Text('下载链接不可用')));
            return;
          }
          Navigator.of(dialogContext).pop();
          final ok = await _openExternalUrl(
            uri,
            LaunchMode.externalApplication,
          );
          if (!ok && mounted) {
            ScaffoldMessenger.of(
              context,
            ).showSnackBar(const SnackBar(content: Text('无法打开下载链接')));
          }
        },
        body: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: context.read<AppState>().isLightTheme
                ? const Color.fromRGBO(34, 44, 64, 0.05)
                : const Color.fromRGBO(255, 255, 255, 0.02),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: context.read<AppState>().isLightTheme
                  ? const Color.fromRGBO(34, 44, 64, 0.09)
                  : const Color.fromRGBO(255, 255, 255, 0.05),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '更新内容',
                style: TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                version.releaseNotes.trim().isEmpty
                    ? '修复已知问题，优化使用体验。'
                    : version.releaseNotes,
                style: TextStyle(
                  color: AppTheme.textSecondary,
                  fontSize: 13,
                  height: 1.5,
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
      builder: (context) => ProfileCustomDialog(
        title: '修改昵称',
        subTitle: '将用于我的页面顶部展示',
        ghostText: '取消',
        primaryText: '保存',
        onPrimary: () => Navigator.pop(context, controller.text.trim()),
        body: ProfileCustomInput(
          controller: controller,
          hintText: '请输入昵称',
          maxLength: 16,
          autofocus: true,
        ),
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
      builder: (context) => ProfileCustomDialog(
        title: '修改密码',
        subTitle: '请输入原密码与新密码后提交',
        ghostText: '取消',
        primaryText: '提交',
        onPrimary: () => Navigator.pop(context, true),
        body: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ProfileCustomInput(
              controller: oldCtrl,
              hintText: '原密码',
              obscureText: true,
            ),
            const SizedBox(height: 12),
            ProfileCustomInput(
              controller: newCtrl,
              hintText: '新密码（至少 6 位）',
              obscureText: true,
            ),
            const SizedBox(height: 12),
            ProfileCustomInput(
              controller: confirmCtrl,
              hintText: '确认新密码',
              obscureText: true,
            ),
          ],
        ),
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
            width: 56, // matching 56px in new ui.html
            height: 56,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: const Color.fromRGBO(171, 203, 255, 0.46),
              ),
              gradient: const LinearGradient(
                colors: [Color(0xFF6B98F7), Color(0xFF4A7BE0)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              boxShadow: const [
                BoxShadow(
                  color: Color.fromRGBO(61, 103, 198, 0.4),
                  blurRadius: 24,
                  offset: Offset(0, 12),
                ),
              ],
              image: hasAvatar
                  ? DecorationImage(image: avatarImage!, fit: BoxFit.cover)
                  : null,
            ),
            alignment: Alignment.center,
            child: hasAvatar
                ? null
                : Text(
                    fallback,
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
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
              Stack(
                clipBehavior: Clip.none,
                children: [_buildAvatar(appState)],
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      name,
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w600,
                        color: appState.isLightTheme
                            ? const Color(0xFF1F2A3D)
                            : const Color(0xFFE6EBF7),
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 5),
                    Text(
                      '已在咔咔记录 $days天',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w400,
                        letterSpacing: 0.01,
                        color: appState.isLightTheme
                            ? const Color(0xFF55617B)
                            : const Color(0xB5FFFFFF),
                      ),
                    ),
                  ],
                ),
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
              activeColor: Colors.white,
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
              activeColor: Colors.white,
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
