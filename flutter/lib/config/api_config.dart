/// API 配置
class ApiConfig {
  /// 客户端环境标识，仅用于配置和排障。
  static const String appEnv = String.fromEnvironment(
    'APP_ENV',
    defaultValue: 'production',
  );

  /// API 基础地址
  /// 生产默认走 HTTPS 域名，避免后续服务器换 IP 时必须重新发包。
  static const String baseUrl = String.fromEnvironment(
    'MOBILE_API_BASE_URL',
    defaultValue: 'https://kakalog.fun',
  );

  /// 生产已切到 HTTPS；本地或临时 IP 调试可用 dart-define 打开。
  static const bool allowInsecureHttp = bool.fromEnvironment(
    'ALLOW_INSECURE_HTTP',
    defaultValue: false,
  );

  /// 多个备用登录入口用逗号分隔，例如：
  /// --dart-define=MOBILE_LOGIN_FALLBACK_BASE_URLS=https://a.example.com,https://b.example.com
  static const String loginFallbackBaseUrls = String.fromEnvironment(
    'MOBILE_LOGIN_FALLBACK_BASE_URLS',
  );

  static List<String> get loginBaseUrlCandidates => normalizeBaseUrls(<String>[
    baseUrl,
    ...splitBaseUrlList(loginFallbackBaseUrls),
  ]);

  static List<String> splitBaseUrlList(String raw) {
    final trimmed = raw.trim();
    if (trimmed.isEmpty) return const <String>[];
    return trimmed
        .split(',')
        .map((item) => item.trim())
        .where((item) => item.isNotEmpty)
        .toList(growable: false);
  }

  static List<String> normalizeBaseUrls(Iterable<String> rawUrls) {
    final normalized = <String>[];
    final seen = <String>{};
    for (final raw in rawUrls) {
      final base = raw.trim().replaceFirst(RegExp(r'/$'), '');
      if (base.isEmpty || seen.contains(base)) continue;
      final uri = Uri.tryParse(base);
      if (uri == null ||
          !uri.hasAuthority ||
          (uri.scheme != 'http' && uri.scheme != 'https')) {
        throw FormatException('Invalid API base URL: $raw');
      }
      seen.add(base);
      normalized.add(base);
    }
    return List<String>.unmodifiable(normalized);
  }

  /// 请求超时时间（秒）
  static const int timeout = 30;

  /// API 端点
  static const String getAppVersion = '/api/app/version';
  static const String webConfig = '/api/web/config';
  static const String login = '/api/auth/login';
  static const String register = '/api/auth/register';
  static const String refresh = '/api/auth/refresh';
  static const String logout = '/api/auth/logout';
  static const String inviteValidate = '/api/auth/invite/validate';

  /// 邀请码申请入口（可替换为你的问卷/表单链接）
  static const String inviteAcquireUrl = 'https://xhslink.com/m/1yML4q97wdK';
  static const String feedbackUrl = 'https://xhslink.com/m/1yML4q97wdK';
  static const String apkDownloadUrl = '$baseUrl/download/apk';
  static const String changePassword = '/api/auth/password/change';
  static const String bootstrapCredentials = '/api/auth/bootstrap_credentials';
  static const String profileMe = '/api/auth/me';
  static const String profileUpdate = '/api/auth/profile';
  static const String portfolio = '/api/portfolio';
  static const String portfolioAdd = '/api/portfolio/add';
  static const String portfolioBuy = '/api/portfolio/buy';
  static const String portfolioBuyWithCash = '/api/portfolio/buy_with_cash';
  static const String portfolioSell = '/api/portfolio/sell';
  static const String portfolioSellToCash = '/api/portfolio/sell_to_cash';
  static const String portfolioModify = '/api/portfolio/modify';
  static const String portfolioAdjustmentEvent =
      '/api/portfolio/adjustment_event';
  static const String portfolioOcrParseAsset = '/api/portfolio/ocr_parse_asset';
  static const String portfolioDelete = '/api/portfolio/delete';
  static const String portfolioDeleteCorrective =
      '/api/portfolio/delete_corrective';
  static const String portfolioUndo = '/api/portfolio/undo';
  static const String portfolioTransactions = '/api/portfolio/transactions';
  static const String portfolioLedgers = '/api/portfolio/ledgers';
  static const String portfolioLedgersReorder =
      '/api/portfolio/ledgers/reorder';
  static const String pricesBatch = '/api/prices/batch';
  static const String cashAssets = '/api/cash_assets';
  static const String otherAssets = '/api/other_assets';
  static const String liabilities = '/api/liabilities';
  static const String analysisOverview = '/api/analysis/overview';
  static const String analysisCalendar = '/api/analysis/calendar';
  static const String analysisCalendarAssetBreakdown =
      '/api/analysis/calendar/asset_breakdown';
  static const String analysisRank = '/api/analysis/rank';
  static const String realtimeToday = '/api/realtime/today';
  static const String news = '/api/news/latest';
  static const String rates = '/api/rates';
  static const String history = '/api/history';
  static const String marketStatus = '/api/market/status';
  static const String syncBootstrap = '/api/sync/bootstrap';
  static const String search = '/api/search';
  static const String aiChat = '/api/ai/chat';
}
