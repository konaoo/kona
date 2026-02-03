import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../providers/app_state.dart';

/// 我的页面
class ProfilePage extends StatelessWidget {
  final VoidCallback onLogout;

  const ProfilePage({super.key, required this.onLogout});

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
                    // 头像
                    CircleAvatar(
                      radius: 35,
                      backgroundColor: AppTheme.accent,
                      child: Text(
                        (appState.email?.substring(0, 1).toUpperCase() ?? 'U'),
                        style: const TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                    ),
                    const SizedBox(width: Spacing.lg),
                    // 用户名和邮箱
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '用户 #${appState.userNumber ?? 0}',
                            style: const TextStyle(
                              fontSize: FontSize.xl,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.textPrimary,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            appState.email ?? 'user@example.com',
                            style: const TextStyle(
                              fontSize: 13,
                              color: AppTheme.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.edit, color: AppTheme.textTertiary),
                      onPressed: () {
                        // TODO: 编辑资料
                      },
                    ),
                  ],
                ),
              ),

          const SizedBox(height: Spacing.lg),

          // 设置项
          _buildSettingItem(Icons.settings, '系统设置', () {}),
          const SizedBox(height: Spacing.sm),
          _buildSettingItem(Icons.info_outline, '关于我们', () {
            _showAboutDialog(context);
          }),

          // 退出登录
          const SizedBox(height: 40),
          SizedBox(
            width: double.infinity,
            child: TextButton(
              onPressed: onLogout,
              style: TextButton.styleFrom(
                backgroundColor: AppTheme.bgCard,
                padding: const EdgeInsets.symmetric(vertical: Spacing.lg),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(AppRadius.md),
                ),
              ),
              child: const Text(
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
                  style: const TextStyle(
                    fontSize: 15,
                    color: AppTheme.textPrimary,
                  ),
                ),
              ),
              const Icon(Icons.chevron_right, size: 20, color: AppTheme.textTertiary),
            ],
          ),
        ),
      ),
    );
  }

  void _showAboutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.bgElevated,
        title: const Text('关于我们', style: TextStyle(color: AppTheme.textPrimary)),
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
              child: const Icon(Icons.account_balance_wallet, size: 32, color: AppTheme.accent),
            ),
            const SizedBox(height: Spacing.md),
            const Text(
              '咔咔记账',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: AppTheme.textPrimary,
              ),
            ),
            const Text('v1.0.0', style: TextStyle(color: AppTheme.textSecondary)),
            const SizedBox(height: 10),
            const Text(
              '专注于个人资产管理的极简应用。',
              style: TextStyle(color: AppTheme.textSecondary),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 4),
            const Text(
              '© 2026 Kona Tool',
              style: TextStyle(fontSize: 12, color: AppTheme.textTertiary),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('确定', style: TextStyle(color: AppTheme.accent)),
          ),
        ],
      ),
    );
  }
}
