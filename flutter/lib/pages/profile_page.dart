import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../providers/app_state.dart';

/// 我的页面
class ProfilePage extends StatefulWidget {
  final VoidCallback onLogout;

  const ProfilePage({super.key, required this.onLogout});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  final ImagePicker _picker = ImagePicker();
  Future<void> _pickAvatar(AppState appState) async {
    try {
      final file = await _picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 85,
        maxWidth: 512,
        maxHeight: 512,
      );
      if (file == null) return;
      final bytes = await File(file.path).readAsBytes();
      final base64Str = base64Encode(bytes);
      await appState.updateProfile(avatar: base64Str);
    } catch (e) {
      debugPrint('选择头像失败: $e');
    }
  }

  Future<void> _removeAvatar(AppState appState) async {
    await appState.updateProfile(avatar: '');
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
    await appState.updateProfile(nickname: newName);
  }

  Widget _buildAvatar(AppState appState) {
    final fallback = (appState.nickname?.isNotEmpty == true
            ? appState.nickname!.substring(0, 1)
            : (appState.email?.substring(0, 1).toUpperCase() ?? 'U'))
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
    return GestureDetector(
      onTap: () => _pickAvatar(appState),
      onLongPress: () => _removeAvatar(appState),
      child: Stack(
        children: [
          CircleAvatar(
            radius: 35,
            backgroundColor: AppTheme.accent,
            backgroundImage: hasAvatar ? MemoryImage(avatarBytes!) : null,
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
              child: Icon(Icons.camera_alt, size: 12, color: AppTheme.textSecondary),
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
                                : '用户 #${appState.userNumber ?? 0}',
                            style: TextStyle(
                              fontSize: FontSize.xl,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.textPrimary,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            appState.email ?? 'user@example.com',
                            style: TextStyle(
                              fontSize: 13,
                              color: AppTheme.textSecondary,
                            ),
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
              _buildThemeToggle(appState),
              const SizedBox(height: Spacing.sm),
              _buildSettingItem(Icons.settings, '系统设置', () {}),
              const SizedBox(height: Spacing.sm),
              _buildSettingItem(Icons.info_outline, '关于我们', () {
                _showAboutDialog(context);
              }),

              const SizedBox(height: 40),
              SizedBox(
                width: double.infinity,
                child: TextButton(
                  onPressed: widget.onLogout,
                  style: TextButton.styleFrom(
                    backgroundColor: AppTheme.bgCard,
                    padding: const EdgeInsets.symmetric(vertical: Spacing.lg),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(AppRadius.md),
                    ),
                  ),
                  child: Text(
                    '退出登录',
                    style: TextStyle(
                      fontSize: FontSize.lg,
                      color: AppTheme.danger,
                    ),
                  ),
                ),
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
                  style: TextStyle(
                    fontSize: 15,
                    color: AppTheme.textPrimary,
                  ),
                ),
              ),
              Icon(Icons.chevron_right, size: 20, color: AppTheme.textTertiary),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildThemeToggle(AppState appState) {
    return Container(
      padding: const EdgeInsets.all(Spacing.lg),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(AppRadius.lg),
      ),
      child: Row(
        children: [
          Icon(Icons.palette_outlined, size: 20, color: AppTheme.accentLight),
          const SizedBox(width: Spacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '切换主题',
                  style: TextStyle(
                    fontSize: 15,
                    color: AppTheme.textPrimary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  '浅色 / 暗黑',
                  style: TextStyle(
                    fontSize: 12,
                    color: AppTheme.textTertiary,
                  ),
                ),
              ],
            ),
          ),
          Switch(
            value: appState.isLightTheme,
            onChanged: (_) => appState.toggleTheme(),
            activeColor: AppTheme.accent,
          ),
        ],
      ),
    );
  }

  void _showAboutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.bgElevated,
        title: Text('关于我们', style: TextStyle(color: AppTheme.textPrimary)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                color: AppTheme.bgCard,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(Icons.account_balance_wallet, size: 32, color: AppTheme.accent),
            ),
            const SizedBox(height: Spacing.md),
            Text(
              '咔咔记账',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: AppTheme.textPrimary,
              ),
            ),
            Text('v1.0.0', style: TextStyle(color: AppTheme.textSecondary)),
            const SizedBox(height: 10),
            Text(
              '专注于个人资产管理的极简应用。',
              style: TextStyle(color: AppTheme.textSecondary),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 4),
            Text(
              '© 2026 Kona Tool',
              style: TextStyle(fontSize: 12, color: AppTheme.textTertiary),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('确定', style: TextStyle(color: AppTheme.accent)),
          ),
        ],
      ),
    );
  }
}
