import 'package:flutter/material.dart';

class DatePickerDropdown extends StatefulWidget {
  const DatePickerDropdown({
    super.key,
    required this.initialYear,
    this.initialMonth,
    required this.selectableYears,
    required this.selectableMonthsByYear,
    required this.onSelected,
  });

  final int initialYear;
  final int? initialMonth;
  final List<int> selectableYears;
  final Map<int, List<int>> selectableMonthsByYear;
  final void Function(int year, int? month, bool isFinal) onSelected;

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
    const Color bg = Color(0xFF1F2128);

    return Container(
      width: 160,
      height: 160,
      decoration: BoxDecoration(
        color: bg.withValues(alpha: 0.98),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.3),
            blurRadius: 12,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: _buildColumn(
              values: widget.selectableYears,
              selectedValue: _selectedYear,
              controller: _yearController,
              onSelectedItemChanged: (index) {
                _onYearChanged(index);
                widget.onSelected(_selectedYear, _selectedMonth, false);
              },
              labelBuilder: (v) => '$v',
              primaryColor: primaryBlue,
              mutedColor: textMuted,
            ),
          ),
          Container(
            width: 1,
            height: 80,
            color: Colors.white.withValues(alpha: 0.05),
          ),
          Expanded(
            child: _isMonthMode
                ? _buildColumn(
                    values: _monthsFor(_selectedYear),
                    selectedValue: _selectedMonth,
                    controller: _monthController,
                    onSelectedItemChanged: (index) {
                      _onMonthChanged(index);
                      widget.onSelected(_selectedYear, _selectedMonth, true);
                    },
                    onTap: () {
                      widget.onSelected(_selectedYear, _selectedMonth, true);
                    },
                    labelBuilder: (v) => '${v}月',
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
    );
  }

  Widget _buildColumn({
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
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: ListWheelScrollView.useDelegate(
        controller: controller,
        itemExtent: 40,
        perspective: 0.005,
        diameterRatio: 1.2,
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
                  fontSize: isSelected ? 18 : 16,
                  fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                  color: isSelected ? primaryColor : mutedColor.withValues(alpha: 0.6),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
