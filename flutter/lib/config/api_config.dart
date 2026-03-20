/// API 配置
class ApiConfig {
  /// API 基础地址
  /// 当前生产仅保留 IP 入口，域名备案完成后再评估恢复域名访问。
  static const String baseUrl = 'http://114.132.238.12';
  static const List<String> loginBaseUrlCandidates = <String>[baseUrl];

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
  static const String portfolioDelete = '/api/portfolio/delete';
  static const String portfolioDeleteCorrective =
      '/api/portfolio/delete_corrective';
  static const String portfolioUndo = '/api/portfolio/undo';
  static const String portfolioTransactions = '/api/portfolio/transactions';
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
  static const String aiChat = '/api/ai/chat';
}
