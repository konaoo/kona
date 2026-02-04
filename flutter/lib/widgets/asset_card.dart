import 'package:flutter/material.dart';
import '../config/theme.dart';

/// 资产卡片组件
class AssetCard extends StatelessWidget {
  final String title;
  final double amount;
  final IconData icon;
  final bool hidden;
  final bool showCurrency;
  final VoidCallback? onTap;

  const AssetCard({
    super.key,
    required this.title,
    required this.amount,
    required this.icon,
    this.hidden = false,
    this.showCurrency = true,
    this.onTap,
  });

  String _formatAmount(double value) {
    if (hidden) return '****';
    if (value == 0) return '--';
    final prefix = showCurrency ? '¥' : '';
    return '$prefix${value.toStringAsFixed(0).replaceAllMapped(
      RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
      (Match m) => '${m[1]},',
    )}';
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppTheme.bgCard,
      borderRadius: BorderRadius.circular(AppRadius.lg),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        child: Container(
          padding: const EdgeInsets.all(Spacing.lg),
          decoration: BoxDecoration(
            border: Border.all(
              color: AppTheme.border.withOpacity(AppTheme.isLight ? 0.7 : 0.4),
              width: 1,
            ),
            borderRadius: BorderRadius.circular(AppRadius.lg),
            boxShadow: AppTheme.cardShadow,
          ),
          child: Row(
            children: [
              Icon(icon, size: 20, color: AppTheme.accent),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        fontSize: FontSize.base,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _formatAmount(amount),
                      style: TextStyle(
                        fontSize: FontSize.xl,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(
                Icons.chevron_right,
                size: 24,
                color: AppTheme.textTertiary,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
