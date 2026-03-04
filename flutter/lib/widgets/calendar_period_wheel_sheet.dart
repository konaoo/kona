import 'package:flutter/material.dart';

class DatePickerDropdown extends StatefulWidget {
  const DatePickerDropdown({
    super.key,
    required this.initialYear,
    this.initialMonth,
    required this.selectableYears,
    required this.selectableMonthsByYear,
    required this.onSelected,
    this.yearWheelKey,
    this.monthWheelKey,
  });

  final int initialYear;
  final int? initialMonth;
  final List<int> selectableYears;
  final Map<int, List<int>> selectableMonthsByYear;
  final void Function(int year, int? month, bool isFinal) onSelected;
  final Key? yearWheelKey;
  final Key? monthWheelKey;

  @override
  State<DatePickerDropdown> createState() => _DatePickerDropdownState();
}

class _DatePickerDropdownState extends State<DatePickerDropdown> {
  late final FixedExtentScrollController _yearController;
  FixedExtentScrollController? _monthController;

  late int _selectedYear;
  int? _selectedMonth;

  bool get _isMonthMode => widget.initialMonth != null;

  @override
  void initState() {
    super.initState();
    _selectedYear = widget.initialYear;
    _selectedMonth = widget.initialMonth;
    _yearController = FixedExtentScrollController(
      initialItem: widget.selectableYears.indexOf(_selectedYear).clamp(0, widget.selectableYears.length - 1),
    );
    if (_isMonthMode) {
      _rebuildMonthController();
    }
  }

  void _rebuildMonthController() {
    final oldController = _monthController;
    final months = _monthsFor(_selectedYear);
    // If current selected month is out of range for the new year, pick the last available month
    if (_selectedMonth != null && !months.contains(_selectedMonth)) {
      _selectedMonth = months.last;
    }
    final initialIndex = _selectedMonth == null ? 0 : months.indexOf(_selectedMonth!).clamp(0, months.length - 1);
    _monthController = FixedExtentScrollController(
      initialItem: initialIndex,
    );
    oldController?.dispose();
  }

  List<int> _monthsFor(int year) {
    return widget.selectableMonthsByYear[year] ?? [];
  }

  void _onYearChanged(int index) {
    if (index < 0 || index >= widget.selectableYears.length) return;
    final year = widget.selectableYears[index];
    if (year == _selectedYear) return;
    setState(() {
      _selectedYear = year;
      if (_isMonthMode) {
        _rebuildMonthController();
      }
    });
  }

  void _onMonthChanged(int index) {
    final months = _monthsFor(_selectedYear);
    if (index < 0 || index >= months.length) return;
    setState(() {
      _selectedMonth = months[index];
    });
  }

  @override
  void dispose() {
    _yearController.dispose();
    _monthController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const Color primaryBlue = Color(0xFF3F8CFF);
    const Color textMuted = Color(0xFF8E8E93);

    return SizedBox(
      width: 120,
      height: 160,
      child: Material(
        color: Colors.transparent,
        child: Row(
          children: [
            Expanded(
              child: _buildColumn(
                key: widget.yearWheelKey,
                values: widget.selectableYears,
                selectedValue: _selectedYear,
                controller: _yearController,
                onSelectedItemChanged: (index) {
                  _onYearChanged(index);
                  widget.onSelected(_selectedYear, _selectedMonth, false);
                },
                onTap: () {
                  widget.onSelected(_selectedYear, _selectedMonth, true);
                },
                labelBuilder: (v) => '$v',
                primaryColor: primaryBlue,
                mutedColor: textMuted,
              ),
            ),
            Container(
              width: 1,
              height: 60,
              color: Colors.white.withValues(alpha: 0.03),
            ),
            Expanded(
              child: _isMonthMode
                  ? _buildColumn(
                      key: widget.monthWheelKey,
                      values: _monthsFor(_selectedYear),
                      selectedValue: _selectedMonth,
                      controller: _monthController,
                      onSelectedItemChanged: (index) {
                        _onMonthChanged(index);
                        widget.onSelected(_selectedYear, _selectedMonth, false);
                      },
                      onTap: () {
                        widget.onSelected(_selectedYear, _selectedMonth, true);
                      },
                      labelBuilder: (v) => '$v月',
                      primaryColor: primaryBlue,
                      mutedColor: textMuted,
                    )
                  : Center(
                      child: Text(
                        '--',
                        style: TextStyle(color: textMuted.withValues(alpha: 0.5), fontSize: 16),
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildColumn({
    Key? key,
    required List<int> values,
    required int? selectedValue,
    required FixedExtentScrollController? controller,
    required ValueChanged<int> onSelectedItemChanged,
    required String Function(int value) labelBuilder,
    required Color primaryColor,
    required Color mutedColor,
    VoidCallback? onTap,
  }) {
    if (values.isEmpty) return const SizedBox();
    return InkWell(
      onTap: onTap,
      splashColor: primaryColor.withValues(alpha: 0.1),
      highlightColor: Colors.transparent,
      child: ListWheelScrollView.useDelegate(
        key: key,
        controller: controller,
        itemExtent: 38,
        perspective: 0.008,
        diameterRatio: 1.0,
        physics: const FixedExtentScrollPhysics(),
        onSelectedItemChanged: onSelectedItemChanged,
        childDelegate: ListWheelChildBuilderDelegate(
          childCount: values.length,
          builder: (context, index) {
            final value = values[index];
            final isSelected = value == selectedValue;
            return Center(
              child: Text(
                labelBuilder(value),
                style: TextStyle(
                  fontSize: isSelected ? 17 : 14,
                  fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                  color: isSelected ? primaryColor : mutedColor.withValues(alpha: 0.5),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
