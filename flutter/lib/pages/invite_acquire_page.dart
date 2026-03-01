import 'package:flutter/material.dart';

import '../config/theme.dart';
import '../services/api_service.dart';

class InviteAcquirePage extends StatefulWidget {
  const InviteAcquirePage({super.key});

  @override
  State<InviteAcquirePage> createState() => _InviteAcquirePageState();
}

class _InviteAcquirePageState extends State<InviteAcquirePage> {
  static const String _defaultText = '小红书被限制了，进微信群领邀请码。';
  static const String _fallbackAsset = 'assets/images/login_logo_light.png';

  final ApiService _api = ApiService();

  bool _loading = true;
  String _text = _defaultText;
  String _imageUrl = '';

  @override
  void initState() {
    super.initState();
    _loadConfig();
  }

  Future<void> _loadConfig() async {
    final payload = await _api.getWebConfig();
    if (!mounted) return;
    setState(() {
      _loading = false;
      _text =
          (payload?['invite_acquire_text']?.toString().trim() ?? '').isNotEmpty
          ? payload!['invite_acquire_text'].toString().trim()
          : _defaultText;
      _imageUrl = payload?['invite_acquire_image_url']?.toString().trim() ?? '';
    });
  }

  Widget _buildFallbackImage() {
    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: Image.asset(
        _fallbackAsset,
        fit: BoxFit.contain,
        width: double.infinity,
      ),
    );
  }

  Widget _buildImageCard() {
    if (_imageUrl.isEmpty) {
      return _buildFallbackImage();
    }
    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: Image.network(
        _imageUrl,
        fit: BoxFit.contain,
        width: double.infinity,
        errorBuilder: (_, error, stackTrace) => _buildFallbackImage(),
        loadingBuilder: (context, child, progress) {
          if (progress == null) return child;
          return Container(
            height: 320,
            alignment: Alignment.center,
            child: CircularProgressIndicator(
              color: AppTheme.accent,
              strokeWidth: 2.2,
            ),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgPrimary,
      appBar: AppBar(
        title: Text(
          '获取邀请码',
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
        child: _loading
            ? Center(
                child: CircularProgressIndicator(
                  color: AppTheme.accent,
                  strokeWidth: 2.2,
                ),
              )
            : SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(
                  Spacing.lg,
                  Spacing.xl,
                  Spacing.lg,
                  Spacing.xl,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      _text,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: AppTheme.textPrimary,
                        fontSize: FontSize.lg,
                        fontWeight: FontWeight.w600,
                        height: 1.5,
                      ),
                    ),
                    const SizedBox(height: Spacing.lg),
                    Container(
                      decoration: BoxDecoration(
                        color: AppTheme.bgCard,
                        borderRadius: BorderRadius.circular(18),
                        border: Border.all(
                          color: AppTheme.border.withValues(alpha: 0.55),
                        ),
                      ),
                      padding: const EdgeInsets.all(Spacing.md),
                      child: _buildImageCard(),
                    ),
                  ],
                ),
              ),
      ),
    );
  }
}
