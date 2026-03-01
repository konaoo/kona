import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:package_info_plus/package_info_plus.dart';

import '../config/theme.dart';
import 'common_webview_page.dart';

/// 关于我们页面
class AboutPage extends StatefulWidget {
  const AboutPage({super.key});

  @override
  State<AboutPage> createState() => _AboutPageState();
}

class _AboutPageState extends State<AboutPage> {
  String _versionInfo = '加载中...';

  @override
  void initState() {
    super.initState();
    _loadAppVersion();
  }

  Future<void> _loadAppVersion() async {
    final info = await PackageInfo.fromPlatform();
    final version = info.version.trim();
    final build = info.buildNumber.trim();
    
    if (!mounted) return;
    
    setState(() {
      if (version.isEmpty) {
        _versionInfo = '当前版本号 未知';
      } else if (build.isEmpty) {
        _versionInfo = '当前版本号 v$version';
      } else {
        _versionInfo = '当前版本号 v$version+$build';
      }
    });
  }

  void _openWebview(String title) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => CommonWebViewPage(title: title),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPrimary,
      appBar: AppBar(
        title: Text(
          '关于App',
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
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 60),
            
            // Logo 区域
            Center(
              child: Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16),
                  color: AppTheme.bgCard,
                ),
                clipBehavior: Clip.antiAlias,
                child: SvgPicture.asset(
                  'assets/images/01_app_icon.svg',
                  fit: BoxFit.cover,
                ),
              ),
            ),
            
            const SizedBox(height: 20),
            
            // 产品名称
            Text(
              '咔咔记账',
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: AppTheme.textPrimary,
              ),
            ),
            
            const SizedBox(height: 8),
            
            // 版本号
            Text(
              _versionInfo,
              style: TextStyle(
                fontSize: 13,
                color: AppTheme.textSecondary,
              ),
            ),
            
            const SizedBox(height: 50),
            
            // 协议卡片
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: Spacing.xl),
              child: Container(
                decoration: BoxDecoration(
                  color: AppTheme.bgCard,
                  borderRadius: BorderRadius.circular(AppRadius.lg),
                ),
                child: Column(
                  children: [
                    _buildProtocolItem('用户协议', isTop: true),
                    Divider(height: 1, color: AppTheme.bgPrimary, indent: 16, endIndent: 16),
                    _buildProtocolItem('隐私协议', isBottom: true),
                  ],
                ),
              ),
            ),
            
            const Spacer(),
            
            // 底部清单与邮件
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                GestureDetector(
                  onTap: () => _openWebview('个人信息收集清单'),
                  child: Text(
                    '《个人信息收集清单》',
                    style: TextStyle(
                      fontSize: 12,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ),
                GestureDetector(
                  onTap: () => _openWebview('第三方信息共享清单'),
                  child: Text(
                    '《第三方信息共享清单》',
                    style: TextStyle(
                      fontSize: 12,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              '联系邮箱: konaeee@gmail.com',
              style: TextStyle(
                fontSize: 12,
                color: AppTheme.textTertiary,
              ),
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _buildProtocolItem(String title, {bool isTop = false, bool isBottom = false}) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => _openWebview(title),
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(isTop ? AppRadius.lg : 0),
          bottom: Radius.circular(isBottom ? AppRadius.lg : 0),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: Spacing.lg, vertical: 20),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                title,
                style: TextStyle(
                  fontSize: 15,
                  color: AppTheme.textPrimary,
                ),
              ),
              Icon(
                Icons.chevron_right,
                size: 18,
                color: AppTheme.textTertiary,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
