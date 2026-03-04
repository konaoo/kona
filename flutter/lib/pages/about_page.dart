// 咔咔记账 about_page.dart 重构匹配 ui.html
import 'package:flutter/material.dart';
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

    if (!mounted) return;

    setState(() {
      if (version.isEmpty) {
        _versionInfo = '当前版本号 未知';
      } else {
        _versionInfo = '当前版本号 v$version';
      }
    });
  }

  void _openWebview(String title) {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (context) => CommonWebViewPage(title: title)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isLight = Theme.of(context).brightness == Brightness.light;

    return Scaffold(
      backgroundColor: AppTheme.bgElevated,
      appBar: AppBar(
        title: Text(
          '关于App',
          style: TextStyle(
            color: AppTheme.textPrimary,
            fontSize: 15,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.01,
          ),
        ),
        backgroundColor: AppTheme.bgElevated,
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: Icon(
            Icons.arrow_back_ios_new,
            size: 20,
            color: AppTheme.textPrimary,
          ),
          onPressed: () => Navigator.of(context).pop(),
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(
            color: isLight ? const Color(0x19222C40) : const Color(0x14FFFFFF),
            height: 1,
          ),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 16),
          child: Column(
            children: [
              // Logo 区域 - `.about-app-top`
              Column(
                children: [
                  Container(
                    width: 80,
                    height: 80,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(22),
                      border: Border.all(color: const Color(0x29FFFFFF)),
                      gradient: const LinearGradient(
                        colors: [
                          Color(0xFFFF7B67),
                          Color(0xFFF24688),
                          Color(0xFFF0279E),
                        ],
                        stops: [0.0, 0.55, 1.0],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      boxShadow: const [
                        BoxShadow(
                          color: Color(0x38F0279E),
                          blurRadius: 26,
                          offset: Offset(0, 12),
                        ),
                      ],
                    ),
                    alignment: Alignment.center,
                    child: const Text(
                      'K',
                      style: TextStyle(
                        fontSize: 36,
                        fontWeight: FontWeight.w800,
                        color: Colors.white,
                        letterSpacing: 0.02,
                        height: 1,
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    '咔咔记账',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                      color: AppTheme.textPrimary,
                      letterSpacing: 0.005,
                      height: 1.1,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _versionInfo,
                    style: TextStyle(
                      fontSize: 12,
                      color: AppTheme.textSecondary,
                      letterSpacing: 0.01,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 32),

              // 协议卡片 - `.about-app-card`
              Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppTheme.borderSubtle),
                  color: AppTheme.bgCard,
                  boxShadow: isLight
                      ? const [
                          BoxShadow(
                            color: Color(0x14222C48),
                            blurRadius: 14,
                            offset: Offset(0, 4),
                          ),
                        ]
                      : const [
                          BoxShadow(
                            color: Color(0x38000000),
                            blurRadius: 28,
                            offset: Offset(0, 12),
                          ),
                        ],
                ),
                child: Column(
                  children: [
                    _buildProtocolItem('用户协议', isTop: true, isLight: isLight),
                    Container(height: 1, color: AppTheme.borderDivider),
                    _buildProtocolItem(
                      '隐私协议',
                      isBottom: true,
                      isLight: isLight,
                    ),
                  ],
                ),
              ),

              const Spacer(),

              // 底部清单与邮件 - `.about-app-footer`
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Column(
                  children: [
                    Wrap(
                      alignment: WrapAlignment.center,
                      spacing: 10,
                      runSpacing: 10,
                      children: [
                        GestureDetector(
                          onTap: () => _openWebview('个人信息收集清单'),
                          child: Text(
                            '《个人信息收集清单》',
                            style: TextStyle(
                              fontSize: 11,
                              color: AppTheme.textSecondary,
                            ),
                          ),
                        ),
                        GestureDetector(
                          onTap: () => _openWebview('第三方信息共享清单'),
                          child: Text(
                            '《第三方信息共享清单》',
                            style: TextStyle(
                              fontSize: 11,
                              color: AppTheme.textSecondary,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Text(
                      '联系邮箱: konaeee@gmail.com',
                      style: TextStyle(
                        fontSize: 11,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProtocolItem(
    String title, {
    bool isTop = false,
    bool isBottom = false,
    required bool isLight,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => _openWebview(title),
        splashColor: isLight
            ? const Color(0x0A222C40)
            : const Color(0x0AFFFFFF),
        highlightColor: isLight
            ? const Color(0x0A222C40)
            : const Color(0x0AFFFFFF),
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(isTop ? 14 : 0),
          bottom: Radius.circular(isBottom ? 14 : 0),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                title,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textPrimary,
                ),
              ),
              Icon(
                Icons.chevron_right_rounded,
                size: 18,
                color: AppTheme.textSecondary,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
