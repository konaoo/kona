import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../providers/app_state.dart';
import '../models/asset.dart';
import '../widgets/add_asset_dialog.dart';

/// 资产详情页面
class AssetDetailPage extends StatelessWidget {
  final String assetType; // 'cash', 'other', 'liability'

  const AssetDetailPage({super.key, required this.assetType});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPrimary,
      appBar: AppBar(
        backgroundColor: AppTheme.bgPrimary,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppTheme.textPrimary),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          _getTitle(),
          style: const TextStyle(color: AppTheme.textPrimary),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        heroTag: 'add_asset_detail_$assetType',
        onPressed: () => _showAddDialog(context),
        backgroundColor: AppTheme.accent,
        child: const Icon(Icons.add, color: AppTheme.textPrimary),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.endFloat,
      body: Consumer<AppState>(
        builder: (context, appState, child) {
          final assets = _getAssets(appState);

          if (assets.isEmpty) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    _getIcon(),
                    size: 64,
                    color: AppTheme.textTertiary,
                  ),
                  const SizedBox(height: Spacing.lg),
                  Text(
                    '暂无${_getTitle()}',
                    style: const TextStyle(
                      fontSize: FontSize.lg,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ],
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(Spacing.xl),
            itemCount: assets.length,
            itemBuilder: (context, index) {
              final asset = assets[index];
              return _buildAssetItem(context, asset, appState);
            },
          );
        },
      ),
    );
  }

  String _getTitle() {
    switch (assetType) {
      case 'cash':
        return '现金资产';
      case 'other':
        return '其他资产';
      case 'liability':
        return '我的负债';
      default:
        return '资产详情';
    }
  }

  IconData _getIcon() {
    switch (assetType) {
      case 'cash':
        return Icons.account_balance_wallet;
      case 'other':
        return Icons.dataset;
      case 'liability':
        return Icons.credit_card;
      default:
        return Icons.attach_money;
    }
  }

  List<Asset> _getAssets(AppState appState) {
    switch (assetType) {
      case 'cash':
        return appState.cashAssets;
      case 'other':
        return appState.otherAssets;
      case 'liability':
        return appState.liabilities;
      default:
        return [];
    }
  }

  Widget _buildAssetItem(BuildContext context, Asset asset, AppState appState) {
    return Container(
      margin: const EdgeInsets.only(bottom: Spacing.md),
      padding: const EdgeInsets.all(Spacing.lg),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(AppRadius.lg),
      ),
      child: Row(
        children: [
          // 图标
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: AppTheme.accent.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              _getIcon(),
              color: AppTheme.accent,
              size: 24,
            ),
          ),
          const SizedBox(width: Spacing.lg),
          // 名称和金额
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  asset.name,
                  style: const TextStyle(
                    fontSize: FontSize.lg,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  asset.amount.toStringAsFixed(2),
                  style: const TextStyle(
                    fontSize: FontSize.base,
                    color: AppTheme.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          // 删除按钮
          IconButton(
            icon: const Icon(Icons.delete_outline, color: AppTheme.danger),
            onPressed: () => _showDeleteDialog(context, asset, appState),
          ),
        ],
      ),
    );
  }

  void _showDeleteDialog(BuildContext context, Asset asset, AppState appState) {
    if (asset.id == null) return;
    showDialog(
      context: context,
      barrierColor: Colors.black.withOpacity(0.5),
      builder: (context) {
        return AlertDialog(
          backgroundColor: AppTheme.bgElevated,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          title: const Text(
            '删除资产',
            style: TextStyle(color: AppTheme.textPrimary),
          ),
          content: Text(
            '确定删除「${asset.name}」吗？',
            style: const TextStyle(color: AppTheme.textSecondary),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('取消'),
            ),
            TextButton(
              onPressed: () async {
                final ok = await appState.deleteAsset(
                  type: assetType,
                  id: asset.id!,
                );
                if (context.mounted) {
                  Navigator.pop(context);
                  if (!ok) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('删除失败，请稍后重试')),
                    );
                  }
                }
              },
              child: const Text(
                '删除',
                style: TextStyle(color: AppTheme.danger),
              ),
            ),
          ],
        );
      },
    );
  }

  void _showAddDialog(BuildContext context) {
    showDialog(
      context: context,
      barrierColor: Colors.black.withOpacity(0.5),
      builder: (context) => AddAssetDialog(fixedAssetType: assetType),
    );
  }
}
