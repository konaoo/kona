import 'package:flutter/foundation.dart';

class AppAsyncFlowResult {
  final String flow;
  final bool ok;
  final String stage;
  final DateTime startedAt;
  final DateTime endedAt;
  final int durationMs;
  final String? error;

  const AppAsyncFlowResult({
    required this.flow,
    required this.ok,
    required this.stage,
    required this.startedAt,
    required this.endedAt,
    required this.durationMs,
    this.error,
  });

  @override
  String toString() {
    return 'AppAsyncFlowResult(flow: $flow, ok: $ok, stage: $stage, durationMs: $durationMs, error: $error)';
  }
}

class AppAsyncFlowTracker {
  final String flow;
  final DateTime startedAt;

  const AppAsyncFlowTracker({
    required this.flow,
    required this.startedAt,
  });
}

AppAsyncFlowTracker startAppAsyncFlow(String flow) {
  return AppAsyncFlowTracker(flow: flow, startedAt: DateTime.now().toUtc());
}

AppAsyncFlowResult finishAppAsyncFlow(
  AppAsyncFlowTracker tracker, {
  required String stage,
  Object? error,
}) {
  final endedAt = DateTime.now().toUtc();
  final result = AppAsyncFlowResult(
    flow: tracker.flow,
    ok: error == null,
    stage: stage,
    startedAt: tracker.startedAt,
    endedAt: endedAt,
    durationMs: endedAt.difference(tracker.startedAt).inMilliseconds,
    error: error?.toString(),
  );
  if (kDebugMode) {
    debugPrint('[async-flow] $result');
  }
  return result;
}
