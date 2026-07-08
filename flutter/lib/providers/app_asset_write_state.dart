import '../models/asset_action_result.dart';
import '../services/api_service.dart';
import 'app_assets_state.dart';
import 'app_home_totals_state.dart';

class AppAssetWriteBindings {
  final void Function() notifyListeners;
  final Future<void> Function(bool awaitRefresh) triggerHomeRefresh;

  const AppAssetWriteBindings({
    required this.notifyListeners,
    required this.triggerHomeRefresh,
  });
}

class AppAssetWriteState {
  final ApiService _api;
  final AppAssetsState _assetsState;
  final AppHomeTotalsState _homeTotalsState;

  AppAssetWriteState({
    required ApiService api,
    required AppAssetsState assetsState,
    required AppHomeTotalsState homeTotalsState,
  }) : _api = api,
       _assetsState = assetsState,
       _homeTotalsState = homeTotalsState;

  Future<AssetActionResult> addAsset({
    required String type,
    required String name,
    required double amount,
    String? curr,
    bool awaitRefresh = true,
    required AppAssetWriteBindings bindings,
  }) async {
    final snapshot = _assetsState.captureAssetSnapshot();
    final changed = _assetsState.optimisticAddAsset(
      type: type,
      name: name,
      amount: amount,
      curr: curr,
      notify: false,
    );
    if (!changed) {
      return const AssetActionResult.failure('不支持的资产类型');
    }
    _recalculateAssetTotals(bindings.notifyListeners);

    final normalizedCurr = _assetsState.normalizeAssetCurrency(curr);
    final result = switch (type) {
      'cash' => await _api.addCashAsset(name, amount, curr: normalizedCurr),
      'other' => await _api.addOtherAsset(name, amount, curr: normalizedCurr),
      'liability' => await _api.addLiability(
        name,
        amount,
        curr: normalizedCurr,
      ),
      _ => const AssetActionResult.failure('不支持的资产类型'),
    };
    if (!result.ok) {
      _restoreAssetSnapshot(snapshot, bindings.notifyListeners);
      return result;
    }
    await bindings.triggerHomeRefresh(awaitRefresh);

    // 捕获新创建的资产 ID：返回后由前端弹窗立即应用（避免 awaitRefresh 带来的延时等待）
    int? createdId;
    if (result.data != null) {
      final rawId = result.data!['id'] ?? result.data!['cash_asset_id'];
      if (rawId is int) {
        createdId = rawId;
      } else if (rawId != null) {
        createdId = int.tryParse(rawId.toString());
      }
    }

    return AssetActionResult.success(data: {'id': createdId});
  }

  Future<AssetActionResult> deleteAsset({
    required String type,
    required int id,
    bool awaitRefresh = true,
    required AppAssetWriteBindings bindings,
  }) async {
    if (id <= 0) {
      return const AssetActionResult.failure('操作失败，请稍后重试');
    }
    final snapshot = _assetsState.captureAssetSnapshot();
    final changed = _assetsState.optimisticDeleteAsset(
      type: type,
      id: id,
      notify: false,
    );
    if (changed) {
      _recalculateAssetTotals(bindings.notifyListeners);
    } else if (type != 'cash' && type != 'other' && type != 'liability') {
      return const AssetActionResult.failure('不支持的资产类型');
    }

    AssetActionResult result;
    if (type == 'cash') {
      result = await _api.deleteCashAsset(id);
    } else if (type == 'other') {
      result = await _api.deleteOtherAsset(id);
    } else if (type == 'liability') {
      result = await _api.deleteLiability(id);
    } else {
      return const AssetActionResult.failure('不支持的资产类型');
    }
    if (!result.ok) {
      if (changed) {
        _restoreAssetSnapshot(snapshot, bindings.notifyListeners);
      }
      return result;
    }
    await bindings.triggerHomeRefresh(awaitRefresh);
    return const AssetActionResult.success();
  }

  Future<AssetActionResult> updateAsset({
    required String type,
    required int id,
    required String name,
    required double amount,
    String? curr,
    bool awaitRefresh = true,
    required AppAssetWriteBindings bindings,
  }) async {
    if (id <= 0) {
      return const AssetActionResult.failure('操作失败，请稍后重试');
    }
    final normalizedCurr = _assetsState.normalizeAssetCurrency(curr);
    final snapshot = _assetsState.captureAssetSnapshot();
    final changed = _assetsState.optimisticUpdateAsset(
      type: type,
      id: id,
      name: name,
      amount: amount,
      curr: normalizedCurr,
      notify: false,
    );
    if (changed) {
      _recalculateAssetTotals(bindings.notifyListeners);
    } else if (type != 'cash' && type != 'other' && type != 'liability') {
      return const AssetActionResult.failure('不支持的资产类型');
    }

    AssetActionResult result;
    if (type == 'cash') {
      result = await _api.updateCashAsset(
        id,
        name,
        amount,
        curr: normalizedCurr,
      );
    } else if (type == 'other') {
      result = await _api.updateOtherAsset(
        id,
        name,
        amount,
        curr: normalizedCurr,
      );
    } else if (type == 'liability') {
      result = await _api.updateLiability(
        id,
        name,
        amount,
        curr: normalizedCurr,
      );
    } else {
      return const AssetActionResult.failure('不支持的资产类型');
    }
    if (!result.ok) {
      if (changed) {
        _restoreAssetSnapshot(snapshot, bindings.notifyListeners);
      }
      return result;
    }
    await bindings.triggerHomeRefresh(awaitRefresh);
    return const AssetActionResult.success();
  }

  Future<AssetActionResult> adjustAsset({
    required String type,
    required int id,
    required String name,
    required double currentAmount,
    required String mode,
    required double delta,
    required String note,
    String? curr,
    double? targetAmount,
    bool awaitRefresh = false,
    required AppAssetWriteBindings bindings,
  }) async {
    if (id <= 0) {
      return const AssetActionResult.failure('操作失败，请稍后重试');
    }
    final normalizedCurr = _assetsState.normalizeAssetCurrency(curr);
    final result = await _api.adjustAsset(
      assetType: type,
      assetId: id,
      name: name,
      mode: mode,
      delta: delta,
      note: note,
      curr: normalizedCurr,
      targetAmount: targetAmount,
    );
    if (!result.ok) {
      return result;
    }

    final rawBalanceAfter = result.data?['balance_after'];
    final balanceAfter = rawBalanceAfter is num
        ? rawBalanceAfter.toDouble()
        : double.tryParse('${rawBalanceAfter ?? ''}') ??
              (mode == 'correct'
                  ? (targetAmount ?? currentAmount)
                  : (mode == 'add'
                        ? currentAmount + delta
                        : currentAmount - delta));
    final changed = type != 'cash' && balanceAfter.abs() <= 1e-9
        ? _assetsState.optimisticDeleteAsset(type: type, id: id, notify: false)
        : _assetsState.optimisticUpdateAsset(
            type: type,
            id: id,
            name: name,
            amount: balanceAfter,
            curr: normalizedCurr,
            notify: false,
          );
    if (changed) {
      _recalculateAssetTotals(bindings.notifyListeners);
    }
    await bindings.triggerHomeRefresh(awaitRefresh);
    return result;
  }

  void _restoreAssetSnapshot(AssetSnapshot snapshot, void Function() notify) {
    _assetsState.restoreAssetSnapshot(snapshot, notify: false);
    _homeTotalsState.recalculateAssetTotals(notify: false);
    notify();
  }

  void _recalculateAssetTotals(void Function() notify) {
    _homeTotalsState.recalculateAssetTotals(notify: false);
    notify();
  }
}
