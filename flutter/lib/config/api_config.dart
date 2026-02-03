/// API 配置
class ApiConfig {
  /// API 基础地址
  static const String baseUrl = 'http://35.78.253.89:5003';
  
  /// 请求超时时间（秒）
  static const int timeout = 10;
  
  /// API 端点
  static const String login = '/api/auth/login';
  static const String portfolio = '/api/portfolio';
  static const String portfolioAdd = '/api/portfolio/add';
  static const String portfolioBuy = '/api/portfolio/buy';
  static const String portfolioSell = '/api/portfolio/sell';
  static const String portfolioDelete = '/api/portfolio/delete';
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
  static const String search = '/api/search';
}
