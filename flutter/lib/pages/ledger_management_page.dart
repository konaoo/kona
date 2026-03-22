import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../config/theme.dart';
import '../providers/app_state.dart';

class LedgerManagementPage extends StatefulWidget {
  const LedgerManagementPage({super.key});

  @override
  State<LedgerManagementPage> createState() => _LedgerManagementPageState();
}

class _LedgerManagementPageState extends State<LedgerManagementPage> {
  List<Map<String, dynamic>> _orderedLedgers = <Map<String, dynamic>>[];
  bool _initialized = false;
  bool _submitting = false;

  static final TextStyle _titleStyle = GoogleFonts.dmSans(
    fontSize: 16,
    fontWeight: FontWeight.w700,
  );
  static final TextStyle _metaStyle = GoogleFonts.dmSans(
    fontSize: 12,
    fontWeight: FontWeight.w500,
  );

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_initialized) return;
    _initialized = true;
    _orderedLedgers = _cloneLedgers(context.read<AppState>().ledgers);
  }

  List<Map<String, dynamic>> _cloneLedgers(List<Map<String, dynamic>> source) {
    return source.map((ledger) => Map<String, dynamic>.from(ledger)).toList();
  }

  Future<void> _reloadLedgers(AppState appState) async {
    await appState.loadLedgers();
    if (!mounted) return;
    setState(() {
      _orderedLedgers = _cloneLedgers(appState.ledgers);
    });
  }

  void _showMessage(String text) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
  }

  Future<void> _showCreateLedgerDialog(AppState appState) async {
    final controller = TextEditingController();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('新建账本'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(hintText: '账本名称'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () {
              if (controller.text.trim().isEmpty) return;
              Navigator.pop(ctx, true);
            },
            child: const Text('创建'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    setState(() => _submitting = true);
    final result = await appState.createLedger(controller.text.trim());
    if (!mounted) return;
    setState(() => _submitting = false);
    if (!result.ok) {
      _showMessage(result.message ?? '创建失败');
      return;
    }
    await _reloadLedgers(appState);
  }

  Future<void> _showRenameLedgerDialog(
    AppState appState,
    Map<String, dynamic> ledger,
  ) async {
    final currentName = (ledger['name'] as String?) ?? '';
    final controller = TextEditingController(text: currentName);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('重命名账本'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(hintText: '账本名称'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('确定'),
          ),
        ],
      ),
    );
    final nextName = controller.text.trim();
    if (confirmed != true || nextName.isEmpty || nextName == currentName) {
      return;
    }

    setState(() => _submitting = true);
    final result = await appState.updateLedger(ledger['id'] as int, nextName);
    if (!mounted) return;
    setState(() => _submitting = false);
    if (!result.ok) {
      _showMessage(result.message ?? '重命名失败');
      return;
    }
    await _reloadLedgers(appState);
  }

  Future<void> _deleteLedger(
    AppState appState,
    Map<String, dynamic> ledger,
  ) async {
    final isDefault = ledger['is_default'] == true || ledger['is_default'] == 1;
    if (isDefault) {
      _showMessage('默认账本不能删除');
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('删除账本'),
        content: Text('确定删除“${ledger['name'] ?? '账本'}”吗？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('删除'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    setState(() => _submitting = true);
    final result = await appState.deleteLedger(ledger['id'] as int);
    if (!mounted) return;
    setState(() => _submitting = false);
    if (!result.ok) {
      _showMessage(result.message ?? '删除失败，账本下可能还有持仓');
      return;
    }
    await _reloadLedgers(appState);
  }

  Future<void> _reorderLedgers(
    AppState appState,
    int oldIndex,
    int newIndex,
  ) async {
    if (_submitting) return;
    final nextLedgers = _cloneLedgers(_orderedLedgers);
    if (newIndex > oldIndex) newIndex -= 1;
    final moved = nextLedgers.removeAt(oldIndex);
    nextLedgers.insert(newIndex, moved);

    setState(() {
      _orderedLedgers = nextLedgers;
      _submitting = true;
    });

    final result = await appState.reorderLedgers(
      nextLedgers
          .map((ledger) => ledger['id'])
          .whereType<int>()
          .toList(growable: false),
    );
    if (!mounted) return;
    setState(() => _submitting = false);
    if (!result.ok) {
      _showMessage(result.message ?? '排序失败');
      await _reloadLedgers(appState);
      return;
    }
    await _reloadLedgers(appState);
  }

  Widget _buildLedgerCard(
    AppState appState,
    int index,
    Map<String, dynamic> ledger,
  ) {
    final isDefault = ledger['is_default'] == true || ledger['is_default'] == 1;
    final description = (ledger['description'] as String? ?? '').trim();

    return Container(
      key: ValueKey<int>(ledger['id'] as int),
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppTheme.cardGradient.first,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: AppTheme.isLight ? AppTheme.border : AppTheme.borderSubtle,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          (ledger['name'] as String?) ?? '账本',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: _titleStyle.copyWith(
                            color: AppTheme.textPrimary,
                          ),
                        ),
                      ),
                      if (isDefault)
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: AppTheme.accent.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(999),
                          ),
                          child: Text(
                            '默认',
                            style: _metaStyle.copyWith(color: AppTheme.accent),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(
                    description.isEmpty ? '拖动右侧把手调整显示顺序' : description,
                    style: _metaStyle.copyWith(color: AppTheme.textMuted),
                  ),
                ],
              ),
            ),
            IconButton(
              tooltip: '重命名',
              onPressed: _submitting
                  ? null
                  : () => _showRenameLedgerDialog(appState, ledger),
              icon: Icon(Icons.edit_outlined, color: AppTheme.textMuted),
            ),
            IconButton(
              tooltip: '删除',
              onPressed: _submitting || isDefault
                  ? null
                  : () => _deleteLedger(appState, ledger),
              icon: Icon(
                Icons.delete_outline,
                color: isDefault ? AppTheme.textMuted : AppTheme.danger,
              ),
            ),
            ReorderableDragStartListener(
              index: index,
              enabled: !_submitting,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 6),
                child: Icon(
                  Icons.drag_handle_rounded,
                  color: AppTheme.textMuted,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();
    final appStateSignature = appState.ledgers
        .map(
          (ledger) =>
              '${ledger['id']}:${ledger['name']}:${ledger['sort_order']}',
        )
        .join('|');
    final localSignature = _orderedLedgers
        .map(
          (ledger) =>
              '${ledger['id']}:${ledger['name']}:${ledger['sort_order']}',
        )
        .join('|');
    if (!_submitting && appStateSignature != localSignature) {
      _orderedLedgers = _cloneLedgers(appState.ledgers);
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('管理账本'),
        actions: [
          TextButton.icon(
            onPressed: _submitting
                ? null
                : () => _showCreateLedgerDialog(appState),
            icon: const Icon(Icons.add_rounded),
            label: const Text('新增'),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: IgnorePointer(
        ignoring: _submitting,
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  '投资页顶部的账本选择器会按这里的顺序展示。',
                  style: _metaStyle.copyWith(color: AppTheme.textMuted),
                ),
              ),
            ),
            Expanded(
              child: ReorderableListView.builder(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                buildDefaultDragHandles: false,
                itemCount: _orderedLedgers.length,
                onReorder: (oldIndex, newIndex) =>
                    _reorderLedgers(appState, oldIndex, newIndex),
                itemBuilder: (context, index) =>
                    _buildLedgerCard(appState, index, _orderedLedgers[index]),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
