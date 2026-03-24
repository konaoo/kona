import '../models/asset.dart';
import '../models/asset_action_result.dart';
import '../services/api_service.dart';

class AppTradeState {
  final ApiService _api;

  AppTradeState({required ApiService api}) : _api = api;

  double convertAmountByCurrency({
    required double amount,
    required String fromCurr,
    required String toCurr,
    required double Function(String curr) rateForCurrency,
  }) {
    final fromRate = rateForCurrency(fromCurr);
    final toRate = rateForCurrency(toCurr);
    if (toRate <= 0) return amount * fromRate;
    return amount * fromRate / toRate;
  }

  AssetActionResult extractUndoInfo(AssetActionResult result) {
    if (!result.ok) return result;
    final data = result.data;
    if (data == null) return result;
    final token = data['undo_token']?.toString();
    final expire = data['undo_expire_at']?.toString();
    if (token == null || token.isEmpty || expire == null || expire.isEmpty) {
      return result;
    }
    return AssetActionResult(
      ok: true,
      data: {...data, 'undo_token': token, 'undo_expire_at': expire},
    );
  }

  Future<AssetActionResult> legacyBuyWithCashFallback({
    required String code,
    required String name,
    required double price,
    required double qty,
    required Asset cashAsset,
    required double cashDeductAmount,
  }) async {
    final buyResult = await _api.buyPortfolioAsset(code, price, qty);
    if (!buyResult.ok) return buyResult;

    final cashId = cashAsset.id;
    if (cashId == null || cashId <= 0) {
      await _api.sellPortfolioAsset(code, price, qty);
      return const AssetActionResult.failure('现金账户无效，请稍后重试');
    }

    final updateResult = await _api.updateCashAsset(
      cashId,
      cashAsset.name,
      cashAsset.amount - cashDeductAmount,
      curr: cashAsset.curr,
    );
    if (updateResult.ok) {
      return const AssetActionResult.success(
        data: {'code': 'LEGACY_BUY_WITH_CASH'},
      );
    }

    final rollbackSell = await _api.sellPortfolioAsset(code, price, qty);
    if (!rollbackSell.ok) {
      return const AssetActionResult.failure('现金扣减失败，且买入回滚失败，请手动核对账户和持仓');
    }
    return AssetActionResult.failure(updateResult.message ?? '现金扣减失败，已回滚买入');
  }

  Future<AssetActionResult> legacySellToCashFallback({
    required String code,
    required double price,
    required double qty,
    required Asset cashAsset,
    required double cashCreditAmount,
  }) async {
    final cashId = cashAsset.id;
    if (cashId == null || cashId <= 0) {
      return const AssetActionResult.failure('现金账户无效，请稍后重试');
    }

    final updateCashResult = await _api.updateCashAsset(
      cashId,
      cashAsset.name,
      cashAsset.amount + cashCreditAmount,
      curr: cashAsset.curr,
    );
    if (!updateCashResult.ok) {
      return updateCashResult;
    }

    final sellResult = await _api.sellPortfolioAsset(code, price, qty);
    if (sellResult.ok) {
      return const AssetActionResult.success(
        data: {'code': 'LEGACY_SELL_TO_CASH'},
      );
    }

    final rollbackCash = await _api.updateCashAsset(
      cashId,
      cashAsset.name,
      cashAsset.amount,
      curr: cashAsset.curr,
    );
    if (!rollbackCash.ok) {
      return const AssetActionResult.failure('卖出失败，且回款回滚失败，请手动核对现金账户');
    }
    return sellResult;
  }
}
