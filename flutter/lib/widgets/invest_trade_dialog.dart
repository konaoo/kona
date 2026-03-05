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

Future<T?> showInvestTradeSheet<T>({
  required BuildContext context,
  required String mode,
  PortfolioItem? item,
  BuildContext? hostContext,
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
  final InvestTradeDialogPresentation presentation;

  const InvestTradeDialog({
    super.key,
    required this.mode,
    this.item,
    this.hostContext,
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
  final _adjustPriceFocusNode = FocusNode();
  final _adjustAmountFocusNode = FocusNode();
  final _priceController = TextEditingController();
  final _qtyController = TextEditingController();
  final _amountController = TextEditingController();
  final _adjustPriceController = TextEditingController();
  final _adjustController = TextEditingController();
  final LayerLink _searchFieldLink = LayerLink();
  final LayerLink _cashFieldLink = LayerLink();
  final GlobalKey _searchTargetKey = GlobalKey();
  final GlobalKey _cashTargetKey = GlobalKey();

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
  String _fundInputMode = 'qty';
  int? _selectedCashAssetId;
  int _searchSeq = 0;
  int _navFetchSeq = 0;
  OverlayEntry? _searchOverlayEntry;
  OverlayEntry? _cashOverlayEntry;
  bool _searchOverlayVisible = false;
  bool _cashOverlayVisible = false;
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
  static const Key _adjustPriceFieldKey = Key('invest_adjust_price_field');
  static const Key _adjustAmountFieldKey = Key('invest_adjust_amount_field');
  static const Key _submitButtonKey = Key('invest_submit_button');
  static const Key _cancelButtonKey = Key('invest_cancel_button');

  bool get _isAdd => widget.mode == 'add';
  bool get _isBuy => widget.mode == 'buy';
  bool get _isSell => widget.mode == 'sell';
  bool get _isTrade => widget.mode == 'trade';
  bool get _isAdjust => _tradeMode == 'adjust';

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
    _adjustPriceController.addListener(_onInputControllerChanged);
    _adjustController.addListener(_onInputControllerChanged);
    _queryFocusNode.addListener(_onQueryFocusChanged);
    _priceFocusNode.addListener(_onInputControllerChanged);
    _qtyFocusNode.addListener(_onInputControllerChanged);
    _amountFocusNode.addListener(_onInputControllerChanged);
    _adjustPriceFocusNode.addListener(_onInputControllerChanged);
    _adjustAmountFocusNode.addListener(_onInputControllerChanged);
    _syncDefaultCashAsset();
    if (!_isAdd && widget.item != null) {
      _prefillPriceFromCurrent();
      if (_isTrade) {
        _tradeMode = 'buy';
        _adjustController.clear();
        _adjustPriceController.clear();
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
    _adjustPriceController.removeListener(_onInputControllerChanged);
    _adjustController.removeListener(_onInputControllerChanged);
    _queryFocusNode.removeListener(_onQueryFocusChanged);
    _priceFocusNode.removeListener(_onInputControllerChanged);
    _qtyFocusNode.removeListener(_onInputControllerChanged);
    _amountFocusNode.removeListener(_onInputControllerChanged);
    _adjustPriceFocusNode.removeListener(_onInputControllerChanged);
    _adjustAmountFocusNode.removeListener(_onInputControllerChanged);
    _hideSearchOverlay(updateState: false);
    _hideCashOverlay(updateState: false);
    _queryFocusNode.dispose();
    _priceFocusNode.dispose();
    _qtyFocusNode.dispose();
    _amountFocusNode.dispose();
    _adjustPriceFocusNode.dispose();
    _adjustAmountFocusNode.dispose();
    _queryController.dispose();
    _priceController.dispose();
    _qtyController.dispose();
    _amountController.dispose();
    _adjustPriceController.dispose();
    _adjustController.dispose();
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

  Widget _marketBadge(String typeName) {
    String label = 'A股';
    Color color = AppTheme.accent;
    switch (typeName) {
      case '美股':
        label = '美股';
        color = AppTheme.danger;
        break;
      case '港股':
        label = '港股';
        color = AppTheme.success;
        break;
      case '基金':
        label = '基金';
        color = const Color(0xFFF59E0B);
        break;
      default:
        label = 'A股';
        color = AppTheme.accent;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.18),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withValues(alpha: 0.6), width: 1),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: FontSize.xs,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
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
    return text.replaceFirst(RegExp(r'\.?0+$'), '');
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

  InputDecoration _compactDecoration(String labelText, {String? hintText}) {
    return InputDecoration(
      labelText: labelText,
      hintText: hintText,
      isDense: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
    );
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

  List<Asset> _recentCashAssets(List<Asset> options) {
    final byId = <int, Asset>{
      for (final asset in options)
        if (asset.id != null) asset.id!: asset,
    };
    final result = <Asset>[];
    for (final id in _recentCashAssetIds) {
      final asset = byId[id];
      if (asset != null) result.add(asset);
    }
    return result;
  }

  Widget _buildCashAssetTile({
    required Asset asset,
    required bool selected,
    required VoidCallback onTap,
  }) {
    final isExternal = asset.id == -999;
    final amountText = isExternal ? '外部' : _formatInputNumber(asset.amount);

    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          border: Border(
            bottom: BorderSide(
              color: AppTheme.border.withOpacity(
                AppTheme.isLight ? 0.55 : 0.22,
              ),
              width: 1,
            ),
          ),
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    asset.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    isExternal ? '外部资金' : asset.curr,
                    style: TextStyle(
                      fontSize: 12,
                      color: AppTheme.textTertiary,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 10),
            Text(
              amountText,
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(width: 10),
            Icon(
              selected ? Icons.check_circle : Icons.radio_button_unchecked,
              size: 18,
              color: selected ? AppTheme.accent : AppTheme.textTertiary,
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _openCashAssetPicker({
    required String actionMode,
    required List<Asset> cashOptions,
  }) async {
    if (_saving || cashOptions.isEmpty) return;

    final currencySet = cashOptions
        .map((e) => e.curr.trim().toUpperCase())
        .where((e) => e.isNotEmpty && e != 'CNY')
        .toSet();
    final subtitle = currencySet.isEmpty
        ? '（CNY）'
        : '（含 ${currencySet.join("/")}）';

    final picked = await showModalBottomSheet<int>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (sheetContext) {
        var query = '';
        return SafeArea(
          child: StatefulBuilder(
            builder: (context, setSheetState) {
              final filtered = cashOptions.where((asset) {
                if (query.trim().isEmpty) return true;
                final key = query.trim().toLowerCase();
                return asset.name.toLowerCase().contains(key) ||
                    asset.curr.toLowerCase().contains(key);
              }).toList();

              final recent = _recentCashAssets(filtered);
              final recentIds = recent
                  .map((asset) => asset.id)
                  .whereType<int>()
                  .toSet();
              final all = filtered.where((asset) {
                final id = asset.id;
                return id == null || !recentIds.contains(id);
              }).toList();

              Widget sectionTitle(String text) {
                return Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                  child: Text(
                    text,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                );
              }

              return FractionallySizedBox(
                heightFactor: 0.7,
                child: Container(
                  decoration: BoxDecoration(
                    color: AppTheme.bgCard,
                    borderRadius: const BorderRadius.vertical(
                      top: Radius.circular(18),
                    ),
                    border: Border.all(
                      color: AppTheme.border.withOpacity(
                        AppTheme.isLight ? 0.7 : 0.3,
                      ),
                      width: 1,
                    ),
                  ),
                  child: Column(
                    children: [
                      const SizedBox(height: 10),
                      Container(
                        width: 38,
                        height: 4,
                        decoration: BoxDecoration(
                          color: AppTheme.textTertiary.withValues(alpha: 0.45),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 14, 16, 2),
                        child: Row(
                          children: [
                            Expanded(
                              child: Text(
                                actionMode == 'sell' ? '选择回款账户' : '选择转入账户',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.w700,
                                  color: AppTheme.textPrimary,
                                ),
                              ),
                            ),
                            TextButton(
                              onPressed: () => Navigator.pop(sheetContext),
                              child: const Text('关闭'),
                            ),
                          ],
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 0, 16, 10),
                        child: Align(
                          alignment: Alignment.centerLeft,
                          child: Text(
                            subtitle,
                            style: TextStyle(
                              fontSize: 12,
                              color: AppTheme.textTertiary,
                            ),
                          ),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 0, 16, 10),
                        child: TextField(
                          autofocus: false,
                          style: TextStyle(
                            fontSize: 14,
                            color: AppTheme.textPrimary,
                          ),
                          decoration: InputDecoration(
                            isDense: true,
                            prefixIcon: Icon(
                              Icons.search,
                              size: 18,
                              color: AppTheme.textSecondary,
                            ),
                            hintText: '搜索账户名 / 币种',
                            hintStyle: TextStyle(
                              fontSize: 14,
                              color: AppTheme.textTertiary,
                            ),
                            border: InputBorder.none,
                            enabledBorder: InputBorder.none,
                            focusedBorder: InputBorder.none,
                            errorBorder: InputBorder.none,
                            focusedErrorBorder: InputBorder.none,
                            disabledBorder: InputBorder.none,
                            contentPadding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 10,
                            ),
                          ),
                          onChanged: (value) {
                            setSheetState(() => query = value);
                          },
                        ),
                      ),
                      Expanded(
                        child: filtered.isEmpty
                            ? Center(
                                child: Text(
                                  '没有匹配账户',
                                  style: TextStyle(
                                    fontSize: 13,
                                    color: AppTheme.textTertiary,
                                  ),
                                ),
                              )
                            : ListView(
                                children: [
                                  if (recent.isNotEmpty) ...[
                                    sectionTitle('最近使用'),
                                    ...recent.map(
                                      (asset) => _buildCashAssetTile(
                                        asset: asset,
                                        selected:
                                            asset.id == _selectedCashAssetId,
                                        onTap: () => Navigator.pop(
                                          sheetContext,
                                          asset.id,
                                        ),
                                      ),
                                    ),
                                  ],
                                  if (all.isNotEmpty) ...[
                                    sectionTitle('全部账户'),
                                    ...all.map(
                                      (asset) => _buildCashAssetTile(
                                        asset: asset,
                                        selected:
                                            asset.id == _selectedCashAssetId,
                                        onTap: () => Navigator.pop(
                                          sheetContext,
                                          asset.id,
                                        ),
                                      ),
                                    ),
                                  ],
                                  const SizedBox(height: 10),
                                ],
                              ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        );
      },
    );

    if (picked != null && mounted) {
      setState(() => _selectedCashAssetId = picked);
      _rememberCashAsset(picked);
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
    FocusScope.of(context).unfocus();
    setState(() {
      _tradeMode = mode;
      _errorText = null;
      _navErrorText = null;
      _navLoading = false;
      if (mode == 'adjust') {
        _adjustController.clear();
        final item = widget.item;
        if (item != null) {
          final decimals =
              _isFundAsset(assetType: item.assetType, code: item.code) ? 4 : 3;
          _adjustPriceController.text = _formatInputNumber(
            item.price,
            decimals: decimals,
          );
        } else {
          _adjustPriceController.clear();
        }
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
        final adjustPriceStr = _adjustPriceController.text.trim();
        final adjustVal = double.tryParse(adjustStr);
        final adjustPriceVal = double.tryParse(adjustPriceStr);
        if (adjustVal == null) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效调整金额';
          });
          return;
        }
        if (adjustPriceVal == null) {
          setState(() {
            _saving = false;
            _errorText = '请输入有效平均成本';
          });
          return;
        }
        final qtyVal = widget.item?.qty ?? 0;
        if (qtyVal <= 0) {
          setState(() {
            _saving = false;
            _errorText = '未找到有效持仓数量';
          });
          return;
        }
        actionFuture = appState.modifyInvestment(
          code: code,
          qty: qtyVal,
          price: adjustPriceVal,
          adjustment: adjustVal,
          awaitRefresh: false,
        );
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

    TopToast.showSuccess(toastContext, '已保存');
    _closeDialog();

    final undoToken = result.data?['undo_token']?.toString();
    if (undoToken != null && undoToken.isNotEmpty) {
      TopToast.showAction(
        toastContext,
        message: '已保存',
        actionLabel: '撤销',
        onAction: () {
          unawaited(() async {
            final undoResult = await appState.undoInvestmentOperation(
              undoToken,
            );
            if (!toastContext.mounted) return;
            if (undoResult.ok) {
              TopToast.showInfo(toastContext, '已撤销');
            } else {
              TopToast.showError(toastContext, undoResult.message ?? '撤销失败');
            }
          }());
        },
        duration: const Duration(seconds: 15),
      );
    }
  }

  Future<void> _confirmCorrectiveDelete() async {
    if (_saving) return;
    final item = widget.item;
    if (item == null) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('删除并清理历史'),
          content: Text(
            '仅用于误录入纠错：将删除「${item.name}」持仓、相关交易记录，并清理受影响快照。\n'
            '注意：不会回款到现金账户。\n'
            '如果是正常平仓，请使用“卖出”并选择回款账户。',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('取消'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('仍要纠错删除'),
            ),
          ],
        );
      },
    );
    if (confirmed != true) return;
    if (!mounted) return;
    // ignore: use_build_context_synchronously
    final appState = context.read<AppState>();
    // ignore: use_build_context_synchronously
    final toastContext = widget.hostContext ?? context;
    // ignore: use_build_context_synchronously
    _closeDialog();
    // ignore: use_build_context_synchronously
    TopToast.showSuccess(toastContext, '已删除');
    unawaited(() async {
      final result = await appState.deleteInvestment(
        code: item.code,
        corrective: true,
        awaitRefresh: false,
      );
      // ignore: use_build_context_synchronously
      if (!toastContext.mounted) return;
      if (!result.ok) {
        TopToast.showError(toastContext, result.message ?? '删除失败，请稍后重试');
      }
    }());
  }

  void _onMoreMenuSelect(String value) {
    if (value == 'corrective_delete') {
      _confirmCorrectiveDelete();
    }
  }

  void _markOverlaysNeedsBuild() {
    _searchOverlayEntry?.markNeedsBuild();
    _cashOverlayEntry?.markNeedsBuild();
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

  void _showSearchOverlay() {
    if (!_isAdd || _selected != null) return;
    if (!_searchTriggered) return;
    if (_queryController.text.trim().isEmpty) return;
    _hideCashOverlay();
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
                separatorBuilder: (_, __) =>
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
                  final changePct = _searchResultChangePct(item, appState);
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
                                    : _formatInputNumber(
                                        price,
                                        decimals: isFund ? 4 : 2,
                                      ),
                                style: _mono(size: 13, color: _tokens.text),
                              ),
                              Text(
                                changePct == null
                                    ? '--'
                                    : '${changePct >= 0 ? '+' : ''}${_formatInputNumber(changePct, decimals: 2)}%',
                                style: _dm(
                                  size: 10,
                                  weight: FontWeight.w500,
                                  color: (changePct ?? 0) >= 0
                                      ? _tokens.green
                                      : _tokens.red,
                                ),
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
    final changePct = _searchResultChangePct(item, appState);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: _tokens.goldDim,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: _tokens.gold.withValues(alpha: 0.2), width: 1),
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
          Text(
            price == null
                ? '--'
                : _formatInputNumber(price, decimals: isFund ? 4 : 2),
            style: _mono(size: 12, color: _tokens.text),
          ),
          const SizedBox(width: 8),
          Text(
            changePct == null
                ? '--'
                : '${changePct >= 0 ? '+' : ''}${_formatInputNumber(changePct, decimals: 2)}%',
            style: _dm(
              size: 10,
              weight: FontWeight.w600,
              color: (changePct ?? 0) >= 0 ? _tokens.green : _tokens.red,
            ),
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
                          : '${asset.curr} ${_formatInputNumber(asset.amount)}';
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
                            color: selected ? _tokens.goldDim : Colors.transparent,
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
                                child: Text(_accountEmoji(asset), style: _dm(size: 15)),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Text(
                                      asset.name,
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
    if (!_isTrade) return const SizedBox.shrink();
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

  Widget _buildTradeInputFields() {
    if (_isTrade && _isAdjust) {
      return Column(
        children: [
          _buildInputCell(
            label: '平均成本',
            focused: _adjustPriceFocusNode.hasFocus,
            field: _buildNumberField(
              key: _adjustPriceFieldKey,
              controller: _adjustPriceController,
              focusNode: _adjustPriceFocusNode,
              hint: '0.00',
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
                signed: true,
              ),
            ),
          ),
          const SizedBox(height: 8),
          _buildInputCell(
            label: '调整金额',
            focused: _adjustAmountFocusNode.hasFocus,
            field: _buildNumberField(
              key: _adjustAmountFieldKey,
              controller: _adjustController,
              focusNode: _adjustAmountFocusNode,
              hint: '0.00',
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
                signed: true,
              ),
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
            const SizedBox(width: 8),
            Expanded(
              child: _buildInputCell(
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
            ),
          ],
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
      return _adjustController.text.trim().isNotEmpty &&
          _adjustPriceController.text.trim().isNotEmpty;
    }
    if (mode == 'buy' && _isFundAmountMode()) {
      return amountReady && priceReady;
    }
    return priceReady && qtyReady;
  }

  String _sheetTitle() {
    if (_isAdd) return '添加资产';
    final action = _currentActionMode();
    if (action == 'sell') return '卖出';
    if (action == 'adjust') return '调整';
    return '买入';
  }

  String _submitLabel() {
    if (_isAdd) return '确认添加';
    final action = _currentActionMode();
    if (action == 'sell') return '确认卖出';
    if (action == 'adjust') return '保存调整';
    return '保存';
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
                        ? selected.name
                        : '${selected.name} · ${selected.curr} ${_formatInputNumber(selected.amount)}',
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
    final hasMatchingCashAccount = matchedCashOptions.isNotEmpty;
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
                  _isAdd ? '添加资产' : '编辑资产',
                  style: _dm(
                    size: 13,
                    weight: FontWeight.w400,
                    color: _tokens.textMuted,
                    letterSpacing: 0.02,
                  ),
                ),
                _isAdd
                    ? InkWell(
                        onTap: _saving ? null : _closeDialog,
                        customBorder: const CircleBorder(),
                        child: Container(
                          width: 24,
                          height: 24,
                          decoration: BoxDecoration(
                            color: _tokens.surface2,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            Icons.close,
                            size: 14,
                            color: _tokens.textMuted,
                          ),
                        ),
                      )
                    : Theme(
                        data: Theme.of(context).copyWith(
                          splashColor: Colors.transparent,
                          highlightColor: Colors.transparent,
                        ),
                        child: PopupMenuButton<String>(
                          onSelected: _onMoreMenuSelect,
                          color: _tokens.surface2,
                          elevation: 8,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                            side: BorderSide(color: _tokens.border, width: 1),
                          ),
                          offset: const Offset(0, 32),
                          itemBuilder: (context) => [
                            PopupMenuItem(
                              value: 'corrective_delete',
                              height: 40,
                              padding: const EdgeInsets.symmetric(horizontal: 16),
                              child: Row(
                                children: [
                                  Icon(Icons.delete_outline, size: 16, color: _tokens.red),
                                  const SizedBox(width: 8),
                                  Text(
                                    '删除该资产',
                                    style: _dm(size: 13, color: _tokens.red, weight: FontWeight.w500),
                                  ),
                                ],
                              ),
                            ),
                          ],
                          child: Container(
                            width: 24,
                            height: 24,
                            decoration: BoxDecoration(
                              color: _tokens.surface2,
                              shape: BoxShape.circle,
                            ),
                            child: Icon(
                              Icons.more_horiz,
                              size: 14,
                              color: _tokens.textMuted,
                            ),
                          ),
                        ),
                      ),
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
                    ] else ...[
                      // Stock Info Card
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 7,
                        ),
                        decoration: BoxDecoration(
                          color: _tokens.goldDim,
                          border: Border.all(
                            color: _tokens.gold.withValues(alpha: 0.2),
                            width: 1,
                          ),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 6,
                                vertical: 1,
                              ),
                              decoration: BoxDecoration(
                                color:
                                    widget.item?.marketType.toLowerCase() ==
                                        'a'
                                    ? const Color(0x243ECF82)
                                    : widget.item?.marketType.toLowerCase() ==
                                          'hk'
                                    ? const Color(0x24E06B3A)
                                    : widget.item?.marketType.toLowerCase() ==
                                          'us'
                                    ? const Color(0x245B8DEF)
                                    : const Color(0x24B57ADB), // fund
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                widget.item?.marketType.toLowerCase() == 'hk'
                                    ? '港股'
                                    : widget.item?.marketType.toLowerCase() ==
                                          'us'
                                    ? '美股'
                                    : widget.item?.marketType.toLowerCase() ==
                                          'fund'
                                    ? '基金'
                                    : 'A股',
                                style: _dm(
                                  size: 10,
                                  weight: FontWeight.w600,
                                  letterSpacing: 0.03,
                                  color:
                                      widget.item?.marketType.toLowerCase() ==
                                          'a'
                                      ? const Color(0xFF3ECF82)
                                      : widget.item?.marketType.toLowerCase() ==
                                            'hk'
                                      ? const Color(0xFFE06B3A)
                                      : widget.item?.marketType.toLowerCase() ==
                                            'us'
                                      ? const Color(0xFF5B8DEF)
                                      : const Color(0xFFB57ADB), // fund
                                ),
                              ),
                            ),
                            const SizedBox(width: 7),
                            Text(
                              _formatDisplayCode(widget.item?.code ?? ''),
                              style: _mono(
                                size: 12,
                                weight: FontWeight.w500,
                                color: _tokens.gold,
                              ),
                            ),
                            const SizedBox(width: 7),
                            Container(
                              width: 1,
                              height: 10,
                              color: _tokens.gold.withValues(alpha: 0.25),
                            ),
                            const SizedBox(width: 7),
                            Expanded(
                              child: Text(
                                (widget.item?.name ?? '').length > 20
                                    ? '${(widget.item?.name ?? '').substring(0, 20)}...'
                                    : (widget.item?.name ?? ''),
                                style: _dm(size: 11, color: _tokens.textSub),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            const SizedBox(width: 7),
                            Text(
                              '368.20', // TODO: Fetch real price if available, hardcoded placeholder for now
                              style: _mono(size: 11, color: _tokens.text),
                            ),
                            const SizedBox(width: 7),
                            Text(
                              '+1.54%', // TODO: Fetch real PnL
                              style: _dm(
                                size: 10,
                                weight: FontWeight.w500,
                                color: _tokens.red,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                    if (_isTrade) ...[
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
                            : const LinearGradient(
                                colors: [Color(0xFF5B8DEF), Color(0xFF4A7BE0)],
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                              ),
                        color: canSave ? null : const Color(0xFF3B4048),
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
                                      : const Color(0xFF8C91A0),
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
