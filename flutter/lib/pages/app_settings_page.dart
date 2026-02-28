import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../config/theme.dart';
import '../providers/app_state.dart';

class AppSettingsPage extends StatefulWidget {
  final VoidCallback onLogout;

  const AppSettingsPage({super.key, required this.onLogout});

  @override
  State<AppSettingsPage> createState() => _AppSettingsPageState();
}

class _AppSettingsPageState extends State<AppSettingsPage> {
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

  void _showAboutDialog() {
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
              child: Icon(
                Icons.account_balance_wallet,
                size: 32,
                color: AppTheme.accent,
              ),
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

  Widget _buildSettingItem({
    required IconData icon,
    required String title,
    required VoidCallback onTap,
  }) {
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
            child: Text(
              '切换主题',
              style: TextStyle(
                fontSize: 15,
                color: AppTheme.textPrimary,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          Switch(
            value: appState.isLightTheme,
            onChanged: (_) => appState.toggleTheme(),
            activeThumbColor: AppTheme.accent,
          ),
        ],
      ),
    );
  }

  Widget _buildBiometricToggle(AppState appState) {
    return Container(
      padding: const EdgeInsets.all(Spacing.lg),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(AppRadius.lg),
      ),
      child: Row(
        children: [
          Icon(Icons.fingerprint, size: 20, color: AppTheme.accentLight),
          const SizedBox(width: Spacing.md),
          Expanded(
            child: Text(
              '生物识别登录',
              style: TextStyle(
                fontSize: 15,
                color: AppTheme.textPrimary,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          Switch(
            value: appState.biometricEnabled,
            onChanged: (v) async {
              final ok = await appState.setBiometricEnabled(v);
              if (!ok && mounted) {
                ScaffoldMessenger.of(
                  context,
                ).showSnackBar(const SnackBar(content: Text('当前设备不可用生物识别')));
              }
            },
            activeThumbColor: AppTheme.accent,
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) => Scaffold(
        appBar: AppBar(title: const Text('系统设置')),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(Spacing.xl),
          child: Column(
            children: [
              _buildThemeToggle(appState),
              const SizedBox(height: Spacing.sm),
              _buildBiometricToggle(appState),
              const SizedBox(height: Spacing.sm),
              _buildSettingItem(
                icon: Icons.lock_reset,
                title: '修改密码',
                onTap: () => _changePassword(appState),
              ),
              const SizedBox(height: Spacing.sm),
              _buildSettingItem(
                icon: Icons.system_update_outlined,
                title: '检查更新',
                onTap: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('检查更新功能建设中，敬请期待')),
                  );
                },
              ),
              const SizedBox(height: Spacing.sm),
              _buildSettingItem(
                icon: Icons.info_outline,
                title: '关于我们',
                onTap: _showAboutDialog,
              ),
              const SizedBox(height: 40),
              SizedBox(
                width: double.infinity,
                child: TextButton(
                  onPressed: () {
                    Navigator.of(
                      context,
                      rootNavigator: true,
                    ).popUntil((route) => route.isFirst);
                    widget.onLogout();
                  },
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
        ),
      ),
    );
  }
}
