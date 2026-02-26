import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../providers/app_state.dart';
import '../widgets/gradient_card.dart';
import '../widgets/asset_card.dart';
import '../widgets/fab_scroll_visibility_controller.dart';

/// 首页 - 资产总览
class HomePage extends StatefulWidget {
  final Function(String) onNavigate;
  final Function(int) onSwitchTab;
  final ValueChanged<bool>? onFabVisibilityChanged;

  const HomePage({
    super.key,
    required this.onNavigate,
    required this.onSwitchTab,
    this.onFabVisibilityChanged,
  });

  @override
  State<HomePage> createState() => HomePageState();
}

class HomePageState extends State<HomePage> {
  final FabScrollVisibilityController _fabVisibilityController =
      FabScrollVisibilityController();

  @override
  void initState() {
    super.initState();
  }

  Future<void> _refreshData() async {
    final appState = context.read<AppState>();
    await appState.refreshAll(force: true);
  }

  void resetFabVisibilityController() {
    _fabVisibilityController.resetVisible();
    widget.onFabVisibilityChanged?.call(true);
  }

  bool _onScrollNotification(ScrollNotification notification) {
    final callback = widget.onFabVisibilityChanged;
    if (callback == null) return false;

    if (notification is ScrollUpdateNotification) {
      final delta = notification.scrollDelta;
      if (delta != null) {
        final next = _fabVisibilityController.onScrollUpdate(delta);
        if (next != null) {
          callback(next);
        }
      }
      return false;
    }

    if (notification is UserScrollNotification &&
        notification.direction == ScrollDirection.idle) {
      _fabVisibilityController.onScrollIdle();
    }
    return false;
  }

  double _bottomContentPadding(BuildContext context) {
    final safeBottom = MediaQuery.of(context).padding.bottom;
    const navBarHeight = 60.0;
    const fabRegion = 76.0;
    return navBarHeight + safeBottom + fabRegion;
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        return RefreshIndicator(
          onRefresh: _refreshData,
          color: AppTheme.accent,
          child: NotificationListener<ScrollNotification>(
            onNotification: _onScrollNotification,
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: EdgeInsets.fromLTRB(
                Spacing.xl,
                0,
                Spacing.xl,
                _bottomContentPadding(context),
              ),
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
                            Text(
                              '总资产估值',
                              style: TextStyle(
                                fontSize: 13,
                                color: AppTheme.textSecondary,
                              ),
                            ),
                            const SizedBox(width: 6),
                            Text(
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
                                  appState.formatAmount(
                                    appState.totalAsset,
                                    prefix: '',
                                  ),
                                  style: TextStyle(
                                    fontSize: FontSize.hero,
                                    fontWeight: FontWeight.bold,
                                    color: AppTheme.textPrimary,
                                  ),
                                ),
                              ),
                            );
                          },
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
          ),
        );
      },
    );
  }


}
