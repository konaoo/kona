class FabScrollVisibilityController {
  FabScrollVisibilityController({
    this.hideThresholdPx = 24.0,
    this.showThresholdPx = 16.0,
    this.minToggleIntervalMs = 180,
  });

  final double hideThresholdPx;
  final double showThresholdPx;
  final int minToggleIntervalMs;

  bool _visible = true;
  double _upAccumulated = 0;
  double _downAccumulated = 0;
  DateTime? _lastToggleAt;

  bool? onScrollUpdate(double delta) {
    if (delta == 0) return null;
    final now = DateTime.now();

    if (delta > 0) {
      _upAccumulated += delta;
      _downAccumulated = 0;
      if (!_visible) return null;
      if (_upAccumulated < hideThresholdPx) return null;
      if (!_canToggle(now)) return null;
      _visible = false;
      _upAccumulated = 0;
      _lastToggleAt = now;
      return false;
    }

    _downAccumulated += -delta;
    _upAccumulated = 0;
    if (_visible) return null;
    if (_downAccumulated < showThresholdPx) return null;
    if (!_canToggle(now)) return null;
    _visible = true;
    _downAccumulated = 0;
    _lastToggleAt = now;
    return true;
  }

  void onScrollIdle() {
    _upAccumulated = 0;
    _downAccumulated = 0;
  }

  void resetVisible() {
    _visible = true;
    _upAccumulated = 0;
    _downAccumulated = 0;
    _lastToggleAt = null;
  }

  bool _canToggle(DateTime now) {
    final last = _lastToggleAt;
    if (last == null) return true;
    return now.difference(last).inMilliseconds >= minToggleIntervalMs;
  }
}
