import 'dart:async';

import '../models/asset_action_result.dart';
import '../services/api_service.dart';
import 'app_assets_state.dart';
import 'app_home_totals_state.dart';
import 'app_trade_state.dart';

class AppInvestmentWriteBindings {
  final void Function() notifyListeners;
  final Future<void> Function(bool awaitRefresh) triggerHomeRefresh;
  final String Function({required String code, String? curr})
  normalizeInvestmentCurrency;
  final double Function(String curr) rateForCurrency;

  const AppInvestmentWriteBindings({
    required this.notifyListeners,
    required this.triggerHomeRefresh,
    required this.normalizeInvestmentCurrency,
    required this.rateForCurrency,
  });
}

class AppInvestmentWriteState {
  final ApiService _api;
  final AppAssetsState _assetsState;
  final AppHomeTotalsState _homeTotalsState;
  final AppTradeState _tradeState;

  AppInvestmentWriteState({
    required ApiService api,
    required AppAssetsState assetsState,
    required AppHomeTotalsState homeTotalsState,
    required AppTradeState tradeState,
  }) : _api = api,
       _assetsState = assetsState,
       _homeTotalsState = homeTotalsState,
       _tradeState = tradeState;

  Future<AssetActionResult> addInvestment({
    required String code,
    required String name,
    required double price,
    required double qty,
    String? curr,
    String? assetType,
    bool awaitRefresh = true,
    required AppInvestmentWriteBindings bindings,
  }) async {
    if (price <= 0 || qty <= 0) {
      return const AssetActionResult.failure('请输入有效价格和数量');
    }
    final normalizedCurr = bindings.normalizeInvestmentCurrency(
      code: code,
      curr: curr,
    );
    final snapshot = _assetsState.capturePortfolioSnapshot();
    final changed = _assetsState.optimisticAddInvestment(
      code: code,
      name: name,
      price: price,
      qty: qty,
      normalizedCurr: normalizedCurr,
      assetType: assetType,
      notify: false,
    );
    if (!changed) {
      return const AssetActionResult.failure('添加失败，请稍后重试');
    }
    _recalculatePortfolioTotals(bindings.notifyListeners);

    final result = await _api.addPortfolioAsset(
      code,
      name,
      price,
      qty,
      curr: normalizedCurr,
      assetType: assetType,
    );
    if (!result.ok) {
      _restorePortfolioSnapshot(snapshot, bindings.notifyListeners);
      return result;
    }
    await bindings.triggerHomeRefresh(awaitRefresh);
    return result;
  }

  Future<AssetActionResult> buyInvestmentWithCash({
    required String code,
    required String name,
    required double price,
    required double qty,
    required int cashAssetId,
    String? curr,
    String? assetType,
    bool awaitRefresh = true,
    required AppInvestmentWriteBindings bindings,
  }) async {
    if (price <= 0 || qty <= 0) {
      return const AssetActionResult.failure('请输入有效价格和数量');
    }
    if (cashAssetId == -999) {
      if (_portfolioIndexByCode(code) >= 0) {
        return buyInvestment(
          code: code,
          price: price,
          qty: qty,
          awaitRefresh: awaitRefresh,
          bindings: bindings,
        );
      }
      return addInvestment(
        code: code,
        name: name,
        price: price,
        qty: qty,
        curr: curr,
        assetType: assetType,
        awaitRefresh: awaitRefresh,
        bindings: bindings,
      );
    }
    if (cashAssetId <= 0) {
      return const AssetActionResult.failure('请选择资金来源账户');
    }

    final cashIndex = _assetsState.cashAssets.indexWhere(
      (asset) => asset.id == cashAssetId,
    );
    if (cashIndex < 0) {
      return const AssetActionResult.failure('未找到资金来源账户');
    }
    final cashAsset = _assetsState.cashAssets[cashIndex];
    final normalizedCurr = bindings.normalizeInvestmentCurrency(
      code: code,
      curr: curr,
    );
    final normalizedCashCurr = _assetsState.normalizeAssetCurrency(
      cashAsset.curr,
    );
    final normalizedInvestCurr = _assetsState.normalizeAssetCurrency(
      normalizedCurr,
    );
    if (normalizedCashCurr != normalizedInvestCurr) {
      return AssetActionResult.failure(
        '资金账户币种不匹配：需要$normalizedInvestCurr账户',
        data: {
          'asset_curr': normalizedInvestCurr,
          'cash_curr': normalizedCashCurr,
        },
      );
    }
    final investAmount = price * qty;
    final cashDeductAmount = _tradeState.convertAmountByCurrency(
      amount: investAmount,
      fromCurr: normalizedCurr,
      toCurr: cashAsset.curr,
      rateForCurrency: bindings.rateForCurrency,
    );
    if (cashDeductAmount <= 0) {
      return const AssetActionResult.failure('扣款金额计算失败');
    }
    if (cashAsset.amount + 1e-6 < cashDeductAmount) {
      return AssetActionResult.failure(
        '账户余额不足：${cashAsset.name}',
        data: {
          'available': cashAsset.amount,
          'required': cashDeductAmount,
          'cash_curr': cashAsset.curr,
        },
      );
    }

    final assetSnapshot = _assetsState.captureAssetSnapshot();
    final portfolioSnapshot = _assetsState.capturePortfolioSnapshot();
    final hadHolding = _portfolioIndexByCode(code) >= 0;
    final portfolioChanged = hadHolding
        ? _assetsState.optimisticBuyInvestment(
            code: code,
            price: price,
            qty: qty,
            notify: false,
          )
        : _assetsState.optimisticAddInvestment(
            code: code,
            name: name,
            price: price,
            qty: qty,
            normalizedCurr: normalizedCurr,
            assetType: assetType,
            notify: false,
          );
    final cashChanged = _assetsState.optimisticAdjustCashAssetAmount(
      cashAssetId: cashAssetId,
      deltaAmount: -cashDeductAmount,
      notify: false,
    );
    if (!portfolioChanged || !cashChanged) {
      _restoreHomeSnapshots(
        assetSnapshot: assetSnapshot,
        portfolioSnapshot: portfolioSnapshot,
        notify: bindings.notifyListeners,
      );
      return const AssetActionResult.failure('买入失败，请稍后重试');
    }
    _recalculateHomeTotals(bindings.notifyListeners);

    final result = await _api.buyPortfolioAssetWithCash(
      code,
      name,
      price,
      qty,
      cashAssetId: cashAssetId,
      curr: normalizedCurr,
      assetType: assetType,
    );
    if (!result.ok) {
      final statusCode = result.data?['status_code'];
      if (statusCode == 404) {
        final fallbackResult = await _tradeState.legacyBuyWithCashFallback(
          code: code,
          name: name,
          price: price,
          qty: qty,
          cashAsset: cashAsset,
          cashDeductAmount: cashDeductAmount,
        );
        if (!fallbackResult.ok) {
          _restoreHomeSnapshots(
            assetSnapshot: assetSnapshot,
            portfolioSnapshot: portfolioSnapshot,
            notify: bindings.notifyListeners,
          );
          return fallbackResult;
        }
        await bindings.triggerHomeRefresh(awaitRefresh);
        return fallbackResult;
      }
      _restoreHomeSnapshots(
        assetSnapshot: assetSnapshot,
        portfolioSnapshot: portfolioSnapshot,
        notify: bindings.notifyListeners,
      );
      return result;
    }
    await bindings.triggerHomeRefresh(awaitRefresh);
    return _tradeState.extractUndoInfo(result);
  }

  Future<AssetActionResult> sellInvestmentToCash({
    required String code,
    required double price,
    required double qty,
    required int cashAssetId,
    bool awaitRefresh = true,
    required AppInvestmentWriteBindings bindings,
  }) async {
    if (cashAssetId == -999) {
      return sellInvestment(
        code: code,
        price: price,
        qty: qty,
        awaitRefresh: awaitRefresh,
        bindings: bindings,
      );
    }
    final index = _portfolioIndexByCode(code);
    if (index < 0) {
      return const AssetActionResult.failure('未找到该持仓');
    }
    if (qty <= 0 || price <= 0) {
      return const AssetActionResult.failure('请输入有效价格和数量');
    }
    final current = _assetsState.portfolio[index];
    if (qty > current.qty + 1e-6) {
      return const AssetActionResult.failure('卖出数量超过持仓数量');
    }
    if (cashAssetId <= 0) {
      return const AssetActionResult.failure('请选择回款账户');
    }

    final cashIndex = _assetsState.cashAssets.indexWhere(
      (asset) => asset.id == cashAssetId,
    );
    if (cashIndex < 0) {
      return const AssetActionResult.failure('未找到回款账户');
    }
    final cashAsset = _assetsState.cashAssets[cashIndex];
    final normalizedAssetCurr = _assetsState.normalizeAssetCurrency(
      current.curr,
    );
    final normalizedCashCurr = _assetsState.normalizeAssetCurrency(
      cashAsset.curr,
    );
    if (normalizedAssetCurr != normalizedCashCurr) {
      return AssetActionResult.failure(
        '回款账户币种不匹配：需要$normalizedAssetCurr账户',
        data: {
          'asset_curr': normalizedAssetCurr,
          'cash_curr': normalizedCashCurr,
        },
      );
    }
    final sellAmount = price * qty;
    final cashCreditAmount = _tradeState.convertAmountByCurrency(
      amount: sellAmount,
      fromCurr: current.curr,
      toCurr: cashAsset.curr,
      rateForCurrency: bindings.rateForCurrency,
    );
    if (cashCreditAmount <= 0) {
      return const AssetActionResult.failure('回款金额计算失败');
    }

    final assetSnapshot = _assetsState.captureAssetSnapshot();
    final portfolioSnapshot = _assetsState.capturePortfolioSnapshot();
    final portfolioChanged = _assetsState.optimisticSellInvestment(
      code: code,
      price: price,
      qty: qty,
      notify: false,
    );
    final cashChanged = _assetsState.optimisticAdjustCashAssetAmount(
      cashAssetId: cashAssetId,
      deltaAmount: cashCreditAmount,
      notify: false,
    );
    if (!portfolioChanged || !cashChanged) {
      _restoreHomeSnapshots(
        assetSnapshot: assetSnapshot,
        portfolioSnapshot: portfolioSnapshot,
        notify: bindings.notifyListeners,
      );
      return const AssetActionResult.failure('卖出失败，请稍后重试');
    }
    _recalculateHomeTotals(bindings.notifyListeners);

    final result = await _api.sellPortfolioAssetToCash(
      code,
      price,
      qty,
      cashAssetId: cashAssetId,
    );
    if (!result.ok) {
      final statusCode = result.data?['status_code'];
      if (statusCode == 404) {
        final fallbackResult = await _tradeState.legacySellToCashFallback(
          code: code,
          price: price,
          qty: qty,
          cashAsset: cashAsset,
          cashCreditAmount: cashCreditAmount,
        );
        if (!fallbackResult.ok) {
          _restoreHomeSnapshots(
            assetSnapshot: assetSnapshot,
            portfolioSnapshot: portfolioSnapshot,
            notify: bindings.notifyListeners,
          );
          return fallbackResult;
        }
        await bindings.triggerHomeRefresh(awaitRefresh);
        return fallbackResult;
      }
      _restoreHomeSnapshots(
        assetSnapshot: assetSnapshot,
        portfolioSnapshot: portfolioSnapshot,
        notify: bindings.notifyListeners,
      );
      return result;
    }

    await bindings.triggerHomeRefresh(awaitRefresh);
    return _tradeState.extractUndoInfo(result);
  }

  Future<AssetActionResult> buyInvestment({
    required String code,
    required double price,
    required double qty,
    bool awaitRefresh = true,
    required AppInvestmentWriteBindings bindings,
  }) async {
    if (price <= 0 || qty <= 0) {
      return const AssetActionResult.failure('请输入有效价格和数量');
    }
    if (_portfolioIndexByCode(code) < 0) {
      return const AssetActionResult.failure('未找到该持仓');
    }
    final snapshot = _assetsState.capturePortfolioSnapshot();
    final changed = _assetsState.optimisticBuyInvestment(
      code: code,
      price: price,
      qty: qty,
      notify: false,
    );
    if (!changed) {
      return const AssetActionResult.failure('买入失败，请稍后重试');
    }
    _recalculatePortfolioTotals(bindings.notifyListeners);

    final result = await _api.buyPortfolioAsset(code, price, qty);
    if (!result.ok) {
      _restorePortfolioSnapshot(snapshot, bindings.notifyListeners);
      return result;
    }
    await bindings.triggerHomeRefresh(awaitRefresh);
    return _tradeState.extractUndoInfo(result);
  }

  Future<AssetActionResult> sellInvestment({
    required String code,
    required double price,
    required double qty,
    bool awaitRefresh = true,
    required AppInvestmentWriteBindings bindings,
  }) async {
    if (price <= 0 || qty <= 0) {
      return const AssetActionResult.failure('请输入有效价格和数量');
    }
    final index = _portfolioIndexByCode(code);
    if (index < 0) {
      return const AssetActionResult.failure('未找到该持仓');
    }
    if (qty > _assetsState.portfolio[index].qty + 1e-6) {
      return const AssetActionResult.failure('卖出数量超过持仓数量');
    }
    final snapshot = _assetsState.capturePortfolioSnapshot();
    final changed = _assetsState.optimisticSellInvestment(
      code: code,
      price: price,
      qty: qty,
      notify: false,
    );
    if (!changed) {
      return const AssetActionResult.failure('卖出失败，请稍后重试');
    }
    _recalculatePortfolioTotals(bindings.notifyListeners);

    final result = await _api.sellPortfolioAsset(code, price, qty);
    if (!result.ok) {
      _restorePortfolioSnapshot(snapshot, bindings.notifyListeners);
      return result;
    }
    await bindings.triggerHomeRefresh(awaitRefresh);
    return _tradeState.extractUndoInfo(result);
  }

  Future<AssetActionResult> modifyInvestment({
    required String code,
    required double qty,
    required double price,
    required double adjustment,
    String? note,
    bool awaitRefresh = true,
    required AppInvestmentWriteBindings bindings,
  }) async {
    if (qty <= 0 || !price.isFinite || !adjustment.isFinite) {
      return const AssetActionResult.failure('请输入有效调整参数');
    }
    if (_portfolioIndexByCode(code) < 0) {
      return const AssetActionResult.failure('未找到该持仓');
    }
    final snapshot = _assetsState.capturePortfolioSnapshot();
    final changed = _assetsState.optimisticModifyInvestment(
      code: code,
      qty: qty,
      price: price,
      adjustment: adjustment,
      notify: false,
    );
    if (!changed) {
      return const AssetActionResult.failure('调整失败，请稍后重试');
    }
    _recalculatePortfolioTotals(bindings.notifyListeners);

    final result = await _api.modifyPortfolioAsset(
      code,
      qty,
      price,
      adjustment,
      note: note,
    );
    if (!result.ok) {
      _restorePortfolioSnapshot(snapshot, bindings.notifyListeners);
      return result;
    }
    await bindings.triggerHomeRefresh(awaitRefresh);
    return _tradeState.extractUndoInfo(result);
  }

  Future<AssetActionResult> addInvestmentAdjustmentEvent({
    required String code,
    required String eventType,
    required double amount,
    String? note,
    bool awaitRefresh = true,
    required AppInvestmentWriteBindings bindings,
  }) async {
    final index = _portfolioIndexByCode(code);
    if (index < 0) {
      return const AssetActionResult.failure('未找到该持仓');
    }
    if (!amount.isFinite || amount <= 0) {
      return const AssetActionResult.failure('请输入有效金额');
    }
    final cleanEventType = eventType.trim();
    if (cleanEventType != 'dividend' && cleanEventType != 'fee') {
      return const AssetActionResult.failure('不支持的修正类型');
    }
    final cleanNote = (note ?? '').trim();

    final current = _assetsState.portfolio[index];
    final nextAdjustment = cleanEventType == 'dividend'
        ? current.adjustment + amount
        : current.adjustment - amount;
    final snapshot = _assetsState.capturePortfolioSnapshot();
    final changed = _assetsState.optimisticModifyInvestment(
      code: code,
      qty: current.qty,
      price: current.price,
      adjustment: nextAdjustment,
      notify: false,
    );
    if (!changed) {
      return const AssetActionResult.failure('保存失败，请稍后重试');
    }
    _recalculatePortfolioTotals(bindings.notifyListeners);

    final result = await _api.addPortfolioAdjustmentEvent(
      code,
      cleanEventType,
      amount,
      note: cleanNote,
      curr: current.curr,
    );
    if (!result.ok) {
      _restorePortfolioSnapshot(snapshot, bindings.notifyListeners);
      return result;
    }
    await bindings.triggerHomeRefresh(awaitRefresh);
    return _tradeState.extractUndoInfo(result);
  }

  Future<AssetActionResult> undoInvestmentOperation(
    String undoToken, {
    required AppInvestmentWriteBindings bindings,
  }) async {
    if (undoToken.trim().isEmpty) {
      return const AssetActionResult.failure('撤销凭证无效');
    }
    final result = await _api.undoPortfolioOperation(undoToken.trim());
    if (!result.ok) {
      return result;
    }
    unawaited(bindings.triggerHomeRefresh(false));
    return result;
  }

  Future<AssetActionResult> deleteInvestment({
    required String code,
    bool corrective = false,
    bool awaitRefresh = true,
    required AppInvestmentWriteBindings bindings,
  }) async {
    final snapshot = _assetsState.capturePortfolioSnapshot();
    final changed = _assetsState.optimisticDeleteInvestment(
      code: code,
      notify: false,
    );
    if (!changed) {
      return const AssetActionResult.failure('未找到该持仓');
    }
    _recalculatePortfolioTotals(bindings.notifyListeners);

    var result = corrective
        ? await _api.deletePortfolioAssetCorrective(code)
        : await _api.deletePortfolioAsset(code);
    if (!result.ok && corrective) {
      result = await _api.deletePortfolioAsset(code);
    }
    if (!result.ok) {
      _restorePortfolioSnapshot(snapshot, bindings.notifyListeners);
      return result;
    }
    await bindings.triggerHomeRefresh(awaitRefresh);
    return const AssetActionResult.success();
  }

  int _portfolioIndexByCode(String code) {
    return _assetsState.portfolioIndexByCode(code);
  }

  void _restorePortfolioSnapshot(
    PortfolioSnapshot snapshot,
    void Function() notify,
  ) {
    _assetsState.restorePortfolioSnapshot(snapshot, notify: false);
    _homeTotalsState.recalculatePortfolioTotals(notify: false);
    notify();
  }

  void _restoreHomeSnapshots({
    required AssetSnapshot assetSnapshot,
    required PortfolioSnapshot portfolioSnapshot,
    required void Function() notify,
  }) {
    _assetsState.restoreAssetSnapshot(assetSnapshot, notify: false);
    _assetsState.restorePortfolioSnapshot(portfolioSnapshot, notify: false);
    _homeTotalsState.recalculateHomeTotals(notify: false);
    notify();
  }

  void _recalculatePortfolioTotals(void Function() notify) {
    _homeTotalsState.recalculatePortfolioTotals(notify: false);
    notify();
  }

  void _recalculateHomeTotals(void Function() notify) {
    _homeTotalsState.recalculateHomeTotals(notify: false);
    notify();
  }
}
