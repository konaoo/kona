import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../providers/app_state.dart';
import '../widgets/gradient_card.dart';

/// 投资页面 - 持仓列表
class InvestPage extends StatefulWidget {
  const InvestPage({super.key});

  @override
  State<InvestPage> createState() => _InvestPageState();
}

class _InvestPageState extends State<InvestPage> {
  @override
  void initState() {
    super.initState();
  }

  Future<void> _loadData() async {
    await context.read<AppState>().refreshHomeData();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, child) {
        return RefreshIndicator(
          onRefresh: _loadData,
          color: AppTheme.accent,
          child: CustomScrollView(
            slivers: [
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.all(Spacing.xl),
                  child: Column(
                    children: [
                      // 汇总卡片
                      GradientCard(
                        padding: Spacing.xl,
                        child: Column(
                          children: [
                            // 总市值
                            Row(
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        children: [
                                          const Text(
                                            '总市值',
                                            style: TextStyle(
                                              fontSize: FontSize.base,
                                              color: AppTheme.textTertiary,
                                            ),
                                          ),
                                          IconButton(
                                            icon: Icon(
                                              appState.amountHidden
                                                  ? Icons.visibility_off
                                                  : Icons.visibility,
                                              size: 16,
                                              color: AppTheme.textSecondary,
                                            ),
                                            onPressed: () => appState.toggleAmountHidden(),
                                          ),
                                        ],
                                      ),
                                      Text(
                                        appState.formatAmount(appState.investTotalMV, prefix: ''),
                                        style: const TextStyle(
                                          fontSize: FontSize.hero,
                                          fontWeight: FontWeight.bold,
                                          color: AppTheme.textPrimary,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    const Text(
                                      '今日盈亏',
                                      style: TextStyle(
                                        fontSize: 11,
                                        color: AppTheme.textTertiary,
                                      ),
                                    ),
                                    Text(
                                      appState.formatPnl(appState.investDayPnl),
                                      style: TextStyle(
                                        fontSize: FontSize.lg,
                                        color: AppState.getPnlColor(appState.investDayPnl),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                            const SizedBox(height: Spacing.md),
                            const Divider(color: AppTheme.border),
                            const SizedBox(height: Spacing.md),
                            // 持仓盈亏
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceAround,
                              children: [
                                _buildStat('持仓盈亏', appState.formatPnl(appState.investHoldingPnl), AppState.getPnlColor(appState.investHoldingPnl)),
                                _buildStat('持仓盈亏率', appState.formatPct(_calculateHoldingPnlRate(appState)), _getHoldingPnlRateColor(appState)),
                                _buildStat('累计盈亏', appState.formatPnl(appState.investHoldingPnl), AppState.getPnlColor(appState.investHoldingPnl)),
                                _buildStat('累计盈亏率', appState.formatPct(_calculateHoldingPnlRate(appState)), _getHoldingPnlRateColor(appState)),
                              ],
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: Spacing.md),
                      // 分类标签
                      _buildCategoryTabs(appState),
                    ],
                  ),
                ),
              ),
              // 持仓列表表头
              if (appState.filteredPortfolio.isNotEmpty)
                SliverToBoxAdapter(
                  child: Container(
                    margin: const EdgeInsets.fromLTRB(Spacing.xl, Spacing.md, Spacing.xl, 4),
                    padding: const EdgeInsets.symmetric(horizontal: Spacing.md, vertical: Spacing.sm),
                    child: Row(
                      children: const [
                        SizedBox(
                          width: 80,
                          child: Text('名称', style: TextStyle(fontSize: FontSize.xs, color: AppTheme.textTertiary)),
                        ),
                        Expanded(child: Text('市值', style: TextStyle(fontSize: FontSize.xs, color: AppTheme.textTertiary))),
                        Expanded(child: Text('现价', style: TextStyle(fontSize: FontSize.xs, color: AppTheme.textTertiary))),
                        Expanded(
                          child: Text('盈亏', textAlign: TextAlign.end, style: TextStyle(fontSize: FontSize.xs, color: AppTheme.textTertiary)),
                        ),
                      ],
                    ),
                  ),
                ),
              // 持仓列表
              if (appState.filteredPortfolio.isEmpty)
                SliverFillRemaining(
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.business_center, size: 48, color: AppTheme.textTertiary),
                        const SizedBox(height: Spacing.md),
                        const Text('暂无持仓', style: TextStyle(color: AppTheme.textSecondary)),
                      ],
                    ),
                  ),
                )
              else
                SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (context, index) {
                      final item = appState.filteredPortfolio[index];
                      final priceInfo = appState.prices[item.code];
                      return _buildPortfolioCard(item, priceInfo, appState);
                    },
                    childCount: appState.filteredPortfolio.length,
                  ),
                ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildStat(String label, String value, Color color) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontSize: FontSize.xs, color: AppTheme.textTertiary)),
        const SizedBox(height: 2),
        Text(value, style: TextStyle(fontSize: FontSize.lg, color: color)),
      ],
    );
  }

  Widget _buildCategoryTabs(AppState appState) {
    final categories = [
      ('all', '全部'),
      ('a', 'A股'),
      ('us', '美股'),
      ('hk', '港股'),
      ('fund', '基金'),
    ];

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: categories.map((cat) {
          final isSelected = appState.currentCategory == cat.$1;
          return Padding(
            padding: const EdgeInsets.only(right: Spacing.sm),
            child: Material(
              color: isSelected ? AppTheme.accent : Colors.transparent,
              borderRadius: BorderRadius.circular(AppRadius.xxl),
              child: InkWell(
                onTap: () => appState.setCategory(cat.$1),
                borderRadius: BorderRadius.circular(AppRadius.xxl),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: Spacing.lg, vertical: Spacing.sm),
                  child: Text(
                    cat.$2,
                    style: TextStyle(
                      fontSize: FontSize.lg,
                      fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                      color: isSelected ? AppTheme.textPrimary : AppTheme.textTertiary,
                    ),
                  ),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildPortfolioCard(dynamic item, dynamic priceInfo, AppState appState) {
    // 检查价格数据是否有效
    final hasValidPrice = priceInfo != null && priceInfo.price > 0;
    final currentPrice = hasValidPrice ? priceInfo.price : item.price;
    final mv = currentPrice * item.qty;
    final costTotal = item.price * item.qty;
    final holdingPnl = mv - costTotal + item.adjustment;
    final holdingPnlPct = costTotal > 0 ? (holdingPnl / costTotal * 100) : 0.0;
    final pnlColor = AppState.getPnlColor(holdingPnl);

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: Spacing.xl, vertical: 4),
      padding: const EdgeInsets.all(Spacing.md),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(AppRadius.md),
      ),
      child: Row(
        children: [
          // 名称
          SizedBox(
            width: 80,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.name.length > 5 ? '${item.name.substring(0, 5)}…' : item.name,
                  style: const TextStyle(
                    fontSize: FontSize.base,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary,
                  ),
                ),
                Text(
                  item.code,
                  style: const TextStyle(fontSize: FontSize.sm, color: AppTheme.textTertiary),
                ),
              ],
            ),
          ),
          // 市值
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  appState.formatAmount(mv, prefix: item.currencySymbol),
                  style: const TextStyle(fontSize: FontSize.md, color: AppTheme.textPrimary),
                ),
                Text(
                  '${item.qty.toStringAsFixed(0)}',
                  style: const TextStyle(fontSize: FontSize.xs, color: AppTheme.textTertiary),
                ),
              ],
            ),
          ),
          // 现价
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${item.currencySymbol}${currentPrice.toStringAsFixed(2)}',
                  style: const TextStyle(fontSize: FontSize.md, color: AppTheme.textPrimary),
                ),
                Text(
                  '${item.currencySymbol}${item.price.toStringAsFixed(2)}',
                  style: const TextStyle(fontSize: FontSize.xs, color: AppTheme.textTertiary),
                ),
              ],
            ),
          ),
          // 盈亏
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  appState.formatPnl(holdingPnl),
                  style: TextStyle(fontSize: FontSize.md, fontWeight: FontWeight.w600, color: pnlColor),
                ),
                Text(
                  appState.formatPct(holdingPnlPct),
                  style: TextStyle(fontSize: FontSize.xs, color: pnlColor),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // 计算持仓盈亏率
  double _calculateHoldingPnlRate(AppState appState) {
    double totalCost = 0;
    double totalPnl = 0;

    for (var item in appState.portfolio) {
      final priceInfo = appState.prices[item.code];
      final currentPrice = priceInfo?.price ?? item.price;
      final cost = item.price * item.qty;
      final mv = currentPrice * item.qty;
      totalCost += cost;
      totalPnl += (mv - cost + item.adjustment);
    }

    return totalCost > 0 ? (totalPnl / totalCost * 100) : 0.0;
  }

  // 获取盈亏率颜色
  Color _getHoldingPnlRateColor(AppState appState) {
    final rate = _calculateHoldingPnlRate(appState);
    return AppState.getPnlColor(rate);
  }
}
