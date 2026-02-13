import 'package:flutter/material.dart';

import '../config/theme.dart';

const Key kCalendarYearWheelKey = Key('calendar-year-wheel');
const Key kCalendarMonthWheelKey = Key('calendar-month-wheel');
const Key kCalendarPickerResetKey = Key('calendar-picker-reset');
const Key kCalendarPickerDoneKey = Key('calendar-picker-done');

enum CalendarPeriodWheelMode { day, month }

class CalendarPeriodWheelSelection {
  const CalendarPeriodWheelSelection({required this.year, this.month});

  final int year;
  final int? month;
}

Future<CalendarPeriodWheelSelection?> showCalendarPeriodWheelSheet({
  required BuildContext context,
  required CalendarPeriodWheelMode mode,
  required List<int> selectableYears,
  Map<int, List<int>> selectableMonthsByYear = const {},
  required int initialYear,
  int? initialMonth,
  required int resetYear,
  int? resetMonth,
}) async {
  if (selectableYears.isEmpty) {
    return null;
  }
  return showModalBottomSheet<CalendarPeriodWheelSelection>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (sheetContext) {
      return _CalendarPeriodWheelSheet(
        mode: mode,
        selectableYears: selectableYears,
        selectableMonthsByYear: selectableMonthsByYear,
        initialYear: initialYear,
        initialMonth: initialMonth,
        resetYear: resetYear,
        resetMonth: resetMonth,
      );
    },
  );
}

class _CalendarPeriodWheelSheet extends StatefulWidget {
  const _CalendarPeriodWheelSheet({
    required this.mode,
    required this.selectableYears,
    required this.selectableMonthsByYear,
    required this.initialYear,
    required this.initialMonth,
    required this.resetYear,
    required this.resetMonth,
  });

  final CalendarPeriodWheelMode mode;
  final List<int> selectableYears;
  final Map<int, List<int>> selectableMonthsByYear;
  final int initialYear;
  final int? initialMonth;
  final int resetYear;
  final int? resetMonth;

  @override
  State<_CalendarPeriodWheelSheet> createState() =>
      _CalendarPeriodWheelSheetState();
}

class _CalendarPeriodWheelSheetState extends State<_CalendarPeriodWheelSheet> {
  static const double _itemExtent = 46;

  late final FixedExtentScrollController _yearController;
  FixedExtentScrollController? _monthController;

  late int _selectedYear;
  int? _selectedMonth;

  bool get _isDayMode => widget.mode == CalendarPeriodWheelMode.day;

  @override
  void initState() {
    super.initState();
    _selectedYear = _coerceYear(widget.initialYear);
    _selectedMonth = _coerceMonth(_selectedYear, widget.initialMonth);
    _yearController = FixedExtentScrollController(
      initialItem: widget.selectableYears.indexOf(_selectedYear),
    );
    if (_isDayMode) {
      _rebuildMonthController();
    }
  }

  @override
  void dispose() {
    _yearController.dispose();
    _monthController?.dispose();
    super.dispose();
  }

  int _coerceYear(int year) {
    if (widget.selectableYears.contains(year)) {
      return year;
    }
    return widget.selectableYears.last;
  }

  int? _coerceMonth(int year, int? month) {
    final months = _monthsFor(year);
    if (months.isEmpty) {
      return null;
    }
    if (month != null && months.contains(month)) {
      return month;
    }
    return months.last;
  }

  List<int> _monthsFor(int year) {
    final raw = widget.selectableMonthsByYear[year] ?? const <int>[];
    final months = raw.where((m) => m >= 1 && m <= 12).toList()..sort();
    return months;
  }

  void _rebuildMonthController() {
    final oldController = _monthController;
    final months = _monthsFor(_selectedYear);
    final selected = _coerceMonth(_selectedYear, _selectedMonth);
    _selectedMonth = selected;
    final initialIndex = selected == null ? 0 : months.indexOf(selected);
    _monthController = FixedExtentScrollController(
      initialItem: initialIndex < 0 ? 0 : initialIndex,
    );
    oldController?.dispose();
  }

  void _onYearChanged(int index) {
    if (index < 0 || index >= widget.selectableYears.length) {
      return;
    }
    final year = widget.selectableYears[index];
    if (year == _selectedYear) {
      return;
    }
    setState(() {
      _selectedYear = year;
      if (_isDayMode) {
        _rebuildMonthController();
      }
    });
  }

  void _onMonthChanged(int index) {
    if (!_isDayMode) {
      return;
    }
    final months = _monthsFor(_selectedYear);
    if (index < 0 || index >= months.length) {
      return;
    }
    setState(() {
      _selectedMonth = months[index];
    });
  }

  void _onReset() {
    final resetYear = _coerceYear(widget.resetYear);
    setState(() {
      _selectedYear = resetYear;
      if (_isDayMode) {
        final targetMonth = _coerceMonth(resetYear, widget.resetMonth);
        _selectedMonth = targetMonth;
        _rebuildMonthController();
      }
    });
    _yearController.jumpToItem(widget.selectableYears.indexOf(resetYear));
  }

  void _onDone() {
    if (_isDayMode && _selectedMonth == null) {
      return;
    }
    Navigator.of(context).pop(
      CalendarPeriodWheelSelection(year: _selectedYear, month: _selectedMonth),
    );
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Container(
        decoration: BoxDecoration(
          color: AppTheme.bgCard,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        ),
        padding: const EdgeInsets.fromLTRB(
          Spacing.lg,
          Spacing.md,
          Spacing.lg,
          Spacing.lg,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppTheme.textTertiary.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(999),
                ),
              ),
            ),
            const SizedBox(height: Spacing.lg),
            Text(
              '日期筛选',
              style: TextStyle(
                fontSize: FontSize.xxl,
                fontWeight: FontWeight.w800,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: Spacing.md),
            SizedBox(
              height: 220,
              child: Row(
                children: [
                  Expanded(
                    child: _buildWheel(
                      key: kCalendarYearWheelKey,
                      values: widget.selectableYears,
                      selectedValue: _selectedYear,
                      controller: _yearController,
                      onSelectedItemChanged: _onYearChanged,
                      labelBuilder: (v) => '${v}年',
                    ),
                  ),
                  if (_isDayMode) ...[
                    const SizedBox(width: Spacing.md),
                    Expanded(
                      child: _buildWheel(
                        key: kCalendarMonthWheelKey,
                        values: _monthsFor(_selectedYear),
                        selectedValue: _selectedMonth,
                        controller: _monthController,
                        onSelectedItemChanged: _onMonthChanged,
                        labelBuilder: (v) => '${v}月',
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: Spacing.lg),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    key: kCalendarPickerResetKey,
                    onPressed: _onReset,
                    style: OutlinedButton.styleFrom(
                      side: BorderSide(
                        color: AppTheme.border.withOpacity(
                          AppTheme.isLight ? 0.9 : 0.7,
                        ),
                      ),
                      foregroundColor: AppTheme.textSecondary,
                    ),
                    child: const Text('重置'),
                  ),
                ),
                const SizedBox(width: Spacing.md),
                Expanded(
                  child: FilledButton(
                    key: kCalendarPickerDoneKey,
                    onPressed: _onDone,
                    child: const Text('完成'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWheel({
    required Key key,
    required List<int> values,
    required int? selectedValue,
    required FixedExtentScrollController? controller,
    required ValueChanged<int> onSelectedItemChanged,
    required String Function(int value) labelBuilder,
  }) {
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(AppRadius.lg),
        color: AppTheme.bgElevated.withOpacity(AppTheme.isLight ? 0.75 : 0.35),
      ),
      child: Stack(
        alignment: Alignment.center,
        children: [
          ListWheelScrollView.useDelegate(
            key: key,
            controller: controller,
            itemExtent: _itemExtent,
            perspective: 0.002,
            physics: const FixedExtentScrollPhysics(),
            onSelectedItemChanged: onSelectedItemChanged,
            childDelegate: ListWheelChildBuilderDelegate(
              childCount: values.length,
              builder: (context, index) {
                if (index < 0 || index >= values.length) {
                  return null;
                }
                final value = values[index];
                final isSelected = value == selectedValue;
                return Center(
                  child: Text(
                    labelBuilder(value),
                    style: TextStyle(
                      fontSize: FontSize.xxl,
                      fontWeight: isSelected
                          ? FontWeight.w700
                          : FontWeight.w500,
                      color: isSelected
                          ? AppTheme.textPrimary
                          : AppTheme.textSecondary.withOpacity(0.6),
                    ),
                  ),
                );
              },
            ),
          ),
          IgnorePointer(
            child: Container(
              height: _itemExtent,
              margin: const EdgeInsets.symmetric(horizontal: 6),
              decoration: BoxDecoration(
                color: AppTheme.bgCard.withOpacity(
                  AppTheme.isLight ? 0.9 : 0.28,
                ),
                borderRadius: BorderRadius.circular(AppRadius.md),
                border: Border.all(color: AppTheme.border.withOpacity(0.35)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
