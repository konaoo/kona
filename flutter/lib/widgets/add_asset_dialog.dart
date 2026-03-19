import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../models/asset.dart';
import '../providers/app_state.dart';
import '../config/theme.dart';
import 'top_toast.dart';

class AddAssetDialog extends StatefulWidget {
  final String? fixedAssetType; // cash | other | liability
  final Asset? editingAsset;
  final BuildContext? hostContext;
  final Set<String>? allowedAssetTypes;
  final String? initialCashCurrency;
  final bool lockCashCurrency;
  final bool returnCreatedAssetId;
  final bool allowDeleteInEdit;
  final VoidCallback? onDeleteSuccess;
  final String? dialogTitleOverride;

  const AddAssetDialog({
    super.key,
    this.fixedAssetType,
    this.editingAsset,
    this.hostContext,
    this.allowedAssetTypes,
    this.initialCashCurrency,
    this.lockCashCurrency = false,
    this.returnCreatedAssetId = false,
    this.allowDeleteInEdit = false,
    this.onDeleteSuccess,
    this.dialogTitleOverride,
  });

  @override
  State<AddAssetDialog> createState() => _AddAssetDialogState();
}

class _AddAssetDialogState extends State<AddAssetDialog> {
  static const Key nameFieldKey = Key('add_asset_name_field');
  static const Key amountFieldKey = Key('add_asset_amount_field');
  static const Key currencyTriggerKey = Key('add_asset_currency_trigger');
  static const Key submitButtonKey = Key('add_asset_submit_button');
  static const Key cancelButtonKey = Key('add_asset_cancel_button');

  static const _typeOrder = <String>['cash', 'other', 'liability'];
  static const _currencies = <({String code, String name, String flag})>[
    (code: 'CNY', name: '人民币', flag: '🇨🇳'),
    (code: 'USD', name: '美元', flag: '🇺🇸'),
    (code: 'HKD', name: '港币', flag: '🇭🇰'),
  ];

  final _nameController = TextEditingController();
  final _amountController = TextEditingController();
  final _nameFocusNode = FocusNode();
  final _amountFocusNode = FocusNode();
  final LayerLink _currencyLink = LayerLink();
  final GlobalKey _currencyTargetKey = GlobalKey();

  OverlayEntry? _currencyOverlayEntry;

  late final Set<String> _allowedTypes;
  String _assetType = 'cash';
  String _cashCurrency = 'CNY';

  bool _saving = false;

  String? _nameError;
  String? _amountError;
  String? _errorText;

  bool get _isEdit => widget.editingAsset != null;
  bool get _canDeleteInEdit => _isEdit && widget.allowDeleteInEdit;

  Color get _kSurface => AppTheme.bgElevated;
  Color get _kSurface2 => AppTheme.surface2;
  Color get _kSurface3 => AppTheme.isLight ? Colors.white : AppTheme.surface3;
  Color get _kBorder => AppTheme.border;
  Color get _kBorderActive => AppTheme.accent;
  Color get _kGold => AppTheme.gold;
  Color get _kGoldDim => AppTheme.goldDim;
  Color get _kText => AppTheme.textPrimary;
  Color get _kTextMuted => AppTheme.textSecondary;
  Color get _kGreen => AppTheme.success;
  Color get _kRed => AppTheme.danger;
  Color get _kBlueStart => AppTheme.accent;
  Color get _kBlueEnd => AppTheme.accentLight;

  LinearGradient get _blueGrad => LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [_kBlueStart, _kBlueEnd],
  );

  TextStyle _dm({double? size, FontWeight? weight, Color? color}) {
    return GoogleFonts.dmSans(fontSize: size, fontWeight: weight, color: color);
  }

  TextStyle _mono({double? size, FontWeight? weight, Color? color}) {
    return GoogleFonts.jetBrainsMono(
      fontSize: size,
      fontWeight: weight,
      color: color,
    );
  }

  String _normalizeCurrency(String? raw) {
    final code = (raw ?? '').trim().toUpperCase();
    if (code == 'USD' || code == 'HKD' || code == 'CNY') {
      return code;
    }
    return 'CNY';
  }

  String _formatAmountInput(double amount) {
    final rounded = amount.roundToDouble();
    if (rounded == amount) {
      return rounded.toStringAsFixed(0);
    }
    return amount.toString();
  }

  String _typeLabel(String type) {
    switch (type) {
      case 'cash':
        return '现金资产';
      case 'other':
        return '其他资产';
      case 'liability':
        return '我的负债';
      default:
        return '资产';
    }
  }

  ({String id, String label, Color color}) _typeOption(String type) {
    switch (type) {
      case 'cash':
        return (id: 'cash', label: '💰 现金资产', color: _kGreen);
      case 'other':
        return (id: 'other', label: '📦 其他资产', color: _kBlueStart);
      case 'liability':
      default:
        return (id: 'liability', label: '💳 我的负债', color: _kRed);
    }
  }

  List<String> get _orderedAllowedTypes {
    return _typeOrder.where(_allowedTypes.contains).toList(growable: false);
  }

  bool get _showTypeTabs {
    if (widget.fixedAssetType != null) return false;
    return _orderedAllowedTypes.length > 1;
  }

  bool get _canChangeCurrency {
    return !widget.lockCashCurrency;
  }

  List<Asset> _assetsByType(AppState appState, String type) {
    switch (type) {
      case 'cash':
        return appState.cashAssets;
      case 'other':
        return appState.otherAssets;
      case 'liability':
        return appState.liabilities;
      default:
        return const <Asset>[];
    }
  }

  Set<int> _assetIdsByType(AppState appState, String type) {
    return _assetsByType(
      appState,
      type,
    ).map((asset) => asset.id ?? 0).where((id) => id > 0).toSet();
  }

  @override
  void initState() {
    super.initState();

    final normalizedAllowed =
        (widget.allowedAssetTypes ?? const {'cash', 'other', 'liability'})
            .map((item) => item.trim())
            .where((item) => _typeOrder.contains(item))
            .toSet();

    _allowedTypes = normalizedAllowed.isEmpty
        ? <String>{'cash', 'other', 'liability'}
        : normalizedAllowed;

    if (widget.fixedAssetType != null &&
        _typeOrder.contains(widget.fixedAssetType)) {
      _allowedTypes.add(widget.fixedAssetType!);
      _assetType = widget.fixedAssetType!;
    } else {
      _assetType = _orderedAllowedTypes.first;
    }

    _cashCurrency = _normalizeCurrency(widget.initialCashCurrency);

    if (widget.editingAsset != null) {
      _nameController.text = widget.editingAsset!.name;
      _amountController.text = _formatAmountInput(widget.editingAsset!.amount);
      final curr = _normalizeCurrency(widget.editingAsset!.curr);
      _cashCurrency = curr;
    }

    _nameFocusNode.addListener(_onFocusChanged);
    _amountFocusNode.addListener(_onFocusChanged);
  }

  @override
  void dispose() {
    _hideCurrencyOverlay(updateState: false);
    _nameFocusNode.removeListener(_onFocusChanged);
    _amountFocusNode.removeListener(_onFocusChanged);
    _nameController.dispose();
    _amountController.dispose();
    _nameFocusNode.dispose();
    _amountFocusNode.dispose();
    super.dispose();
  }

  void _onFocusChanged() {
    if (!mounted) return;
    setState(() {});
  }

  Size _targetSize(GlobalKey key) {
    final targetContext = key.currentContext;
    if (targetContext == null) return const Size(280, 40);
    final box = targetContext.findRenderObject();
    if (box is! RenderBox) return const Size(280, 40);
    return box.size;
  }

  void _hideCurrencyOverlay({bool updateState = true}) {
    _currencyOverlayEntry?.remove();
    _currencyOverlayEntry = null;
    if (!mounted) return;
    if (updateState) {
      setState(() {});
    }
  }

  void _showCurrencyOverlay() {
    if (_saving || !_canChangeCurrency) return;
    if (_currencyOverlayEntry != null) {
      _currencyOverlayEntry?.markNeedsBuild();
      return;
    }

    final overlay = Overlay.of(context, rootOverlay: true);
    _currencyOverlayEntry = OverlayEntry(
      builder: (_) {
        final width = _targetSize(_currencyTargetKey).width;
        final offset = Offset(0, _targetSize(_currencyTargetKey).height + 6);
        return Stack(
          children: [
            Positioned.fill(
              child: GestureDetector(
                behavior: HitTestBehavior.translucent,
                onTap: _hideCurrencyOverlay,
                child: const SizedBox.expand(),
              ),
            ),
            CompositedTransformFollower(
              link: _currencyLink,
              showWhenUnlinked: false,
              offset: offset,
              child: Material(
                color: Colors.transparent,
                child: SizedBox(
                  width: width,
                  child: _buildCurrencyOverlayCard(),
                ),
              ),
            ),
          ],
        );
      },
    );
    overlay.insert(_currencyOverlayEntry!);
    if (mounted) setState(() {});
  }

  Widget _buildCurrencyOverlayCard() {
    return TweenAnimationBuilder<double>(
      tween: Tween<double>(begin: 0, end: 1),
      duration: const Duration(milliseconds: 180),
      curve: Curves.easeOutBack,
      builder: (context, value, child) {
        final opacity = value.clamp(0.0, 1.0).toDouble();
        return Opacity(
          opacity: opacity,
          child: Transform.translate(
            offset: Offset(0, (1 - opacity) * -5),
            child: child,
          ),
        );
      },
      child: Container(
        decoration: BoxDecoration(
          color: _kSurface2,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: _kBorderActive, width: 1),
          boxShadow: [
            BoxShadow(
              color: const Color(0x8C000000),
              blurRadius: 36,
              offset: const Offset(0, 16),
            ),
          ],
        ),
        child: MediaQuery.removePadding(
          context: context,
          removeTop: true,
          child: ListView.separated(
            padding: EdgeInsets.zero,
            primary: false,
            shrinkWrap: true,
            itemCount: _currencies.length,
            separatorBuilder: (_, index) => Divider(height: 1, color: _kBorder),
            itemBuilder: (context, index) {
              final option = _currencies[index];
              final selected = option.code == _cashCurrency;
              return InkWell(
                onTap: () {
                  setState(() => _cashCurrency = option.code);
                  _hideCurrencyOverlay();
                },
                child: Container(
                  color: selected ? _kGoldDim : Colors.transparent,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 13,
                    vertical: 10,
                  ),
                  child: Row(
                    children: [
                      Text(option.flag, style: _mono(size: 16, color: _kText)),
                      const SizedBox(width: 10),
                      SizedBox(
                        width: 40,
                        child: Text(
                          option.code,
                          style: _mono(
                            size: 13,
                            weight: FontWeight.w600,
                            color: _kText,
                          ),
                        ),
                      ),
                      Expanded(
                        child: Text(
                          option.name,
                          style: _dm(size: 12, color: _kTextMuted),
                        ),
                      ),
                      if (selected) Icon(Icons.check, size: 13, color: _kGold),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  Future<void> _submit() async {
    if (_saving) return;

    final name = _nameController.text.trim();
    final amountText = _amountController.text.trim();
    final amount = double.tryParse(amountText);

    setState(() {
      _nameError = null;
      _amountError = null;
      _errorText = null;
    });

    var valid = true;
    if (name.isEmpty) {
      _nameError = '请输入账户名称';
      valid = false;
    }
    if (amount == null || amount <= 0) {
      _amountError = '请输入有效金额';
      valid = false;
    }
    if (!valid) {
      setState(() {});
      return;
    }

    final appState = context.read<AppState>();
    final toastContext = widget.hostContext ?? context;

    if (_isEdit && widget.editingAsset?.id == null) {
      setState(() {
        _errorText = '资产ID无效，无法保存';
      });
      return;
    }

    final beforeIds = _assetIdsByType(appState, _assetType);

    setState(() {
      _saving = true;
    });

    final result = _isEdit
        ? await appState.updateAsset(
            type: _assetType,
            id: widget.editingAsset!.id!,
            name: name,
            amount: amount!,
            curr: _cashCurrency,
            awaitRefresh: true,
          )
        : await appState.addAsset(
            type: _assetType,
            name: name,
            amount: amount!,
            curr: _cashCurrency,
            awaitRefresh: true,
          );

    if (!mounted) return;

    if (!result.ok) {
      setState(() {
        _saving = false;
        _errorText = result.message ?? '保存失败，请稍后重试';
      });
      if (toastContext.mounted) {
        TopToast.showError(toastContext, result.message ?? '保存失败，请稍后重试');
      }
      return;
    }

    int? createdId;
    if (!_isEdit) {
      final afterAssets = _assetsByType(
        appState,
        _assetType,
      ).where((asset) => (asset.id ?? 0) > 0).toList();
      final fresh =
          afterAssets
              .where((asset) => !beforeIds.contains(asset.id ?? 0))
              .toList()
            ..sort((a, b) => (b.id ?? 0).compareTo(a.id ?? 0));

      if (fresh.isNotEmpty) {
        createdId = fresh.first.id;
      } else {
        final byName =
            afterAssets.where((asset) => asset.name.trim() == name).toList()
              ..sort((a, b) => (b.id ?? 0).compareTo(a.id ?? 0));
        if (byName.isNotEmpty) {
          createdId = byName.first.id;
        }
      }
    }

    if (toastContext.mounted) {
      TopToast.showSuccess(toastContext, _isEdit ? '已保存' : '已创建');
    }

    if (widget.returnCreatedAssetId && !_isEdit) {
      Navigator.of(context).pop(createdId);
      return;
    }
    Navigator.of(context).pop();
  }

  Future<bool> _confirmDelete() async {
    return (await showDialog<bool>(
          context: context,
          barrierColor: const Color(0x9E000000),
          builder: (dialogContext) {
            return Center(
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
                              '确定删除「${widget.editingAsset?.name ?? ''}」吗？',
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
                                      onPressed: () => Navigator.of(
                                        dialogContext,
                                      ).pop(false),
                                      style: OutlinedButton.styleFrom(
                                        backgroundColor: _kSurface2,
                                        side: BorderSide(
                                          color: _kBorder,
                                          width: 1,
                                        ),
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(
                                            8,
                                          ),
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
                                        onPressed: () => Navigator.of(
                                          dialogContext,
                                        ).pop(true),
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
            );
          },
        )) ??
        false;
  }

  Future<void> _deleteInEditMode() async {
    if (_saving || !_canDeleteInEdit) return;
    final editingId = widget.editingAsset?.id;
    if (editingId == null || editingId <= 0) {
      setState(() {
        _errorText = '资产ID无效，无法删除';
      });
      return;
    }

    _hideCurrencyOverlay(updateState: false);
    final confirmed = await _confirmDelete();
    if (!confirmed || !mounted) return;

    final appState = context.read<AppState>();
    final toastContext = widget.hostContext ?? context;

    setState(() {
      _saving = true;
      _errorText = null;
    });

    final result = await appState.deleteAsset(
      type: _assetType,
      id: editingId,
      awaitRefresh: true,
    );
    if (!mounted) return;

    if (!result.ok) {
      setState(() {
        _saving = false;
        _errorText = result.message ?? '删除失败，请稍后重试';
      });
      if (toastContext.mounted) {
        TopToast.showError(toastContext, result.message ?? '删除失败，请稍后重试');
      }
      return;
    }

    if (toastContext.mounted) {
      TopToast.showSuccess(toastContext, '已删除');
    }
    widget.onDeleteSuccess?.call();
    Navigator.of(context).pop();
  }

  Widget _buildTypeTabs() {
    final options = _orderedAllowedTypes
        .map(_typeOption)
        .toList(growable: false);
    return Container(
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(
        color: _kSurface2,
        borderRadius: BorderRadius.circular(9),
      ),
      child: Row(
        children: [
          for (final option in options)
            Expanded(
              child: GestureDetector(
                onTap: _saving
                    ? null
                    : () {
                        setState(() {
                          _assetType = option.id;
                          _hideCurrencyOverlay(updateState: false);
                        });
                      },
                child: SizedBox(
                  height: 32,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      // Animated background for selected state
                      AnimatedOpacity(
                        duration: const Duration(milliseconds: 150),
                        opacity: _assetType == option.id ? 1.0 : 0.0,
                        curve: Curves.easeInOut,
                        child: Container(
                          decoration: BoxDecoration(
                            color: _kSurface3,
                            borderRadius: BorderRadius.circular(7),
                            boxShadow: AppTheme.isLight
                                ? [
                                    BoxShadow(
                                      color: const Color(0x1F222C48),
                                      blurRadius: 4,
                                      offset: const Offset(0, 1),
                                    ),
                                  ]
                                : [
                                    BoxShadow(
                                      color: const Color(0x4D000000),
                                      blurRadius: 4,
                                      offset: const Offset(0, 1),
                                    ),
                                  ],
                          ),
                        ),
                      ),
                      // Text
                      AnimatedDefaultTextStyle(
                        duration: const Duration(milliseconds: 150),
                        style: _dm(
                          size: 12,
                          weight: FontWeight.w500,
                          color: _assetType == option.id
                              ? option.color
                              : _kTextMuted,
                        ),
                        child: Text(option.label),
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildCurrencySelector() {
    final selected = _currencies.firstWhere(
      (item) => item.code == _cashCurrency,
    );
    final isOverlayOpen = _currencyOverlayEntry != null;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('币种', style: _dm(size: 11, color: _kTextMuted)),
        const SizedBox(height: 5),
        CompositedTransformTarget(
          link: _currencyLink,
          child: Container(
            key: _currencyTargetKey,
            height: 40,
            decoration: BoxDecoration(
              color: _kSurface2,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: isOverlayOpen ? _kBorderActive : _kBorder,
                width: 1,
              ),
            ),
            child: InkWell(
              key: currencyTriggerKey,
              onTap: (_saving || !_canChangeCurrency)
                  ? null
                  : () {
                      if (_currencyOverlayEntry != null) {
                        _hideCurrencyOverlay();
                      } else {
                        _showCurrencyOverlay();
                      }
                    },
              borderRadius: BorderRadius.circular(8),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(12, 0, 10, 0),
                child: Row(
                  children: [
                    Text(selected.flag, style: _mono(size: 16, color: _kText)),
                    const SizedBox(width: 8),
                    Text(
                      selected.code,
                      style: _mono(
                        size: 13,
                        weight: FontWeight.w600,
                        color: _kText,
                      ),
                    ),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        selected.name,
                        style: _dm(size: 12, color: _kTextMuted),
                      ),
                    ),
                    AnimatedRotation(
                      turns: isOverlayOpen ? 0.5 : 0,
                      duration: const Duration(milliseconds: 200),
                      child: Icon(
                        Icons.keyboard_arrow_down,
                        size: 18,
                        color: _kTextMuted,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildRequiredLabel(String text) {
    return Row(
      children: [
        Container(
          width: 4,
          height: 4,
          decoration: const BoxDecoration(
            color: Color(0xFF5B8DEF),
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 4),
        Text(text, style: _dm(size: 11, color: _kTextMuted)),
      ],
    );
  }

  Widget _buildFieldContainer({
    required Widget child,
    required bool active,
    required bool hasError,
  }) {
    return Container(
      height: 40,
      decoration: BoxDecoration(
        color: _kSurface2,
        borderRadius: BorderRadius.circular(8),
        // Keep a single-layer border in dark mode to avoid "double stroke" artifacts.
        border: Border.all(
          color: hasError
              ? const Color(0x99F05A55)
              : active
              ? const Color(0x8C5B8DEF)
              : _kBorder,
          width: 1,
        ),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(7),
        child: child,
      ),
    );
  }

  String _dialogTitle() {
    if (widget.dialogTitleOverride != null &&
        widget.dialogTitleOverride!.trim().isNotEmpty) {
      return widget.dialogTitleOverride!.trim();
    }
    if (_isEdit) return '编辑${_typeLabel(_assetType)}';
    if (widget.fixedAssetType != null) return '添加${_typeLabel(_assetType)}';
    return '记一笔';
  }

  @override
  Widget build(BuildContext context) {
    // 监听全局状态变化，使得主题切换能够及时生效
    context.watch<AppState>();
    final canSubmit = !_saving;
    final suffixCurrency = _cashCurrency;

    return Center(
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
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(18, 14, 14, 10),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                _dialogTitle(),
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
                        if (_canDeleteInEdit)
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
                              if (value == 'delete') {
                                _deleteInEditMode();
                              }
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
                          )
                        else
                          InkWell(
                            onTap: _saving
                                ? null
                                : () => Navigator.of(context).pop(),
                            borderRadius: BorderRadius.circular(12),
                            child: Container(
                              width: 24,
                              height: 24,
                              decoration: BoxDecoration(
                                color: _kSurface2,
                                shape: BoxShape.circle,
                              ),
                              child: Icon(
                                Icons.close,
                                size: 10,
                                color: _kTextMuted,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(18, 0, 18, 14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (_showTypeTabs) ...[
                          _buildTypeTabs(),
                          const SizedBox(height: 14),
                        ],
                        _buildCurrencySelector(),
                        const SizedBox(height: 14),
                        _buildRequiredLabel('账户名称'),
                        const SizedBox(height: 5),
                        _buildFieldContainer(
                          active: _nameFocusNode.hasFocus,
                          hasError: _nameError != null,
                          child: TextField(
                            key: nameFieldKey,
                            controller: _nameController,
                            focusNode: _nameFocusNode,
                            enabled: !_saving,
                            maxLines: 1,
                            textAlignVertical: TextAlignVertical.center,
                            style: _dm(size: 13, color: _kText),
                            decoration: InputDecoration(
                              isDense: true,
                              filled: true,
                              fillColor: Colors.transparent,
                              hintText: '如：招商银行储蓄卡',
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
                        const SizedBox(height: 12),
                        _buildRequiredLabel('金额'),
                        const SizedBox(height: 5),
                        _buildFieldContainer(
                          active: _amountFocusNode.hasFocus,
                          hasError: _amountError != null,
                          child: TextField(
                            key: amountFieldKey,
                            controller: _amountController,
                            focusNode: _amountFocusNode,
                            enabled: !_saving,
                            maxLines: 1,
                            textAlignVertical: TextAlignVertical.center,
                            keyboardType: const TextInputType.numberWithOptions(
                              decimal: true,
                            ),
                            style: _mono(size: 13, color: _kText),
                            decoration: InputDecoration(
                              isDense: true,
                              filled: true,
                              fillColor: Colors.transparent,
                              hintText: '请输入金额',
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
                              suffixText: suffixCurrency,
                              suffixStyle: _dm(size: 11, color: _kTextMuted),
                            ),
                            onChanged: (_) {
                              if (_amountError != null) {
                                setState(() => _amountError = null);
                              }
                            },
                          ),
                        ),
                        if (_amountError != null) ...[
                          const SizedBox(height: 4),
                          Text(
                            _amountError!,
                            style: _dm(size: 10, color: _kRed),
                          ),
                        ],
                        if (_errorText != null) ...[
                          const SizedBox(height: 8),
                          Text(_errorText!, style: _dm(size: 11, color: _kRed)),
                        ],
                      ],
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(18, 0, 18, 18),
                    child: Row(
                      children: [
                        Expanded(
                          child: SizedBox(
                            height: 42,
                            child: OutlinedButton(
                              key: cancelButtonKey,
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
                        Expanded(
                          child: SizedBox(
                            height: 42,
                            child: DecoratedBox(
                              decoration: BoxDecoration(
                                color: canSubmit ? null : _kSurface3,
                                gradient: canSubmit ? _blueGrad : null,
                                borderRadius: BorderRadius.circular(8),
                                border: canSubmit
                                    ? null
                                    : Border.all(color: _kBorder, width: 1),
                              ),
                              child: ElevatedButton(
                                key: submitButtonKey,
                                onPressed: canSubmit ? _submit : null,
                                style: ElevatedButton.styleFrom(
                                  elevation: 0,
                                  backgroundColor: Colors.transparent,
                                  shadowColor: Colors.transparent,
                                  disabledBackgroundColor: Colors.transparent,
                                  disabledForegroundColor: _kTextMuted,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                ),
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
                                        _isEdit ? '保存' : '创建账户',
                                        style: _dm(
                                          size: 13,
                                          weight: FontWeight.w600,
                                          color: canSubmit
                                              ? Colors.white
                                              : _kTextMuted,
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
