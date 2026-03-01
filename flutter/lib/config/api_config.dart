/// API 配置
class ApiConfig {
  /// API 基础地址
  /// 注意：域名 DNS 当前解析异常（198.18.x.x），临时使用 IP 直连。
  /// DNS 修复后应切回 https://kakawallet.fun。
  static const String baseUrl = 'http://114.132.238.12';
  static const String loginFallbackBaseUrl = 'https://kakawallet.fun';
  static const List<String> loginBaseUrlCandidates = <String>[
    baseUrl,
    loginFallbackBaseUrl,
    'https://www.kakawallet.fun',
  ];

  /// 请求超时时间（秒）
  static const int timeout = 30;

  /// API 端点
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
  static const String portfolioDelete = '/api/portfolio/delete';
  static const String portfolioDeleteCorrective =
      '/api/portfolio/delete_corrective';
  static const String portfolioUndo = '/api/portfolio/undo';
  static const String pricesBatch = '/api/prices/batch';
  static const String cashAssets = '/api/cash_assets';
  static const String otherAssets = '/api/other_assets';
  static const String liabilities = '/api/liabilities';
  static const String analysisOverview = '/api/analysis/overview';
  static const String analysisCalendar = '/api/analysis/calendar';
  static const String analysisRank = '/api/analysis/rank';
  static const String news = '/api/news/latest';
  static const String rates = '/api/rates';
  static const String history = '/api/history';
  static const String marketStatus = '/api/market/status';
  static const String syncBootstrap = '/api/sync/bootstrap';
  static const String search = '/api/search';
}
