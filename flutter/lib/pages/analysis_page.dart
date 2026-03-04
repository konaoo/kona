import 'dart:async';

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../config/theme.dart';
import '../services/api_service.dart';
import '../services/cache_service.dart';
import '../providers/app_state.dart';
import '../widgets/calendar_period_wheel_sheet.dart';

enum CalendarPeriodWheelMode { day, month }

// Test Keys
const kCalendarYearWheelKey = Key('calendar-year-wheel');
const kCalendarMonthWheelKey = Key('calendar-month-wheel');
const kCalendarPickerDoneKey = Key('calendar-picker-done');
const kCalendarPickerResetKey = Key('calendar-picker-reset');

// ──────────────────────────────────────────────────
// Cached TextStyles – DM Sans for labels, JetBrains Mono for numbers
// ──────────────────────────────────────────────────
class _S {
  _S._();
  // Overview
  static final label = GoogleFonts.dmSans(
    fontSize: 12, fontWeight: FontWeight.w500, letterSpacing: 0.01,
  );
  static final value = GoogleFonts.jetBrainsMono(
    fontSize: 28, fontWeight: FontWeight.w600, letterSpacing: -0.02,
  );
  static final pnlRate = GoogleFonts.dmSans(
    fontSize: 12, fontWeight: FontWeight.w700,
  );
  // Calendar
  static final calDate = GoogleFonts.jetBrainsMono(
    fontSize: 13, fontWeight: FontWeight.w600,
  );
  static final calPnl = GoogleFonts.jetBrainsMono(
    fontSize: 9, fontWeight: FontWeight.w700,
  );
  static final calSumLabel = GoogleFonts.dmSans(
    fontSize: 11, fontWeight: FontWeight.w500,
  );
  static final calSumVal = GoogleFonts.jetBrainsMono(
    fontSize: 18, fontWeight: FontWeight.w700,
  );
  // Rankings
  static final rankName = GoogleFonts.dmSans(
    fontSize: 14, fontWeight: FontWeight.w600, height: 1.2,
  );
  static final rankCode = GoogleFonts.jetBrainsMono(
    fontSize: 10, fontWeight: FontWeight.w500, letterSpacing: 0.02,
  );
  static final rankVal = GoogleFonts.jetBrainsMono(
    fontSize: 15, fontWeight: FontWeight.w700,
  );
  static final rankPct = GoogleFonts.dmSans(
    fontSize: 11, fontWeight: FontWeight.w600,
  );
  static final tabText = GoogleFonts.dmSans(
    fontSize: 13, fontWeight: FontWeight.w600,
  );
}

/// 分析页面 - 盈亏分析
class AnalysisPage extends StatefulWidget {
  const AnalysisPage({super.key, this.overviewLoader, this.calendarLoader});

  final Future<Map<String, dynamic>> Function(String period)? overviewLoader;
  final Future<Map<String, dynamic>> Function({
    required String timeType,
    int? year,
    int? month,
  })?
  calendarLoader;

  @override
  State<AnalysisPage> createState() => _AnalysisPageState();
}

class _AnalysisPageState extends State<AnalysisPage> {
  final ApiService _api = ApiService();
  final CacheService _cache = CacheService();
  final LayerLink _datePickerLink = LayerLink();
  OverlayEntry? _datePickerOverlay;
  static const int _maxTransientRetry = 3;
  static const String _legacyOverviewStorageKey = 'cache_analysis_overview';
  String _currentPeriod = 'day';
  Map<String, dynamic> _overview = {};
  bool _loading = true;
  bool _isRefreshing = false;
  bool _overviewLoaded = false;
  int _overviewRetryCount = 0;
  Timer? _overviewRetryTimer;

  // 收益日历相关
  String _calendarTimeType = 'day';
  Map<String, dynamic> _calendarData = {};
  bool _calendarLoading = false;
  int _calendarRetryCount = 0;
  Timer? _calendarRetryTimer;
  final Map<String, Map<String, dynamic>> _calendarCache = {};
  int? _selectedDayYear;
  int? _selectedDayMonth;
  int? _selectedMonthYear;
  int? _selectedMonthMonth;
  List<int> _selectableDayYears = const [];
  Map<int, List<int>> _selectableMonthsByYear = const {};
  List<int> _selectableMonthYears = const [];

  // 盈亏排行相关
  String _rankType = 'profit'; // 'profit' 或 'loss'

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    _selectedDayYear = now.year;
    _selectedDayMonth = now.month;
    _selectedMonthYear = now.year;
    _selectedMonthMonth = now.month;
    _loadData();
    _loadCalendar();
  }

  @override
  void dispose() {
    _overviewRetryTimer?.cancel();
    _calendarRetryTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadData({
    bool force = false,
    bool showLoadingUi = true,
  }) async {
    var renderedByCache = false;
    if (!force && !_overviewLoaded) {
      final cached = await _loadOverviewFromStorage();
      if (cached != null && mounted) {
        setState(() {
          _overview = cached;
          _loading = false;
        });
        renderedByCache = true;
      }
    }
    if (_overviewLoaded && !force) return;
    if (!renderedByCache && showLoadingUi) {
      setState(() => _loading = true);
    }
    try {
      final data = widget.overviewLoader != null
          ? await widget.overviewLoader!('all')
          : await _api.getAnalysisOverview(period: 'all');
      if (!mounted) return;
      setState(() {
        _overview = data;
        _loading = false;
        _overviewLoaded = true;
      });
      unawaited(_saveOverviewToStorage(data));
      _overviewRetryTimer?.cancel();
      _overviewRetryCount = 0;
    } catch (e) {
      debugPrint('加载分析数据失败: $e');
      if (!mounted) return;
      if (!renderedByCache && showLoadingUi) {
        setState(() => _loading = false);
      }
      if (_overviewRetryCount < _maxTransientRetry) {
        _overviewRetryCount += 1;
        final retryCount = _overviewRetryCount;
        final delayMs = 600 * retryCount;
        _overviewRetryTimer?.cancel();
        _overviewRetryTimer = Timer(Duration(milliseconds: delayMs), () {
          if (!mounted) return;
          unawaited(_loadData(force: true));
        });
      }
    }
  }

  Future<Map<String, dynamic>?> _loadOverviewFromStorage() async {
    try {
      final payload =
          await _cache.getJson(_overviewStorageKey()) ??
          await _cache.getJson(_legacyOverviewStorageKey);
      if (payload == null) return null;
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
  }) async {
    final requestCacheKey = _calendarCacheKey();
    final requestStorageKey = _calendarStorageKey(requestCacheKey);
    var renderedByCache = false;

    if (!force) {
      var cached = _calendarCache[requestCacheKey];
      if (cached == null) {
        cached = await _loadCalendarFromStorage(requestStorageKey);
        if (cached != null) {
          _calendarCache[requestCacheKey] = cached;
        }
      }
      if (cached != null && mounted) {
        final cachedData = cached;
        setState(() {
          _syncCalendarMetaFromData(cachedData);
          _normalizeCalendarSelections();
          _calendarData = cachedData;
          _calendarLoading = false;
        });
        renderedByCache = true;
      }
    }

    if (!renderedByCache && showLoadingUi) {
      setState(() => _calendarLoading = true);
    }
    try {
      final data = widget.calendarLoader != null
          ? await widget.calendarLoader!(
              timeType: _calendarTimeType,
              year: _currentCalendarRequestYear,
              month: _currentCalendarRequestMonth,
            )
          : await _api.getAnalysisCalendar(
              timeType: _calendarTimeType,
              year: _currentCalendarRequestYear,
              month: _currentCalendarRequestMonth,
            );
      if (!mounted) return;
      setState(() {
        _syncCalendarMetaFromData(data);
        _normalizeCalendarSelections();
        _calendarData = data;
        final resolvedCacheKey = _calendarCacheKey();
        _calendarCache[resolvedCacheKey] = data;
        _calendarLoading = false;
      });
      _calendarRetryTimer?.cancel();
      _calendarRetryCount = 0;
      final resolvedStorageKey = _calendarStorageKey(_calendarCacheKey());
      unawaited(_saveCalendarToStorage(resolvedStorageKey, data));
    } catch (e) {
      debugPrint('加载收益日历失败: $e');
      if (!mounted) return;
      if (!renderedByCache && showLoadingUi) {
        setState(() => _calendarLoading = false);
      }
      if (_calendarRetryCount < _maxTransientRetry) {
        _calendarRetryCount += 1;
        final retryCount = _calendarRetryCount;
        final delayMs = 700 * retryCount;
        _calendarRetryTimer?.cancel();
        _calendarRetryTimer = Timer(Duration(milliseconds: delayMs), () {
          if (!mounted) return;
          unawaited(_loadCalendar(force: true));
        });
      }
    }
  }

  String _calendarStorageKey(String cacheKey) {
    final rawUserId = context.read<AppState>().userId?.trim();
    final userId = (rawUserId == null || rawUserId.isEmpty)
        ? 'guest'
        : rawUserId;
    return 'analysis_calendar_v1:$userId:$cacheKey';
  }

  String _overviewStorageKey() {
    final rawUserId = context.read<AppState>().userId?.trim();
    final userId = (rawUserId == null || rawUserId.isEmpty)
        ? 'guest'
        : rawUserId;
    return 'analysis_overview_v1:$userId';
  }

  Future<Map<String, dynamic>?> _loadCalendarFromStorage(String key) async {
    try {
      final payload = await _cache.getJson(key);
      if (payload == null) return null;
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

  void _onCalendarTypeChanged(String nextType) {
    if (_calendarTimeType == nextType) return;
    setState(() => _calendarTimeType = nextType);
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

  Future<void> _onPullToRefresh() async {
    if (_isRefreshing) return;
    setState(() => _isRefreshing = true);
    _overviewRetryTimer?.cancel();
    _calendarRetryTimer?.cancel();
    _overviewRetryCount = 0;
    _calendarRetryCount = 0;
    final appState = context.read<AppState>();
    if (!appState.portfolioLoaded) {
      unawaited(appState.refreshHomeData());
    }
    try {
      await Future.wait<void>([
        _loadData(force: true, showLoadingUi: false),
        _loadCalendar(force: true, showLoadingUi: false),
      ]);
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
              const SizedBox(height: 14),
              _buildCalendarSection(appState),
              const SizedBox(height: 14),
              _buildCalendarSummary(appState),
              const SizedBox(height: 16),
              _buildRankSection(appState),
              const SizedBox(height: 100),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildOverviewCard(AppState appState) {
    final periodData = _overview[_currentPeriod] ?? {};
    final apiPnl = (periodData['pnl'] as num?)?.toDouble();
    final apiRate = (periodData['pnl_rate'] as num?)?.toDouble();
    final isDay = _currentPeriod == 'day';
    final pnl = isDay ? appState.investDayPnl : (apiPnl ?? 0);
    final pnlRate = isDay ? appState.investDayPnlRate : (apiRate ?? 0);
    final pnlColor = pnl >= 0 ? AppTheme.danger : AppTheme.success;
    final showLoading = _loading && !_overviewLoaded && !isDay;
    final amountText = appState.amountHidden ? '****' : '¥${pnl.toStringAsFixed(0)}';

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

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 15),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0x265B8DEF)),
        gradient: const LinearGradient(
          begin: Alignment(-0.6, -1),
          end: Alignment(1, 1),
          colors: [
            Color(0xFF171C2E),
            Color(0xFF111520),
            Color(0xFF0F1219),
          ],
          stops: [0.0, 0.6, 1.0],
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.35),
            blurRadius: 26,
            offset: const Offset(0, 12),
          ),
        ],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            title,
            style: _S.label.copyWith(color: const Color(0xFF9AA3B7), fontSize: 13),
          ),
          const SizedBox(height: 12),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.center,
            child: Text(
              showLoading ? '加载中...' : amountText,
              style: _S.value.copyWith(
                color: showLoading ? const Color(0xFFF0F4FF) : pnlColor,
                fontSize: 32,
              ),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                pnlRate >= 0 ? Icons.trending_up_rounded : Icons.trending_down_rounded,
                size: 16,
                color: pnlColor,
              ),
              const SizedBox(width: 4),
              Text(
                '收益率',
                style: _S.label.copyWith(color: pnlColor, fontSize: 13),
              ),
              const SizedBox(width: 4),
              Text(
                showLoading ? '--' : '${pnlRate >= 0 ? '+' : ''}${pnlRate.toStringAsFixed(2)}%',
                style: _S.pnlRate.copyWith(
                  color: pnlColor,
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          _buildPeriodSegmentedControl(),
        ],
      ),
    );
  }

  Widget _buildPeriodSegmentedControl() {
    return Container(
      height: 44,
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: const Color(0xFF16181F),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _buildPeriodButton('当日', _currentPeriod == 'day', 'day'),
          _buildPeriodButton('本月', _currentPeriod == 'month', 'month'),
          _buildPeriodButton('本年', _currentPeriod == 'year', 'year'),
          _buildPeriodButton('全部', _currentPeriod == 'profit', 'profit'),
        ],
      ),
    );
  }

  Widget _buildPeriodButton(String label, bool isSelected, String period) {
    final blue = const Color(0xFF3F8CFF);
    return Expanded(
      child: GestureDetector(
        onTap: () => _changePeriod(period),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: isSelected ? blue : Colors.transparent,
            borderRadius: BorderRadius.circular(999),
            boxShadow: isSelected
                ? [
                    BoxShadow(
                      color: blue.withValues(alpha: 0.3),
                      blurRadius: 8,
                      offset: const Offset(0, 2),
                    )
                  ]
                : null,
          ),
          child: Text(
            label,
            style: _S.label.copyWith(
              fontSize: 13,
              fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
              color: isSelected ? Colors.white : AppTheme.textSecondary,
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
        calendarGrid.add({'day': i, 'date': '${i}月', 'pnl': null});
      }
    } else {
      for (int i = 0; i < 6; i++) {
        final year = now.year - 5 + i;
        calendarGrid.add({'day': year, 'date': '${year}年', 'pnl': null});
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
    if (_calendarTimeType == 'day' && dayYear == now.year && dayMonth == now.month) {
      final todayKey = DateTime.now().day;
      pnlMap[todayKey] = appState.investDayPnl;
    }

    for (var gridItem in calendarGrid) {
      final key = gridItem['day'] as int;
      if (pnlMap.containsKey(key)) {
        gridItem['pnl'] = pnlMap[key];
      }
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withValues(alpha: 0.055)),
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            AppTheme.bgCard.withValues(alpha: 0.8),
            AppTheme.bgPrimary.withValues(alpha: 0.5),
          ],
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '收益日历',
                style: _S.label.copyWith(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _buildCalendarHeaderControls(),
          const SizedBox(height: 14),
          _buildCalendarGrid(calendarGrid, appState),
        ],
      ),
    );
  }

  Widget _buildCalendarHeaderControls() {
    return Row(
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
            color: Colors.black.withValues(alpha: 0.2),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Row(
            children: [
              _buildHeaderToggle('日', _calendarTimeType == 'day', () => _onCalendarTypeChanged('day')),
              _buildHeaderToggle('月', _calendarTimeType == 'month', () => _onCalendarTypeChanged('month')),
              _buildHeaderToggle('年', _calendarTimeType == 'year', () => _onCalendarTypeChanged('year')),
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
        onTap: _calendarPeriodPickerEnabled ? _toggleDatePicker : null,
        child: Container(
          height: 32,
          padding: const EdgeInsets.symmetric(horizontal: 16),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: const Color(0xFF16181F),
            borderRadius: BorderRadius.circular(999),
            border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                _calendarPeriodButtonText(),
                style: _S.label.copyWith(
                  fontSize: 13,
                  color: _calendarPeriodPickerEnabled ? AppTheme.textPrimary : AppTheme.textMuted,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(width: 6),
              Icon(
                Icons.keyboard_arrow_down_rounded,
                size: 16,
                color: _calendarPeriodPickerEnabled ? AppTheme.textSecondary : AppTheme.textMuted,
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

    final now = DateTime.now();
    final selectableYears = List<int>.generate(now.year - 2018 + 1, (index) => 2018 + index);
    final Map<int, List<int>> selectableMonthsByYear = {};
    for (var year in selectableYears) {
      if (year < now.year) {
        selectableMonthsByYear[year] = List<int>.generate(12, (index) => index + 1);
      } else {
        selectableMonthsByYear[year] = List<int>.generate(now.month, (index) => index + 1);
      }
    }

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
              child: DatePickerDropdown(
                initialYear: _calendarTimeType == 'day' ? (_selectedDayYear ?? DateTime.now().year) : (_selectedMonthYear ?? DateTime.now().year),
                initialMonth: _calendarTimeType == 'day' 
                    ? (_selectedDayMonth ?? DateTime.now().month) 
                    : (_selectedMonthMonth ?? DateTime.now().month),
                selectableYears: selectableYears,
                selectableMonthsByYear: selectableMonthsByYear,
                onSelected: (year, month, isFinal) {
                  if (_calendarTimeType == 'day') {
                    setState(() {
                      _selectedDayYear = year;
                      _selectedDayMonth = month;
                    });
                  } else {
                    setState(() {
                      _selectedMonthYear = year;
                      _selectedMonthMonth = month;
                    });
                  }
                  
                  if (isFinal) {
                    _hideDatePicker();
                  }

                  // Debounce the load to avoid jumping during rapid scroll
                  _calendarRetryTimer?.cancel();
                  _calendarRetryTimer = Timer(const Duration(milliseconds: 100), () {
                    if (mounted) _loadCalendar();
                  });
                },
              ),
            ),
          ),
        ],
      ),
    );

    Overlay.of(context).insert(_datePickerOverlay!);
  }

  Widget _buildCalendarGrid(List<Map<String, dynamic>> calendarGrid, AppState appState) {
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
        final isSelected = _calendarTimeType == 'day' 
            ? item['day'] == DateTime.now().day && (_selectedDayYear == null || _selectedDayYear == DateTime.now().year) && (_selectedDayMonth == null || _selectedDayMonth == DateTime.now().month)
            : false;

        return _buildCalendarItem(item['date'], pnl, isSelected, appState);
      },
    );
  }

  Widget _buildCalendarItem(String label, double? pnl, bool isSelected, AppState appState) {
    final hasData = pnl != null;
    final color = pnl == null ? AppTheme.textMuted : (pnl >= 0 ? AppTheme.danger : AppTheme.success);
    
    return Container(
      decoration: BoxDecoration(
        color: isSelected ? AppTheme.accent.withValues(alpha: 0.15) : AppTheme.surface2.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: isSelected ? AppTheme.accent : Colors.white.withValues(alpha: 0.05),
          width: isSelected ? 1.5 : 1,
        ),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(label, style: _S.calDate.copyWith(
            fontSize: label.contains('-') ? 11 : 13,
            color: isSelected ? Colors.white : AppTheme.textPrimary,
          )),
          const SizedBox(height: 2),
          Text(
            hasData ? _formatCalendarPnl(pnl, appState) : '--',
            style: _S.calPnl.copyWith(color: color),
          ),
        ],
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

    final pnlValue = _calendarSummaryText(appState);
    final pnlRate = _calendarSummaryRate(appState);
    final pnlRaw = _calendarSummaryRawValue();
    final pnlColor = pnlRaw >= 0 ? AppTheme.danger : AppTheme.success;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppTheme.bgCard.withValues(alpha: 0.9),
            AppTheme.bgPrimary.withValues(alpha: 0.8),
          ],
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.2),
            blurRadius: 15,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Text('$pnlLabel：', style: _S.calSumLabel.copyWith(color: AppTheme.textSecondary, fontSize: 13)),
              Text(
                pnlValue,
                style: _S.calSumVal.copyWith(
                  color: pnlColor,
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          Row(
            children: [
              Text('盈亏率：', style: _S.calSumLabel.copyWith(color: AppTheme.textSecondary, fontSize: 13)),
              Text(
                pnlRate,
                style: _S.calSumVal.copyWith(
                  color: pnlColor,
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  double _calendarSummaryRawValue() {
    double total = 0;
    final items = _calendarData['items'] as List<dynamic>? ?? [];
    for (var item in items) {
      total += (item['pnl'] as num?)?.toDouble() ?? 0;
    }
    return total;
  }

  Widget _buildRankSection(AppState appState) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withValues(alpha: 0.055)),
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            AppTheme.bgCard.withValues(alpha: 0.8),
            AppTheme.bgPrimary.withValues(alpha: 0.5),
          ],
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '盈亏排行',
                style: _S.label.copyWith(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary,
                ),
              ),
              GestureDetector(
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => AnalysisRankAllPage(rankType: _rankType),
                  ),
                ),
                child: Row(
                  children: [
                    Text('查看全部', style: _S.label.copyWith(color: AppTheme.accent, fontSize: 11)),
                    Icon(Icons.chevron_right, size: 14, color: AppTheme.accent),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              _buildRankTab('盈利榜', _rankType == 'profit', () => setState(() => _rankType = 'profit')),
              const SizedBox(width: 8),
              _buildRankTab('亏损榜', _rankType == 'loss', () => setState(() => _rankType = 'loss')),
            ],
          ),
          const SizedBox(height: 14),
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
          color: isSelected ? AppTheme.accent.withValues(alpha: 0.1) : Colors.transparent,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: isSelected ? AppTheme.accent.withValues(alpha: 0.3) : Colors.transparent),
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
    final items = _buildRankItemsData(appState);
    final isProfit = _rankType == 'profit';
    final filtered = items.where((i) => isProfit ? i.pnlCny > 0 : i.pnlCny < 0).toList();
    
    // 排序：盈利榜降序，亏损榜升序（绝对值大的排前面）
    filtered.sort((a, b) => isProfit 
        ? b.pnlCny.compareTo(a.pnlCny) 
        : a.pnlCny.compareTo(b.pnlCny));
    
    if (filtered.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 20),
          child: Text('暂无数据', style: _S.label.copyWith(color: AppTheme.textMuted)),
        ),
      );
    }

    final limit = filtered.length > 5 ? 5 : filtered.length;
    final topItems = filtered.sublist(0, limit);

    return Column(
      children: List.generate(topItems.length, (idx) {
        return _buildRankCard(topItems[idx], appState, idx + 1);
      }),
    );
  }

  Widget _buildRankCard(_RankItem item, AppState appState, int rank) {
    final pnlColor = item.pnl >= 0 ? AppTheme.danger : AppTheme.success;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
      decoration: BoxDecoration(
        color: AppPalette.dark.surface2.withValues(alpha: 0.4),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.white.withValues(alpha: 0.03)),
      ),
      child: Row(
        children: [
          _rankBadge(rank),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.name, style: _S.rankName.copyWith(color: AppTheme.textPrimary)),
                const SizedBox(height: 2),
                Text(_formatDisplayCode(item.code), style: _S.rankCode.copyWith(color: AppTheme.textMuted)),
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
                (item.pnlRate >= 0 ? '+' : '') + item.pnlRate.toStringAsFixed(2) + '%',
                style: _S.rankPct.copyWith(color: pnlColor.withValues(alpha: 0.8)),
              ),
            ],
          ),
        ],
      ),
    );
  }

  List<_RankItem> _buildRankItemsData(AppState appState) {
    final list = <_RankItem>[];
    for (var asset in appState.portfolio) {
      final priceInfo = appState.resolvePriceInfo(asset);
      final currentPrice = (priceInfo != null && priceInfo.price > 0)
          ? priceInfo.price
          : (asset.price > 0 ? asset.price : 0.0);
      
      // 累计盈亏 = (现价 - 均价) * 数量 + 调整额
      final pnl = appState.amountHidden ? 0.0 : (currentPrice - asset.price) * asset.qty + asset.adjustment;
      final cost = asset.price * asset.qty;
      final rate = cost > 0 ? (pnl / cost) * 100 : 0.0;
      
      final exchangeRate = appState.getCurrencyRate(asset.curr);
      list.add(_RankItem(
        code: asset.code,
        name: asset.name,
        pnl: pnl,
        pnlCny: pnl * exchangeRate,
        pnlRate: rate,
        currencySymbol: asset.currencySymbol,
      ));
    }
    return list;
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

  String _formatDisplayCode(String code) {
    if (code.startsWith('gb_')) return code.substring(3).toUpperCase();
    if (code.startsWith('f_')) return code.substring(2);
    if (code.startsWith('ft_')) return code.substring(3);
    return code.toUpperCase();
  }

  int? _parseLabelKey(String label) {
    if (_calendarTimeType == 'day') {
      final parts = label.split('-');
      if (parts.length == 2) return int.tryParse(parts[1]);
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
    if (absPnl >= 100000) return (pnl / 10000).toStringAsFixed(1) + 'w';
    if (absPnl >= 10000) return (pnl / 10000).toStringAsFixed(2) + 'w';
    return pnl.toStringAsFixed(0);
  }

  String _calendarSummaryText(AppState appState) {
    if (appState.amountHidden) return '****';
    double total = _calendarSummaryRawValue();
    return '¥${total.toStringAsFixed(0)}';
  }

  String _calendarSummaryRate(AppState appState) {
    if (appState.amountHidden) return '--%';
    double totalPnl = 0;
    double totalCost = 0;
    final items = _calendarData['items'] as List<dynamic>? ?? [];
    for (var item in items) {
      totalPnl += (item['pnl'] as num?)?.toDouble() ?? 0;
      totalCost += (item['cost'] as num?)?.toDouble() ?? 0;
    }
    if (totalCost == 0) return '0.00%';
    final rate = (totalPnl / totalCost) * 100;
    return (rate >= 0 ? '+' : '') + rate.toStringAsFixed(2) + '%';
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

class AnalysisRankAllPage extends StatelessWidget {
  final String rankType; // profit / loss
  const AnalysisRankAllPage({super.key, required this.rankType});

  @override
  Widget build(BuildContext context) {
    final appState = context.watch<AppState>();
    final items = _buildRankItemsData(appState);
    final isProfit = rankType == 'profit';
    final list = isProfit
        ? items.where((x) => x.pnlCny > 0).toList()
        : items.where((x) => x.pnlCny < 0).toList();
    
    if (isProfit) {
      list.sort((a, b) => b.pnlCny.compareTo(a.pnlCny));
    } else {
      list.sort((a, b) => a.pnlCny.compareTo(b.pnlCny));
    }

    return Scaffold(
      backgroundColor: AppTheme.bgPrimary,
      appBar: AppBar(
        backgroundColor: AppTheme.bgPrimary,
        elevation: 0,
        centerTitle: true,
        title: Text(
          rankType == 'profit' ? '盈利榜' : '亏损榜',
          style: _S.label.copyWith(
            fontSize: 18,
            fontWeight: FontWeight.w700,
            color: AppTheme.textPrimary,
          ),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: list.length,
        separatorBuilder: (context, index) => const SizedBox(height: 8),
        itemBuilder: (context, index) {
          final item = list[index];
          return _buildRankCard(item, appState, index + 1);
        },
      ),
    );
  }

  Widget _buildRankCard(_RankItem item, AppState appState, int rank) {
    final pnlColor = item.pnl >= 0 ? AppTheme.danger : AppTheme.success;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      decoration: BoxDecoration(
        color: AppPalette.dark.surface2.withValues(alpha: 0.4),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withValues(alpha: 0.03)),
      ),
      child: Row(
        children: [
          _rankBadge(rank),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item.name, style: _S.rankName.copyWith(color: AppTheme.textPrimary)),
                const SizedBox(height: 2),
                Text(_formatDisplayCode(item.code), style: _S.rankCode.copyWith(color: AppTheme.textMuted)),
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
                (item.pnlRate >= 0 ? '+' : '') + item.pnlRate.toStringAsFixed(2) + '%',
                style: _S.rankPct.copyWith(color: pnlColor.withValues(alpha: 0.8)),
              ),
            ],
          ),
        ],
      ),
    );
  }

  List<_RankItem> _buildRankItemsData(AppState appState) {
    final list = <_RankItem>[];
    for (var asset in appState.portfolio) {
      final priceInfo = appState.resolvePriceInfo(asset);
      final currentPrice = (priceInfo != null && priceInfo.price > 0)
          ? priceInfo.price
          : (asset.price > 0 ? asset.price : 0.0);
      
      final pnl = appState.amountHidden ? 0.0 : (currentPrice - asset.price) * asset.qty + asset.adjustment;
      final cost = asset.price * asset.qty;
      final rate = cost > 0 ? (pnl / cost) * 100 : 0.0;
      
      final exchangeRate = appState.getCurrencyRate(asset.curr);
      list.add(_RankItem(
        code: asset.code,
        name: asset.name,
        pnl: pnl,
        pnlCny: pnl * exchangeRate,
        pnlRate: rate,
        currencySymbol: asset.currencySymbol,
      ));
    }
    return list;
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
  final double pnlCny;
  final double pnlRate;
  final String currencySymbol;

  _RankItem({
    required this.code,
    required this.name,
    required this.pnl,
    required this.pnlCny,
    required this.pnlRate,
    required this.currencySymbol,
  });
}
