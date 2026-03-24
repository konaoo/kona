import 'package:flutter/material.dart';

import '../config/theme.dart';

/// 通用的 WebView 页面（当前为占位页面）
class CommonWebViewPage extends StatelessWidget {
  final String title;
  final String? url;

  const CommonWebViewPage({super.key, required this.title, this.url});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPrimary,
      appBar: AppBar(
        title: Text(
          title,
          style: TextStyle(
            color: AppTheme.textPrimary,
            fontSize: 18,
            fontWeight: FontWeight.w600,
          ),
        ),
        backgroundColor: AppTheme.bgPrimary,
        elevation: 0,
        iconTheme: IconThemeData(color: AppTheme.textPrimary),
        centerTitle: true,
      ),
      body: Center(
        child: Text(
          '开发中...',
          style: TextStyle(
            color: AppTheme.textSecondary,
            fontSize: 16,
          ),
        ),
      ),
    );
  }
}
