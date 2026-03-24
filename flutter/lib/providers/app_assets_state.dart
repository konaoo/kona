import 'package:flutter/foundation.dart';

import '../models/asset.dart';
import '../models/portfolio.dart';

class AssetSnapshot {
  final List<Asset> cashAssets;
  final List<Asset> otherAssets;
  final List<Asset> liabilities;

  const AssetSnapshot({
    required this.cashAssets,
    required this.otherAssets,
    required this.liabilities,
  });
}

class PortfolioSnapshot {
  final List<PortfolioItem> portfolio;

  const PortfolioSnapshot({required this.portfolio});
}

class AppAssetsState extends ChangeNotifier {
  List<PortfolioItem> _portfolio = <PortfolioItem>[];
  List<Asset> _cashAssets = <Asset>[];
  List<Asset> _otherAssets = <Asset>[];
  List<Asset> _liabilities = <Asset>[];
  int _nextTempAssetId = -1;

  List<PortfolioItem> get portfolio => _portfolio;
  List<Asset> get cashAssets => _cashAssets;
  List<Asset> get otherAssets => _otherAssets;
  List<Asset> get liabilities => _liabilities;

  void replacePortfolio(List<PortfolioItem> next, {bool notify = true}) {
    _portfolio = next;
    if (notify) {
      notifyListeners();
    }
  }

  void replaceCashAssets(List<Asset> next, {bool notify = true}) {
    _cashAssets = next;
    if (notify) {
      notifyListeners();
    }
  }

  void replaceOtherAssets(List<Asset> next, {bool notify = true}) {
    _otherAssets = next;
    if (notify) {
      notifyListeners();
    }
  }

  void replaceLiabilities(List<Asset> next, {bool notify = true}) {
    _liabilities = next;
    if (notify) {
      notifyListeners();
    }
  }

  void clearAll({bool notify = true}) {
    _portfolio = <PortfolioItem>[];
    _cashAssets = <Asset>[];
    _otherAssets = <Asset>[];
    _liabilities = <Asset>[];
    _nextTempAssetId = -1;
    if (notify) {
      notifyListeners();
    }
  }

  String normalizeAssetCurrency(String? curr) {
    final code = (curr ?? '').trim().toUpperCase();
    if (code == 'USD' || code == 'HKD') return code;
    return 'CNY';
  }

  AssetSnapshot captureAssetSnapshot() {
    return AssetSnapshot(
      cashAssets: List<Asset>.from(_cashAssets),
      otherAssets: List<Asset>.from(_otherAssets),
      liabilities: List<Asset>.from(_liabilities),
    );
  }

  void restoreAssetSnapshot(AssetSnapshot snapshot, {bool notify = true}) {
    _cashAssets = snapshot.cashAssets;
    _otherAssets = snapshot.otherAssets;
    _liabilities = snapshot.liabilities;
    if (notify) {
      notifyListeners();
    }
  }

  PortfolioSnapshot capturePortfolioSnapshot() {
    return PortfolioSnapshot(portfolio: List<PortfolioItem>.from(_portfolio));
  }

  void restorePortfolioSnapshot(
    PortfolioSnapshot snapshot, {
    bool notify = true,
  }) {
    _portfolio = snapshot.portfolio;
    if (notify) {
      notifyListeners();
    }
  }

  int portfolioIndexByCode(String code) {
    return _portfolio.indexWhere((item) => item.code == code);
  }

  bool optimisticAddAsset({
    required String type,
    required String name,
    required double amount,
    String? curr,
    bool notify = true,
  }) {
    final normalizedCurr = normalizeAssetCurrency(curr);
    final tempAsset = Asset(
      id: _nextTempAssetId--,
      name: name,
      amount: amount,
      curr: normalizedCurr,
    );

    switch (type) {
      case 'cash':
        _cashAssets = [..._cashAssets, tempAsset];
        break;
      case 'other':
        _otherAssets = [..._otherAssets, tempAsset];
        break;
      case 'liability':
        _liabilities = [..._liabilities, tempAsset];
        break;
      default:
        return false;
    }

    if (notify) {
      notifyListeners();
    }
    return true;
  }

  bool optimisticDeleteAsset({
    required String type,
    required int id,
    bool notify = true,
  }) {
    bool changed;
    switch (type) {
      case 'cash':
        final before = _cashAssets.length;
        _cashAssets = _cashAssets.where((item) => item.id != id).toList();
        changed = _cashAssets.length != before;
        break;
      case 'other':
        final before = _otherAssets.length;
        _otherAssets = _otherAssets.where((item) => item.id != id).toList();
        changed = _otherAssets.length != before;
        break;
      case 'liability':
        final before = _liabilities.length;
        _liabilities = _liabilities.where((item) => item.id != id).toList();
        changed = _liabilities.length != before;
        break;
      default:
        return false;
    }

    if (changed && notify) {
      notifyListeners();
    }
    return changed;
  }

  bool optimisticUpdateAsset({
    required String type,
    required int id,
    required String name,
    required double amount,
    String? curr,
    bool notify = true,
  }) {
    final normalizedCurr = normalizeAssetCurrency(curr);
    var updated = false;

    List<Asset> updateList(List<Asset> source) {
      return source.map((asset) {
        if (asset.id != id) return asset;
        updated = true;
        return Asset(
          id: asset.id,
          name: name,
          amount: amount,
          curr: normalizedCurr,
        );
      }).toList();
    }

    switch (type) {
      case 'cash':
        _cashAssets = updateList(_cashAssets);
        break;
      case 'other':
        _otherAssets = updateList(_otherAssets);
        break;
      case 'liability':
        _liabilities = updateList(_liabilities);
        break;
      default:
        return false;
    }

    if (updated && notify) {
      notifyListeners();
    }
    return updated;
  }

  bool optimisticAddInvestment({
    required String code,
    required String name,
    required double price,
    required double qty,
    required String normalizedCurr,
    String? assetType,
    bool notify = true,
  }) {
    final next = PortfolioItem(
      code: code,
      name: name,
      qty: qty,
      price: price,
      adjustment: 0,
      curr: normalizedCurr,
      assetType: (assetType == null || assetType.isEmpty) ? '' : assetType,
    );
    final index = portfolioIndexByCode(code);
    if (index >= 0) {
      final updated = List<PortfolioItem>.from(_portfolio);
      updated[index] = next;
      _portfolio = updated;
    } else {
      _portfolio = [..._portfolio, next];
    }

    if (notify) {
      notifyListeners();
    }
    return true;
  }

  bool optimisticBuyInvestment({
    required String code,
    required double price,
    required double qty,
    bool notify = true,
  }) {
    final index = portfolioIndexByCode(code);
    if (index < 0) return false;
    final old = _portfolio[index];
    final newQty = old.qty + qty;
    if (newQty <= 0) return false;
    final newPrice = (old.qty * old.price + qty * price) / newQty;
    final updated = List<PortfolioItem>.from(_portfolio);
    updated[index] = PortfolioItem(
      id: old.id,
      code: old.code,
      name: old.name,
      qty: newQty,
      price: newPrice,
      adjustment: old.adjustment,
      curr: old.curr,
      assetType: old.assetType,
    );
    _portfolio = updated;
    if (notify) {
      notifyListeners();
    }
    return true;
  }

  bool optimisticSellInvestment({
    required String code,
    required double price,
    required double qty,
    bool notify = true,
  }) {
    final index = portfolioIndexByCode(code);
    if (index < 0) return false;
    final old = _portfolio[index];
    if (qty > old.qty + 1e-6) return false;
    final pnl = (price - old.price) * qty;
    final newQty = old.qty - qty;
    final updated = List<PortfolioItem>.from(_portfolio);
    if (newQty < 0.001) {
      updated.removeAt(index);
    } else {
      updated[index] = PortfolioItem(
        id: old.id,
        code: old.code,
        name: old.name,
        qty: newQty,
        price: old.price,
        adjustment: old.adjustment + pnl,
        curr: old.curr,
        assetType: old.assetType,
      );
    }
    _portfolio = updated;
    if (notify) {
      notifyListeners();
    }
    return true;
  }

  bool optimisticModifyInvestment({
    required String code,
    required double qty,
    required double price,
    double? adjustment,
    bool notify = true,
  }) {
    final index = portfolioIndexByCode(code);
    if (index < 0) return false;
    final old = _portfolio[index];
    final updated = List<PortfolioItem>.from(_portfolio);
    updated[index] = PortfolioItem(
      id: old.id,
      code: old.code,
      name: old.name,
      qty: qty,
      price: price,
      adjustment: adjustment ?? old.adjustment,
      curr: old.curr,
      assetType: old.assetType,
    );
    _portfolio = updated;
    if (notify) {
      notifyListeners();
    }
    return true;
  }

  bool optimisticDeleteInvestment({required String code, bool notify = true}) {
    final before = _portfolio.length;
    _portfolio = _portfolio.where((item) => item.code != code).toList();
    final changed = _portfolio.length != before;
    if (changed && notify) {
      notifyListeners();
    }
    return changed;
  }

  bool optimisticAdjustCashAssetAmount({
    required int cashAssetId,
    required double deltaAmount,
    bool notify = true,
  }) {
    var updated = false;
    _cashAssets = _cashAssets.map((asset) {
      if (asset.id != cashAssetId) return asset;
      final nextAmount = asset.amount + deltaAmount;
      if (nextAmount < -1e-6) {
        return asset;
      }
      updated = true;
      return Asset(
        id: asset.id,
        name: asset.name,
        amount: nextAmount < 0 ? 0 : nextAmount,
        curr: asset.curr,
      );
    }).toList();

    if (updated && notify) {
      notifyListeners();
    }
    return updated;
  }
}
