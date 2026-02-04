import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../services/api_service.dart';

/// 快讯页面
class NewsPage extends StatefulWidget {
  const NewsPage({super.key});

  @override
  State<NewsPage> createState() => _NewsPageState();
}

class _NewsPageState extends State<NewsPage> {
  final ApiService _api = ApiService();
  List<Map<String, dynamic>> _news = [];
  bool _loading = true;
  bool _onlyImportant = true;
  final Set<String> _expandedKeys = {};
  final ScrollController _scrollController = ScrollController();
  final Set<String> _newsIds = {};
  int _page = 1;
  final int _pageSize = 30;
  bool _hasMore = true;
  bool _loadingMore = false;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
    _loadNews(reset: true);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (!_hasMore || _loadingMore) return;
    if (_scrollController.position.pixels >= _scrollController.position.maxScrollExtent - 200) {
      _loadNews();
    }
  }

  Future<void> _loadNews({bool reset = false}) async {
    if (_loadingMore && !reset) return;
    if (reset) {
      setState(() {
        _loading = true;
        _page = 1;
        _hasMore = true;
        _news = [];
        _newsIds.clear();
        _expandedKeys.clear();
      });
    } else {
      setState(() => _loadingMore = true);
    }
    try {
      final data = await _api.getNews(page: _page, pageSize: _pageSize);
      final items = (data['items'] as List?)?.map((e) => e as Map<String, dynamic>).toList() ?? [];
      final hasMore = data['has_more'] == true;

      for (final item in items) {
        final key = _itemKey(item);
        if (_newsIds.add(key)) {
          _news.add(item);
        }
      }

      setState(() {
        _loading = false;
        _loadingMore = false;
        _hasMore = hasMore;
        if (items.isNotEmpty) _page += 1;
      });
    } catch (e) {
      debugPrint('加载快讯失败: $e');
      setState(() {
        _loading = false;
        _loadingMore = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final filteredNews = _onlyImportant ? _news.where((e) => e['important'] == true).toList() : _news;
    return RefreshIndicator(
      onRefresh: () => _loadNews(reset: true),
      color: AppTheme.accent,
      child: CustomScrollView(
        controller: _scrollController,
        slivers: [
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(Spacing.xl, Spacing.lg, Spacing.xl, Spacing.md),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    '市场快讯',
                    style: TextStyle(
                      fontSize: FontSize.xxl,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  Row(
                    children: [
                      const Text(
                        '只看重要',
                        style: TextStyle(fontSize: FontSize.sm, color: AppTheme.textSecondary),
                      ),
                      const SizedBox(width: 6),
                      Transform.scale(
                        scale: 0.75,
                        child: Switch(
                          value: _onlyImportant,
                          activeColor: AppTheme.accent,
                          materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                          onChanged: (val) {
                            setState(() => _onlyImportant = val);
                          },
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          if (_loading)
            const SliverFillRemaining(
              child: Center(
                child: CircularProgressIndicator(color: AppTheme.accent),
              ),
            )
          else if (filteredNews.isEmpty)
            SliverFillRemaining(
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.flash_on, size: 48, color: AppTheme.textTertiary),
                    const SizedBox(height: Spacing.md),
                    const Text('暂无快讯', style: TextStyle(color: AppTheme.textSecondary)),
                  ],
                ),
              ),
            )
          else
            SliverList(
              delegate: SliverChildBuilderDelegate(
                (context, index) => _buildNewsItem(filteredNews[index]),
                childCount: filteredNews.length,
              ),
            ),
          if (_loadingMore)
            const SliverToBoxAdapter(
              child: Padding(
                padding: EdgeInsets.symmetric(vertical: Spacing.md),
                child: Center(
                  child: SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.accent),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildNewsItem(Map<String, dynamic> item) {
    final isImportant = item['important'] == true;
    final key = _itemKey(item);
    final expanded = _expandedKeys.contains(key);

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: Spacing.xl, vertical: 4),
      padding: const EdgeInsets.all(Spacing.lg),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: isImportant ? Border.all(color: AppTheme.accent.withOpacity(0.3), width: 1) : null,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (isImportant)
                Container(
                  margin: const EdgeInsets.only(right: 8),
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppTheme.accent,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: const Text(
                    '重要',
                    style: TextStyle(fontSize: 10, color: AppTheme.textPrimary),
                  ),
                ),
              Text(
                item['time'] ?? '',
                style: const TextStyle(
                  fontSize: FontSize.sm,
                  color: AppTheme.textTertiary,
                ),
              ),
            ],
          ),
          const SizedBox(height: Spacing.sm),
          GestureDetector(
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
              item['content'] ?? '',
              maxLines: expanded ? null : 5,
              overflow: expanded ? TextOverflow.visible : TextOverflow.ellipsis,
              style: const TextStyle(
                fontSize: FontSize.base,
                color: AppTheme.textPrimary,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _itemKey(Map<String, dynamic> item) {
    return '${item['time'] ?? ''}_${item['content'] ?? ''}';
  }
}
