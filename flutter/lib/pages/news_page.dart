import 'dart:async';

import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../services/api_service.dart';

// ══════════════════════════════════════════════════════════════
//  常量 / 映射
// ══════════════════════════════════════════════════════════════

const _categories = <String, String>{
  'all': '全部',
  'macro': '宏观',
  'company': '公司',
  'trade': '交易',
  'policy': '政策',
};

const _badgeColors = <String, Color>{
  'macro': Color(0xFF5B8DEF),
  'company': Color(0xFF76DCA7),
  'trade': Color(0xFFFFB06E),
  'policy': Color(0xFFD4B5FF),
};

const _badgeBgColors = <String, Color>{
  'macro': Color(0x245B8DEF),
  'company': Color(0x243ECF82),
  'trade': Color(0x28F09A50),
  'policy': Color(0x24B57ADB),
};

// ══════════════════════════════════════════════════════════════
//  基于内容的智能分类
// ══════════════════════════════════════════════════════════════

const _macroKeywords = [
  '央行',
  '利率',
  'CPI',
  'GDP',
  'PMI',
  '通胀',
  '汇率',
  '美联储',
  '逆回购',
  '国债',
  'LPR',
  '降息',
  '加息',
  '外汇',
  '人民币',
  '美元',
  '经济数据',
  '就业',
  '失业率',
  '货币政策',
  '财政',
  '宏观',
  '通缩',
  '社融',
  'M1',
  'M2',
  '贸易',
  '进出口',
  '关税',
  '期货',
  '原油',
  '黄金',
  '铜',
  '大宗商品',
  '欧央行',
  '日央行',
  '英央行',
  '联储',
  '非农',
  '消费者信心',
  '制造业',
  'PPI',
  '零售',
  'PCE',
];

const _companyKeywords = [
  '公司',
  '股份',
  '集团',
  '回购',
  '增持',
  '减持',
  '业绩',
  '营收',
  '净利',
  '分红',
  '并购',
  'IPO',
  '上市',
  '董事',
  '腾讯',
  '阿里',
  '百度',
  '华为',
  '小米',
  '京东',
  '美团',
  '字节',
  '比亚迪',
  '宁德',
  '茅台',
  '特斯拉',
  '苹果',
  '英伟达',
  '微软',
  '谷歌',
  '亚马逊',
  '财报',
  '盈利',
  '亏损',
  '季报',
  '年报',
  '中报',
  '预告',
  '管理层',
  '董秘',
  '股东',
  '解禁',
  '定增',
  '配股',
  '转债',
];

const _tradeKeywords = [
  '北向资金',
  '成交',
  '涨停',
  '跌停',
  'ETF',
  '板块',
  '指数',
  '大盘',
  '沪指',
  '深指',
  '创业板',
  '科创',
  '主力',
  '资金流',
  '净流入',
  '净流出',
  '开盘',
  '收盘',
  '盘中',
  '盘面',
  '涨幅',
  '跌幅',
  '午盘',
  '尾盘',
  '放量',
  '缩量',
  '换手',
  '量能',
  '突破',
  '支撑',
  '压力',
  '反弹',
  '回调',
  '震荡',
  '走势',
  '行情',
  '赛道',
  '概念股',
  '龙头',
  '融资',
  '融券',
  '两融',
  '港股通',
  '南向资金',
];

const _policyKeywords = [
  '政策',
  '监管',
  '证监会',
  '银保监',
  '发改委',
  '国务院',
  '部委',
  '法规',
  '条例',
  '新规',
  '改革',
  '规划',
  '意见',
  '通知',
  '办法',
  '审批',
  '备案',
  '许可',
  '处罚',
  '调查',
  '合规',
  '监察',
  '国资委',
  '财政部',
  '商务部',
  '工信部',
  '住建部',
  '交通部',
  '多部门',
  '联合发布',
  '征求意见',
  '试点',
  '落地',
  '推进',
];

String _classifyCategory(String content) {
  int macroScore = 0;
  int companyScore = 0;
  int tradeScore = 0;
  int policyScore = 0;

  for (final kw in _macroKeywords) {
    if (content.contains(kw)) macroScore++;
  }
  for (final kw in _companyKeywords) {
    if (content.contains(kw)) companyScore++;
  }
  for (final kw in _tradeKeywords) {
    if (content.contains(kw)) tradeScore++;
  }
  for (final kw in _policyKeywords) {
    if (content.contains(kw)) policyScore++;
  }

  final maxScore = [
    macroScore,
    companyScore,
    tradeScore,
    policyScore,
  ].reduce((a, b) => a > b ? a : b);
  if (maxScore == 0) return 'macro'; // 默认宏观

  if (policyScore == maxScore) return 'policy';
  if (tradeScore == maxScore) return 'trade';
  if (companyScore == maxScore) return 'company';
  return 'macro';
}

// ══════════════════════════════════════════════════════════════
//  基于内容的影响力/情绪分析
// ══════════════════════════════════════════════════════════════

const _bullishKeywords = [
  '涨',
  '上涨',
  '上行',
  '走高',
  '走强',
  '反弹',
  '增长',
  '利好',
  '偏多',
  '回暖',
  '放量',
  '净流入',
  '回购',
  '增持',
  '突破',
  '新高',
  '上扬',
  '提振',
  '强势',
  '活跃',
  '加速',
  '扩大',
  '超预期',
  '景气',
  '修复',
  '复苏',
  '乐观',
];

const _bearishKeywords = [
  '跌',
  '下跌',
  '下行',
  '走低',
  '走弱',
  '回调',
  '下滑',
  '利空',
  '偏空',
  '缩量',
  '净流出',
  '减持',
  '下调',
  '承压',
  '疲软',
  '低迷',
  '新低',
  '萎缩',
  '收窄',
  '放缓',
  '回落',
  '下挫',
  '失守',
  '不及预期',
  '悲观',
  '风险',
  '亏损',
];

/// 返回 ('up'|'down'|'neutral', '影响文字')
(String, String) _classifyImpact(String content) {
  int bullish = 0;
  int bearish = 0;

  for (final kw in _bullishKeywords) {
    if (content.contains(kw)) bullish++;
  }
  for (final kw in _bearishKeywords) {
    if (content.contains(kw)) bearish++;
  }

  if (bullish > bearish && bullish > 0) {
    return ('up', '+偏多');
  }
  if (bearish > bullish && bearish > 0) {
    return ('down', '-偏空');
  }
  return ('neutral', '中性');
}

// ══════════════════════════════════════════════════════════════
//  从内容中提取关联标的
// ══════════════════════════════════════════════════════════════

String _extractSymbol(String content, String category) {
  // 匹配常见标的
  final patterns = <String, String>{
    '沪指': 'A:沪指',
    '深指': 'A:深指',
    '创业板': 'A:创业板',
    '科创50': 'A:科创50',
    '北证50': 'A:北证50',
    '恒生指数': 'HK:恒指',
    '恒指': 'HK:恒指',
    '道指': 'US:道指',
    '纳指': 'US:纳指',
    '标普': 'US:标普',
    '北向资金': 'A:北向资金',
    '南向资金': 'HK:南向资金',
    '人民币': 'CNY',
    '美元': 'USD',
    '欧元': 'EUR',
    '日元': 'JPY',
    '黄金': '黄金',
    '原油': '原油',
    '铜': '铜',
    '腾讯': 'HK:00700',
    '阿里': 'US:BABA',
    '茅台': 'A:600519',
    '比亚迪': 'A:002594',
    '宁德时代': 'A:300750',
    '特斯拉': 'US:TSLA',
    '苹果': 'US:AAPL',
    '英伟达': 'US:NVDA',
    'ETF': 'ETF',
    '国债': '国债',
    '期货': '期货',
  };

  for (final entry in patterns.entries) {
    if (content.contains(entry.key)) {
      return entry.value;
    }
  }

  // 按分类给默认
  switch (category) {
    case 'macro':
      return '宏观';
    case 'trade':
      return 'A股';
    case 'policy':
      return '政策';
    case 'company':
      return '公司';
    default:
      return '市场';
  }
}

// ══════════════════════════════════════════════════════════════
//  从内容中提取标题
// ══════════════════════════════════════════════════════════════

/// 拆分出 (标题, 正文)
(String?, String) _splitTitleContent(String content) {
  // 模式1: 【xxx】yyy
  final bracketIndex = content.indexOf('】');
  if (bracketIndex > 0 && bracketIndex < 30) {
    final title = content.substring(0, bracketIndex + 1);
    final body = content.substring(bracketIndex + 1).trim();
    if (body.isNotEmpty) {
      return (title, body);
    }
  }

  // 模式2: 用逗号或句号分割第一句作为标题（如果内容较长）
  if (content.length > 40) {
    // 找第一个逗号或句号
    int cutAt = -1;
    for (int i = 0; i < content.length && i < 35; i++) {
      if (content[i] == '，' ||
          content[i] == '。' ||
          content[i] == ',' ||
          content[i] == ';' ||
          content[i] == '；') {
        cutAt = i;
        break;
      }
    }
    if (cutAt > 6) {
      return (content.substring(0, cutAt), content.substring(cutAt + 1).trim());
    }
  }

  return (null, content);
}

// ══════════════════════════════════════════════════════════════
//  缓存已分析的新闻属性
// ══════════════════════════════════════════════════════════════

class _AnalyzedNews {
  final String category;
  final String? title;
  final String body;
  final String symbol;
  final String impact;
  final String impactText;
  final String source;

  const _AnalyzedNews({
    required this.category,
    required this.title,
    required this.body,
    required this.symbol,
    required this.impact,
    required this.impactText,
    required this.source,
  });
}

_AnalyzedNews _analyzeItem(Map<String, dynamic> item) {
  final content =
      item['content']?.toString() ?? item['title']?.toString() ?? '';

  // 如果已有 category 字段直接用
  String category;
  if (item['category'] != null &&
      item['category'].toString().isNotEmpty &&
      _categories.containsKey(item['category'].toString())) {
    category = item['category'].toString();
  } else {
    category = _classifyCategory(content);
  }

  // 情绪分析
  String impact;
  String impactText;
  if (item['impact'] != null && item['impact'].toString().isNotEmpty) {
    impact = item['impact'].toString();
    impactText =
        item['impact_text']?.toString() ??
        item['impactText']?.toString() ??
        (impact == 'up' ? '+偏多' : (impact == 'down' ? '-偏空' : '中性'));
  } else {
    final result = _classifyImpact(content);
    impact = result.$1;
    impactText = result.$2;
  }

  // 标的提取
  final symbol =
      item['symbol']?.toString() ?? _extractSymbol(content, category);

  // 标题拆分
  String? title;
  String body;
  if (item['title'] != null &&
      item['summary'] != null &&
      item['title'].toString().isNotEmpty) {
    title = item['title'].toString();
    body = item['summary'].toString();
  } else {
    final split = _splitTitleContent(content);
    title = split.$1;
    body = split.$2;
  }

  // 来源
  final source = item['source']?.toString() ?? '';

  return _AnalyzedNews(
    category: category,
    title: title,
    body: body,
    symbol: symbol,
    impact: impact,
    impactText: impactText,
    source: source,
  );
}

// ══════════════════════════════════════════════════════════════
//  NewsPage Widget
// ══════════════════════════════════════════════════════════════

/// 快讯页面（1:1 复刻 H5 版本）
class NewsPage extends StatefulWidget {
  const NewsPage({super.key, this.newsLoader});

  final Future<Map<String, dynamic>> Function({
    required int page,
    required int pageSize,
  })?
  newsLoader;

  @override
  State<NewsPage> createState() => _NewsPageState();
}

class _NewsPageState extends State<NewsPage> {
  final ApiService _api = ApiService();
  static const Duration _autoRefreshInterval = Duration(seconds: 3);
  static const int _maxNewsItems = 500;

  // ── 数据 ──
  List<Map<String, dynamic>> _news = [];
  final Set<String> _newsIds = {};
  final Map<String, _AnalyzedNews> _analysisCache = {};

  // ── 分页 ──
  int _page = 1;
  final int _pageSize = 50;
  bool _hasMore = true;
  bool _loadingMore = false;
  String? _latestNewsId;
  bool _polling = false;
  Timer? _autoRefreshTimer;

  // ── 加载状态 ──
  bool _isInitialLoading = true;
  bool _isRefreshing = false;

  // ── 筛选 ──
  String _selectedCategory = 'all';
  bool _onlyImportant = false;

  // ── 展开/折叠 ──
  final Set<String> _expandedKeys = {};

  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
    _loadNews(reset: true);
    _startAutoRefresh();
  }

  @override
  void dispose() {
    _autoRefreshTimer?.cancel();
    _scrollController.dispose();
    super.dispose();
  }

  void _startAutoRefresh() {
    // 单测注入 loader 时，不启用后台轮询，避免引入额外不确定性。
    if (widget.newsLoader != null) return;
    _autoRefreshTimer?.cancel();
    _autoRefreshTimer = Timer.periodic(_autoRefreshInterval, (_) {
      _pollLatestNews();
    });
  }

  // ─────────────  获取分析结果  ─────────────

  _AnalyzedNews _getAnalysis(Map<String, dynamic> item) {
    final key = _itemKey(item);
    return _analysisCache.putIfAbsent(key, () => _analyzeItem(item));
  }

  // ─────────────  滚动加载更多  ─────────────

  void _onScroll() {
    if (!_hasMore || _loadingMore || _isRefreshing || _isInitialLoading) return;
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      _loadNews();
    }
  }

  // ─────────────  加载数据  ─────────────

  Future<void> _loadNews({bool reset = false}) async {
    if (reset) {
      if (_isRefreshing || _loadingMore) return;
      if (!mounted) return;
      setState(() {
        _page = 1;
        _hasMore = true;
        if (_news.isEmpty) {
          _isInitialLoading = true;
        } else {
          _isRefreshing = true;
        }
      });
    } else {
      if (_loadingMore || _isRefreshing || _isInitialLoading || !_hasMore) {
        return;
      }
      if (!mounted) return;
      setState(() => _loadingMore = true);
    }

    if (reset) {
      _analysisCache.clear();
      _expandedKeys.clear();
    }

    try {
      final loader = widget.newsLoader;
      final requestPage = reset ? 1 : _page;
      final data = loader != null
          ? await loader(page: requestPage, pageSize: _pageSize)
          : await _api.getNews(page: requestPage, pageSize: _pageSize);
      final items =
          (data['items'] as List?)
              ?.map((e) => e as Map<String, dynamic>)
              .toList() ??
          [];
      final hasMore = data['has_more'] == true;
      final latestIdFromApi = data['latest_id']?.toString();

      if (!mounted) return;
      if (reset) {
        final nextNews = <Map<String, dynamic>>[];
        final nextIds = <String>{};
        for (final item in items) {
          final key = _itemKey(item);
          if (nextIds.add(key)) nextNews.add(item);
        }
        setState(() {
          _news = nextNews;
          _newsIds
            ..clear()
            ..addAll(nextIds);
          _latestNewsId =
              latestIdFromApi ??
              (nextNews.isNotEmpty ? _itemKey(nextNews.first) : null);
          _isInitialLoading = false;
          _isRefreshing = false;
          _loadingMore = false;
          _hasMore = hasMore;
          _page = items.isNotEmpty ? 2 : 1;
        });
      } else {
        for (final item in items) {
          final key = _itemKey(item);
          if (_newsIds.add(key)) _news.add(item);
        }
        setState(() {
          _latestNewsId =
              latestIdFromApi ??
              (_news.isNotEmpty ? _itemKey(_news.first) : _latestNewsId);
          _loadingMore = false;
          _hasMore = hasMore;
          if (items.isNotEmpty) _page += 1;
        });
      }
    } catch (e) {
      debugPrint('加载快讯失败: $e');
      if (!mounted) return;
      setState(() {
        _isInitialLoading = false;
        _isRefreshing = false;
        _loadingMore = false;
      });
    }
  }

  Future<void> _pollLatestNews() async {
    if (!mounted ||
        _polling ||
        _isInitialLoading ||
        _isRefreshing ||
        _loadingMore ||
        widget.newsLoader != null) {
      return;
    }

    final marker = (_latestNewsId ?? '').trim();
    if (marker.isEmpty) {
      return;
    }

    _polling = true;
    try {
      final data = await _api.getNews(
        page: 1,
        pageSize: _pageSize,
        sinceId: marker,
      );
      final items =
          (data['items'] as List?)
              ?.map((e) => e as Map<String, dynamic>)
              .toList() ??
          <Map<String, dynamic>>[];
      final latestIdFromApi = data['latest_id']?.toString();

      if (!mounted) return;

      if (items.isEmpty) {
        if (latestIdFromApi != null && latestIdFromApi.isNotEmpty) {
          _latestNewsId = latestIdFromApi;
        }
        return;
      }

      final prepend = <Map<String, dynamic>>[];
      for (final item in items) {
        final key = _itemKey(item);
        if (_newsIds.add(key)) {
          prepend.add(item);
        }
      }
      if (prepend.isEmpty) {
        if (latestIdFromApi != null && latestIdFromApi.isNotEmpty) {
          _latestNewsId = latestIdFromApi;
        }
        return;
      }

      setState(() {
        _news = [...prepend, ..._news];
        if (_news.length > _maxNewsItems) {
          _news = _news.take(_maxNewsItems).toList();
          _newsIds
            ..clear()
            ..addAll(_news.map(_itemKey));
        }
        _latestNewsId =
            latestIdFromApi ??
            (_news.isNotEmpty ? _itemKey(_news.first) : _latestNewsId);
      });
    } catch (e) {
      debugPrint('轮询快讯失败: $e');
    } finally {
      _polling = false;
    }
  }

  String _itemKey(Map<String, dynamic> item) {
    if (item['id'] != null) return item['id'].toString();
    return '${item['time'] ?? ''}_${item['content'] ?? item['title'] ?? ''}';
  }

  // ─────────────  过滤列表  ─────────────

  List<Map<String, dynamic>> get _filteredNews {
    var list = _news;
    if (_selectedCategory != 'all') {
      list = list.where((e) {
        final analysis = _getAnalysis(e);
        return analysis.category == _selectedCategory;
      }).toList();
    }
    if (_onlyImportant) {
      list = list.where((e) => e['important'] == true).toList();
    }
    return list;
  }

  // ═══════════════════════════════════════  BUILD  ═══════════

  @override
  Widget build(BuildContext context) {
    final filtered = _filteredNews;

    return RefreshIndicator(
      onRefresh: () => _loadNews(reset: true),
      color: AppTheme.accent,
      child: CustomScrollView(
        controller: _scrollController,
        slivers: [
          // ── Hero 区域 ──
          SliverToBoxAdapter(child: _buildHero()),

          // ── 列表内容 ──
          if (filtered.isNotEmpty)
            SliverPadding(
              padding: const EdgeInsets.symmetric(horizontal: 14),
              sliver: SliverList(
                delegate: SliverChildBuilderDelegate(
                  (context, index) => Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: _buildNewsCard(filtered[index]),
                  ),
                  childCount: filtered.length,
                ),
              ),
            )
          else if (_isInitialLoading)
            SliverPadding(
              padding: const EdgeInsets.symmetric(horizontal: 14),
              sliver: SliverToBoxAdapter(
                child: Column(
                  children: List.generate(
                    4,
                    (_) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: _buildSkeletonCard(),
                    ),
                  ),
                ),
              ),
            )
          else
            SliverToBoxAdapter(child: _buildEmpty()),

          // ── 加载更多 ──
          if (_loadingMore)
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 14),
                child: Center(
                  child: SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: AppTheme.accent.withValues(alpha: 0.6),
                    ),
                  ),
                ),
              ),
            ),

          // ── 底部安全区 ──
          const SliverToBoxAdapter(child: SizedBox(height: 100)),
        ],
      ),
    );
  }

  // ═══════════════════════  Hero  ═══════════════════════════

  Widget _buildHero() {
    return Container(
      margin: const EdgeInsets.fromLTRB(14, 10, 14, 8),
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 14),
      decoration: AppTheme.heroDecoration,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(
                  '市场快讯',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.textPrimary,
                    height: 1.15,
                    letterSpacing: -0.3,
                  ),
                ),
              ),
              _buildImportantPill(),
            ],
          ),
          const SizedBox(height: 14),
          _buildCategoryTabs(),
        ],
      ),
    );
  }

  Widget _buildImportantPill() {
    final active = _onlyImportant;
    return GestureDetector(
      onTap: () => setState(() => _onlyImportant = !_onlyImportant),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 160),
        height: 30,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(999),
          border: Border.all(
            color: active
                ? AppTheme.accent.withValues(alpha: 0.52)
                : AppTheme.isLight
                ? const Color(0x14222C40)
                : Colors.white.withValues(alpha: 0.07),
          ),
          gradient: active
              ? LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    AppTheme.accent.withValues(alpha: 0.24),
                    const Color(0xFF4A7BE0).withValues(alpha: 0.18),
                  ],
                )
              : null,
          color: active ? null : Colors.transparent,
          boxShadow: active
              ? [
                  BoxShadow(
                    color: const Color(0xFF4A7BE0).withValues(alpha: 0.20),
                    blurRadius: 14,
                    offset: const Offset(0, 6),
                  ),
                ]
              : null,
        ),
        child: Center(
          child: Text(
            active ? '仅看重要 · 开' : '仅看重要',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: active ? AppTheme.textPrimary : AppTheme.textSecondary,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildCategoryTabs() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: _categories.entries.map((entry) {
          final isActive = _selectedCategory == entry.key;
          return Padding(
            padding: const EdgeInsets.only(right: 7),
            child: GestureDetector(
              onTap: () {
                if (_selectedCategory == entry.key) return;
                setState(() => _selectedCategory = entry.key);
              },
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 160),
                height: 30,
                padding: const EdgeInsets.symmetric(horizontal: 14),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(
                    color: isActive
                        ? AppTheme.accent.withValues(alpha: 0.48)
                        : Colors.transparent,
                  ),
                  gradient: isActive
                      ? const LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [Color(0xFF5B8DEF), Color(0xFF4A7BE0)],
                        )
                      : null,
                  color: isActive ? null : Colors.transparent,
                  boxShadow: isActive
                      ? [
                          BoxShadow(
                            color: const Color(
                              0xFF4A7BE0,
                            ).withValues(alpha: 0.24),
                            blurRadius: 14,
                            offset: const Offset(0, 6),
                          ),
                        ]
                      : null,
                ),
                child: Center(
                  child: Text(
                    entry.value,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: isActive ? Colors.white : AppTheme.textSecondary,
                    ),
                  ),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  // ═══════════════════════  News Card  ════════════════════════

  Widget _buildNewsCard(Map<String, dynamic> item) {
    final a = _getAnalysis(item);
    final isImportant = item['important'] == true;
    final time = item['time']?.toString() ?? '';

    final badgeColor = _badgeColors[a.category] ?? AppTheme.accent;
    final badgeBg =
        _badgeBgColors[a.category] ?? AppTheme.accent.withValues(alpha: 0.14);
    final categoryText = _categories[a.category] ?? '宏观';

    // 来源显示
    final sourceDisplay = isImportant
        ? (a.source.isNotEmpty ? '${a.source} · 重要' : '重要')
        : a.source;

    // 影响力颜色
    Color impactColor;
    switch (a.impact) {
      case 'up':
        impactColor = AppTheme.danger;
        break;
      case 'down':
        impactColor = AppTheme.success;
        break;
      default:
        impactColor = AppTheme.textSecondary;
    }

    return Container(
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.borderSubtle),
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: AppTheme.isLight
              ? [Colors.white, const Color(0xFFF5F8FF)]
              : [const Color(0xF51A1D25), const Color(0xFA171A22)],
        ),
        boxShadow: AppTheme.isLight
            ? [
                BoxShadow(
                  color: AppTheme.isLight
                      ? const Color(0x12222C40)
                      : const Color(0xFF222C48).withValues(alpha: 0.07),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ]
            : [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.24),
                  blurRadius: 18,
                  offset: const Offset(0, 8),
                ),
              ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── 顶部: badge + source + time ──
          Row(
            children: [
              // 分类 Badge
              Container(
                height: 20,
                padding: const EdgeInsets.symmetric(horizontal: 8),
                decoration: BoxDecoration(
                  color: badgeBg,
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Center(
                  child: Text(
                    categoryText,
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      color: badgeColor,
                      letterSpacing: 0.1,
                    ),
                  ),
                ),
              ),
              if (sourceDisplay.isNotEmpty) ...[
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    sourceDisplay,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 11, color: AppTheme.textMuted),
                  ),
                ),
              ] else
                const Spacer(),
              Text(
                time,
                style: TextStyle(
                  fontSize: 12,
                  fontFamily: 'monospace',
                  fontWeight: FontWeight.w500,
                  color: AppTheme.textTertiary,
                  letterSpacing: 0.3,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // ── 标题（如果有）──
          if (a.title != null && a.title!.isNotEmpty) ...[
            Text(
              a.title!,
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w700,
                color: AppTheme.textPrimary,
                height: 1.35,
              ),
            ),
            const SizedBox(height: 6),
          ],

          // ── 正文（最多5行，点击展开）──
          if (a.body.isNotEmpty)
            Builder(
              builder: (context) {
                final key = _itemKey(item);
                final expanded = _expandedKeys.contains(key);
                return GestureDetector(
                  onTap: () {
                    setState(() {
                      if (expanded) {
                        _expandedKeys.remove(key);
                      } else {
                        _expandedKeys.add(key);
                      }
                    });
                  },
                  child: Text(
                    a.body,
                    maxLines: expanded ? null : 5,
                    overflow: expanded
                        ? TextOverflow.visible
                        : TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: a.title != null ? 12.5 : 14,
                      fontWeight: a.title != null
                          ? FontWeight.w400
                          : FontWeight.w500,
                      color: a.title != null
                          ? AppTheme.textSecondary
                          : AppTheme.textPrimary,
                      height: 1.5,
                      letterSpacing: 0.1,
                    ),
                  ),
                );
              },
            ),
          const SizedBox(height: 10),

          // ── 底部: symbol + impact ──
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                a.symbol,
                style: TextStyle(
                  fontSize: 11,
                  fontFamily: 'monospace',
                  color: AppTheme.textSecondary,
                  letterSpacing: 0.1,
                ),
              ),
              Text(
                a.impactText,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  fontFamily: 'monospace',
                  color: impactColor,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ═══════════════════════  Skeleton  ═════════════════════════

  Widget _buildSkeletonCard() {
    Widget line({required double width, required double height}) {
      return Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
          color: AppTheme.bgElevated.withValues(alpha: 0.9),
          borderRadius: BorderRadius.circular(6),
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.borderSubtle),
        boxShadow: AppTheme.cardShadow,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              line(width: 44, height: 20),
              const SizedBox(width: 8),
              line(width: 60, height: 12),
              const Spacer(),
              line(width: 44, height: 14),
            ],
          ),
          const SizedBox(height: 12),
          line(width: double.infinity, height: 14),
          const SizedBox(height: 8),
          line(width: double.infinity, height: 14),
          const SizedBox(height: 8),
          line(width: 200, height: 14),
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              line(width: 56, height: 12),
              line(width: 40, height: 12),
            ],
          ),
        ],
      ),
    );
  }

  // ═══════════════════════  Empty  ═══════════════════════════

  Widget _buildEmpty() {
    final catText = _categories[_selectedCategory] ?? '当前分类';
    return Container(
      margin: const EdgeInsets.fromLTRB(14, 4, 14, 14),
      padding: const EdgeInsets.symmetric(vertical: 32, horizontal: 16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: AppTheme.isLight
              ? const Color(0x29222C40)
              : const Color(0x24FFFFFF),
          width: 1,
          strokeAlign: BorderSide.strokeAlignInside,
        ),
        color: AppTheme.isLight
            ? const Color(0x8CDCE4F5)
            : const Color(0xA81A1D25),
      ),
      child: Center(
        child: Column(
          children: [
            Text(
              '暂无快讯',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              '$catText频道当前没有符合条件的消息',
              style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
            ),
          ],
        ),
      ),
    );
  }
}
