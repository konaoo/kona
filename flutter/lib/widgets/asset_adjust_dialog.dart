import 'dart:async';

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../models/asset.dart';
import '../providers/app_state.dart';
import '../config/theme.dart';
import 'top_toast.dart';

/// 资产调整弹窗 - 增加/减少 tab + 名称 + 金额 + 备注 + 删除
class AssetAdjustDialog extends StatefulWidget {
  final Asset asset;
  final String assetType; // cash | other | liability
  final BuildContext hostContext;
  final VoidCallback? onDeleteSuccess;

  const AssetAdjustDialog({
    super.key,
    required this.asset,
    required this.assetType,
    required this.hostContext,
    this.onDeleteSuccess,
  });

  @override
  State<AssetAdjustDialog> createState() => _AssetAdjustDialogState();
}

class _AssetAdjustDialogState extends State<AssetAdjustDialog> {
  final _nameController = TextEditingController();
  final _amountController = TextEditingController();
  final _noteController = TextEditingController();
  final _nameFocusNode = FocusNode();
  final _amountFocusNode = FocusNode();

  String _mode = 'add'; // 'add' | 'sub'
  bool _saving = false;
  String? _nameError;
  String? _amountError;
  String? _errorText;

  // ── 颜色别名，与 AddAssetDialog 保持一致 ──
  Color get _kSurface => AppTheme.bgElevated;
  Color get _kSurface2 => AppTheme.surface2;
  Color get _kSurface3 => AppTheme.isLight ? Colors.white : AppTheme.surface3;
  Color get _kBorder => AppTheme.border;
  Color get _kBorderActive => AppTheme.accent;
  Color get _kText => AppTheme.textPrimary;
  Color get _kTextMuted => AppTheme.textSecondary;
  Color get _kGreen => AppTheme.success;
  Color get _kRed => AppTheme.danger;

  TextStyle _dm({double? size, FontWeight? weight, Color? color}) =>
      GoogleFonts.dmSans(fontSize: size, fontWeight: weight, color: color);

  TextStyle _mono({double? size, FontWeight? weight, Color? color}) =>
      GoogleFonts.jetBrainsMono(
        fontSize: size,
        fontWeight: weight,
        color: color,
      );

  @override
  void initState() {
    super.initState();
    _nameController.text = widget.asset.name;
    _nameFocusNode.addListener(() => setState(() {}));
    _amountFocusNode.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _nameController.dispose();
    _amountController.dispose();
    _noteController.dispose();
    _nameFocusNode.dispose();
    _amountFocusNode.dispose();
    super.dispose();
  }

  String _currencySymbol() {
    switch (widget.asset.curr.toUpperCase()) {
      case 'USD':
        return r'$';
      case 'HKD':
        return 'HK\$';
      default:
        return '¥';
    }
  }

  /// 与 AddAssetDialog 一致的输入框容器
  Widget _buildFieldContainer({
    required Widget child,
    required bool active,
    required bool hasError,
    double height = 40,
  }) {
    return Container(
      height: height,
      decoration: BoxDecoration(
        color: _kSurface2,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: hasError
              ? const Color(0x99F05A55)
              : active
              ? const Color(0x8C5B8DEF)
              : _kBorder,
          width: 1,
        ),
      ),
      child: child,
    );
  }

  /// 增加/减少 segmented tab
  Widget _buildSegmentedTab() {
    final isAdd = _mode == 'add';
    final addActiveBg = AppTheme.isLight
        ? const Color(0x2216A34A)
        : const Color(0x262ECC8A);
    final subActiveBg = AppTheme.isLight
        ? const Color(0x22E45656)
        : const Color(0x1EF05A55);

    return Container(
      height: 38,
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(
        color: _kSurface2,
        borderRadius: BorderRadius.circular(9),
      ),
      child: Row(
        children: [
          // ─ 增加 ─
          Expanded(
            child: GestureDetector(
              onTap: _saving ? null : () => setState(() => _mode = 'add'),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                decoration: BoxDecoration(
                  color: isAdd ? addActiveBg : Colors.transparent,
                  borderRadius: BorderRadius.circular(7),
                  boxShadow: isAdd
                      ? [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.2),
                            blurRadius: 4,
                            offset: const Offset(0, 1),
                          ),
                        ]
                      : [],
                ),
                alignment: Alignment.center,
                child: AnimatedDefaultTextStyle(
                  duration: const Duration(milliseconds: 150),
                  style: _dm(
                    size: 13,
                    weight: FontWeight.w500,
                    color: isAdd ? _kGreen : _kTextMuted,
                  ),
                  child: const Text('增加'),
                ),
              ),
            ),
          ),
          const SizedBox(width: 3),
          // ─ 减少 ─
          Expanded(
            child: GestureDetector(
              onTap: _saving ? null : () => setState(() => _mode = 'sub'),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                decoration: BoxDecoration(
                  color: !isAdd ? subActiveBg : Colors.transparent,
                  borderRadius: BorderRadius.circular(7),
                  boxShadow: !isAdd
                      ? [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.2),
                            blurRadius: 4,
                            offset: const Offset(0, 1),
                          ),
                        ]
                      : [],
                ),
                alignment: Alignment.center,
                child: AnimatedDefaultTextStyle(
                  duration: const Duration(milliseconds: 150),
                  style: _dm(
                    size: 13,
                    weight: FontWeight.w500,
                    color: !isAdd ? _kRed : _kTextMuted,
                  ),
                  child: const Text('减少'),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _submit() async {
    // 验证名称
    final name = _nameController.text.trim();
    if (name.isEmpty) {
      setState(() => _nameError = '账户名称不能为空');
      _nameFocusNode.requestFocus();
      return;
    }

    // 验证金额
    final deltaStr = _amountController.text.trim();
    final delta = double.tryParse(deltaStr);
    if (delta == null || delta <= 0) {
      setState(() => _amountError = '请输入有效金额');
      _amountFocusNode.requestFocus();
      return;
    }

    // 减少时不能超过余额
    final currentAmount = widget.asset.amount;
    if (_mode == 'sub' && delta > currentAmount.abs()) {
      setState(() => _amountError = '减少金额不能超过当前余额');
      return;
    }

    final newAmount = _mode == 'add'
        ? currentAmount + delta
        : currentAmount - delta;

    // 乐观成功：立即关闭弹窗，API 后台执行
    final note = _noteController.text.trim();
    final mode = _mode;
    final assetType = widget.assetType;
    final assetId = widget.asset.id!;
    final assetCurr = widget.asset.curr;
    final hostContext = widget.hostContext;
    final appState = context.read<AppState>();

    if (hostContext.mounted) {
      TopToast.showSuccess(hostContext, '已记录');
    }
    Navigator.of(context).pop({
      'mode': mode,
      'delta': delta,
      'note': note,
      'balanceAfter': newAmount,
    });

    // 后台调用 API，失败时补一条错误 toast
    unawaited(
      appState.adjustAsset(
        type: assetType,
        id: assetId,
        name: name,
        currentAmount: currentAmount,
        mode: mode,
        delta: delta,
        note: note,
        curr: assetCurr,
      ).then((result) {
        if (!result.ok && hostContext.mounted) {
          TopToast.showError(
            hostContext,
            result.message ?? '保存失败，请稍后重试',
          );
        }
      }),
    );
  }

  Future<void> _confirmAndDelete() async {
    if (_saving) return;
    final assetId = widget.asset.id;
    if (assetId == null || assetId <= 0) return;

    final confirmed =
        await showDialog<bool>(
          context: context,
          barrierColor: const Color(0x9E000000),
          builder: (dlgCtx) => Center(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 360),
                child: Material(
                  color: Colors.transparent,
                  child: Container(
                    decoration: BoxDecoration(
                      color: _kSurface,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: _kBorder),
                      boxShadow: AppTheme.isLight
                          ? const [
                              BoxShadow(
                                color: Color(0x26222C48),
                                blurRadius: 40,
                                offset: Offset(0, 16),
                              ),
                            ]
                          : const [
                              BoxShadow(
                                color: Color(0xB3000000),
                                blurRadius: 64,
                                offset: Offset(0, 24),
                              ),
                            ],
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Padding(
                          padding: const EdgeInsets.fromLTRB(16, 16, 16, 10),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '删除资产',
                                style: _dm(
                                  size: 14,
                                  weight: FontWeight.w600,
                                  color: _kText,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                '该操作不可撤销',
                                style: _dm(size: 11, color: _kTextMuted),
                              ),
                            ],
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                          child: Text(
                            '确定删除「${widget.asset.name}」吗？',
                            style: _dm(size: 13, color: _kTextMuted),
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                          child: Row(
                            children: [
                              Expanded(
                                child: SizedBox(
                                  height: 42,
                                  child: OutlinedButton(
                                    onPressed: () =>
                                        Navigator.of(dlgCtx).pop(false),
                                    style: OutlinedButton.styleFrom(
                                      backgroundColor: _kSurface2,
                                      side: BorderSide(
                                        color: _kBorder,
                                        width: 1,
                                      ),
                                      shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                    ),
                                    child: Text(
                                      '取消',
                                      style: _dm(
                                        size: 13,
                                        weight: FontWeight.w600,
                                        color: _kTextMuted,
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: SizedBox(
                                  height: 42,
                                  child: DecoratedBox(
                                    decoration: BoxDecoration(
                                      borderRadius: BorderRadius.circular(8),
                                      gradient: const LinearGradient(
                                        begin: Alignment.topLeft,
                                        end: Alignment.bottomRight,
                                        colors: [
                                          Color(0xFFF05A55),
                                          Color(0xFFDB4B46),
                                        ],
                                      ),
                                    ),
                                    child: ElevatedButton(
                                      onPressed: () =>
                                          Navigator.of(dlgCtx).pop(true),
                                      style: ElevatedButton.styleFrom(
                                        elevation: 0,
                                        backgroundColor: Colors.transparent,
                                        shadowColor: Colors.transparent,
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(
                                            8,
                                          ),
                                        ),
                                      ),
                                      child: Text(
                                        '确认删除',
                                        style: _dm(
                                          size: 13,
                                          weight: FontWeight.w600,
                                          color: Colors.white,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ) ??
        false;

    if (!confirmed || !mounted) return;

    setState(() => _saving = true);
    final appState = context.read<AppState>();

    final result = await appState.deleteAsset(
      type: widget.assetType,
      id: assetId,
      awaitRefresh: true,
    );

    if (!mounted) return;

    if (!result.ok) {
      setState(() {
        _saving = false;
        _errorText = result.message ?? '删除失败，请稍后重试';
      });
      if (widget.hostContext.mounted) {
        TopToast.showError(
          widget.hostContext,
          result.message ?? '删除失败，请稍后重试',
        );
      }
      return;
    }

    if (widget.hostContext.mounted) {
      TopToast.showSuccess(widget.hostContext, '已删除');
    }
    Navigator.of(context).pop(); // 关闭弹窗
    widget.onDeleteSuccess?.call(); // 返回详情页
  }

  @override
  Widget build(BuildContext context) {
    context.watch<AppState>();

    final isAdd = _mode == 'add';
    final okColor = isAdd ? _kGreen : _kRed;
    final sym = _currencySymbol();

    return Center(
      child: Padding(
        padding: EdgeInsets.only(
          left: 20,
          right: 20,
          top: 20,
          bottom: MediaQuery.of(context).viewInsets.bottom + 20,
        ),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 360),
          child: Material(
            color: Colors.transparent,
            child: Container(
              decoration: BoxDecoration(
                color: _kSurface,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: _kBorder),
                boxShadow: AppTheme.isLight
                    ? const [
                        BoxShadow(
                          color: Color(0x26222C48),
                          blurRadius: 40,
                          offset: Offset(0, 16),
                        ),
                      ]
                    : const [
                        BoxShadow(
                          color: Color(0xB3000000),
                          blurRadius: 64,
                          offset: Offset(0, 24),
                        ),
                      ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // ── 标题行 ──
                  Padding(
                    padding: const EdgeInsets.fromLTRB(18, 14, 14, 10),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '编辑资产',
                                style: _dm(
                                  size: 14,
                                  weight: FontWeight.w600,
                                  color: _kText,
                                ),
                              ),
                              Text(
                                '账户名称和金额为必填项',
                                style: _dm(size: 11, color: _kTextMuted),
                              ),
                            ],
                          ),
                        ),
                        // ··· 删除菜单
                        PopupMenuButton<String>(
                          enabled: !_saving,
                          color: _kSurface2,
                          elevation: 10,
                          tooltip: '更多操作',
                          offset: const Offset(0, 28),
                          constraints: const BoxConstraints(
                            minWidth: 116,
                            maxWidth: 116,
                          ),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                            side: BorderSide(color: _kBorderActive, width: 1),
                          ),
                          onSelected: (value) {
                            if (value == 'delete') _confirmAndDelete();
                          },
                          itemBuilder: (ctx) => [
                            PopupMenuItem<String>(
                              value: 'delete',
                              height: 34,
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 4,
                              ),
                              child: Text(
                                '删除资产',
                                style: _dm(
                                  size: 12,
                                  weight: FontWeight.w600,
                                  color: _kRed,
                                ),
                              ),
                            ),
                          ],
                          child: Container(
                            width: 24,
                            height: 24,
                            decoration: BoxDecoration(
                              color: _kSurface2,
                              shape: BoxShape.circle,
                              border: Border.all(color: _kBorder),
                            ),
                            alignment: Alignment.center,
                            child: Text(
                              '···',
                              style: _dm(
                                size: 14,
                                weight: FontWeight.w600,
                                color: _kTextMuted,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  // ── 表单区 ──
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // 账户名称
                        _buildFieldContainer(
                          active: _nameFocusNode.hasFocus,
                          hasError: _nameError != null,
                          child: TextField(
                            controller: _nameController,
                            focusNode: _nameFocusNode,
                            enabled: !_saving,
                            expands: true,
                            minLines: null,
                            maxLines: null,
                            textAlignVertical: TextAlignVertical.center,
                            style: _dm(size: 13, color: _kText),
                            decoration: InputDecoration(
                              filled: true,
                              fillColor: Colors.transparent,
                              hintText: '账户名称',
                              hintStyle: _dm(size: 12, color: _kTextMuted),
                              contentPadding: const EdgeInsets.symmetric(
                                horizontal: 11,
                                vertical: 10,
                              ),
                              border: InputBorder.none,
                              enabledBorder: InputBorder.none,
                              focusedBorder: InputBorder.none,
                              errorBorder: InputBorder.none,
                              focusedErrorBorder: InputBorder.none,
                              disabledBorder: InputBorder.none,
                            ),
                            onChanged: (_) {
                              if (_nameError != null) {
                                setState(() => _nameError = null);
                              }
                            },
                          ),
                        ),
                        if (_nameError != null) ...[
                          const SizedBox(height: 4),
                          Text(_nameError!, style: _dm(size: 10, color: _kRed)),
                        ],
                        const SizedBox(height: 10),

                        // 增加/减少 tab
                        _buildSegmentedTab(),
                        const SizedBox(height: 10),

                        // 金额输入
                        _buildFieldContainer(
                          active: _amountFocusNode.hasFocus,
                          hasError: _amountError != null,
                          child: Row(
                            children: [
                              const SizedBox(width: 12),
                              Text(
                                sym,
                                style: _dm(
                                  size: 16,
                                  weight: FontWeight.w500,
                                  color: _kTextMuted,
                                ),
                              ),
                              const SizedBox(width: 6),
                              Expanded(
                                child: TextField(
                                  controller: _amountController,
                                  focusNode: _amountFocusNode,
                                  enabled: !_saving,
                                  expands: true,
                                  minLines: null,
                                  maxLines: null,
                                  textAlignVertical: TextAlignVertical.center,
                                  keyboardType:
                                      const TextInputType.numberWithOptions(
                                        decimal: true,
                                      ),
                                  style: _mono(
                                    size: 18,
                                    weight: FontWeight.w500,
                                    color: _kText,
                                  ),
                                  decoration: InputDecoration(
                                    filled: true,
                                    fillColor: Colors.transparent,
                                    hintText: '0.00',
                                    hintStyle: _dm(
                                      size: 15,
                                      color: _kTextMuted,
                                    ),
                                    contentPadding: EdgeInsets.zero,
                                    border: InputBorder.none,
                                    enabledBorder: InputBorder.none,
                                    focusedBorder: InputBorder.none,
                                    errorBorder: InputBorder.none,
                                    focusedErrorBorder: InputBorder.none,
                                    disabledBorder: InputBorder.none,
                                  ),
                                  onChanged: (_) {
                                    if (_amountError != null) {
                                      setState(() => _amountError = null);
                                    }
                                  },
                                ),
                              ),
                              const SizedBox(width: 12),
                            ],
                          ),
                        ),
                        if (_amountError != null) ...[
                          const SizedBox(height: 4),
                          Text(
                            _amountError!,
                            style: _dm(size: 10, color: _kRed),
                          ),
                        ],
                        const SizedBox(height: 10),

                        // 备注
                        _buildFieldContainer(
                          active: false,
                          hasError: false,
                          height: 36,
                          child: Row(
                            children: [
                              const SizedBox(width: 12),
                              Icon(
                                Icons.edit_note_outlined,
                                size: 14,
                                color: _kTextMuted,
                              ),
                              const SizedBox(width: 7),
                              Expanded(
                                child: TextField(
                                  controller: _noteController,
                                  enabled: !_saving,
                                  expands: true,
                                  minLines: null,
                                  maxLines: null,
                                  textAlignVertical: TextAlignVertical.center,
                                  style: _dm(size: 13, color: _kText),
                                  decoration: InputDecoration(
                                    filled: true,
                                    fillColor: Colors.transparent,
                                    hintText: '备注（可选）',
                                    hintStyle: _dm(
                                      size: 12,
                                      color: _kTextMuted,
                                    ),
                                    contentPadding: EdgeInsets.zero,
                                    border: InputBorder.none,
                                    enabledBorder: InputBorder.none,
                                    focusedBorder: InputBorder.none,
                                    errorBorder: InputBorder.none,
                                    focusedErrorBorder: InputBorder.none,
                                    disabledBorder: InputBorder.none,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 12),
                            ],
                          ),
                        ),

                        if (_errorText != null) ...[
                          const SizedBox(height: 8),
                          Text(
                            _errorText!,
                            style: _dm(size: 11, color: _kRed),
                          ),
                        ],
                      ],
                    ),
                  ),

                  // ── 底部按钮 ──
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                    child: Row(
                      children: [
                        // 取消 (flex 1)
                        Expanded(
                          child: SizedBox(
                            height: 42,
                            child: OutlinedButton(
                              onPressed: _saving
                                  ? null
                                  : () => Navigator.of(context).pop(),
                              style: OutlinedButton.styleFrom(
                                backgroundColor: _kSurface2,
                                side: BorderSide(color: _kBorder, width: 1),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(8),
                                ),
                              ),
                              child: Text(
                                '取消',
                                style: _dm(
                                  size: 13,
                                  weight: FontWeight.w600,
                                  color: _kTextMuted,
                                ),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        // 确认 (flex 2, 颜色跟随 tab)
                        Expanded(
                          flex: 2,
                          child: SizedBox(
                            height: 42,
                            child: AnimatedContainer(
                              duration: const Duration(milliseconds: 200),
                              decoration: BoxDecoration(
                                color: _saving ? _kSurface3 : okColor,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Material(
                                color: Colors.transparent,
                                borderRadius: BorderRadius.circular(8),
                                child: InkWell(
                                  borderRadius: BorderRadius.circular(8),
                                  onTap: _saving ? null : _submit,
                                  child: Center(
                                    child: _saving
                                        ? const SizedBox(
                                            width: 16,
                                            height: 16,
                                            child: CircularProgressIndicator(
                                              strokeWidth: 2,
                                              valueColor:
                                                  AlwaysStoppedAnimation<Color>(
                                                    Colors.white,
                                                  ),
                                            ),
                                          )
                                        : Text(
                                            '确认',
                                            style: _dm(
                                              size: 13,
                                              weight: FontWeight.w600,
                                              color: Colors.white,
                                            ),
                                          ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
