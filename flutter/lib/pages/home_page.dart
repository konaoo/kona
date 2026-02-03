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
                          const Text(
                            '￥',
                            style: TextStyle(
                              fontSize: 11,
                              color: AppTheme.textTertiary,
                              fontWeight: FontWeight.w500,
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

}
