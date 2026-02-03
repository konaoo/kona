import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../providers/app_state.dart';
import '../widgets/gradient_card.dart';
import '../widgets/asset_card.dart';

/// 首页 - 资产总览
class HomePage extends StatefulWidget {
  final Function(String) onNavigate;
  final Function(int) onSwitchTab;

  const HomePage({
    super.key,
    required this.onNavigate,
    required this.onSwitchTab,
  });

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  @override
  void initState() {
    super.initState();
  }

  Future<void> _refreshData() async {
    final appState = context.read<AppState>();
    await appState.refreshAll();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        return RefreshIndicator(
          onRefresh: _refreshData,
          color: AppTheme.accent,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.symmetric(horizontal: Spacing.xl),
            child: Column(
              children: [
                const SizedBox(height: Spacing.lg),

                // 总资产卡片
                GradientCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // 标题 + 眼睛图标
                      Row(
                        children: [
                          const Text(
                            '总资产估值',
                            style: TextStyle(
                              fontSize: 13,
                              color: AppTheme.textSecondary,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppTheme.bgCard,
                              borderRadius: BorderRadius.circular(6),
                              border: Border.all(color: AppTheme.border, width: 1),
                            ),
                            child: const Text(
                              '￥',
                              style: TextStyle(
                                fontSize: 10,
                                color: AppTheme.textTertiary,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                          IconButton(
                            icon: Icon(
                              appState.amountHidden
                                  ? Icons.visibility_off
                                  : Icons.visibility,
                              size: 18,
                              color: AppTheme.textSecondary,
                            ),
                            onPressed: () => appState.toggleAmountHidden(),
                          ),
                        ],
                      ),

                      // 总资产金额（自动缩放避免溢出）
                      LayoutBuilder(
                        builder: (context, constraints) {
                          return SizedBox(
                            width: constraints.maxWidth,
                            child: FittedBox(
                              fit: BoxFit.scaleDown,
                              alignment: Alignment.centerLeft,
                              child: Text(
                        appState.formatAmount(appState.totalAsset, prefix: ''),
                                style: const TextStyle(
                                  fontSize: FontSize.hero,
                                  fontWeight: FontWeight.bold,
                                  color: AppTheme.textPrimary,
                                ),
                              ),
                            ),
                          );
                        },
                      ),

                      const SizedBox(height: Spacing.xl),

                      // 资产里程碑（三列）
                      Row(
                        children: [
                          _buildMilestone('本月变动', appState.monthChange, appState),
                          _buildMilestone('今年变动', appState.yearChange, appState),
                          _buildMilestone('历史峰值', appState.historyPeak, appState),
                        ],
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: Spacing.xxl),

                // 资产分类卡片
                AssetCard(
                  title: '现金资产',
                  amount: appState.totalCash,
                  icon: Icons.account_balance_wallet,
                  hidden: appState.amountHidden,
                  showCurrency: false,
                  onTap: () => widget.onNavigate('cash_detail'),
                ),
                const SizedBox(height: Spacing.md),

                AssetCard(
                  title: '投资资产',
                  amount: appState.totalInvest,
                  icon: Icons.trending_up,
                  hidden: appState.amountHidden,
                  showCurrency: false,
                  onTap: () => widget.onSwitchTab(1),
                ),
                const SizedBox(height: Spacing.md),

                AssetCard(
                  title: '其他资产',
                  amount: appState.totalOther,
                  icon: Icons.dataset,
                  hidden: appState.amountHidden,
                  showCurrency: false,
                  onTap: () => widget.onNavigate('other_detail'),
                ),
                const SizedBox(height: Spacing.md),

                AssetCard(
                  title: '我的负债',
                  amount: appState.totalLiability,
                  icon: Icons.credit_card,
                  hidden: appState.amountHidden,
                  showCurrency: false,
                  onTap: () => widget.onNavigate('liability_detail'),
                ),

                const SizedBox(height: Spacing.xxl),

                // 添加按钮
                Center(
                  child: ElevatedButton.icon(
                    onPressed: () => _showAddDialog(context),
                    icon: const Icon(Icons.add),
                    label: const Text('记一笔'),
                  ),
                ),

                const SizedBox(height: Spacing.xxl),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildMilestone(String label, double value, AppState appState) {
    final color = value >= 0 ? AppTheme.success : AppTheme.danger;
    final isHistoryPeak = label == '历史峰值';
    final hasBaseline = isHistoryPeak ||
        (label == '本月变动' ? appState.hasMonthBaseline : label == '今年变动' ? appState.hasYearBaseline : true);
    final displayText = hasBaseline ? appState.formatAmount(value, prefix: '') : '--';
    final displayColor = hasBaseline
        ? (isHistoryPeak ? AppTheme.textPrimary : color)
        : AppTheme.textTertiary;

    return Expanded(
      child: Column(
        children: [
          Text(
            label,
            style: const TextStyle(fontSize: 11, color: AppTheme.textTertiary),
          ),
          const SizedBox(height: 4),
          SizedBox(
            width: double.infinity,
            child: FittedBox(
              fit: BoxFit.scaleDown,
              alignment: Alignment.center,
              child: Text(
                displayText,
                style: TextStyle(
                  fontSize: FontSize.lg,
                  fontWeight: FontWeight.w600,
                  color: displayColor,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showAddDialog(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppTheme.bgElevated,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => const AddAssetSheet(),
    );
  }
}

/// 添加资产弹窗
class AddAssetSheet extends StatefulWidget {
  const AddAssetSheet({super.key});

  @override
  State<AddAssetSheet> createState() => _AddAssetSheetState();
}

class _AddAssetSheetState extends State<AddAssetSheet> {
  String _assetType = 'cash';
  final _nameController = TextEditingController();
  final _amountController = TextEditingController();
  bool _saving = false;

  @override
  void dispose() {
    _nameController.dispose();
    _amountController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final name = _nameController.text.trim();
    final amountStr = _amountController.text.trim();

    if (name.isEmpty || amountStr.isEmpty) {
      return;
    }

    final amount = double.tryParse(amountStr);
    if (amount == null) {
      return;
    }

    setState(() => _saving = true);

    // TODO: 调用 API 保存

    setState(() => _saving = false);
    if (mounted) Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: Spacing.xxl,
        right: Spacing.xxl,
        top: Spacing.xxl,
        bottom: MediaQuery.of(context).viewInsets.bottom + Spacing.xxl,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text(
            '记一笔',
            style: TextStyle(
              fontSize: FontSize.xxl,
              fontWeight: FontWeight.bold,
              color: AppTheme.textPrimary,
            ),
          ),
          const SizedBox(height: Spacing.xl),

          // 类型选择
          DropdownButtonFormField<String>(
            value: _assetType,
            dropdownColor: AppTheme.bgCard,
            decoration: const InputDecoration(labelText: '资产类型'),
            items: const [
              DropdownMenuItem(value: 'cash', child: Text('现金资产')),
              DropdownMenuItem(value: 'other', child: Text('其他资产')),
              DropdownMenuItem(value: 'liability', child: Text('我的负债')),
            ],
            onChanged: (value) => setState(() => _assetType = value!),
          ),

          const SizedBox(height: Spacing.lg),

          // 名称
          TextField(
            controller: _nameController,
            style: const TextStyle(color: AppTheme.textPrimary),
            decoration: const InputDecoration(labelText: '资产名称'),
          ),

          const SizedBox(height: Spacing.lg),

          // 金额
          TextField(
            controller: _amountController,
            keyboardType: TextInputType.number,
            style: const TextStyle(color: AppTheme.textPrimary),
            decoration: const InputDecoration(labelText: '金额'),
          ),

          const SizedBox(height: Spacing.xxl),

          // 保存按钮
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _saving ? null : _save,
              child: _saving
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('保存'),
            ),
          ),
        ],
      ),
    );
  }
}
