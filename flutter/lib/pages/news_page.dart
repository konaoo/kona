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
  bool _onlyImportant = false;
  final Set<String> _expandedKeys = {};

  @override
  void initState() {
    super.initState();
    _loadNews();
  }

  Future<void> _loadNews() async {
    setState(() => _loading = true);
    try {
      final data = await _api.getNews();
      setState(() {
        _news = data.map((e) => e as Map<String, dynamic>).toList();
        _loading = false;
        _expandedKeys.clear();
      });
    } catch (e) {
      debugPrint('加载快讯失败: $e');
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final filteredNews = _onlyImportant ? _news.where((e) => e['important'] == true).toList() : _news;
    return RefreshIndicator(
      onRefresh: _loadNews,
      color: AppTheme.accent,
      child: CustomScrollView(
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
                        style: TextStyle(fontSize: FontSize.xs, color: AppTheme.textSecondary),
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
