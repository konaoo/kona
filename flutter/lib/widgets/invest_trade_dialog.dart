import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../providers/app_state.dart';
import '../models/asset_action_result.dart';
import '../models/portfolio.dart';
import '../models/asset.dart';
import 'add_funding_account_dialog.dart';
import 'top_toast.dart';

enum InvestTradeDialogPresentation { sheet, centered }

class _AdjustModeOption {
  final String value;
  final String label;

  const _AdjustModeOption(this.value, this.label);
}

class _ResolvedAdjustPayload {
  final double qty;
  final double price;
  final double adjustment;

  const _ResolvedAdjustPayload({
    required this.qty,
    required this.price,
    required this.adjustment,
  });
}

Future<T?> showInvestTradeSheet<T>({
  required BuildContext context,
  required String mode,
  PortfolioItem? item,
  BuildContext? hostContext,
  Future<void> Function()? onPortfolioChanged,
  String? initialTradeMode,
  InvestTradeDialogPresentation presentation =
      InvestTradeDialogPresentation.sheet,
}) {
  if (presentation == InvestTradeDialogPresentation.centered) {
    return showDialog<T>(
      context: context,
      barrierDismissible: true,
      barrierColor: const Color(0x8C000000),
      builder: (_) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: InvestTradeDialog(
          mode: mode,
          item: item,
          hostContext: hostContext,
          onPortfolioChanged: onPortfolioChanged,
          initialTradeMode: initialTradeMode,
          presentation: presentation,
        ),
      ),
    );
  }

  return showModalBottomSheet<T>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    barrierColor: const Color(0x8C000000),
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(18)),
    ),
    builder: (_) => Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
      ),
      child: InvestTradeDialog(
        mode: mode,
        item: item,
        hostContext: hostContext,
        onPortfolioChanged: onPortfolioChanged,
        initialTradeMode: initialTradeMode,
        presentation: presentation,
      ),
    ),
  );
}

class _InvestSheetTokens {
  final Color bg;
  final Color surface;
  final Color surface2;
  final Color surface3;
  final Color border;
  final Color borderActive;
  final Color gold;
  final Color goldDim;
  final Color goldGlow;
  final Color text;
  final Color textMuted;
  final Color textSub;
  final Color green;
  final Color red;
  final Color blueStart;
  final Color blueEnd;
  final Color divider;

  const _InvestSheetTokens({
    required this.bg,
    required this.surface,
    required this.surface2,
    required this.surface3,
    required this.border,
    required this.borderActive,
    required this.gold,
    required this.goldDim,
    required this.goldGlow,
    required this.text,
    required this.textMuted,
    required this.textSub,
    required this.green,
    required this.red,
    required this.blueStart,
    required this.blueEnd,
    required this.divider,
  });

  LinearGradient get blueGrad => LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [blueStart, blueEnd],
  );
}

class _SearchCacheEntry {
  final List<dynamic> results;
  final DateTime savedAt;

  const _SearchCacheEntry({required this.results, required this.savedAt});
}

class InvestTradeDialog extends StatefulWidget {
  final String mode; // add | buy | sell
  final PortfolioItem? item;
  final BuildContext? hostContext;
  final Future<void> Function()? onPortfolioChanged;
  final String? initialTradeMode;
  final InvestTradeDialogPresentation presentation;

  const InvestTradeDialog({
    super.key,
    required this.mode,
    this.item,
    this.hostContext,
    this.onPortfolioChanged,
    this.initialTradeMode,
    this.presentation = InvestTradeDialogPresentation.sheet,
  });

  @override
  State<InvestTradeDialog> createState() => _InvestTradeDialogState();
}

class _InvestTradeDialogState extends State<InvestTradeDialog> {
  final _queryController = TextEditingController();
  final _queryFocusNode = FocusNode();
  final _priceFocusNode = FocusNode();
  final _qtyFocusNode = FocusNode();
  final _amountFocusNode = FocusNode();
  final _adjustAmountFocusNode = FocusNode();
  final _noteFocusNode = FocusNode();
  final _priceController = TextEditingController();
  final _qtyController = TextEditingController();
  final _amountController = TextEditingController();
  final _adjustController = TextEditingController();
  final _noteController = TextEditingController();
  final LayerLink _searchFieldLink = LayerLink();
  final LayerLink _cashFieldLink = LayerLink();
  final LayerLink _adjustTypeFieldLink = LayerLink();
  final GlobalKey _searchTargetKey = GlobalKey();
  final GlobalKey _cashTargetKey = GlobalKey();
  final GlobalKey _adjustTypeTargetKey = GlobalKey();

  bool _saving = false;
  bool _inlineClosed = false;
  bool _searching = false;
  bool _navLoading = false;
  String? _errorText;
  String? _searchErrorText;
  String? _navErrorText;
  List<dynamic> _results = [];
  Map<String, dynamic>? _selected;
  String _tradeMode = 'buy';
  String _adjustType = 'cost_price';
  String _fundInputMode = 'qty';
  int? _selectedCashAssetId;
  int _searchSeq = 0;
  int _navFetchSeq = 0;
  OverlayEntry? _searchOverlayEntry;
  OverlayEntry? _cashOverlayEntry;
  OverlayEntry? _adjustTypeOverlayEntry;
  bool _searchOverlayVisible = false;
  bool _cashOverlayVisible = false;
  bool _adjustTypeOverlayVisible = false;
  bool _searchTriggered = false;
  bool _syncingAmountQty = false;
  final Map<String, _SearchCacheEntry> _searchCache =
      <String, _SearchCacheEntry>{};
  static const Duration _searchCacheTtl = Duration(seconds: 20);
  static const int _maxRecentCashAssets = 5;
  static final List<int> _recentCashAssetIds = <int>[];
  static final List<TextInputFormatter> _qtyInputFormatters =
      <TextInputFormatter>[
        FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d{0,2}$')),
      ];
  static final List<TextInputFormatter> _fundQtyInputFormatters =
      <TextInputFormatter>[
        FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d{0,4}$')),
      ];
  static const Key _sheetRootKey = Key('invest_sheet_root');
  static const Key _sheetHandleKey = Key('invest_sheet_handle');
  static const Key _searchFieldKey = Key('invest_search_field');
  static const Key _searchButtonKey = Key('invest_search_button');
  static const Key _cashTriggerKey = Key('invest_cash_trigger');
  static const Key _priceFieldKey = Key('invest_price_field');
  static const Key _qtyFieldKey = Key('invest_qty_field');
  static const Key _amountFieldKey = Key('invest_amount_field');
  static const Key _adjustAmountFieldKey = Key('invest_adjust_amount_field');
  static const Key _noteFieldKey = Key('invest_note_field');
  static const Key _submitButtonKey = Key('invest_submit_button');
  static const Key _cancelButtonKey = Key('invest_cancel_button');
  static const List<_AdjustModeOption> _adjustModeOptions = [
    _AdjustModeOption('cost_price', '成本价'),
    _AdjustModeOption('quantity', '数量'),
    _AdjustModeOption('dividend', '分红'),
    _AdjustModeOption('fee', '手续费'),
  ];

  bool get _isAdd => widget.mode == 'add';
  bool get _isBuy => widget.mode == 'buy';
  bool get _isSell => widget.mode == 'sell';
  bool get _isTrade => widget.mode == 'trade';
  bool get _isAdjust => _tradeMode == 'adjust';
  bool get _isDirectAdjustEntry =>
      _isTrade && widget.initialTradeMode == 'adjust';

  _InvestSheetTokens get _tokens {
    if (AppTheme.isLight) {
      return const _InvestSheetTokens(
        bg: Color(0xFFF5F2ED),
        surface: Color(0xFFFFFFFF),
        surface2: Color(0xFFF4F6FA),
        surface3: Color(0xFFE9EDF5),
        border: Color(0x140E1628),
        borderActive: Color(0x73D4AF64),
        gold: Color(0xFFD4AF64),
        goldDim: Color(0x1FD4AF64),
        goldGlow: Color(0x12D4AF64),
        text: Color(0xFF1F2A37),
        textMuted: Color(0xFF7B8494),
        textSub: Color(0xFF8C94A4),
        green: Color(0xFF16A34A),
        red: Color(0xFFE45656),
        blueStart: Color(0xFF5B8DEF),
        blueEnd: Color(0xFF4A7BE0),
        divider: Color(0x140E1628),
      );
    }
    return const _InvestSheetTokens(
      bg: Color(0xFF0D0E12),
      surface: Color(0xFF13151B),
      surface2: Color(0xFF1A1D25),
      surface3: Color(0xFF20242E),
      border: Color(0x12FFFFFF),
      borderActive: Color(0x73D4AF64),
      gold: Color(0xFFD4AF64),
      goldDim: Color(0x1FD4AF64),
      goldGlow: Color(0x12D4AF64),
      text: Color(0xFFE4E5EA),
      textMuted: Color(0xFF575D6E),
      textSub: Color(0xFF888FA0),
      green: Color(0xFF3ECF82),
      red: Color(0xFFF05A55),
      blueStart: Color(0xFF5B8DEF),
      blueEnd: Color(0xFF4A7BE0),
      divider: Color(0x1CFFFFFF),
    );
  }

  TextStyle _dm({
    double? size,
    FontWeight? weight,
    Color? color,
    double? letterSpacing,
  }) {
    return GoogleFonts.dmSans(
      fontSize: size,
      fontWeight: weight,
      color: color,
      letterSpacing: letterSpacing,
    );
  }

  TextStyle _mono({
    double? size,
    FontWeight? weight,
    Color? color,
    double? letterSpacing,
  }) {
    return GoogleFonts.jetBrainsMono(
      fontSize: size,
      fontWeight: weight,
      color: color,
      letterSpacing: letterSpacing,
    );
  }

  @override
  void initState() {
    super.initState();
    _queryController.addListener(_onInputControllerChanged);
    _priceController.addListener(_onPriceChanged);
    _qtyController.addListener(_onQtyChanged);
    _amountController.addListener(_onAmountChanged);
    _adjustController.addListener(_onInputControllerChanged);
    _noteController.addListener(_onInputControllerChanged);
    _queryFocusNode.addListener(_onQueryFocusChanged);
    _priceFocusNode.addListener(_onInputControllerChanged);
    _qtyFocusNode.addListener(_onInputControllerChanged);
    _amountFocusNode.addListener(_onInputControllerChanged);
    _adjustAmountFocusNode.addListener(_onInputControllerChanged);
    _noteFocusNode.addListener(_onInputControllerChanged);
    _syncDefaultCashAsset();
    if (!_isAdd && widget.item != null) {
      _prefillPriceFromCurrent();
      if (_isTrade) {
        _tradeMode = widget.initialTradeMode ?? 'buy';
        _adjustType = 'cost_price';
        _adjustController.clear();
        if (_isCurrentFundTarget()) {
          _fundInputMode = 'amount';
          unawaited(_prefillFundNavForCode(widget.item!.code));
        }
      }
    }
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _syncDefaultCashAsset();
  }

  @override
  void dispose() {
    _queryController.removeListener(_onInputControllerChanged);
    _priceController.removeListener(_onPriceChanged);
    _qtyController.removeListener(_onQtyChanged);
    _amountController.removeListener(_onAmountChanged);
    _adjustController.removeListener(_onInputControllerChanged);
    _noteController.removeListener(_onInputControllerChanged);
    _queryFocusNode.removeListener(_onQueryFocusChanged);
    _priceFocusNode.removeListener(_onInputControllerChanged);
    _qtyFocusNode.removeListener(_onInputControllerChanged);
    _amountFocusNode.removeListener(_onInputControllerChanged);
    _adjustAmountFocusNode.removeListener(_onInputControllerChanged);
    _noteFocusNode.removeListener(_onInputControllerChanged);
    _hideSearchOverlay(updateState: false);
    _hideCashOverlay(updateState: false);
    _hideAdjustTypeOverlay(updateState: false);
    _queryFocusNode.dispose();
    _priceFocusNode.dispose();
    _qtyFocusNode.dispose();
    _amountFocusNode.dispose();
    _adjustAmountFocusNode.dispose();
    _noteFocusNode.dispose();
    _queryController.dispose();
    _priceController.dispose();
    _qtyController.dispose();
    _amountController.dispose();
    _adjustController.dispose();
    _noteController.dispose();
    super.dispose();
  }

  void _onInputControllerChanged() {
    if (!mounted) return;
    setState(() {});
    _markOverlaysNeedsBuild();
  }

  void _setControllerText(TextEditingController controller, String nextText) {
    if (controller.text == nextText) return;
    controller.value = TextEditingValue(
      text: nextText,
      selection: TextSelection.collapsed(offset: nextText.length),
    );
  }

  double? _parsePositive(String text) {
    final value = double.tryParse(text.trim());
    if (value == null || value <= 0) return null;
    return value;
  }

  void _syncAmountFromPriceQty() {
    if (_syncingAmountQty || _isAdjust || _isFundAmountMode()) return;
    final price = _parsePositive(_priceController.text);
    final qty = _parsePositive(_qtyController.text);
    if (price == null || qty == null) {
      if (_amountController.text.isNotEmpty) {
        _syncingAmountQty = true;
        _setControllerText(_amountController, '');
        _syncingAmountQty = false;
      }
      return;
    }
    final amount = price * qty;
    final decimals = _isCurrentFundTarget() ? 4 : 2;
    final text = _formatInputNumber(amount, decimals: decimals);
    _syncingAmountQty = true;
    _setControllerText(_amountController, text);
    _syncingAmountQty = false;
  }

  void _syncQtyFromAmount() {
    if (_syncingAmountQty || _isAdjust || _isFundAmountMode()) return;
    final price = _parsePositive(_priceController.text);
    final amount = _parsePositive(_amountController.text);
    if (price == null || amount == null) return;
    final rawQty = amount / price;
    if (rawQty <= 0) return;
    final isFund = _isCurrentFundTarget();
    final qty = isFund
        ? (rawQty * 10000).floor() / 10000
        : rawQty.floorToDouble();
    final nextQty = isFund ? _formatQtyDisplay(qty) : qty.toStringAsFixed(0);
    _syncingAmountQty = true;
    _setControllerText(_qtyController, nextQty);
    _syncingAmountQty = false;
  }

  void _onPriceChanged() {
    if (_syncingAmountQty) return;
    _syncAmountFromPriceQty();
    _onInputControllerChanged();
  }

  void _onQtyChanged() {
    if (_syncingAmountQty) return;
    _syncAmountFromPriceQty();
    _onInputControllerChanged();
  }

  void _onAmountChanged() {
    if (_syncingAmountQty) return;
    if (_amountFocusNode.hasFocus) {
      _syncQtyFromAmount();
    }
    _onInputControllerChanged();
  }

  void _onQueryFocusChanged() {
    if (!_queryFocusNode.hasFocus || !_isAdd || _selected != null) return;
    _hideSearchOverlay();
  }

  String _formatDisplayCode(String code) {
    const customMap = {'ft_LU1116320737': 'BLK'};
    if (customMap.containsKey(code)) {
      return customMap[code]!;
    }
    var c = code;
    if (c.toLowerCase().startsWith('gb_')) {
      c = c.substring(3).toUpperCase();
    } else if (c.toLowerCase().startsWith('f_')) {
      c = c.substring(2);
    } else if (c.toLowerCase().startsWith('ft_')) {
      c = c.substring(3);
    } else if (c.toLowerCase().startsWith('sh') ||
        c.toLowerCase().startsWith('sz') ||
        c.toLowerCase().startsWith('bj')) {
      c = c.substring(2);
    }
    if (c.toUpperCase().endsWith('.HK')) {
      c = c.substring(0, c.length - 3);
    }
    return c;
  }

  void _onQueryChanged(String value) {
    final next = value.trim();
    final selectedName = (_selected?['name']?.toString() ?? '').trim();
    if (_selected != null && next.isNotEmpty && next == selectedName) {
      return;
    }
    setState(() {
      _selected = null;
      _errorText = null;
      _searchErrorText = null;
      _navErrorText = null;
      _navLoading = false;
      _fundInputMode = 'qty';
      _amountController.clear();
      _searching = false;
      _searchSeq += 1;
      _navFetchSeq += 1;
      _searchTriggered = false;
      _results = [];
    });
    _hideSearchOverlay();
    if (next.isEmpty) return;
  }

  Future<void> _onSearchTap() async {
    if (_searching) return;
    final query = _queryController.text.trim();
    if (query.isEmpty) {
      setState(() {
        _searchErrorText = '请输入代码或名称';
        _searchTriggered = false;
      });
      _hideSearchOverlay();
      return;
    }
    await _search(query);
    if (!mounted) return;
    if ((_searchErrorText ?? '').isNotEmpty) {
      setState(() => _searchTriggered = false);
      _hideSearchOverlay();
      return;
    }
    setState(() => _searchTriggered = true);
    _showSearchOverlay();
  }

  Future<void> _search(String query) async {
    final key = query.toLowerCase();
    final now = DateTime.now();
    final cached = _searchCache[key];
    if (cached != null && now.difference(cached.savedAt) < _searchCacheTtl) {
      if (!mounted) return;
      setState(() {
        _results = cached.results;
        _searching = false;
        _searchErrorText = null;
      });
      _markOverlaysNeedsBuild();
      return;
    }

    final seq = ++_searchSeq;
    setState(() {
      _searching = true;
      _searchErrorText = null;
    });
    final appState = context.read<AppState>();
    List<dynamic> results;
    try {
      results = await appState.searchStocks(query);
    } catch (_) {
      if (!mounted || seq != _searchSeq) return;
      setState(() {
        _searching = false;
        _searchErrorText = '搜索失败，请稍后重试';
      });
      _markOverlaysNeedsBuild();
      return;
    }
    if (!mounted) return;
    if (seq != _searchSeq) return;

    _searchCache[key] = _SearchCacheEntry(results: results, savedAt: now);
    setState(() {
      _results = results;
      _searching = false;
      _searchErrorText = null;
    });
    _markOverlaysNeedsBuild();
  }

  void _closeDialog() {
    _hideSearchOverlay();
    _hideCashOverlay();
    _hideAdjustTypeOverlay();
    final navigator = Navigator.maybeOf(context);
    if (navigator != null && navigator.canPop()) {
      navigator.pop();
      return;
    }
    setState(() {
      _inlineClosed = true;
    });
  }

  String _formatInputNumber(double value, {int decimals = 3}) {
    final text = value.toStringAsFixed(decimals);
    if (!text.contains('.')) return text;
    return text
        .replaceFirst(RegExp(r'0+$'), '')
        .replaceFirst(RegExp(r'\.$'), '');
  }

  bool _isFundAsset({String? assetType, String? code}) {
    final normalizedType = (assetType ?? '').trim().toLowerCase();
    if (normalizedType == 'fund') return true;
    final normalizedCode = (code ?? '').trim().toLowerCase();
    return normalizedCode.startsWith('f_') || normalizedCode.startsWith('ft_');
  }

  bool _isCurrentFundTarget() {
    final mode = _currentActionMode();
    if (mode == 'sell' || mode == 'adjust') return false;
    if (_isAdd) {
      return _isFundAsset(
        assetType: _selected?['asset_type']?.toString(),
        code: _selected?['code']?.toString(),
      );
    }
    final item = widget.item;
    if (item == null) return false;
    return _isFundAsset(assetType: item.assetType, code: item.code);
  }

  bool _isFundAmountMode() {
    return _isCurrentFundTarget() && _fundInputMode == 'amount';
  }

  void _setFundInputMode(String mode) {
    if (_fundInputMode == mode) return;
    setState(() {
      _fundInputMode = mode;
      _errorText = null;
      _navErrorText = null;
    });
    if (mode == 'amount' && _isCurrentFundTarget()) {
      final code = _isAdd
          ? (_selected?['code']?.toString() ?? '')
          : (widget.item?.code ?? '');
      if (code.isNotEmpty) {
        unawaited(_prefillFundNavForCode(code));
      }
    }
  }

  Future<void> _notifyPortfolioChanged() async {
    final callback = widget.onPortfolioChanged;
    if (callback == null) return;
    try {
      await callback();
    } catch (_) {
      // 刷新失败不应影响已成功的写操作，页面下次进入时会重新拉取。
    }
  }

  double? _deriveFundQtyFromAmountNav() {
    final amount = double.tryParse(_amountController.text.trim());
    final nav = double.tryParse(_priceController.text.trim());
    if (amount == null || nav == null || amount <= 0 || nav <= 0) return null;
    final rawQty = amount / nav;
    final qty = (rawQty * 10000).floor() / 10000;
    if (qty <= 0) return null;
    return qty;
  }

  String _formatQtyDisplay(double value) {
    final text = value.toStringAsFixed(4);
    return text.replaceFirst(RegExp(r'\.?0+$'), '');
  }

  double _currentHoldingQty() {
    return (widget.item?.qty ?? 0).toDouble();
  }

  double _currentRawCostPrice() {
    return (widget.item?.price ?? 0).toDouble();
  }

  double _currentDisplayCostPrice() {
    final displayCostPrice = widget.item?.displayCostPrice;
    if (displayCostPrice != null && displayCostPrice.isFinite) {
      return displayCostPrice;
    }
    final qty = _currentHoldingQty();
    if (qty <= 0) return _currentRawCostPrice();
    return (_currentRawCostPrice() * qty - (widget.item?.adjustment ?? 0)) / qty;
  }

  String _adjustInputLabel() {
    if (_adjustType == 'cost_price') return '目标成本价';
    if (_adjustType == 'quantity') return '目标数量';
    if (_adjustType == 'dividend') return '分红金额';
    if (_adjustType == 'fee') return '手续费金额';
    return '目标成本价';
  }

  int _adjustInputDecimals() {
    if (_adjustType == 'cost_price') {
      return _isFundAsset(
            assetType: widget.item?.assetType,
            code: widget.item?.code,
          )
          ? 4
          : 3;
    }
    if (_adjustType == 'quantity') {
      return _isFundAsset(
            assetType: widget.item?.assetType,
            code: widget.item?.code,
          )
          ? 4
          : 2;
    }
    return 2;
  }

  void _syncAdjustInputDefault() {
    if (!_isTrade || !_isAdjust) return;
    final qty = _currentHoldingQty();
    if (_adjustType == 'cost_price') {
      _setControllerText(
        _adjustController,
        _formatInputNumber(
          _currentDisplayCostPrice(),
          decimals: _adjustInputDecimals(),
        ),
      );
      return;
    }
    if (_adjustType == 'quantity') {
      _setControllerText(
        _adjustController,
        _formatInputNumber(qty, decimals: _adjustInputDecimals()),
      );
      return;
    }
    if (_adjustType == 'dividend' || _adjustType == 'fee') {
      _setControllerText(_adjustController, '');
      return;
    }
    _setControllerText(
      _adjustController,
      _formatInputNumber(
        _currentDisplayCostPrice(),
        decimals: _adjustInputDecimals(),
      ),
    );
  }

  void _setAdjustType(String? nextType) {
    if (nextType == null || nextType == _adjustType || _saving) return;
    FocusScope.of(context).unfocus();
    setState(() {
      _adjustType = nextType;
      _errorText = null;
      _syncAdjustInputDefault();
    });
  }

  String? _validateAdjustPayload({required double qty, required double value}) {
    if (_adjustType == 'cost_price') {
      if (qty <= 0) return '当前持仓数量无效，不能调整成本价';
      if (value <= 0) return '目标成本价必须大于 0';
      return null;
    }
    if (_adjustType == 'quantity') {
      if (value <= 0) return '目标数量必须大于 0，清仓请用卖出';
      return null;
    }
    if (_adjustType == 'dividend') {
      if (qty <= 0) return '当前持仓数量无效，不能记录分红';
      if (value <= 0) return '分红金额必须大于 0';
      return null;
    }
    if (_adjustType == 'fee') {
      if (qty <= 0) return '当前持仓数量无效，不能记录手续费';
      if (value <= 0) return '手续费金额必须大于 0';
      return null;
    }
    if (qty <= 0) return '当前持仓数量无效，不能调整成本价';
    if (value <= 0) return '目标成本价必须大于 0';
    return null;
  }

  _ResolvedAdjustPayload _buildAdjustPayload({
    required double qty,
    required double rawPrice,
    required double currentAdjustment,
    required double value,
  }) {
    if (_adjustType == 'cost_price') {
      return _ResolvedAdjustPayload(
        qty: qty,
        price: qty > 0 ? value + currentAdjustment / qty : value,
        adjustment: currentAdjustment,
      );
    }
    if (_adjustType == 'quantity') {
      return _ResolvedAdjustPayload(
        qty: value,
        price: rawPrice,
        adjustment: currentAdjustment,
      );
    }
    if (_adjustType == 'dividend') {
      return _ResolvedAdjustPayload(
        qty: qty,
        price: rawPrice,
        adjustment: currentAdjustment + value,
      );
    }
    if (_adjustType == 'fee') {
      return _ResolvedAdjustPayload(
        qty: qty,
        price: rawPrice,
        adjustment: currentAdjustment - value,
      );
    }
    return _ResolvedAdjustPayload(
      qty: qty,
      price: rawPrice,
      adjustment: rawPrice * qty - value * qty,
    );
  }

  Future<void> _prefillFundNavForCode(String code) async {
    final normalizedCode = code.trim();
    if (normalizedCode.isEmpty) return;
    final seq = ++_navFetchSeq;
    setState(() {
      _navLoading = true;
      _navErrorText = null;
    });
    final appState = context.read<AppState>();
    final nav = await appState.fetchLatestPriceForCode(normalizedCode);
    if (!mounted || seq != _navFetchSeq) return;
    setState(() {
      _navLoading = false;
      if (nav != null && nav > 0) {
        _priceController.text = _formatInputNumber(nav, decimals: 4);
        _navErrorText = null;
      } else {
        _navErrorText = '净值获取失败，可手动输入';
      }
    });
  }

  String _normalizeCurrencyCode(String? curr) {
    final code = (curr ?? '').trim().toUpperCase();
    if (code == 'USD' || code == 'HKD' || code == 'CNY') return code;
    return 'CNY';
  }

  String _targetCashCurrency(AppState appState, String actionMode) {
    if (_isAdd) {
      final selectedCode = _selected?['code']?.toString() ?? '';
      final selectedCurr = _selected?['currency']?.toString();
      if (selectedCode.isNotEmpty) {
        return _normalizeCurrencyCode(
          appState.normalizeInvestmentCurrency(
            code: selectedCode,
            curr: selectedCurr,
          ),
        );
      }
      return _normalizeCurrencyCode(selectedCurr);
    }
    final item = widget.item;
    if (item != null) {
      return _normalizeCurrencyCode(
        appState.normalizeInvestmentCurrency(code: item.code, curr: item.curr),
      );
    }
    if (actionMode == 'sell') return 'CNY';
    return 'CNY';
  }

  Future<void> _openAddFundingAccountDialog({
    required String targetCurrency,
  }) async {
    if (_saving) return;
    final createdId = await showAddFundingAccountDialog(
      context: context,
      hostContext: widget.hostContext ?? context,
      initialCurrency: targetCurrency,
      lockCurrency: true,
      forceAssetTypeCash: true,
    );
    if (!mounted || createdId == null) return;
    setState(() {
      _selectedCashAssetId = createdId;
      _errorText = null;
    });
    _rememberCashAsset(createdId);
  }

  void _syncDefaultCashAsset() {
    final appState = context.read<AppState>();
    final actionMode = _currentActionMode();
    final targetCurrency = _targetCashCurrency(appState, actionMode);
    final cashOptions = appState.cashAssets
        .where((asset) => (asset.id ?? 0) > 0)
        .where((asset) => _normalizeCurrencyCode(asset.curr) == targetCurrency)
        .toList();
    if (actionMode != 'sell') {
      cashOptions.insert(
        0,
        Asset(id: -999, name: '外部资金/初始转入', amount: 0.0, curr: targetCurrency),
      );
    }
    if (cashOptions.isEmpty) {
      _selectedCashAssetId = null;
      return;
    }
    final selected = _selectedCashAssetId;
    final exists =
        selected != null && cashOptions.any((asset) => asset.id == selected);
    if (!exists) {
      _selectedCashAssetId = cashOptions.first.id;
    }
  }

  String _currentActionMode() {
    if (_isTrade) return _tradeMode;
    if (_isBuy) return 'buy';
    if (_isSell) return 'sell';
    return 'buy';
  }

  bool _requiresCashSource(String mode) {
    return _isAdd || mode == 'buy' || mode == 'sell';
  }

  void _rememberCashAsset(int? assetId) {
    if (assetId == null) return;
    _recentCashAssetIds.remove(assetId);
    _recentCashAssetIds.insert(0, assetId);
    if (_recentCashAssetIds.length > _maxRecentCashAssets) {
      _recentCashAssetIds.removeRange(
        _maxRecentCashAssets,
        _recentCashAssetIds.length,
      );
    }
  }

  void _prefillPriceFromCurrent() {
    final item = widget.item;
    if (item == null) return;
    final appState = context.read<AppState>();
    final livePrice = appState.prices[item.code]?.price ?? 0;
    final defaultPrice = livePrice > 0 ? livePrice : item.price;
    if (defaultPrice > 0) {
      final decimals = _isFundAsset(assetType: item.assetType, code: item.code)
          ? 4
          : 3;
      _priceController.text = _formatInputNumber(
        defaultPrice,
        decimals: decimals,
      );
    }
  }

  void _setTradeMode(String mode) {
    if (_saving || _tradeMode == mode) return;
    _hideSearchOverlay();
    _hideCashOverlay();
    _hideAdjustTypeOverlay();
    FocusScope.of(context).unfocus();
    setState(() {
      _tradeMode = mode;
      _errorText = null;
      _navErrorText = null;
      _navLoading = false;
      if (mode == 'adjust') {
        _adjustType = 'cost_price';
        _syncAdjustInputDefault();
      } else if (_priceController.text.trim().isEmpty) {
        _prefillPriceFromCurrent();
      }
      if (mode != 'buy') {
        _fundInputMode = 'qty';
        _amountController.clear();
        _navFetchSeq += 1;
      } else if (_isCurrentFundTarget()) {
        _fundInputMode = 'amount';
        _amountController.clear();
      }
    });
    if (mode == 'buy' && _isCurrentFundTarget()) {
      final code = widget.item?.code ?? '';
      if (code.isNotEmpty) {
        unawaited(_prefillFundNavForCode(code));
      }
    }
  }

  Future<void> _submit() async {
    if (_saving) return;
    final appState = context.read<AppState>();
    final toastContext = widget.hostContext ?? context;
    final mode = _currentActionMode();

    double? price;
    double? qty;

    setState(() {
      _saving = true;
      _errorText = null;
    });

    late final Future<AssetActionResult> actionFuture;
    final needsCashSource = _requiresCashSource(mode);
    if (needsCashSource &&
        (_selectedCashAssetId == null ||
            (_selectedCashAssetId! <= 0 && _selectedCashAssetId != -999))) {
      setState(() {
        _saving = false;
        _errorText = '请选择资金账户';
      });
      return;
    }
    if (needsCashSource) {
      _rememberCashAsset(_selectedCashAssetId);
    }
    if (_isAdd) {
      final priceStr = _priceController.text.trim();
      price = double.tryParse(priceStr);
      if (price == null) {
        setState(() {
          _saving = false;
          _errorText = '请输入有效价格';
        });
        return;
      }
      if (price <= 0) {
        setState(() {
          _saving = false;
          _errorText = '价格必须大于 0';
        });
        return;
      }
      if (_selected == null) {
        setState(() {
          _saving = false;
          _errorText = '必须从下拉列表选择资产';
        });
        return;
      }
      final isFund = _isCurrentFundTarget();
      if (isFund && _isFundAmountMode()) {
        final amount = double.tryParse(_amountController.text.trim());
        if (amount == null || amount <= 0) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效买入金额';
          });
          return;
        }
        qty = _deriveFundQtyFromAmountNav();
        if (qty == null || qty <= 0) {
          setState(() {
            _saving = false;
            _errorText = '金额过小，按当前净值不足以买入最小份额（0.0001）';
          });
          return;
        }
      } else {
        final qtyStr = _qtyController.text.trim();
        qty = double.tryParse(qtyStr);
        if (qty == null) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效数量';
          });
          return;
        }
        if (qty <= 0) {
          setState(() {
            _saving = false;
            _errorText = '数量必须大于 0';
          });
          return;
        }
      }
      final code = _selected?['code'] ?? '';
      final name = _selected?['name'] ?? '';
      final curr = _selected?['currency'];
      final assetType = _selected?['asset_type'];
      actionFuture = appState.buyInvestmentWithCash(
        code: code,
        name: name,
        price: price,
        qty: qty,
        cashAssetId: _selectedCashAssetId!,
        curr: curr,
        assetType: assetType,
        awaitRefresh: false,
      );
    } else {
      final code = widget.item?.code ?? '';
      if (code.isEmpty) {
        setState(() {
          _saving = false;
          _errorText = '未找到持仓代码';
        });
        return;
      }
      if (mode == 'adjust') {
        final adjustStr = _adjustController.text.trim();
        final note = _noteController.text.trim();
        final adjustVal = double.tryParse(adjustStr);
        if (adjustVal == null) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效${_adjustInputLabel()}';
          });
          return;
        }
        final qtyVal = widget.item?.qty ?? 0;
        final rawPriceVal = widget.item?.price ?? 0;
        final validationError = _validateAdjustPayload(
          qty: qtyVal.toDouble(),
          value: adjustVal,
        );
        if (validationError != null) {
          setState(() {
            _saving = false;
            _errorText = validationError;
          });
          return;
        }
        final payload = _buildAdjustPayload(
          qty: qtyVal.toDouble(),
          rawPrice: rawPriceVal.toDouble(),
          currentAdjustment: (widget.item?.adjustment ?? 0).toDouble(),
          value: adjustVal,
        );
        if (_adjustType == 'dividend' || _adjustType == 'fee') {
          actionFuture = appState.addInvestmentAdjustmentEvent(
            code: code,
            eventType: _adjustType,
            amount: adjustVal,
            note: note,
            awaitRefresh: false,
          );
        } else {
          actionFuture = appState.modifyInvestment(
            code: code,
            qty: payload.qty,
            price: payload.price,
            note: note,
            awaitRefresh: false,
          );
        }
      } else if (mode == 'buy') {
        final priceStr = _priceController.text.trim();
        price = double.tryParse(priceStr);
        if (price == null) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效价格';
          });
          return;
        }
        if (price <= 0) {
          setState(() {
            _saving = false;
            _errorText = '价格必须大于 0';
          });
          return;
        }
        final isFund = _isCurrentFundTarget();
        if (isFund && _isFundAmountMode()) {
          final amount = double.tryParse(_amountController.text.trim());
          if (amount == null || amount <= 0) {
            setState(() {
              _saving = false;
              _errorText = '请输入有效买入金额';
            });
            return;
          }
          qty = _deriveFundQtyFromAmountNav();
          if (qty == null || qty <= 0) {
            setState(() {
              _saving = false;
              _errorText = '金额过小，按当前净值不足以买入最小份额（0.0001）';
            });
            return;
          }
        } else {
          final qtyStr = _qtyController.text.trim();
          qty = double.tryParse(qtyStr);
          if (qty == null) {
            setState(() {
              _saving = false;
              _errorText = '请输入有效数量';
            });
            return;
          }
          if (qty <= 0) {
            setState(() {
              _saving = false;
              _errorText = '数量必须大于 0';
            });
            return;
          }
        }
        actionFuture = appState.buyInvestmentWithCash(
          code: code,
          name: widget.item?.name ?? code,
          price: price,
          qty: qty,
          cashAssetId: _selectedCashAssetId!,
          curr: widget.item?.curr,
          assetType: widget.item?.assetType,
          awaitRefresh: false,
        );
      } else {
        final priceStr = _priceController.text.trim();
        final qtyStr = _qtyController.text.trim();
        price = double.tryParse(priceStr);
        qty = double.tryParse(qtyStr);
        if (price == null) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效价格';
          });
          return;
        }
        if (qty == null) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效数量';
          });
          return;
        }
        if (qty <= 0) {
          setState(() {
            _saving = false;
            _errorText = '数量必须大于 0';
          });
          return;
        }
        if (price <= 0) {
          setState(() {
            _saving = false;
            _errorText = '价格必须大于 0';
          });
          return;
        }
        actionFuture = appState.sellInvestmentToCash(
          code: code,
          price: price,
          qty: qty,
          cashAssetId: _selectedCashAssetId!,
          awaitRefresh: false,
        );
      }
    }

    final result = await actionFuture;
    if (!mounted || !toastContext.mounted) return;
    if (!result.ok) {
      setState(() {
        _saving = false;
        _errorText = result.message ?? '保存失败，请稍后重试';
      });
      TopToast.showError(toastContext, result.message ?? '保存失败，请稍后重试');
      return;
    }

    await _notifyPortfolioChanged();
    if (!mounted || !toastContext.mounted) return;
    _closeDialog();

    final undoToken = result.data?['undo_token']?.toString();
    if (undoToken != null && undoToken.isNotEmpty) {
      TopToast.showAction(
        toastContext,
        message: '已保存',
        actionLabel: '撤销',
        placement: TopToastPlacement.bottom,
        onAction: () {
          unawaited(() async {
            final undoResult = await appState.undoInvestmentOperation(
              undoToken,
            );
            if (!toastContext.mounted) return;
            if (undoResult.ok) {
              await _notifyPortfolioChanged();
              if (!toastContext.mounted) return;
              TopToast.showInfo(toastContext, '已撤销');
            } else {
              TopToast.showError(toastContext, undoResult.message ?? '撤销失败');
            }
          }());
        },
        duration: const Duration(seconds: 5),
      );
      return;
    }

    TopToast.showSuccess(toastContext, '已保存');
  }

  void _markOverlaysNeedsBuild() {
    _searchOverlayEntry?.markNeedsBuild();
    _cashOverlayEntry?.markNeedsBuild();
    _adjustTypeOverlayEntry?.markNeedsBuild();
  }

  Size _targetSize(GlobalKey key) {
    final targetContext = key.currentContext;
    if (targetContext == null) return const Size(280, 40);
    final box = targetContext.findRenderObject();
    if (box is! RenderBox) return const Size(280, 40);
    return box.size;
  }

  double? _asDouble(dynamic value) {
    if (value is num) return value.toDouble();
    if (value == null) return null;
    return double.tryParse(value.toString().replaceAll(',', ''));
  }

  double? _firstValidNumber(
    Map<String, dynamic> item,
    List<String> keys, {
    bool allowZero = false,
  }) {
    for (final key in keys) {
      final value = _asDouble(item[key]);
      if (value == null) continue;
      if (!allowZero && value == 0) continue;
      return value;
    }
    return null;
  }

  double? _searchResultPrice(Map<String, dynamic> item, AppState appState) {
    final direct = _firstValidNumber(item, const [
      'price',
      'latest',
      'latest_price',
      'current_price',
      'last_price',
      'close',
    ]);
    if (direct != null && direct > 0) return direct;
    final code = item['code']?.toString() ?? '';
    if (code.isEmpty) return null;
    final info = appState.resolvePriceInfoByCode(code);
    if (info != null && info.price > 0) {
      return info.price;
    }
    return null;
  }

  double? _searchResultChangePct(Map<String, dynamic> item, AppState appState) {
    final pct = _firstValidNumber(item, const [
      'changePct',
      'change_pct',
      'chg',
      'pct',
      'change_percent',
    ], allowZero: true);
    if (pct != null) return pct;

    final code = item['code']?.toString() ?? '';
    if (code.isNotEmpty) {
      final info = appState.resolvePriceInfoByCode(code);
      if (info != null) return info.changePct;
    }

    final amt = _firstValidNumber(item, const [
      'change',
      'amt',
      'delta',
    ], allowZero: true);
    final yclose = _firstValidNumber(item, const [
      'yclose',
      'pre_close',
      'prev_close',
    ], allowZero: false);
    if (amt != null && yclose != null && yclose != 0) {
      return amt / yclose * 100;
    }
    return null;
  }

  double? _searchResultChangeAmount(
    Map<String, dynamic> item,
    AppState appState,
  ) {
    final direct = _firstValidNumber(item, const [
      'change',
      'amt',
      'delta',
    ], allowZero: true);
    if (direct != null) return direct;

    final code = item['code']?.toString() ?? '';
    if (code.isEmpty) return null;
    final info = appState.resolvePriceInfoByCode(code);
    if (info != null) return info.change;
    return null;
  }

  String _searchResultCurrencyCode(Map<String, dynamic> item) {
    final raw = (item['currency'] ?? item['curr'] ?? '')
        .toString()
        .trim()
        .toUpperCase();
    if (raw == 'USD' || raw == 'HKD' || raw == 'CNY') return raw;
    final code = (item['code'] ?? '').toString().trim().toLowerCase();
    if (code.startsWith('gb_') || code.startsWith('ft_')) return 'USD';
    if (code.endsWith('.hk') || code.startsWith('hk')) return 'HKD';
    return 'CNY';
  }

  String _searchResultCurrencySymbol(Map<String, dynamic> item) {
    switch (_searchResultCurrencyCode(item)) {
      case 'HKD':
        return 'HK\$';
      case 'USD':
        return '\$';
      default:
        return '¥';
    }
  }

  String _assetCurrencySymbol(String? curr) {
    switch ((curr ?? '').trim().toUpperCase()) {
      case 'HKD':
        return 'HK\$';
      case 'USD':
        return '\$';
      default:
        return '¥';
    }
  }

  List<Map<String, dynamic>> _filteredSearchResults() {
    final query = _queryController.text.trim().toLowerCase();
    return _results.whereType<Map<String, dynamic>>().where((item) {
      if (query.isEmpty) return true;
      final name = (item['name']?.toString() ?? '').toLowerCase();
      final code = (item['code']?.toString() ?? '').toLowerCase();
      return name.contains(query) || code.contains(query);
    }).toList();
  }

  void _hideSearchOverlay({bool updateState = true}) {
    _searchOverlayEntry?.remove();
    _searchOverlayEntry = null;
    if (updateState && mounted) {
      setState(() => _searchOverlayVisible = false);
    } else {
      _searchOverlayVisible = false;
    }
  }

  void _hideCashOverlay({bool updateState = true}) {
    _cashOverlayEntry?.remove();
    _cashOverlayEntry = null;
    if (updateState && mounted) {
      setState(() => _cashOverlayVisible = false);
    } else {
      _cashOverlayVisible = false;
    }
  }

  void _hideAdjustTypeOverlay({bool updateState = true}) {
    _adjustTypeOverlayEntry?.remove();
    _adjustTypeOverlayEntry = null;
    if (updateState && mounted) {
      setState(() => _adjustTypeOverlayVisible = false);
    } else {
      _adjustTypeOverlayVisible = false;
    }
  }

  void _showSearchOverlay() {
    if (!_isAdd || _selected != null) return;
    if (!_searchTriggered) return;
    if (_queryController.text.trim().isEmpty) return;
    _hideCashOverlay();
    _hideAdjustTypeOverlay();
    if (_searchOverlayEntry != null) {
      _markOverlaysNeedsBuild();
      return;
    }
    final overlay = Overlay.of(context, rootOverlay: true);
    if (mounted) {
      setState(() => _searchOverlayVisible = true);
    } else {
      _searchOverlayVisible = true;
    }
    _searchOverlayEntry = OverlayEntry(
      builder: (overlayContext) => Stack(
        children: [
          CompositedTransformFollower(
            link: _searchFieldLink,
            showWhenUnlinked: false,
            offset: Offset(0, _targetSize(_searchTargetKey).height + 6),
            child: Material(
              color: Colors.transparent,
              child: SizedBox(
                width: _targetSize(_searchTargetKey).width,
                child: _buildSearchOverlayCard(),
              ),
            ),
          ),
        ],
      ),
    );
    overlay.insert(_searchOverlayEntry!);
  }

  void _showCashOverlay({
    required List<Asset> cashOptions,
    required String targetCurrency,
    required bool showAddCashAction,
  }) {
    if (_saving) return;
    if (cashOptions.isEmpty && !showAddCashAction) return;
    _hideSearchOverlay();
    _hideAdjustTypeOverlay();
    if (_cashOverlayEntry != null) {
      _markOverlaysNeedsBuild();
      return;
    }
    final overlay = Overlay.of(context, rootOverlay: true);
    if (mounted) {
      setState(() => _cashOverlayVisible = true);
    } else {
      _cashOverlayVisible = true;
    }
    _cashOverlayEntry = OverlayEntry(
      builder: (overlayContext) => Stack(
        children: [
          CompositedTransformFollower(
            link: _cashFieldLink,
            showWhenUnlinked: false,
            offset: Offset(0, _targetSize(_cashTargetKey).height + 6),
            child: Material(
              color: Colors.transparent,
              child: SizedBox(
                width: _targetSize(_cashTargetKey).width,
                child: _buildCashOverlayCard(
                  options: cashOptions,
                  targetCurrency: targetCurrency,
                  showAddCashAction: showAddCashAction,
                ),
              ),
            ),
          ),
        ],
      ),
    );
    overlay.insert(_cashOverlayEntry!);
  }

  void _showAdjustTypeOverlay() {
    if (_saving) return;
    _hideSearchOverlay();
    _hideCashOverlay();
    if (_adjustTypeOverlayEntry != null) {
      _markOverlaysNeedsBuild();
      return;
    }
    final overlay = Overlay.of(context, rootOverlay: true);
    if (mounted) {
      setState(() => _adjustTypeOverlayVisible = true);
    } else {
      _adjustTypeOverlayVisible = true;
    }
    _adjustTypeOverlayEntry = OverlayEntry(
      builder: (overlayContext) => Stack(
        children: [
          CompositedTransformFollower(
            link: _adjustTypeFieldLink,
            showWhenUnlinked: false,
            offset: Offset(0, _targetSize(_adjustTypeTargetKey).height + 6),
            child: Material(
              color: Colors.transparent,
              child: SizedBox(
                width: _targetSize(_adjustTypeTargetKey).width,
                child: _buildAdjustTypeOverlayCard(),
              ),
            ),
          ),
        ],
      ),
    );
    overlay.insert(_adjustTypeOverlayEntry!);
  }

  void _selectSearchResult(Map<String, dynamic> item) {
    final codeRaw = item['code']?.toString() ?? '';
    final isFund = _isFundAsset(
      assetType: item['asset_type']?.toString(),
      code: codeRaw,
    );
    setState(() {
      _selected = item;
      _queryController.text = item['name']?.toString() ?? '';
      _errorText = null;
      _searchErrorText = null;
      _fundInputMode = isFund ? 'amount' : 'qty';
      _priceController.clear();
      _qtyController.clear();
      _amountController.clear();
      _navErrorText = null;
      _navLoading = false;
    });
    _hideSearchOverlay();
    FocusScope.of(context).unfocus();
    if (isFund) {
      unawaited(_prefillFundNavForCode(codeRaw));
    }
  }

  void _clearSelectedAsset() {
    setState(() {
      _selected = null;
      _queryController.clear();
      _priceController.clear();
      _qtyController.clear();
      _amountController.clear();
      _errorText = null;
      _searchErrorText = null;
      _results = [];
      _fundInputMode = 'qty';
      _navLoading = false;
      _navErrorText = null;
      _searchTriggered = false;
    });
    _hideSearchOverlay();
    _queryFocusNode.requestFocus();
  }

  Widget _buildMarketTag(String typeName) {
    final mapping = <String, ({Color fg, Color bg})>{
      '港股': (fg: const Color(0xFFE06B3A), bg: const Color(0x1FE06B3A)),
      '美股': (fg: const Color(0xFF5B8DEF), bg: const Color(0x1F5B8DEF)),
      'A股': (fg: const Color(0xFF3ECF82), bg: const Color(0x1F3ECF82)),
      '基金': (fg: const Color(0xFFB57ADB), bg: const Color(0x1FB57ADB)),
    };
    final style = mapping[typeName] ?? mapping['A股']!;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
      decoration: BoxDecoration(
        color: style.bg,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        typeName.isEmpty ? 'A股' : typeName,
        style: _dm(
          size: 10,
          weight: FontWeight.w600,
          color: style.fg,
          letterSpacing: 0.03,
        ),
      ),
    );
  }

  Widget _buildSearchOverlayCard() {
    final appState = context.read<AppState>();
    final rows = _filteredSearchResults();
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
        constraints: const BoxConstraints(maxHeight: 280),
        decoration: BoxDecoration(
          color: _tokens.surface2,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: _tokens.border, width: 1),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.55),
              blurRadius: 36,
              offset: const Offset(0, 16),
            ),
          ],
        ),
        child: _searching
            ? Padding(
                padding: const EdgeInsets.symmetric(vertical: 24),
                child: Center(
                  child: Text(
                    '搜索中...',
                    style: _dm(size: 12, color: _tokens.textSub),
                  ),
                ),
              )
            : rows.isEmpty
            ? Padding(
                padding: const EdgeInsets.symmetric(vertical: 24),
                child: Center(
                  child: Text(
                    '暂无匹配结果',
                    style: _dm(size: 12, color: _tokens.textSub),
                  ),
                ),
              )
            : ListView.separated(
                padding: EdgeInsets.zero,
                primary: false,
                shrinkWrap: true,
                itemCount: rows.length,
                separatorBuilder: (context, index) =>
                    Divider(height: 1, color: _tokens.border),
                itemBuilder: (context, index) {
                  final item = rows[index];
                  final codeRaw = item['code']?.toString() ?? '';
                  final name = item['name']?.toString() ?? '';
                  final typeName = item['type_name']?.toString() ?? 'A股';
                  final code = _formatDisplayCode(codeRaw);
                  final isFund = _isFundAsset(
                    assetType: item['asset_type']?.toString(),
                    code: codeRaw,
                  );
                  final price = _searchResultPrice(item, appState);
                  final changeAmt = _searchResultChangeAmount(item, appState);
                  final changePct = _searchResultChangePct(item, appState);
                  final quoteColor = (changePct ?? changeAmt ?? 0) >= 0
                      ? _tokens.green
                      : _tokens.red;
                  final symbol = _searchResultCurrencySymbol(item);
                  final selectedCode = _selected?['code']?.toString() ?? '';
                  final selected =
                      selectedCode == codeRaw && selectedCode.isNotEmpty;
                  return InkWell(
                    onTap: () => _selectSearchResult(item),
                    child: Container(
                      color: selected ? _tokens.goldDim : Colors.transparent,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 9,
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  name,
                                  style: _dm(
                                    size: 13,
                                    weight: FontWeight.w500,
                                    color: _tokens.text,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Row(
                                  children: [
                                    _buildMarketTag(typeName),
                                    const SizedBox(width: 6),
                                    Text(
                                      code,
                                      style: _mono(
                                        size: 11,
                                        color: _tokens.textMuted,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 8),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Text(
                                price == null
                                    ? '--'
                                    : '$symbol${_formatInputNumber(price, decimals: isFund ? 4 : 2)}',
                                style: _mono(size: 13, color: _tokens.text),
                              ),
                              Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Text(
                                    changeAmt == null
                                        ? '--'
                                        : '${changeAmt >= 0 ? '+' : ''}${_formatInputNumber(changeAmt, decimals: isFund ? 4 : 2)}',
                                    style: _mono(
                                      size: 10,
                                      color: quoteColor,
                                      weight: FontWeight.w600,
                                    ),
                                  ),
                                  const SizedBox(width: 6),
                                  Text(
                                    changePct == null
                                        ? '--'
                                        : '${changePct >= 0 ? '+' : ''}${_formatInputNumber(changePct, decimals: 2)}%',
                                    style: _dm(
                                      size: 10,
                                      weight: FontWeight.w500,
                                      color: quoteColor,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                          if (selected) ...[
                            const SizedBox(width: 8),
                            Icon(Icons.check, size: 12, color: _tokens.gold),
                          ],
                        ],
                      ),
                    ),
                  );
                },
              ),
      ),
    );
  }

  Widget _buildSelectedPill() {
    final item = _selected ?? <String, dynamic>{};
    final appState = context.read<AppState>();
    final codeRaw = item['code']?.toString() ?? '';
    final code = _formatDisplayCode(item['code']?.toString() ?? '');
    final name = item['name']?.toString() ?? '';
    final typeName = item['type_name']?.toString() ?? 'A股';
    final isFund = _isFundAsset(
      assetType: item['asset_type']?.toString(),
      code: codeRaw,
    );
    final price = _searchResultPrice(item, appState);
    final changeAmt = _searchResultChangeAmount(item, appState);
    final changePct = _searchResultChangePct(item, appState);
    final quoteColor = (changePct ?? changeAmt ?? 0) >= 0
        ? _tokens.green
        : _tokens.red;
    final symbol = _searchResultCurrencySymbol(item);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: _tokens.goldDim,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(
          color: _tokens.gold.withValues(alpha: 0.2),
          width: 1,
        ),
      ),
      child: Row(
        children: [
          _buildMarketTag(typeName),
          const SizedBox(width: 8),
          Text(code, style: _mono(size: 12, color: _tokens.text)),
          const SizedBox(width: 6),
          Container(width: 1, height: 12, color: _tokens.border),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              name,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: _dm(
                size: 12,
                weight: FontWeight.w500,
                color: _tokens.text,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                price == null
                    ? '--'
                    : '$symbol${_formatInputNumber(price, decimals: isFund ? 4 : 2)}',
                style: _mono(size: 12, color: _tokens.text),
              ),
              const SizedBox(height: 2),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    changeAmt == null
                        ? '--'
                        : '${changeAmt >= 0 ? '+' : ''}${_formatInputNumber(changeAmt, decimals: isFund ? 4 : 2)}',
                    style: _mono(
                      size: 10,
                      color: quoteColor,
                      weight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    changePct == null
                        ? '--'
                        : '${changePct >= 0 ? '+' : ''}${_formatInputNumber(changePct, decimals: 2)}%',
                    style: _dm(
                      size: 10,
                      weight: FontWeight.w600,
                      color: quoteColor,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(width: 8),
          InkWell(
            onTap: _clearSelectedAsset,
            borderRadius: BorderRadius.circular(12),
            child: Container(
              width: 17,
              height: 17,
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.07),
                shape: BoxShape.circle,
              ),
              child: Icon(Icons.close, size: 8, color: _tokens.textMuted),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchField() {
    final focused = _queryFocusNode.hasFocus || _searchOverlayVisible;
    final field = Container(
      key: _searchTargetKey,
      height: 48,
      padding: const EdgeInsets.only(left: 14, right: 6),
      decoration: BoxDecoration(
        color: _tokens.surface2,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: focused ? const Color(0x996395EB) : _tokens.border,
          width: 1,
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              key: _searchFieldKey,
              controller: _queryController,
              focusNode: _queryFocusNode,
              textCapitalization: TextCapitalization.characters,
              onChanged: _onQueryChanged,
              cursorColor: _tokens.blueStart,
              style: _dm(size: 14, color: _tokens.text),
              decoration: InputDecoration(
                filled: true,
                fillColor: Colors.transparent,
                isDense: true,
                border: InputBorder.none,
                enabledBorder: InputBorder.none,
                focusedBorder: InputBorder.none,
                errorBorder: InputBorder.none,
                focusedErrorBorder: InputBorder.none,
                disabledBorder: InputBorder.none,
                hintText: '输入代码或名称',
                hintStyle: _dm(size: 14, color: _tokens.textMuted),
                contentPadding: EdgeInsets.zero,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Container(
            height: 34,
            decoration: BoxDecoration(
              gradient: _tokens.blueGrad,
              borderRadius: BorderRadius.circular(6),
              boxShadow: [
                BoxShadow(
                  color: const Color(0x384A7BE0),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                key: _searchButtonKey,
                onTap: _searching ? null : _onSearchTap,
                borderRadius: BorderRadius.circular(6),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.search, size: 15, color: Colors.white),
                      const SizedBox(width: 4),
                      Text(
                        _searching ? '搜索中' : '搜索',
                        style: _dm(
                          size: 13,
                          weight: FontWeight.w600,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
    return CompositedTransformTarget(
      link: _searchFieldLink,
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 200),
        transitionBuilder: (child, animation) {
          return FadeTransition(
            opacity: animation,
            child: SlideTransition(
              position: Tween<Offset>(
                begin: const Offset(0, 0.03),
                end: Offset.zero,
              ).animate(animation),
              child: child,
            ),
          );
        },
        child: _selected == null
            ? field
            : KeyedSubtree(
                key: const ValueKey<String>('selected-pill'),
                child: _buildSelectedPill(),
              ),
      ),
    );
  }

  String _accountEmoji(Asset asset) {
    if (asset.id == -999) return '↗';
    final lower = asset.name.toLowerCase();
    if (lower.contains('微信')) return '💬';
    if (lower.contains('支付')) return '💙';
    return '🏦';
  }

  Color _accountBgColor(Asset asset) {
    if (asset.id == -999) return const Color(0x1F5B8DEF);
    final lower = asset.name.toLowerCase();
    if (lower.contains('微信')) return const Color(0x1F3ECF82);
    if (lower.contains('支付')) return const Color(0x1F5B8DEF);
    return const Color(0x1FE74C3C);
  }

  Widget _buildCashOverlayCard({
    required List<Asset> options,
    required String targetCurrency,
    required bool showAddCashAction,
  }) {
    final rows = options;
    const itemHeight = 52.0;
    final visibleRows = rows.length > 5 ? 5 : rows.length;
    final listHeight = (visibleRows <= 0 ? 1 : visibleRows) * itemHeight;
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
        constraints: const BoxConstraints(maxHeight: 320),
        decoration: BoxDecoration(
          color: _tokens.surface2,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: _tokens.border, width: 1),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.55),
              blurRadius: 36,
              offset: const Offset(0, 16),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (rows.isEmpty && !showAddCashAction)
              SizedBox(
                height: 96,
                child: Center(
                  child: Text(
                    '暂无可选账户',
                    style: _dm(size: 12, color: _tokens.textSub),
                  ),
                ),
              ),
            if (rows.isNotEmpty)
              SizedBox(
                height: listHeight,
                child: MediaQuery.removePadding(
                  context: context,
                  removeTop: true,
                  child: ListView.builder(
                    padding: EdgeInsets.zero,
                    primary: false,
                    itemCount: rows.length,
                    itemBuilder: (context, index) {
                      final asset = rows[index];
                      final selected = asset.id == _selectedCashAssetId;
                      final amountText = asset.id == -999
                          ? null
                          : '${_assetCurrencySymbol(asset.curr)} ${_formatInputNumber(asset.amount)}';
                      return InkWell(
                        onTap: () {
                          setState(() => _selectedCashAssetId = asset.id);
                          _rememberCashAsset(asset.id);
                          _hideCashOverlay();
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 13,
                            vertical: 11,
                          ),
                          decoration: BoxDecoration(
                            color: selected
                                ? _tokens.goldDim
                                : Colors.transparent,
                            border: index < rows.length - 1
                                ? Border(
                                    bottom: BorderSide(
                                      color: _tokens.border,
                                      width: 1,
                                    ),
                                  )
                                : null,
                          ),
                          child: Row(
                            children: [
                              Container(
                                width: 30,
                                height: 30,
                                decoration: BoxDecoration(
                                  color: _accountBgColor(asset),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                alignment: Alignment.center,
                                child: Text(
                                  _accountEmoji(asset),
                                  style: _dm(size: 15),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Text(
                                      asset.displayName,
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: _dm(
                                        size: 13,
                                        weight: FontWeight.w500,
                                        color: _tokens.text,
                                      ),
                                    ),
                                    if (amountText != null) ...[
                                      const SizedBox(height: 2),
                                      Text(
                                        amountText,
                                        style: _mono(
                                          size: 11,
                                          color: _tokens.textMuted,
                                        ),
                                      ),
                                    ],
                                  ],
                                ),
                              ),
                              if (selected)
                                Icon(
                                  Icons.check,
                                  size: 16,
                                  color: _tokens.gold,
                                ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ),
            if (showAddCashAction)
              InkWell(
                onTap: () {
                  _hideCashOverlay();
                  unawaited(
                    _openAddFundingAccountDialog(
                      targetCurrency: targetCurrency,
                    ),
                  );
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 13,
                    vertical: 11,
                  ),
                  decoration: BoxDecoration(
                    border: Border(
                      top: BorderSide(color: _tokens.border, width: 1),
                    ),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 30,
                        height: 30,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          color: const Color(0x1A5B8DEF),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: const Color(0x595B8DEF),
                            width: 1,
                          ),
                        ),
                        child: const Icon(
                          Icons.add,
                          size: 15,
                          color: Color(0xFF5B8DEF),
                        ),
                      ),
                      const SizedBox(width: 9),
                      Text(
                        '添加账户',
                        style: _dm(
                          size: 13,
                          weight: FontWeight.w500,
                          color: const Color(0xFF5B8DEF),
                        ),
                      ),
                      const Spacer(),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildTradeToggle() {
    if (!_isTrade || _isDirectAdjustEntry) return const SizedBox.shrink();
    Widget item(String mode, String label) {
      final selected = _tradeMode == mode;
      return Expanded(
        child: InkWell(
          onTap: _saving ? null : () => _setTradeMode(mode),
          borderRadius: BorderRadius.circular(8),
          child: Container(
            height: 34,
            decoration: BoxDecoration(
              gradient: selected
                  ? const LinearGradient(
                      colors: [Color(0xF25B8DEF), Color(0xF24A7BE0)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    )
                  : null,
              color: selected ? null : _tokens.surface2,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: selected ? const Color(0x7A5B8DEF) : _tokens.border,
                width: 1,
              ),
              boxShadow: selected
                  ? [
                      BoxShadow(
                        color: const Color(0x384A7BE0),
                        blurRadius: 16,
                        offset: const Offset(0, 6),
                      ),
                    ]
                  : null,
            ),
            alignment: Alignment.center,
            child: Text(
              label,
              style: _dm(
                size: 12,
                weight: FontWeight.w600,
                color: selected ? Colors.white : _tokens.textMuted,
              ),
            ),
          ),
        ),
      );
    }

    return Row(
      children: [
        item('buy', '买入'),
        const SizedBox(width: 8),
        item('sell', '卖出'),
        const SizedBox(width: 8),
        item('adjust', '调整'),
      ],
    );
  }

  Widget _buildFundInputModeToggle() {
    if (!_isCurrentFundTarget()) return const SizedBox.shrink();
    Widget item(String value, String label) {
      final selected = _fundInputMode == value;
      return Expanded(
        child: InkWell(
          onTap: _saving ? null : () => _setFundInputMode(value),
          borderRadius: BorderRadius.circular(9),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 7),
            decoration: BoxDecoration(
              color: selected ? _tokens.goldDim : Colors.transparent,
              borderRadius: BorderRadius.circular(9),
              border: Border.all(
                color: selected ? _tokens.borderActive : _tokens.border,
                width: 1,
              ),
            ),
            child: Text(
              label,
              textAlign: TextAlign.center,
              style: _dm(
                size: 12,
                weight: FontWeight.w600,
                color: selected ? _tokens.text : _tokens.textMuted,
              ),
            ),
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('基金买入方式', style: _dm(size: 11, color: _tokens.textMuted)),
        const SizedBox(height: 6),
        Row(
          children: [
            item('qty', '按份额'),
            const SizedBox(width: 8),
            item('amount', '按金额'),
          ],
        ),
        if (_isFundAmountMode() && _navLoading)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(
              '正在获取最新净值…',
              style: _dm(size: 11, color: _tokens.textSub),
            ),
          ),
        if (_isFundAmountMode() && _navErrorText != null)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(
              _navErrorText!,
              style: _dm(size: 11, color: _tokens.red),
            ),
          ),
      ],
    );
  }

  Widget _buildInputCell({
    required String label,
    required TextField field,
    required bool focused,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: _dm(
            size: 11,
            weight: FontWeight.w500,
            color: _tokens.textMuted,
          ),
        ),
        const SizedBox(height: 6),
        AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          height: 38,
          padding: const EdgeInsets.symmetric(horizontal: 10),
          decoration: BoxDecoration(
            color: _tokens.surface2,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: focused ? const Color(0x996395EB) : _tokens.border,
              width: 1,
            ),
            boxShadow: focused
                ? [
                    BoxShadow(
                      color: const Color(0x1A6395EB),
                      blurRadius: 0,
                      spreadRadius: 3,
                    ),
                  ]
                : null,
          ),
          child: field,
        ),
      ],
    );
  }

  Widget _buildReadOnlyCell({required String label, required String value}) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: _dm(
              size: 11,
              weight: FontWeight.w500,
              color: _tokens.textMuted,
            ),
          ),
          const SizedBox(height: 6),
          Container(
            height: 38,
            decoration: BoxDecoration(
              color: _tokens.surface2,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: _tokens.border, width: 1),
            ),
            alignment: Alignment.centerLeft,
            padding: const EdgeInsets.symmetric(horizontal: 10),
            child: Text(
              value,
              style: _mono(
                size: 14,
                weight: FontWeight.w500,
                color: _tokens.text,
              ),
            ),
          ),
        ],
      ),
    );
  }

  TextField _buildNumberField({
    required Key key,
    required TextEditingController controller,
    required String hint,
    required TextInputType keyboardType,
    FocusNode? focusNode,
    List<TextInputFormatter>? inputFormatters,
    bool readOnly = false,
  }) {
    return TextField(
      key: key,
      controller: controller,
      focusNode: focusNode,
      readOnly: readOnly,
      expands: true,
      minLines: null,
      maxLines: null,
      textAlignVertical: TextAlignVertical.center,
      keyboardType: keyboardType,
      inputFormatters: inputFormatters,
      cursorColor: _tokens.blueStart,
      style: _mono(size: 14, weight: FontWeight.w500, color: _tokens.text),
      decoration: InputDecoration(
        filled: true,
        fillColor: Colors.transparent,
        border: InputBorder.none,
        enabledBorder: InputBorder.none,
        focusedBorder: InputBorder.none,
        errorBorder: InputBorder.none,
        focusedErrorBorder: InputBorder.none,
        disabledBorder: InputBorder.none,
        hintText: hint,
        hintStyle: _mono(size: 14, color: _tokens.textSub),
        isDense: true,
        contentPadding: EdgeInsets.zero,
      ),
    );
  }

  TextField _buildTextField({
    Key? key,
    required TextEditingController controller,
    required String hint,
    FocusNode? focusNode,
  }) {
    return TextField(
      key: key,
      controller: controller,
      focusNode: focusNode,
      expands: true,
      minLines: null,
      maxLines: null,
      textAlignVertical: TextAlignVertical.center,
      keyboardType: TextInputType.text,
      cursorColor: _tokens.blueStart,
      style: _dm(size: 14, weight: FontWeight.w500, color: _tokens.text),
      decoration: InputDecoration(
        filled: true,
        fillColor: Colors.transparent,
        border: InputBorder.none,
        enabledBorder: InputBorder.none,
        focusedBorder: InputBorder.none,
        errorBorder: InputBorder.none,
        focusedErrorBorder: InputBorder.none,
        disabledBorder: InputBorder.none,
        hintText: hint,
        hintStyle: _dm(size: 13, color: _tokens.textSub),
        isDense: true,
        contentPadding: EdgeInsets.zero,
      ),
    );
  }

  Widget _buildAdjustTypeField() {
    final selectedOption = _adjustModeOptions.firstWhere(
      (option) => option.value == _adjustType,
      orElse: () => _adjustModeOptions.first,
    );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '调整类型',
          style: _dm(
            size: 11,
            weight: FontWeight.w500,
            color: _tokens.textMuted,
          ),
        ),
        const SizedBox(height: 6),
        CompositedTransformTarget(
          link: _adjustTypeFieldLink,
          child: Container(
            key: _adjustTypeTargetKey,
            child: InkWell(
              onTap: _saving
                  ? null
                  : () {
                      if (_adjustTypeOverlayVisible) {
                        _hideAdjustTypeOverlay();
                      } else {
                        _showAdjustTypeOverlay();
                      }
                    },
              borderRadius: BorderRadius.circular(8),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 180),
                height: 38,
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  color: _tokens.surface2,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: _adjustTypeOverlayVisible
                        ? const Color(0x73D4AF64)
                        : _tokens.border,
                    width: 1,
                  ),
                  boxShadow: _adjustTypeOverlayVisible
                      ? [
                          const BoxShadow(
                            color: Color(0x12D4AF64),
                            blurRadius: 0,
                            spreadRadius: 3,
                          ),
                        ]
                      : null,
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        selectedOption.label,
                        style: _dm(
                          size: 13,
                          weight: FontWeight.w600,
                          color: _tokens.text,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    AnimatedRotation(
                      turns: _adjustTypeOverlayVisible ? 0.5 : 0,
                      duration: const Duration(milliseconds: 180),
                      child: Icon(
                        Icons.keyboard_arrow_down_rounded,
                        color: _tokens.textMuted,
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

  Widget _buildAdjustTypeOverlayCard() {
    return Container(
      decoration: BoxDecoration(
        color: _tokens.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: _tokens.borderActive, width: 1),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.35),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: _adjustModeOptions.map((option) {
          final selected = option.value == _adjustType;
          return InkWell(
            onTap: () {
              _setAdjustType(option.value);
              _hideAdjustTypeOverlay();
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                color: selected ? const Color(0x1A5B8DEF) : Colors.transparent,
                border: Border(
                  bottom: BorderSide(
                    color: _tokens.divider,
                    width: option == _adjustModeOptions.last ? 0 : 1,
                  ),
                ),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      option.label,
                      style: _dm(
                        size: 13,
                        weight: selected ? FontWeight.w700 : FontWeight.w500,
                        color: selected ? _tokens.blueStart : _tokens.text,
                      ),
                    ),
                  ),
                  if (selected)
                    Icon(Icons.check_rounded, size: 16, color: _tokens.gold),
                ],
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildTradeInputFields() {
    if (_isTrade && _isAdjust) {
      return Column(
        children: [
          _buildAdjustTypeField(),
          const SizedBox(height: 8),
          _buildInputCell(
            label: _adjustInputLabel(),
            focused: _adjustAmountFocusNode.hasFocus,
            field: _buildNumberField(
              key: _adjustAmountFieldKey,
              controller: _adjustController,
              focusNode: _adjustAmountFocusNode,
              hint: '0.00',
              keyboardType: TextInputType.numberWithOptions(
                decimal: true,
                signed: false,
              ),
            ),
          ),
          const SizedBox(height: 8),
          _buildInputCell(
            label: '备注',
            focused: _noteFocusNode.hasFocus,
            field: _buildTextField(
              key: _noteFieldKey,
              controller: _noteController,
              focusNode: _noteFocusNode,
              hint: '可选，补充本次修正说明',
            ),
          ),
        ],
      );
    }

    final amountMode = _isFundAmountMode();
    final qtyPreview = _deriveFundQtyFromAmountNav();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (_isCurrentFundTarget()) ...[
          _buildFundInputModeToggle(),
          const SizedBox(height: 10),
        ],
        Row(
          children: [
            Expanded(
              child: _buildInputCell(
                label: amountMode ? '净值' : '成本价',
                focused: _priceFocusNode.hasFocus,
                field: _buildNumberField(
                  key: _priceFieldKey,
                  controller: _priceController,
                  focusNode: _priceFocusNode,
                  hint: '0.00',
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                    signed: true,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            amountMode
                ? _buildReadOnlyCell(
                    label: '数量',
                    value: qtyPreview == null
                        ? '--'
                        : _formatQtyDisplay(qtyPreview),
                  )
                : Expanded(
                    child: _buildInputCell(
                      label: '数量',
                      focused: _qtyFocusNode.hasFocus,
                      field: _buildNumberField(
                        key: _qtyFieldKey,
                        controller: _qtyController,
                        focusNode: _qtyFocusNode,
                        hint: '0',
                        keyboardType: const TextInputType.numberWithOptions(
                          decimal: true,
                          signed: false,
                        ),
                        inputFormatters: _isCurrentFundTarget()
                            ? _fundQtyInputFormatters
                            : _qtyInputFormatters,
                      ),
                    ),
                  ),
          ],
        ),
        const SizedBox(height: 8),
        _buildInputCell(
          label: '金额',
          focused: _amountFocusNode.hasFocus,
          field: _buildNumberField(
            key: _amountFieldKey,
            controller: _amountController,
            focusNode: _amountFocusNode,
            hint: '0.00',
            keyboardType: const TextInputType.numberWithOptions(
              decimal: true,
              signed: false,
            ),
          ),
        ),
      ],
    );
  }

  bool _isSaveInputReady() {
    final mode = _currentActionMode();
    final priceReady = _priceController.text.trim().isNotEmpty;
    final qtyReady = _qtyController.text.trim().isNotEmpty;
    final amountReady = _amountController.text.trim().isNotEmpty;
    if (_isAdd) {
      if (_isFundAmountMode()) {
        return _selected != null && amountReady && priceReady;
      }
      return _selected != null && priceReady && qtyReady;
    }
    if (mode == 'adjust') {
      return _adjustController.text.trim().isNotEmpty;
    }
    if (mode == 'buy' && _isFundAmountMode()) {
      return amountReady && priceReady;
    }
    return priceReady && qtyReady;
  }

  String _submitLabel() {
    if (_isAdd) return '确认添加';
    final action = _currentActionMode();
    if (action == 'sell') return '确认卖出';
    if (action == 'adjust') return '保存调整';
    return '保存';
  }

  String _dialogTitle() {
    if (_isAdd) return '添加资产';
    final name = (widget.item?.displayName ?? '').trim();
    final suffix = name.isEmpty ? '' : ' · $name';
    final action = _currentActionMode();
    if (action == 'sell') return '减仓$suffix';
    if (action == 'adjust') return '修正$suffix';
    return '加仓$suffix';
  }

  Widget _buildCashSelector({
    required List<Asset> cashOptions,
    required String targetCurrency,
    required bool showAddCashAction,
  }) {
    Asset? selected;
    for (final asset in cashOptions) {
      if (asset.id == _selectedCashAssetId) {
        selected = asset;
        break;
      }
    }
    return CompositedTransformTarget(
      link: _cashFieldLink,
      child: Container(
        key: _cashTargetKey,
        height: 38,
        decoration: BoxDecoration(
          color: _tokens.surface2,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: _cashOverlayVisible
                ? const Color(0x996395EB)
                : _tokens.border,
            width: 1,
          ),
          boxShadow: _cashOverlayVisible
              ? [
                  BoxShadow(
                    color: const Color(0x1A6395EB),
                    blurRadius: 0,
                    spreadRadius: 3,
                  ),
                ]
              : null,
        ),
        child: InkWell(
          key: _cashTriggerKey,
          onTap: _saving || (cashOptions.isEmpty && !showAddCashAction)
              ? null
              : () {
                  if (_cashOverlayVisible) {
                    _hideCashOverlay();
                  } else {
                    _showCashOverlay(
                      cashOptions: cashOptions,
                      targetCurrency: targetCurrency,
                      showAddCashAction: showAddCashAction,
                    );
                  }
                },
          borderRadius: BorderRadius.circular(8),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(12, 0, 10, 0),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    selected == null
                        ? '请选择账户'
                        : selected.id == -999
                        ? selected.displayName
                        : '${selected.displayName} · ${_assetCurrencySymbol(selected.curr)} ${_formatInputNumber(selected.amount)}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: _dm(
                      size: 13,
                      weight: FontWeight.w500,
                      color: selected == null
                          ? _tokens.textMuted
                          : _tokens.text,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                AnimatedRotation(
                  turns: _cashOverlayVisible ? 0.5 : 0.0,
                  duration: const Duration(milliseconds: 200),
                  child: Icon(
                    Icons.keyboard_arrow_down_rounded,
                    color: _tokens.textMuted,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_inlineClosed) return const SizedBox.shrink();
    final appState = context.watch<AppState>();
    final actionMode = _currentActionMode();
    final targetCashCurrency = _targetCashCurrency(appState, actionMode);
    final matchedCashOptions = appState.cashAssets
        .where((asset) => (asset.id ?? 0) > 0)
        .where(
          (asset) => _normalizeCurrencyCode(asset.curr) == targetCashCurrency,
        )
        .toList();
    final cashOptions = <Asset>[...matchedCashOptions];
    if (actionMode != 'sell') {
      cashOptions.insert(
        0,
        Asset(
          id: -999,
          name: '外部资金/初始转入',
          amount: 0.0,
          curr: targetCashCurrency,
        ),
      );
    }
    if (_selectedCashAssetId != null &&
        cashOptions.every((asset) => asset.id != _selectedCashAssetId)) {
      _selectedCashAssetId = null;
    }
    if (_selectedCashAssetId == null && cashOptions.isNotEmpty) {
      final realAccounts = cashOptions.where((a) => a.id != -999);
      if (realAccounts.isNotEmpty) {
        _selectedCashAssetId = realAccounts.first.id;
      } else {
        _selectedCashAssetId = cashOptions.first.id;
      }
    }
    final needsCashSource = _requiresCashSource(actionMode);
    final showAddCashAction = true;
    final canSave =
        !_saving &&
        _isSaveInputReady() &&
        (!needsCashSource || _selectedCashAssetId != null);

    final centered =
        widget.presentation == InvestTradeDialogPresentation.centered;
    final dialogBody = Container(
      key: _sheetRootKey,
      width: double.infinity,
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.86,
        maxWidth: 390,
      ),
      decoration: BoxDecoration(
        color: _tokens.surface,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0x12FFFFFF), width: 1.0),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.7),
            blurRadius: 64,
            offset: const Offset(0, 24),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Handle for tests
          SizedBox(key: _sheetHandleKey, height: 0),
          // Header
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 11),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  _dialogTitle(),
                  style: _dm(
                    size: 16,
                    weight: FontWeight.w700,
                    color: _tokens.text,
                    letterSpacing: -0.01,
                  ),
                ),
                const SizedBox(width: 24, height: 24),
              ],
            ),
          ),
          Divider(height: 1, color: _tokens.border),
          Flexible(
            child: SingleChildScrollView(
              keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(14, 12, 14, 14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (_isAdd) ...[
                      _buildSearchField(),
                      if (_searchErrorText != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 6),
                          child: Text(
                            _searchErrorText!,
                            style: _dm(size: 11, color: _tokens.red),
                          ),
                        ),
                    ],
                    if (_isTrade && !_isDirectAdjustEntry) ...[
                      const SizedBox(height: 10),
                      _buildTradeToggle(),
                    ],
                    if (needsCashSource) ...[
                      const SizedBox(height: 10),
                      Text(
                        '资金账户',
                        style: _dm(size: 11, color: _tokens.textMuted),
                      ),
                      const SizedBox(height: 5),
                      _buildCashSelector(
                        cashOptions: cashOptions,
                        targetCurrency: targetCashCurrency,
                        showAddCashAction: showAddCashAction,
                      ),
                    ],
                    const SizedBox(height: 12),
                    _buildTradeInputFields(),
                    if (_errorText != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: Text(
                          _errorText!,
                          style: _dm(size: 12, color: _tokens.red),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),
          Divider(height: 1, color: _tokens.border),
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
            child: Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: 44,
                    child: TextButton(
                      key: _cancelButtonKey,
                      onPressed: _saving ? null : _closeDialog,
                      style: TextButton.styleFrom(
                        backgroundColor: _tokens.surface2,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                      child: Text(
                        '取消',
                        style: _dm(
                          size: 14,
                          weight: FontWeight.w600,
                          color: _tokens.textSub,
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: SizedBox(
                    height: 44,
                    child: Container(
                      decoration: BoxDecoration(
                        gradient: !canSave
                            ? null
                            : LinearGradient(
                                colors: [_tokens.blueStart, _tokens.blueEnd],
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                              ),
                        color: canSave
                            ? null
                            : (AppTheme.isLight
                                  ? const Color(0xFFE4E5EA)
                                  : const Color(0xFF3B4048)),
                        borderRadius: BorderRadius.circular(8),
                        boxShadow: !canSave
                            ? null
                            : [
                                BoxShadow(
                                  color: const Color(0x384A7BE0),
                                  blurRadius: 16,
                                  offset: const Offset(0, 6),
                                ),
                              ],
                      ),
                      child: ElevatedButton(
                        key: _submitButtonKey,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.transparent,
                          foregroundColor: Colors.transparent,
                          shadowColor: Colors.transparent,
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                        onPressed: canSave ? _submit : null,
                        child: _saving
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : Text(
                                _submitLabel(),
                                style: _dm(
                                  size: 14,
                                  weight: FontWeight.w600,
                                  color: canSave
                                      ? Colors.white
                                      : _tokens.textSub,
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
    );

    return Material(
      color: Colors.transparent,
      child: centered
          ? SafeArea(
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 20,
                  ),
                  child: dialogBody,
                ),
              ),
            )
          : SafeArea(
              top: false,
              child: Align(
                alignment: Alignment.bottomCenter,
                child: dialogBody,
              ),
            ),
    );
  }
}
