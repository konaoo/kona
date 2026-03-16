import 'package:flutter/foundation.dart';

import '../models/asset.dart';
import 'app_assets_state.dart';
import 'app_market_state.dart';
import 'app_portfolio_view_state.dart';

class AppHomeTotalsState extends ChangeNotifier {
  final AppAssetsState _assetsState;
  final AppMarketState _marketState;
  final AppPortfolioViewState _portfolioViewState;

  double _totalAsset = 0;
  double _totalCash = 0;
  double _totalInvest = 0;
  double _totalOther = 0;
  double _totalLiability = 0;

  AppHomeTotalsState({
    required AppAssetsState assetsState,
    required AppMarketState marketState,
    required AppPortfolioViewState portfolioViewState,
  }) : _assetsState = assetsState,
       _marketState = marketState,
       _portfolioViewState = portfolioViewState;

  double get totalAsset => _totalAsset;
  double get totalCash => _totalCash;
  double get totalInvest => _totalInvest;
  double get totalOther => _totalOther;
  double get totalLiability => _totalLiability;

  double assetAmountToCny(Asset item, {bool useAbs = false}) {
    final amount = useAbs ? item.amount.abs() : item.amount;
    return _marketState.convertToCny(
      amount,
      _assetsState.normalizeAssetCurrency(item.curr),
    );
  }

  double sumAssetListToCny(List<Asset> items, {bool useAbs = false}) {
    double total = 0;
    for (final item in items) {
      total += assetAmountToCny(item, useAbs: useAbs);
    }
    return total;
  }

  void recalculateHomeTotals({bool notify = true}) {
    _totalCash = sumAssetListToCny(_assetsState.cashAssets);
    _totalOther = sumAssetListToCny(_assetsState.otherAssets);
    _totalLiability = sumAssetListToCny(_assetsState.liabilities, useAbs: true);
    _totalInvest = _portfolioViewState.investTotalMV;
    _totalAsset = _totalCash + _totalInvest + _totalOther - _totalLiability;
    if (notify) {
      notifyListeners();
    }
  }

  void recalculateAssetTotals({bool notify = true}) {
    _totalCash = sumAssetListToCny(_assetsState.cashAssets);
    _totalOther = sumAssetListToCny(_assetsState.otherAssets);
    _totalLiability = sumAssetListToCny(_assetsState.liabilities, useAbs: true);
    _totalAsset = _totalCash + _totalInvest + _totalOther - _totalLiability;
    if (notify) {
      notifyListeners();
    }
  }

  void recalculatePortfolioTotals({bool notify = true}) {
    _totalInvest = _portfolioViewState.investTotalMV;
    _totalAsset = _totalCash + _totalInvest + _totalOther - _totalLiability;
    if (notify) {
      notifyListeners();
    }
  }
}
