import 'dart:async';

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../utils/asset_name_utils.dart';
import '../services/api_service.dart';
import '../services/cache_service.dart';
import '../providers/app_state.dart';
import '../widgets/calendar_period_wheel_sheet.dart';

enum CalendarPeriodWheelMode { day, month }

// Test Keys
const kCalendarYearWheelKey = Key('calendar-year-wheel');
const kCalendarMonthWheelKey = Key('calendar-month-wheel');

String _currencySymbol(String curr) {
  final upper = curr.trim().toUpperCase();
  if (upper == 'HKD') return 'HK\$';
  if (upper == 'USD') return '\$';
  return '¥';
}

// ──────────────────────────────────────────────────
// Cached TextStyles – DM Sans for labels, JetBrains Mono for numbers
// ──────────────────────────────────────────────────
class _S {
  _S._();
  // Overview
  static final label = GoogleFonts.dmSans(
    fontSize: 12,
    fontWeight: FontWeight.w500,
    letterSpacing: 0.01,
  );
  static final value = GoogleFonts.jetBrainsMono(
    fontSize: 28,
    fontWeight: FontWeight.w600,
    letterSpacing: -0.02,
  );
  static final pnlRate = GoogleFonts.dmSans(
    fontSize: 12,
    fontWeight: FontWeight.w700,
  );
  // Calendar
  static final calDate = GoogleFonts.jetBrainsMono(
    fontSize: 13,
    fontWeight: FontWeight.w600,
  );
  static final calPnl = GoogleFonts.jetBrainsMono(
    fontSize: 12,
    fontWeight: FontWeight.w700,
  );
  static final calSumLabel = GoogleFonts.dmSans(
    fontSize: 11,
    fontWeight: FontWeight.w500,
  );
  static final calSumVal = GoogleFonts.jetBrainsMono(
    fontSize: 18,
    fontWeight: FontWeight.w700,
  );
  // Rankings
  static final rankName = GoogleFonts.dmSans(
    fontSize: 14,
    fontWeight: FontWeight.w600,
    height: 1.2,
  );
  static final rankCode = GoogleFonts.jetBrainsMono(
    fontSize: 10,
    fontWeight: FontWeight.w500,
    letterSpacing: 0.02,
  );
  static final rankVal = GoogleFonts.jetBrainsMono(
    fontSize: 15,
    fontWeight: FontWeight.w700,
  );
  static final rankPct = GoogleFonts.dmSans(
    fontSize: 11,
    fontWeight: FontWeight.w600,
  );
  static final tabText = GoogleFonts.dmSans(
    fontSize: 13,
    fontWeight: FontWeight.w600,
  );
}

/// 分析页面 - 盈亏分析
class AnalysisPage extends StatefulWidget {
  const AnalysisPage({
    super.key,
    this.isActive = true,
    this.autoRefreshInterval = const Duration(minutes: 2),
    this.screenLoader,
    this.overviewLoader,
    this.calendarLoader,
    this.rankLoader,
  });

  final bool isActive;
  final Duration autoRefreshInterval;
  final Future<Map<String, dynamic>> Function({
    required String timeType,
    int? year,
    int? month,
  })?
  screenLoader;
  final Future<Map<String, dynamic>> Function(String period)? overviewLoader;
  final Future<Map<String, dynamic>> Function({
    required String timeType,
    int? year,
    int? month,
  })?
  calendarLoader;
  final Future<Map<String, dynamic>> Function({String rankType, String market})?
  rankLoader;

  @override
  State<AnalysisPage> createState() => _AnalysisPageState();
}

class _AnalysisPageState extends State<AnalysisPage>
    with WidgetsBindingObserver {
  final ApiService _api = ApiService();
  final CacheService _cache = CacheService();
  final LayerLink _datePickerLink = LayerLink();
  OverlayEntry? _datePickerOverlay;
  static const int _maxTransientRetry = 3;
  static const int _cacheTtlMs = 10 * 60 * 1000; // 10 minutes
  static const String _legacyOverviewStorageKey = 'cache_analysis_overview';
  String _currentPeriod = 'day';
  Map<String, dynamic> _overview = {};
  bool _loading = true;
  bool _isRefreshing = false;
  bool _overviewLoaded = false;
  int _overviewRetryCount = 0;
  Timer? _overviewRetryTimer;
  int? _activeLedgerId;
  int _screenRequestId = 0;
  Map<String, dynamic> _screenMeta = {};
  Map<String, dynamic> _screenRealtimeToday = {};

  // 收益日历相关
  String _calendarTimeType = 'day';
  Map<String, dynamic> _calendarData = {};
  Timer? _calendarRetryTimer;
  final Map<String, Map<String, dynamic>> _calendarCache = {};
  final Map<String, Map<String, dynamic>> _calendarDetailCache = {};
  int? _selectedDayYear;
  int? _selectedDayMonth;
  int? _selectedMonthYear;
  List<int> _selectableDayYears = const [];
  Map<int, List<int>> _selectableMonthsByYear = const {};
  List<int> _selectableMonthYears = const [];
  Map<String, dynamic>? _selectedCalendarDetail;
  Map<String, dynamic> _calendarDetailData = {};
  bool _calendarDetailLoading = false;
  String? _calendarDetailError;
  int _calendarDetailRequestId = 0;

  // 盈亏排行相关
  String _rankType = 'profit'; // 'profit' 或 'loss'
  Map<String, dynamic> _rankData = {};
  bool _rankLoading = false;
  Timer? _rankRetryTimer;
  Timer? _autoRefreshTimer;
  AppLifecycleState _lifecycleState = AppLifecycleState.resumed;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    final now = DateTime.now();
    _selectedDayYear = now.year;
    _selectedDayMonth = now.month;
    _selectedMonthYear = now.year;
    _loadScreen();
    _syncAutoRefreshTimer();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final ledgerId = context.read<AppState>().currentLedgerId;
    if (_activeLedgerId == ledgerId) {
      return;
    }
    final initialMount = _activeLedgerId == null && !_overviewLoaded;
    _activeLedgerId = ledgerId;
    if (initialMount) {
      return;
    }
    _handleLedgerChanged();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _overviewRetryTimer?.cancel();
    _calendarRetryTimer?.cancel();
    _rankRetryTimer?.cancel();
    _autoRefreshTimer?.cancel();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant AnalysisPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    final becameActive = !oldWidget.isActive && widget.isActive;
    if (oldWidget.isActive != widget.isActive ||
        oldWidget.autoRefreshInterval != widget.autoRefreshInterval) {
      _syncAutoRefreshTimer();
    }
    if (becameActive) {
      _triggerSilentRefresh();
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    _lifecycleState = state;
    _syncAutoRefreshTimer();
  }

  bool get _canAutoRefresh =>
      widget.isActive && _lifecycleState == AppLifecycleState.resumed;

  void _syncAutoRefreshTimer() {
    _autoRefreshTimer?.cancel();
    _autoRefreshTimer = null;
    if (!_canAutoRefresh) {
      return;
    }
    _autoRefreshTimer = Timer.periodic(widget.autoRefreshInterval, (_) {
      _triggerSilentRefresh();
    });
  }

  void _triggerSilentRefresh() {
    if (!mounted || !_canAutoRefresh) return;
    _calendarCache.clear();
    _calendarDetailCache.clear();
    unawaited(_loadScreen(force: true, showLoadingUi: false));
  }

  void _handleLedgerChanged() {
    _overviewRetryTimer?.cancel();
    _calendarRetryTimer?.cancel();
    _rankRetryTimer?.cancel();
    if (!mounted) return;
    setState(() {
      _overview = {};
      _overviewLoaded = false;
      _loading = true;
      _overviewRetryCount = 0;
      _calendarData = {};
      _clearCalendarDetail();
      _rankData = {};
      _rankLoading = true;
      _screenMeta = {};
      _screenRealtimeToday = {};
    });
    unawaited(_loadScreen(force: true));
  }

  Future<void> _loadData({
    bool force = false,
    bool showLoadingUi = true,
  }) => _loadScreen(force: force, showLoadingUi: showLoadingUi);

  Future<Map<String, dynamic>?> _loadOverviewFromStorage() async {
    try {
      final payload =
          await _cache.getJson(_overviewStorageKey()) ??
          await _cache.getJson(_legacyOverviewStorageKey);
      if (payload == null) return null;
      final savedAt = payload['saved_at'];
      if (savedAt is int) {
        final age = DateTime.now().millisecondsSinceEpoch - savedAt;
        if (age > _cacheTtlMs) return null;
      }
      final data = payload['data'];
      if (data is Map<String, dynamic>) return data;
      if (data is Map) return Map<String, dynamic>.from(data);
    } catch (e) {
      debugPrint('读取概览持久缓存失败: $e');
    }
    return null;
  }

  Future<void> _saveOverviewToStorage(Map<String, dynamic> data) async {
    try {
      await _cache.setJson(_overviewStorageKey(), {
        'saved_at': DateTime.now().millisecondsSinceEpoch,
        'data': data,
      });
    } catch (e) {
      debugPrint('写入概览持久缓存失败: $e');
    }
  }

  Future<void> _loadCalendar({
    bool force = false,
    bool showLoadingUi = true,
  }) => _loadScreen(force: force, showLoadingUi: showLoadingUi);

  Future<void> _loadScreen({
    bool force = false,
    bool showLoadingUi = true,
  }) async {
    final requestCacheKey = 'screen:${_calendarCacheKey()}';
    final requestStorageKey = _calendarStorageKey(requestCacheKey);
    var renderedByCache = false;

    if (!force) {
      var cached = _calendarCache[requestCacheKey];
      var cacheExpired = false;
      if (cached != null) {
        final cachedAt = cached['_cached_at'];
        if (cachedAt is int) {
          final age = DateTime.now().millisecondsSinceEpoch - cachedAt;
          if (age > _cacheTtlMs) cacheExpired = true;
        }
      }
      if (cached == null) {
        cached = await _loadCalendarFromStorage(requestStorageKey);
        if (cached != null) {
          _calendarCache[requestCacheKey] = {
            ...cached,
            '_cached_at': DateTime.now().millisecondsSinceEpoch,
          };
        }
      }
      if (cached != null && mounted) {
        final cachedData = Map<String, dynamic>.from(cached);
        setState(() {
          _applyScreenPayload(cachedData);
        });
        renderedByCache = true;
      } else if (!_overviewLoaded) {
        final cachedOverview = await _loadOverviewFromStorage();
        if (cachedOverview != null && mounted) {
          setState(() {
            _overview = cachedOverview;
            _loading = false;
          });
          renderedByCache = true;
        }
      }
      if (cacheExpired) {
        force = true;
      }
    }

    if (!renderedByCache && showLoadingUi && mounted) {
      setState(() {
        _loading = true;
        _rankLoading = true;
      });
    }

    final requestId = ++_screenRequestId;
    try {
      if (!mounted) return;
      final ledgerId = context.read<AppState>().currentLedgerId;
      final payload = await _fetchScreenPayload(ledgerId: ledgerId);
      if (!mounted || requestId != _screenRequestId) return;
      setState(() {
        _applyScreenPayload(payload);
      });
      _calendarCache[requestCacheKey] = {
        ...payload,
        '_cached_at': DateTime.now().millisecondsSinceEpoch,
      };
      unawaited(_saveCalendarToStorage(requestStorageKey, payload));
      unawaited(_saveOverviewToStorage(_overview));
      _overviewRetryTimer?.cancel();
      _calendarRetryTimer?.cancel();
      _rankRetryTimer?.cancel();
      _overviewRetryCount = 0;
    } catch (e) {
      debugPrint('加载分析屏幕数据失败: $e');
      if (!mounted || requestId != _screenRequestId) return;
      if (!renderedByCache && showLoadingUi) {
        setState(() {
          _loading = false;
          _rankLoading = false;
        });
      }
      if (_overviewRetryCount < _maxTransientRetry) {
        _overviewRetryCount += 1;
        final retryCount = _overviewRetryCount;
        final delayMs = 700 * retryCount;
        _overviewRetryTimer?.cancel();
        _overviewRetryTimer = Timer(Duration(milliseconds: delayMs), () {
          if (!mounted) return;
          unawaited(_loadScreen(force: true));
        });
      }
    }
  }

  Future<Map<String, dynamic>> _fetchScreenPayload({int? ledgerId}) async {
    if (widget.screenLoader != null) {
      return widget.screenLoader!(
        timeType: _calendarTimeType,
        year: _currentCalendarRequestYear,
        month: _currentCalendarRequestMonth,
      );
    }
    if (widget.overviewLoader != null ||
        widget.calendarLoader != null ||
        widget.rankLoader != null) {
      final appState = context.read<AppState>();
      final overview = widget.overviewLoader != null
          ? await widget.overviewLoader!('all')
          : <String, dynamic>{
              'day': {'pnl': 0.0, 'pnl_rate': 0.0},
              'month': {'pnl': 0.0, 'pnl_rate': 0.0},
              'year': {'pnl': 0.0, 'pnl_rate': 0.0},
              'all': {'pnl': 0.0, 'pnl_rate': 0.0},
            };
      final calendar = widget.calendarLoader != null
          ? await widget.calendarLoader!(
              timeType: _calendarTimeType,
              year: _currentCalendarRequestYear,
              month: _currentCalendarRequestMonth,
            )
          : <String, dynamic>{
              'items': <Map<String, dynamic>>[],
              'total_pnl': 0.0,
              'total_rate': 0.0,
              'title': '',
              'period': <String, dynamic>{},
              'selectable': {
                'day': {'years': <int>[], 'months_by_year': <String, dynamic>{}},
                'month': {'years': <int>[]},
              },
            };
      final rank = widget.rankLoader != null
          ? await widget.rankLoader!(rankType: 'all', market: 'all')
          : <String, dynamic>{
              'gain': <Map<String, dynamic>>[],
              'loss': <Map<String, dynamic>>[],
            };
      final realtimeToday = _asMap(appState.realtimeToday);
      return _buildScreenPayloadFromLegacyLoaders(
        overview: overview,
        calendar: calendar,
        rank: rank,
        realtimeToday: realtimeToday,
        ledgerId: ledgerId,
      );
    }
    return _api.getAnalysisScreen(
      timeType: _calendarTimeType,
      year: _currentCalendarRequestYear,
      month: _currentCalendarRequestMonth,
      ledgerId: ledgerId,
    );
  }

  Map<String, dynamic> _buildScreenPayloadFromLegacyLoaders({
    required Map<String, dynamic> overview,
    required Map<String, dynamic> calendar,
    required Map<String, dynamic> rank,
    required Map<String, dynamic> realtimeToday,
    required int? ledgerId,
  }) {
    final normalizedOverview = Map<String, dynamic>.from(overview);
    final realtimeTotals = _asMap(realtimeToday['totals']);
    if (realtimeTotals.isNotEmpty) {
      normalizedOverview['day'] = {
        'pnl': (realtimeTotals['day_pnl'] as num?)?.toDouble() ?? 0.0,
        'pnl_rate': (realtimeTotals['day_pnl_rate'] as num?)?.toDouble() ?? 0.0,
        'base_value': (realtimeTotals['day_pnl_base'] as num?)?.toDouble() ?? 0.0,
        'source': 'realtime',
      };
    }
    final normalizedCalendar = _applyLegacyRealtimeToCalendar(calendar, realtimeToday);
    return {
      'meta': {
        'analysis_version': DateTime.now().toUtc().toIso8601String(),
        'generated_at': DateTime.now().toUtc().toIso8601String(),
        'ledger_id': ledgerId,
        'today_effective_date': realtimeToday['effective_date'],
        'today_status': _resolveLegacyTodayStatus(realtimeToday),
      },
      'overview': normalizedOverview,
      'calendar': normalizedCalendar,
      'rank': rank,
      'realtime_today': realtimeToday,
    };
  }

  Map<String, dynamic> _applyLegacyRealtimeToCalendar(
    Map<String, dynamic> calendar,
    Map<String, dynamic> realtimeToday,
  ) {
    final normalized = Map<String, dynamic>.from(calendar);
    final realtimeTotals = _asMap(realtimeToday['totals']);
    final effectiveDateRaw = realtimeToday['effective_date']?.toString() ?? '';
    final period = _asMap(normalized['period']);
    final items = (normalized['items'] as List<dynamic>? ?? [])
        .map((item) => item is Map<String, dynamic>
            ? Map<String, dynamic>.from(item)
            : Map<String, dynamic>.from(item as Map))
        .toList();
    normalized['summary'] = {
      'label': _calendarTimeType == 'day'
          ? '本月盈亏'
          : (_calendarTimeType == 'month' ? '本年盈亏' : '累计盈亏'),
      'total_pnl': normalized['total_pnl'],
      'total_rate': normalized['total_rate'],
    };
    if (_calendarTimeType != 'day' ||
        realtimeTotals.isEmpty ||
        effectiveDateRaw.isEmpty ||
        normalized['code'] == 'INVALID_CALENDAR_PERIOD') {
      normalized['items'] = items;
      return normalized;
    }
    final effectiveDate = DateTime.tryParse(effectiveDateRaw);
    if (effectiveDate == null) {
      normalized['items'] = items;
      return normalized;
    }
    final periodYear = (period['year'] as num?)?.toInt() ?? 0;
    final periodMonth = (period['month'] as num?)?.toInt() ?? 0;
    if (effectiveDate.year != periodYear || effectiveDate.month != periodMonth) {
      normalized['items'] = items;
      return normalized;
    }
    final targetLabel = '$periodMonth-${effectiveDate.day}';
    final realtimePnl = (realtimeTotals['day_pnl'] as num?)?.toDouble() ?? 0.0;
    var originalPnl = 0.0;
    var replaced = false;
    for (final item in items) {
      if ((item['label'] ?? '').toString() != targetLabel) continue;
      originalPnl = (item['pnl'] as num?)?.toDouble() ?? 0.0;
      item['pnl'] = realtimePnl;
      replaced = true;
      break;
    }
    if (!replaced) {
      items.add({'label': targetLabel, 'pnl': realtimePnl});
    }
    final totalPnl = (normalized['total_pnl'] as num?)?.toDouble() ?? 0.0;
    final originalRate = (normalized['total_rate'] as num?)?.toDouble();
    final inferredBaseValue =
        originalRate != null && originalRate != 0
        ? totalPnl / (originalRate / 100)
        : 0.0;
    final baseValue =
        (normalized['base_value'] as num?)?.toDouble() ?? inferredBaseValue;
    final adjustedTotal = totalPnl - originalPnl + realtimePnl;
    final adjustedRate = baseValue > 0 ? adjustedTotal / baseValue * 100 : 0.0;
    normalized['items'] = items;
    normalized['total_pnl'] = adjustedTotal;
    normalized['total_rate'] = adjustedRate;
    normalized['summary'] = {
      'label': '本月盈亏',
      'total_pnl': adjustedTotal,
      'total_rate': adjustedRate,
    };
    return normalized;
  }

  String _resolveLegacyTodayStatus(Map<String, dynamic> realtimeToday) {
    final raw = realtimeToday['effective_date']?.toString() ?? '';
    final effectiveDate = DateTime.tryParse(raw);
    if (effectiveDate == null) return 'unavailable';
    final now = DateTime.now();
    if (effectiveDate.year == now.year &&
        effectiveDate.month == now.month &&
        effectiveDate.day == now.day) {
      return 'ready';
    }
    return 'pending';
  }

  void _applyScreenPayload(Map<String, dynamic> payload) {
    final overview = _asMap(payload['overview']);
    final calendar = _asMap(payload['calendar']);
    final rank = _asMap(payload['rank']);
    _syncCalendarMetaFromData(calendar);
    _normalizeCalendarSelections();
    _overview = overview;
    _calendarData = calendar;
    _rankData = rank;
    _screenMeta = _asMap(payload['meta']);
    _screenRealtimeToday = _asMap(payload['realtime_today']);
    _loading = false;
    _overviewLoaded = true;
    _rankLoading = false;
  }

  String _calendarStorageKey(String cacheKey) {
    final appState = context.read<AppState>();
    final rawUserId = appState.userId?.trim();
    final userId = (rawUserId == null || rawUserId.isEmpty)
        ? 'guest'
        : rawUserId;
    final ledgerId = appState.currentLedgerId;
    final ledgerSuffix = ledgerId != null ? ':l$ledgerId' : '';
    return 'analysis_calendar_v1:$userId$ledgerSuffix:$cacheKey';
  }

  String _overviewStorageKey() {
    final appState = context.read<AppState>();
    final rawUserId = appState.userId?.trim();
    final userId = (rawUserId == null || rawUserId.isEmpty)
        ? 'guest'
        : rawUserId;
    final ledgerId = appState.currentLedgerId;
    final ledgerSuffix = ledgerId != null ? ':l$ledgerId' : '';
    return 'analysis_overview_v1:$userId$ledgerSuffix';
  }

  Future<Map<String, dynamic>?> _loadCalendarFromStorage(String key) async {
    try {
      final payload = await _cache.getJson(key);
      if (payload == null) return null;
      final savedAt = payload['saved_at'];
      if (savedAt is int) {
        final age = DateTime.now().millisecondsSinceEpoch - savedAt;
        if (age > _cacheTtlMs) return null;
      }
      final data = payload['data'];
      if (data is Map<String, dynamic>) return data;
      if (data is Map) return Map<String, dynamic>.from(data);
    } catch (e) {
      debugPrint('读取日历持久缓存失败: $e');
    }
    return null;
  }

  Future<void> _saveCalendarToStorage(
    String key,
    Map<String, dynamic> data,
  ) async {
    try {
      await _cache.setJson(key, {
        'saved_at': DateTime.now().millisecondsSinceEpoch,
        'data': data,
      });
    } catch (e) {
      debugPrint('写入日历持久缓存失败: $e');
    }
  }

  String _calendarCacheKey() {
    if (_calendarTimeType == 'day') {
      if (_selectedDayYear == null || _selectedDayMonth == null) {
        return 'day:current';
      }
      return 'day:$_selectedDayYear-${_selectedDayMonth!.toString().padLeft(2, '0')}';
    }
    if (_calendarTimeType == 'month') {
      if (_selectedMonthYear == null) return 'month:current';
      return 'month:$_selectedMonthYear';
    }
    return 'year';
  }

  int? get _currentCalendarRequestYear {
    if (_calendarTimeType == 'day') return _selectedDayYear;
    if (_calendarTimeType == 'month') return _selectedMonthYear;
    return null;
  }

  int? get _currentCalendarRequestMonth {
    if (_calendarTimeType == 'day') return _selectedDayMonth;
    return null;
  }

  void _syncCalendarMetaFromData(Map<String, dynamic> data) {
    final selectable = _asMap(data['selectable']);
    final daySelectable = _asMap(selectable['day']);
    final monthSelectable = _asMap(selectable['month']);
    final dayYears = _toIntList(daySelectable['years']);
    final monthYears = _toIntList(monthSelectable['years']);
    final monthsByYearRaw = _asMap(daySelectable['months_by_year']);
    final monthsByYear = <int, List<int>>{};
    monthsByYearRaw.forEach((k, v) {
      final y = int.tryParse(k);
      if (y == null) return;
      monthsByYear[y] = _toIntList(v);
    });

    _selectableDayYears = dayYears;
    _selectableMonthsByYear = monthsByYear;
    _selectableMonthYears = monthYears;

    final period = _asMap(data['period']);
    final pYear = _asInt(period['year']);
    final pMonth = _asInt(period['month']);
    if (_calendarTimeType == 'day') {
      if (pYear != null) _selectedDayYear = pYear;
      if (pMonth != null) _selectedDayMonth = pMonth;
    } else if (_calendarTimeType == 'month') {
      if (pYear != null) _selectedMonthYear = pYear;
    }
  }

  void _normalizeCalendarSelections() {
    if (_selectableDayYears.isNotEmpty) {
      var dayYear = _selectedDayYear;
      if (dayYear == null || !_selectableDayYears.contains(dayYear)) {
        dayYear = _selectableDayYears.last;
      }
      final months = _selectableMonthsByYear[dayYear] ?? const <int>[];
      var dayMonth = _selectedDayMonth;
      if (dayMonth == null || !months.contains(dayMonth)) {
        dayMonth = months.isEmpty ? 1 : months.last;
      }
      _selectedDayYear = dayYear;
      _selectedDayMonth = dayMonth;
    }

    if (_selectableMonthYears.isNotEmpty) {
      var monthYear = _selectedMonthYear;
      if (monthYear == null || !_selectableMonthYears.contains(monthYear)) {
        monthYear = _selectableMonthYears.last;
      }
      _selectedMonthYear = monthYear;
    }
  }

  Map<String, dynamic> _asMap(dynamic value) {
    if (value is Map<String, dynamic>) return value;
    if (value is Map) return Map<String, dynamic>.from(value);
    return const {};
  }

  int? _asInt(dynamic value) {
    if (value is int) return value;
    if (value is num) return value.toInt();
    if (value is String) return int.tryParse(value);
    return null;
  }

  List<int> _toIntList(dynamic value) {
    if (value is! List) return const [];
    final result = <int>[];
    for (final item in value) {
      final parsed = _asInt(item);
      if (parsed != null) result.add(parsed);
    }
    result.sort();
    return result;
  }

  Map<String, dynamic> _realtimeTodayTotals() {
    return _asMap(_screenRealtimeToday['totals']);
  }

  DateTime? _realtimeTodayEffectiveDate() {
    final raw = _screenRealtimeToday['effective_date']?.toString() ?? '';
    if (raw.isEmpty) return null;
    try {
      return DateTime.parse(raw);
    } catch (_) {
      return null;
    }
  }

  double? _currentMonthTodayCellPnlOverride() {
    if (_calendarTimeType != 'day') return null;
    final now = DateTime.now();
    final dayYear = _selectedDayYear ?? now.year;
    final dayMonth = _selectedDayMonth ?? now.month;
    if (dayYear != now.year || dayMonth != now.month) {
      return null;
    }

    if (_screenRealtimeToday.isEmpty) {
      return null;
    }
    if ((_screenMeta['today_status']?.toString() ?? '') == 'unavailable') {
      return null;
    }

    final totals = _realtimeTodayTotals();
    final realtimeDayPnl = (totals['day_pnl'] as num?)?.toDouble() ?? 0.0;
    final effectiveDate = _realtimeTodayEffectiveDate();
    if (effectiveDate == null) {
      return null;
    }

    final isTodayEffective =
        effectiveDate.year == now.year &&
        effectiveDate.month == now.month &&
        effectiveDate.day == now.day;
    return isTodayEffective ? realtimeDayPnl : 0.0;
  }

  void _onCalendarTypeChanged(String nextType) {
    if (_calendarTimeType == nextType) return;
    setState(() {
      _calendarTimeType = nextType;
      _clearCalendarDetail();
    });
    _loadCalendar();
  }

  String _calendarPeriodButtonText() {
    if (_calendarTimeType == 'day') {
      if (_selectedDayYear == null || _selectedDayMonth == null) {
        return '暂无可选周期';
      }
      return '$_selectedDayYear年${_selectedDayMonth!.toString().padLeft(2, '0')}月';
    }
    if (_calendarTimeType == 'month') {
      if (_selectedMonthYear == null) return '暂无可选周期';
      return '$_selectedMonthYear年';
    }
    return '';
  }

  bool get _calendarPeriodPickerEnabled {
    if (_calendarTimeType == 'day') return _selectableDayYears.isNotEmpty;
    if (_calendarTimeType == 'month') return _selectableMonthYears.isNotEmpty;
    return false;
  }

  void _changePeriod(String period) {
    setState(() => _currentPeriod = period);
    if (period != 'day') {
      _loadData(force: true);
    }
  }

  void _clearCalendarDetail() {
    _selectedCalendarDetail = null;
    _calendarDetailData = {};
    _calendarDetailLoading = false;
    _calendarDetailError = null;
    _calendarDetailRequestId += 1;
  }

  String _calendarDetailCacheKey({
    required String scope,
    required String date,
    int? ledgerId,
  }) {
    final ledgerKey = ledgerId == null ? 'all' : ledgerId.toString();
    return '$ledgerKey:$scope:$date';
  }

  Map<String, dynamic>? _getCachedCalendarDetail(String cacheKey) {
    final cached = _calendarDetailCache[cacheKey];
    if (cached == null) return null;
    final savedAt = cached['_cached_at'];
    if (savedAt is int) {
      final age = DateTime.now().millisecondsSinceEpoch - savedAt;
      if (age > _cacheTtlMs) return null;
    }
    return cached;
  }

  void _storeCalendarDetailCache(String cacheKey, Map<String, dynamic> payload) {
    _calendarDetailCache[cacheKey] = {
      ...payload,
      '_cached_at': DateTime.now().millisecondsSinceEpoch,
    };
  }

  List<int> _calendarPrefetchNeighborKeys(int currentKey) {
    final items = _calendarData['items'] as List<dynamic>? ?? [];
    final validKeys = <int>[];
    for (final item in items) {
      final label = item['label'] ?? '';
      final pnl = (item['pnl'] as num?)?.toDouble();
      final key = _parseLabelKey(label.toString());
      if (key != null && pnl != null) {
        validKeys.add(key);
      }
    }
    final effectiveDate = _realtimeTodayEffectiveDate();
    final realtimeDayPnl =
        (_realtimeTodayTotals()['day_pnl'] as num?)?.toDouble();
    if (_calendarTimeType == 'day' &&
        effectiveDate != null &&
        realtimeDayPnl != null &&
        effectiveDate.year == _selectedDayYear &&
        effectiveDate.month == _selectedDayMonth &&
        !validKeys.contains(effectiveDate.day)) {
      validKeys.add(effectiveDate.day);
      validKeys.sort();
    }
    final currentIndex = validKeys.indexOf(currentKey);
    if (currentIndex < 0) return const [];
    final result = <int>[];
    if (currentIndex > 0) result.add(validKeys[currentIndex - 1]);
    if (currentIndex + 1 < validKeys.length) result.add(validKeys[currentIndex + 1]);
    return result;
  }

  String? _calendarDetailDateForKey(int key) {
    if (_calendarTimeType == 'day') {
      if (_selectedDayYear == null || _selectedDayMonth == null) return null;
      final month = _selectedDayMonth!.toString().padLeft(2, '0');
      final day = key.toString().padLeft(2, '0');
      return '${_selectedDayYear!}-$month-$day';
    }
    if (_calendarTimeType == 'month') {
      if (_selectedMonthYear == null) return null;
      final month = key.toString().padLeft(2, '0');
      return '${_selectedMonthYear!}-$month-01';
    }
    return '$key-01-01';
  }

  bool _isCalendarCellSelected(int key) {
    return (_selectedCalendarDetail?['scope'] == _calendarTimeType) &&
        (_selectedCalendarDetail?['key'] == key);
  }

  Future<void> _loadCalendarDetail(int key, {bool background = false}) async {
    final date = _calendarDetailDateForKey(key);
    if (date == null) return;
    if (!background &&
        _selectedCalendarDetail?['scope'] == _calendarTimeType &&
        _selectedCalendarDetail?['key'] == key &&
        _selectedCalendarDetail?['date'] == date) {
      setState(_clearCalendarDetail);
      return;
    }
    final ledgerId = context.read<AppState>().currentLedgerId;
    final selection = {
      'scope': _calendarTimeType,
      'key': key,
      'date': date,
    };
    final cacheKey = _calendarDetailCacheKey(
      scope: _calendarTimeType,
      date: date,
      ledgerId: ledgerId,
    );
    final cached = _getCachedCalendarDetail(cacheKey);
    final requestId = background ? _calendarDetailRequestId : ++_calendarDetailRequestId;

    if (cached != null) {
      if (!background && mounted) {
        setState(() {
          _selectedCalendarDetail = selection;
          _calendarDetailData = Map<String, dynamic>.from(cached);
          _calendarDetailLoading = false;
          _calendarDetailError = null;
        });
      }
      return;
    }

    if (!background) {
      setState(() {
        _selectedCalendarDetail = selection;
        _calendarDetailLoading = true;
        _calendarDetailError = null;
      });
    }

    try {
      final data = await _api.getAnalysisCalendarAssetBreakdown(
        scope: _calendarTimeType,
        date: date,
        ledgerId: ledgerId,
      );
      _storeCalendarDetailCache(cacheKey, data);
      if (!background) {
        if (!mounted || requestId != _calendarDetailRequestId) return;
        setState(() {
          _calendarDetailData = data;
          _calendarDetailLoading = false;
        });
        for (final neighborKey in _calendarPrefetchNeighborKeys(key)) {
          unawaited(_loadCalendarDetail(neighborKey, background: true));
        }
      }
    } catch (e) {
      if (!background) {
        if (!mounted || requestId != _calendarDetailRequestId) return;
        setState(() {
          _calendarDetailLoading = false;
          _calendarDetailError = '明细加载失败';
        });
      }
    }
  }

  Future<void> _onPullToRefresh() async {
    if (_isRefreshing) return;
    setState(() => _isRefreshing = true);
    _overviewRetryTimer?.cancel();
    _calendarRetryTimer?.cancel();
    _overviewRetryCount = 0;
    final appState = context.read<AppState>();
    if (!appState.portfolioLoaded) {
      unawaited(appState.refreshHomeData());
    }
    try {
      _calendarCache.clear();
      _calendarDetailCache.clear();
      await _loadScreen(force: true, showLoadingUi: false);
    } finally {
      if (mounted) {
        setState(() => _isRefreshing = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();
    return Scaffold(
      backgroundColor: AppTheme.bgPrimary,
      body: RefreshIndicator(
        onRefresh: _onPullToRefresh,
        color: AppTheme.accent,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 12),
              _buildOverviewCard(appState),
              _buildSectionDivider(vertical: 6),
              _buildCalendarSection(appState),
              _buildSectionDivider(vertical: 8),
              _buildCalendarSummary(appState),
              _buildSectionDivider(),
              _buildRankSection(appState),
              const SizedBox(height: 100),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildOverviewCard(AppState appState) {
    final periodData = _asMap(_overview[_currentPeriod]);
    final apiPnl = (periodData['pnl'] as num?)?.toDouble();
    final apiRate = (periodData['pnl_rate'] as num?)?.toDouble();
    final effectivePnl = apiPnl;
    final effectiveRate = apiRate;
    final hasPnl = effectivePnl != null;
    final hasRate = effectiveRate != null;
    final pnl = effectivePnl ?? 0;
    final pnlColor = hasPnl
        ? (pnl >= 0 ? AppTheme.danger : AppTheme.success)
        : AppTheme.textMuted;
    final showLoading = _loading && !_overviewLoaded;
    final pnlValue = effectivePnl ?? 0;
    final amountText = appState.amountHidden
        ? '****'
        : (hasPnl ? '¥${pnlValue.toStringAsFixed(0)}' : '--');
    final rateValue = effectiveRate ?? 0;
    final rateText = appState.amountHidden
        ? '--'
        : (hasRate
              ? '${rateValue >= 0 ? '+' : ''}${rateValue.toStringAsFixed(2)}%'
              : '--');
    final rateIcon = hasRate
        ? (rateValue >= 0
              ? Icons.trending_up_rounded
              : Icons.trending_down_rounded)
        : Icons.remove_rounded;
    String title;
    switch (_currentPeriod) {
      case 'day':
        title = '当日盈亏';
        break;
      case 'month':
        title = '本月盈亏';
        break;
      case 'year':
        title = '本年盈亏';
        break;
      default:
        title = '累计盈亏';
    }

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            title,
            style: _S.label.copyWith(
              color: const Color(0xFF9AA3B7),
              fontSize: 12,
              letterSpacing: 0.05,
            ),
          ),
          const SizedBox(height: 10),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.center,
            child: Text(
              showLoading ? '加载中...' : amountText,
              style: _S.value.copyWith(
                color: showLoading ? const Color(0xFFF0F4FF) : pnlColor,
                fontSize: 34,
              ),
            ),
          ),
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                rateIcon,
                size: 16,
                color: hasRate ? pnlColor : AppTheme.textMuted,
              ),
              const SizedBox(width: 4),
              Text(
                '收益率',
                style: _S.label.copyWith(
                  color: hasRate ? pnlColor : AppTheme.textMuted,
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(width: 4),
              Text(
                showLoading ? '--' : rateText,
                style: _S.pnlRate.copyWith(
                  color: hasRate ? pnlColor : AppTheme.textMuted,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          _buildPeriodSegmentedControl(),
        ],
      ),
    );
  }

  Widget _buildPeriodSegmentedControl() {
    return Container(
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: Colors.white.withValues(alpha: 0.06),
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          _buildPeriodButton('当日', _currentPeriod == 'day', 'day'),
          _buildPeriodButton('本月', _currentPeriod == 'month', 'month'),
          _buildPeriodButton('本年', _currentPeriod == 'year', 'year'),
          _buildPeriodButton('全部', _currentPeriod == 'all', 'all'),
        ],
      ),
    );
  }

  Widget _buildPeriodButton(String label, bool isSelected, String period) {
    return Expanded(
      child: GestureDetector(
        onTap: () => _changePeriod(period),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          alignment: Alignment.center,
          padding: const EdgeInsets.only(bottom: 10, top: 2),
          decoration: BoxDecoration(
            border: Border(
              bottom: BorderSide(
                color: isSelected ? AppTheme.accent : Colors.transparent,
                width: 2,
              ),
            ),
          ),
          child: Text(
            label,
            style: _S.label.copyWith(
              fontSize: 13,
              fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
              color: isSelected ? AppTheme.textPrimary : AppTheme.textMuted,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildCalendarSection(AppState appState) {
    final now = DateTime.now();
    List<Map<String, dynamic>> calendarGrid = [];
    final dayYear = _selectedDayYear ?? now.year;
    final dayMonth = _selectedDayMonth ?? now.month;

    if (_calendarTimeType == 'day') {
      final lastDayOfMonth = DateTime(dayYear, dayMonth + 1, 0);
      final daysInMonth = lastDayOfMonth.day;
      for (int i = 1; i <= daysInMonth; i++) {
        calendarGrid.add({'day': i, 'date': i.toString(), 'pnl': null});
      }
    } else if (_calendarTimeType == 'month') {
      for (int i = 1; i <= 12; i++) {
        calendarGrid.add({'day': i, 'date': '$i月', 'pnl': null});
      }
    } else {
      for (int i = 0; i < 6; i++) {
        final year = now.year - 5 + i;
        calendarGrid.add({'day': year, 'date': '$year年', 'pnl': null});
      }
    }

    final items = _calendarData['items'] as List<dynamic>? ?? [];
    final pnlMap = <int, double>{};
    for (var item in items) {
      final label = item['label'] ?? '';
      final pnl = (item['pnl'] as num?)?.toDouble();
      final key = _parseLabelKey(label.toString());
      if (key != null && pnl != null) {
        pnlMap[key] = pnl;
      }
    }
    for (var gridItem in calendarGrid) {
      final key = gridItem['day'] as int;
      if (pnlMap.containsKey(key)) {
        gridItem['pnl'] = pnlMap[key];
      }
    }
    final todayCellPnlOverride = _currentMonthTodayCellPnlOverride();
    if (_calendarTimeType == 'day' &&
        dayYear == now.year &&
        dayMonth == now.month &&
        todayCellPnlOverride != null) {
      for (final gridItem in calendarGrid) {
        if (gridItem['day'] == now.day) {
          gridItem['pnl'] = todayCellPnlOverride;
          break;
        }
      }
    }

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '收益日历',
                style: _S.label.copyWith(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          _buildCalendarHeaderControls(),
          const SizedBox(height: 12),
          _buildCalendarGrid(calendarGrid, appState),
          if (_selectedCalendarDetail != null) ...[
            const SizedBox(height: 12),
            _buildCalendarDetailCard(appState),
          ],
        ],
      ),
    );
  }

  Widget _buildCalendarHeaderControls() {
    return Row(
      key: const Key('calendar-header-controls-row'),
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        if (_calendarTimeType != 'year')
          _buildCalendarPeriodPicker()
        else
          const SizedBox.shrink(),
        Container(
          height: 28,
          padding: const EdgeInsets.all(2),
          decoration: BoxDecoration(
            color: AppTheme.isLight
                ? const Color(0xFFDDE4F1)
                : Colors.black.withValues(alpha: 0.2),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: AppTheme.isLight
                  ? const Color(0x1A222C40)
                  : Colors.transparent,
              width: 0.6,
            ),
          ),
          child: Row(
            children: [
              _buildHeaderToggle(
                '日',
                _calendarTimeType == 'day',
                () => _onCalendarTypeChanged('day'),
              ),
              _buildHeaderToggle(
                '月',
                _calendarTimeType == 'month',
                () => _onCalendarTypeChanged('month'),
              ),
              _buildHeaderToggle(
                '年',
                _calendarTimeType == 'year',
                () => _onCalendarTypeChanged('year'),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildCalendarPeriodPicker() {
    return CompositedTransformTarget(
      link: _datePickerLink,
      child: GestureDetector(
        key: const Key('calendar-period-button'),
        onTap: _calendarPeriodPickerEnabled ? _toggleDatePicker : null,
        child: Container(
          height: 30,
          padding: const EdgeInsets.symmetric(horizontal: 14),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: AppTheme.isLight
                ? AppTheme.surface3
                : const Color(0xFF16181F),
            borderRadius: BorderRadius.circular(999),
            border: Border.all(color: AppTheme.border),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                _calendarPeriodButtonText(),
                style: _S.label.copyWith(
                  fontSize: 12,
                  color: _calendarPeriodPickerEnabled
                      ? AppTheme.textPrimary
                      : AppTheme.textMuted,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(width: 4),
              Icon(
                Icons.keyboard_arrow_down_rounded,
                size: 14,
                color: _calendarPeriodPickerEnabled
                    ? AppTheme.textSecondary
                    : AppTheme.textMuted,
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _hideDatePicker() {
    _datePickerOverlay?.remove();
    _datePickerOverlay = null;
  }

  void _toggleDatePicker() {
    if (_datePickerOverlay != null) {
      _hideDatePicker();
      return;
    }

    // Use the API-returned selectable data
    final List<int> selectableYears;
    final Map<int, List<int>> selectableMonthsByYear;
    final int initialYear;
    final int? initialMonth;

    if (_calendarTimeType == 'day') {
      selectableYears = _selectableDayYears;
      selectableMonthsByYear = _selectableMonthsByYear;
      initialYear =
          _selectedDayYear ??
          (selectableYears.isNotEmpty
              ? selectableYears.last
              : DateTime.now().year);
      initialMonth =
          _selectedDayMonth ??
          (selectableMonthsByYear[initialYear]?.isNotEmpty == true
              ? selectableMonthsByYear[initialYear]!.last
              : DateTime.now().month);
    } else {
      selectableYears = _selectableMonthYears;
      selectableMonthsByYear = const {};
      initialYear =
          _selectedMonthYear ??
          (selectableYears.isNotEmpty
              ? selectableYears.last
              : DateTime.now().year);
      initialMonth = null; // month mode: no month wheel
    }

    // Track temporary selections within the picker
    int tempYear = initialYear;
    int? tempMonth = initialMonth;

    _datePickerOverlay = OverlayEntry(
      builder: (context) => Stack(
        children: [
          GestureDetector(
            onTap: _hideDatePicker,
            child: Container(color: Colors.transparent),
          ),
          CompositedTransformFollower(
            link: _datePickerLink,
            showWhenUnlinked: false,
            targetAnchor: Alignment.bottomLeft,
            followerAnchor: Alignment.topLeft,
            offset: const Offset(0, 8),
            child: Material(
              color: Colors.transparent,
              child: Container(
                width: 140,
                decoration: BoxDecoration(
                  color: AppTheme.isLight
                      ? AppTheme.bgCard.withValues(alpha: 0.98)
                      : const Color(0xFF1F2128).withValues(alpha: 0.98),
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.3),
                      blurRadius: 12,
                      offset: const Offset(0, 6),
                    ),
                  ],
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const SizedBox(height: 8),
                    SizedBox(
                      height: 160,
                      child: DatePickerDropdown(
                        initialYear: initialYear,
                        initialMonth: initialMonth,
                        selectableYears: selectableYears,
                        selectableMonthsByYear: selectableMonthsByYear,
                        yearWheelKey: kCalendarYearWheelKey,
                        monthWheelKey: kCalendarMonthWheelKey,
                        onSelected: (year, month, isFinal) {
                          tempYear = year;
                          tempMonth = month;
                          if (isFinal) {
                            WidgetsBinding.instance.addPostFrameCallback((_) {
                              if (_calendarTimeType == 'day') {
                                setState(() {
                                  _selectedDayYear = tempYear;
                                  _selectedDayMonth = tempMonth;
                                  _clearCalendarDetail();
                                });
                              } else {
                                setState(() {
                                  _selectedMonthYear = tempYear;
                                  _clearCalendarDetail();
                                });
                              }
                              _hideDatePicker();
                              _loadCalendar();
                            });
                          }
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );

    Overlay.of(context).insert(_datePickerOverlay!);
  }

  Widget _buildCalendarGrid(
    List<Map<String, dynamic>> calendarGrid,
    AppState appState,
  ) {
    int crossAxisCount = 7;
    double aspectRatio = 0.85;

    if (_calendarTimeType == 'month') {
      crossAxisCount = 4;
      aspectRatio = 1.3;
    } else if (_calendarTimeType == 'year') {
      crossAxisCount = 3;
      aspectRatio = 1.6;
    }

    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: crossAxisCount,
        mainAxisSpacing: 8,
        crossAxisSpacing: 8,
        childAspectRatio: aspectRatio,
      ),
      itemCount: calendarGrid.length,
      itemBuilder: (context, index) {
        final item = calendarGrid[index];
        final pnl = item['pnl'] as double?;
        final isSelected = _isCalendarCellSelected(item['day'] as int);

        return _buildCalendarItem(
          item['date'],
          item['day'] as int,
          pnl,
          isSelected,
          appState,
        );
      },
    );
  }

  Widget _buildCalendarItem(
    String label,
    int key,
    double? pnl,
    bool isSelected,
    AppState appState,
  ) {
    final hasData = pnl != null;
    final color = pnl == null
        ? AppTheme.textMuted
        : (pnl >= 0 ? AppTheme.danger : AppTheme.success);

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: hasData ? () => unawaited(_loadCalendarDetail(key)) : null,
        borderRadius: BorderRadius.circular(8),
        child: Ink(
          decoration: BoxDecoration(
            color: isSelected
                ? AppTheme.accent.withValues(alpha: 0.12)
                : Colors.white.withValues(alpha: 0.02),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: isSelected
                  ? AppTheme.accent.withValues(alpha: 0.45)
                  : Colors.white.withValues(alpha: 0.06),
              width: 1,
            ),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              SizedBox(
                height: 14,
                child: FittedBox(
                  fit: BoxFit.scaleDown,
                  child: Text(
                    label,
                    style: _S.calDate.copyWith(
                      fontSize: label.contains('-') ? 11 : 12,
                      color: isSelected
                          ? (AppTheme.isLight ? Colors.black : Colors.white)
                          : AppTheme.textPrimary,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 1),
              SizedBox(
                height: 13,
                child: FittedBox(
                  fit: BoxFit.scaleDown,
                  child: Text(
                    hasData ? _formatCalendarPnl(pnl, appState) : '--',
                    style: _S.calPnl.copyWith(color: color),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCalendarSummary(AppState appState) {
    String pnlLabel;
    if (_calendarTimeType == 'day') {
      pnlLabel = '本月盈亏';
    } else if (_calendarTimeType == 'month') {
      pnlLabel = '本年盈亏';
    } else {
      pnlLabel = '累计盈亏';
    }

    final pnlRaw = _calendarSummaryRawValue();
    final pnlValue = _calendarSummaryText(appState, pnlRaw);
    final pnlRate = _calendarSummaryRate(appState);
    final hasSummary = pnlRaw != null;
    final pnlColor = !hasSummary
        ? AppTheme.textMuted
        : (pnlRaw >= 0 ? AppTheme.danger : AppTheme.success);

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: AppTheme.isLight
                ? const Color(0x14111F3A)
                : Colors.white.withValues(alpha: 0.08),
            width: 1,
          ),
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: AppTheme.isLight
                ? const [Color(0x08111F3A), Color(0x04111F3A)]
                : [Colors.white.withValues(alpha: 0.055), Colors.white.withValues(alpha: 0.02)],
          ),
        ),
        child: Row(
          children: [
            Text(
              pnlLabel,
              style: _S.calSumLabel.copyWith(
                color: AppTheme.textSecondary,
                fontSize: 11,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                pnlValue,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: _S.calSumVal.copyWith(
                  color: pnlColor,
                  fontSize: 14,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
            const SizedBox(width: 10),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: AppTheme.isLight
                    ? const Color(0x0F111F3A)
                    : Colors.white.withValues(alpha: 0.06),
                borderRadius: BorderRadius.circular(999),
                border: Border.all(
                  color: AppTheme.isLight
                      ? const Color(0x14111F3A)
                      : Colors.white.withValues(alpha: 0.08),
                  width: 1,
                ),
              ),
              child: Text(
                pnlRate,
                style: _S.calSumLabel.copyWith(
                  color: pnlColor,
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCalendarDetailCard(AppState appState) {
    final selected = _selectedCalendarDetail;
    if (selected == null) {
      return const SizedBox.shrink();
    }
    final items = (_calendarDetailData['items'] as List<dynamic>? ?? [])
        .map((item) => item is Map<String, dynamic>
            ? item
            : Map<String, dynamic>.from(item as Map))
        .toList();
    final totalPnl = (_calendarDetailData['total_pnl'] as num?)?.toDouble();
    final totalRate = (_calendarDetailData['total_rate'] as num?)?.toDouble();

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.isLight ? AppTheme.surface3 : const Color(0xFF171A22),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '个股盈亏',
                      style: _S.label.copyWith(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                  ],
                ),
              ),
              if (totalPnl != null)
                Builder(
                  builder: (_) {
                    final totalColor = totalPnl >= 0
                        ? AppTheme.danger
                        : AppTheme.success;
                    return Row(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Text(
                          _formatDetailPnl(totalPnl, appState),
                          style: _S.rankVal.copyWith(
                            color: totalColor,
                            fontSize: 14,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 7,
                            vertical: 3,
                          ),
                          decoration: BoxDecoration(
                            color: totalColor.withValues(alpha: 0.10),
                            borderRadius: BorderRadius.circular(999),
                          ),
                          child: Text(
                            _formatDetailRate(totalRate, appState),
                            style: _S.rankPct.copyWith(
                              color: totalColor.withValues(alpha: 0.88),
                              fontSize: 9.5,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                      ],
                    );
                  },
                ),
            ],
          ),
          const SizedBox(height: 10),
          if (_calendarDetailError != null && items.isEmpty)
            Text(
              _calendarDetailError!,
              style: _S.label.copyWith(color: AppTheme.danger),
            )
          else if (items.isEmpty)
            Text(
              _calendarDetailLoading ? '正在加载明细…' : '当天没有可展示的资产明细',
              style: _S.label.copyWith(color: AppTheme.textSecondary),
            )
          else
            Column(
              children: [
                if (_calendarDetailLoading)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Align(
                      alignment: Alignment.centerLeft,
                      child: Text(
                        '正在更新明细…',
                        style: _S.label.copyWith(
                          fontSize: 10.5,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    ),
                  ),
                Container(
                  padding: const EdgeInsets.only(top: 2, bottom: 8),
                  decoration: BoxDecoration(
                    border: Border(
                      bottom: BorderSide(
                        color: AppTheme.border.withValues(alpha: 0.35),
                        width: 0.6,
                      ),
                    ),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: Text(
                          '股票名称',
                          style: _S.label.copyWith(
                            fontSize: 10,
                            color: AppTheme.textSecondary,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      SizedBox(
                        width: 88,
                        child: Text(
                          '盈亏金额',
                          textAlign: TextAlign.right,
                          style: _S.label.copyWith(
                            fontSize: 10,
                            color: AppTheme.textSecondary,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      SizedBox(
                        width: 60,
                        child: Text(
                          '收益率',
                          textAlign: TextAlign.right,
                          style: _S.label.copyWith(
                            fontSize: 10,
                            color: AppTheme.textSecondary,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                ...items.map((item) {
                  final pnl = (item['pnl'] as num?)?.toDouble() ?? 0.0;
                  final pnlRate = (item['pnl_rate'] as num?)?.toDouble();
                  final name = (item['name'] ?? item['code'] ?? '').toString();
                  final pnlColor =
                      pnl >= 0 ? AppTheme.danger : AppTheme.success;
                  return Container(
                    padding: const EdgeInsets.symmetric(vertical: 9),
                    decoration: BoxDecoration(
                      border: Border(
                        bottom: BorderSide(
                          color: AppTheme.border.withValues(alpha: 0.28),
                          width: 0.6,
                        ),
                      ),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Text(
                            name,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: _S.rankName.copyWith(
                              fontSize: 11.5,
                              color: AppTheme.textPrimary,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                        SizedBox(
                          width: 88,
                          child: Text(
                            _formatDetailPnl(pnl, appState),
                            textAlign: TextAlign.right,
                            style: _S.rankVal.copyWith(
                              fontSize: 11.5,
                              color: pnlColor,
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        SizedBox(
                          width: 60,
                          child: Text(
                            _formatDetailRate(pnlRate, appState),
                            textAlign: TextAlign.right,
                            style: _S.rankPct.copyWith(
                              color: pnlColor,
                              fontSize: 10,
                            ),
                          ),
                        ),
                      ],
                    ),
                  );
                }),
              ],
            ),
        ],
      ),
    );
  }

  double? _calendarSummaryRawValue() {
    final apiTotal = _calendarData['total_pnl'];
    if (apiTotal is num) return apiTotal.toDouble();
    return null;
  }

  Widget _buildRankSection(AppState appState) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '盈亏排行',
                style: _S.label.copyWith(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary,
                ),
              ),
              GestureDetector(
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => AnalysisRankAllPage(
                      rankType: _rankType,
                      rankLoader: widget.rankLoader,
                    ),
                  ),
                ),
                child: Row(
                  children: [
                    Text(
                      '查看全部',
                      style: _S.label.copyWith(
                        color: AppTheme.accent,
                        fontSize: 10,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    Icon(Icons.chevron_right, size: 14, color: AppTheme.accent),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              _buildRankTab(
                '盈利榜',
                _rankType == 'profit',
                () => setState(() => _rankType = 'profit'),
              ),
              const SizedBox(width: 6),
              _buildRankTab(
                '亏损榜',
                _rankType == 'loss',
                () => setState(() => _rankType = 'loss'),
              ),
            ],
          ),
          const SizedBox(height: 10),
          _buildRankItems(appState),
        ],
      ),
    );
  }

  Widget _buildRankTab(String text, bool isSelected, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 28,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: isSelected
              ? AppTheme.accent.withValues(alpha: 0.1)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(
            color: isSelected
                ? AppTheme.accent.withValues(alpha: 0.3)
                : Colors.transparent,
          ),
        ),
        child: Text(
          text,
          style: _S.tabText.copyWith(
            fontSize: 11,
            color: isSelected ? AppTheme.accent : AppTheme.textSecondary,
          ),
        ),
      ),
    );
  }

  Widget _buildRankItems(AppState appState) {
    final items = _buildRankItemsData();
    if (_rankLoading && items.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 20),
          child: Text(
            '加载中...',
            style: _S.label.copyWith(color: AppTheme.textMuted),
          ),
        ),
      );
    }
    if (items.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 20),
          child: Text(
            '暂无数据',
            style: _S.label.copyWith(color: AppTheme.textMuted),
          ),
        ),
      );
    }

    final limit = items.length > 5 ? 5 : items.length;
    final topItems = items.sublist(0, limit);

    return Column(
      children: List.generate(topItems.length, (idx) {
        return _buildRankCard(topItems[idx], appState, idx + 1);
      }),
    );
  }

  Widget _buildRankCard(_RankItem item, AppState appState, int rank) {
    final pnlColor = item.pnl >= 0 ? AppTheme.danger : AppTheme.success;
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: Colors.white.withValues(alpha: 0.03),
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          _rankBadge(rank),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.displayName,
                  style: _S.rankName.copyWith(
                    color: AppTheme.textPrimary,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 1),
                Text(
                  _formatDisplayCode(item.code),
                  style: _S.rankCode.copyWith(color: AppTheme.textMuted),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${item.currencySymbol}${item.pnl.toStringAsFixed(0)}',
                style: _S.rankVal.copyWith(color: pnlColor, fontSize: 14),
              ),
              const SizedBox(height: 1),
              Text(
                '${item.pnlRate >= 0 ? '+' : ''}${item.pnlRate.toStringAsFixed(2)}%',
                style: _S.rankPct.copyWith(
                  color: pnlColor.withValues(alpha: 0.8),
                  fontSize: 10,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  List<_RankItem> _buildRankItemsData() {
    final key = _rankType == 'loss' ? 'loss' : 'gain';
    final raw = _rankData[key];
    if (raw is! List) return [];
    return raw.map((item) {
      final map = item is Map
          ? Map<String, dynamic>.from(item)
          : <String, dynamic>{};
      final code = (map['code'] ?? '').toString();
      final name = (map['name'] ?? '').toString();
      final pnl = (map['pnl'] as num?)?.toDouble() ?? 0.0;
      final pnlRate = (map['pnl_rate'] as num?)?.toDouble() ?? 0.0;
      final curr = (map['curr'] ?? 'CNY').toString();
      return _RankItem(
        code: code,
        name: name,
        pnl: pnl,
        pnlRate: pnlRate,
        currencySymbol: _currencySymbol(curr),
      );
    }).toList();
  }

  Widget _buildHeaderToggle(String text, bool isSelected, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: isSelected ? AppTheme.accent : Colors.transparent,
          borderRadius: BorderRadius.circular(6),
          boxShadow: isSelected && AppTheme.isLight
              ? [
                  BoxShadow(
                    color: AppTheme.accent.withValues(alpha: 0.18),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ]
              : null,
        ),
        child: Text(
          text,
          style: TextStyle(
            fontSize: 11,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
            color: isSelected ? Colors.white : AppTheme.textSecondary,
          ),
        ),
      ),
    );
  }

  Widget _buildSectionDivider({double vertical = 16}) {
    return Container(
      margin: EdgeInsets.symmetric(vertical: vertical),
      height: 1,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            Colors.transparent,
            Colors.white.withValues(alpha: 0.06),
            Colors.transparent,
          ],
        ),
      ),
    );
  }

  String _formatDisplayCode(String code) {
    if (code.startsWith('gb_')) return code.substring(3).toUpperCase();
    if (code.startsWith('f_')) return code.substring(2);
    if (code.startsWith('ft_')) return code.substring(3);
    return code.toUpperCase();
  }

  int? _parseLabelKey(String label) {
    if (_calendarTimeType == 'day') {
      if (label.contains('-')) {
        final parts = label.split('-');
        return int.tryParse(parts.last);
      }
      return int.tryParse(label);
    } else if (_calendarTimeType == 'month') {
      final val = label.replaceAll('月', '');
      return int.tryParse(val);
    } else if (_calendarTimeType == 'year') {
      final val = label.replaceAll('年', '');
      return int.tryParse(val);
    }
    return null;
  }

  String _formatCalendarPnl(double pnl, AppState appState) {
    if (appState.amountHidden) return '***';
    final absPnl = pnl.abs();
    if (absPnl >= 100000) return '${(pnl / 10000).toStringAsFixed(1)}w';
    if (absPnl >= 10000) return '${(pnl / 10000).toStringAsFixed(2)}w';
    return pnl.toStringAsFixed(0);
  }

  String _calendarSummaryText(AppState appState, double? total) {
    if (appState.amountHidden) return '****';
    if (total == null) return '--';
    return '¥${total.toStringAsFixed(0)}';
  }

  String _calendarSummaryRate(AppState appState) {
    if (appState.amountHidden) return '--%';

    // Try to get the rate directly from the backend response keys
    final apiRate =
        _calendarData['total_rate'] ??
        _calendarData['pnl_rate'] ??
        _calendarData['rate'];
    if (apiRate != null) {
      final rate = (apiRate as num).toDouble();
      return '${rate > 0 ? '+' : ''}${rate.toStringAsFixed(2)}%';
    }
    return '--%';
  }

  String _formatDetailPnl(double? pnl, AppState appState) {
    if (appState.amountHidden) return '****';
    if (pnl == null) return '--';
    final sign = pnl >= 0 ? '+' : '-';
    return '$sign¥ ${pnl.abs().round()}';
  }

  String _formatDetailRate(double? pnlRate, AppState appState) {
    if (appState.amountHidden) return '--%';
    if (pnlRate == null) return '--';
    final sign = pnlRate >= 0 ? '+' : '';
    return '$sign${pnlRate.toStringAsFixed(2)}%';
  }

  Widget _rankBadge(int rank) {
    if (rank <= 3) {
      final List<Color> g = rank == 1
          ? [const Color(0xFFFFD700), const Color(0xFFFFA500)]
          : (rank == 2
                ? [const Color(0xFFE2E8F0), const Color(0xFF94A3B8)]
                : [const Color(0xFFCE8E59), const Color(0xFF8B4513)]);
      return Container(
        width: 24,
        height: 24,
        alignment: Alignment.center,
        child: Stack(
          alignment: Alignment.center,
          children: [
            Container(
              width: 20,
              height: 20,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: g,
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: g[1].withValues(alpha: 0.25),
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
            ),
            const Icon(Icons.military_tech, size: 14, color: Color(0xFF0F172A)),
          ],
        ),
      );
    }
    return Container(
      width: 24,
      height: 24,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: AppTheme.bgElevated,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        '$rank',
        style: TextStyle(
          fontSize: 11,
          color: AppTheme.textTertiary,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class AnalysisRankAllPage extends StatefulWidget {
  final String rankType; // profit / loss
  final Future<Map<String, dynamic>> Function({String rankType, String market})?
  rankLoader;
  const AnalysisRankAllPage({
    super.key,
    required this.rankType,
    this.rankLoader,
  });

  @override
  State<AnalysisRankAllPage> createState() => _AnalysisRankAllPageState();
}

class _AnalysisRankAllPageState extends State<AnalysisRankAllPage> {
  final ApiService _api = ApiService();
  bool _loading = false;
  List<_RankItem> _items = const [];
  int _retryCount = 0;
  Timer? _retryTimer;
  int? _activeLedgerId;

  @override
  void initState() {
    super.initState();
    _loadRank();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final ledgerId = context.read<AppState>().currentLedgerId;
    if (_activeLedgerId == ledgerId) {
      return;
    }
    final initialMount = _activeLedgerId == null && _items.isEmpty && !_loading;
    _activeLedgerId = ledgerId;
    if (initialMount) {
      return;
    }
    unawaited(_loadRank(force: true));
  }

  @override
  void dispose() {
    _retryTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadRank({bool force = false}) async {
    if (_loading && !force) return;
    setState(() => _loading = true);
    try {
      final ledgerId = context.read<AppState>().currentLedgerId;
      final data = widget.rankLoader != null
          ? await widget.rankLoader!(rankType: 'all', market: 'all')
          : await _api.getAnalysisRank(
              rankType: 'all',
              market: 'all',
              ledgerId: ledgerId,
            );
      if (!mounted) return;
      final items = _parseRankItems(data);
      setState(() {
        _items = items;
        _loading = false;
        _retryCount = 0;
      });
      _retryTimer?.cancel();
    } catch (e) {
      debugPrint('加载盈亏排行失败: $e');
      if (!mounted) return;
      setState(() => _loading = false);
      if (_retryCount < 3) {
        _retryCount += 1;
        final delayMs = 600 * _retryCount;
        _retryTimer?.cancel();
        _retryTimer = Timer(Duration(milliseconds: delayMs), () {
          if (!mounted) return;
          unawaited(_loadRank(force: true));
        });
      }
    }
  }

  List<_RankItem> _parseRankItems(Map<String, dynamic> data) {
    final key = widget.rankType == 'loss' ? 'loss' : 'gain';
    final raw = data[key];
    if (raw is! List) return [];
    return raw.map((item) {
      final map = item is Map
          ? Map<String, dynamic>.from(item)
          : <String, dynamic>{};
      final code = (map['code'] ?? '').toString();
      final name = (map['name'] ?? '').toString();
      final pnl = (map['pnl'] as num?)?.toDouble() ?? 0.0;
      final pnlRate = (map['pnl_rate'] as num?)?.toDouble() ?? 0.0;
      final curr = (map['curr'] ?? 'CNY').toString();
      return _RankItem(
        code: code,
        name: name,
        pnl: pnl,
        pnlRate: pnlRate,
        currencySymbol: _currencySymbol(curr),
      );
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final title = widget.rankType == 'profit' ? '盈利榜' : '亏损榜';
    return Scaffold(
      backgroundColor: AppTheme.bgPrimary,
      appBar: AppBar(
        backgroundColor: AppTheme.bgPrimary,
        elevation: 0,
        centerTitle: true,
        title: Text(
          title,
          style: _S.label.copyWith(
            fontSize: 18,
            fontWeight: FontWeight.w700,
            color: AppTheme.textPrimary,
          ),
        ),
        leading: IconButton(
          icon: const Icon(
            Icons.arrow_back_ios_new,
            color: Colors.white,
            size: 20,
          ),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: _loading
          ? Center(
              child: Text(
                '加载中...',
                style: _S.label.copyWith(color: AppTheme.textMuted),
              ),
            )
          : _items.isEmpty
          ? Center(
              child: Text(
                '暂无数据',
                style: _S.label.copyWith(color: AppTheme.textMuted),
              ),
            )
          : ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: _items.length,
              separatorBuilder: (context, index) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final item = _items[index];
                return _buildRankCard(item, index + 1);
              },
            ),
    );
  }

  Widget _buildRankCard(_RankItem item, int rank) {
    final pnlColor = item.pnl >= 0 ? AppTheme.danger : AppTheme.success;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      decoration: BoxDecoration(
        color: AppTheme.isLight
            ? const Color(0x0A222C40)
            : AppPalette.dark.surface2.withValues(alpha: 0.4),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppTheme.isLight
              ? const Color(0x0A222C40)
              : Colors.white.withValues(alpha: 0.03),
        ),
      ),
      child: Row(
        children: [
          _rankBadge(rank),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.displayName,
                  style: _S.rankName.copyWith(color: AppTheme.textPrimary),
                ),
                const SizedBox(height: 2),
                Text(
                  _formatDisplayCode(item.code),
                  style: _S.rankCode.copyWith(color: AppTheme.textMuted),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${item.currencySymbol}${item.pnl.toStringAsFixed(0)}',
                style: _S.rankVal.copyWith(color: pnlColor),
              ),
              const SizedBox(height: 2),
              Text(
                '${item.pnlRate >= 0 ? '+' : ''}${item.pnlRate.toStringAsFixed(2)}%',
                style: _S.rankPct.copyWith(
                  color: pnlColor.withValues(alpha: 0.8),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _formatDisplayCode(String code) {
    if (code.startsWith('gb_')) return code.substring(3).toUpperCase();
    if (code.startsWith('f_')) return code.substring(2);
    if (code.startsWith('ft_')) return code.substring(3);
    return code.toUpperCase();
  }

  Widget _rankBadge(int rank) {
    if (rank <= 3) {
      final List<Color> g = rank == 1
          ? [const Color(0xFFFFD700), const Color(0xFFFFA500)]
          : (rank == 2
                ? [const Color(0xFFE2E8F0), const Color(0xFF94A3B8)]
                : [const Color(0xFFCE8E59), const Color(0xFF8B4513)]);
      return Container(
        width: 24,
        height: 24,
        alignment: Alignment.center,
        child: Stack(
          alignment: Alignment.center,
          children: [
            Container(
              width: 20,
              height: 20,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: g,
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: g[1].withValues(alpha: 0.25),
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
            ),
            const Icon(Icons.military_tech, size: 14, color: Color(0xFF0F172A)),
          ],
        ),
      );
    }
    return Container(
      width: 24,
      height: 24,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: AppTheme.bgElevated,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        '$rank',
        style: TextStyle(
          fontSize: 11,
          color: AppTheme.textTertiary,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class _RankItem {
  final String code;
  final String name;
  final double pnl;
  final double pnlRate;
  final String currencySymbol;

  _RankItem({
    required this.code,
    required this.name,
    required this.pnl,
    required this.pnlRate,
    required this.currencySymbol,
  });

  String get displayName => formatAssetDisplayName(name);
}
