import 'package:flutter/material.dart';
import '../config/theme.dart';

/// 渐变卡片组件
class GradientCard extends StatelessWidget {
  final Widget child;
  final double padding;

  const GradientCard({
    super.key,
    required this.child,
    this.padding = Spacing.xxl,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(padding),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: AppTheme.cardGradient,
        ),
        borderRadius: BorderRadius.circular(AppRadius.xxl),
      ),
      child: child,
    );
  }
}
