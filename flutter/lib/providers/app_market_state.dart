import 'package:flutter/foundation.dart';

class ParsedMarketStatus {
  final Map<String, bool> open;
  final Map<String, bool> tradingDay;

  const ParsedMarketStatus({required this.open, required this.tradingDay});
}

class AppMarketState extends ChangeNotifier {
  static const Map<String, bool> fallbackMarketOpenStatus = {
    'a': false,
    'hk': false,
    'us': false,
    'fund': false,
  };
  static const Map<String, bool> fallbackMarketTradingDayStatus = {
    'a': false,
    'hk': false,
    'us': false,
    'fund': false,
  };

  Map<String, double> _exchangeRates = const {
    'USD': 7.25,
    'HKD': 0.93,
    'CNY': 1.0,
  };
  Map<String, bool> _marketOpenStatus = fallbackMarketOpenStatus;
  Map<String, bool> _marketTradingDayStatus = fallbackMarketTradingDayStatus;

  Map<String, double> get exchangeRates =>
      Map<String, double>.from(_exchangeRates);
  Map<String, bool> get marketOpenStatus =>
      Map<String, bool>.from(_marketOpenStatus);
  Map<String, bool> get marketTradingDayStatus =>
      Map<String, bool>.from(_marketTradingDayStatus);

  bool get hasAnyMarketOpen => _marketOpenStatus.values.any((open) => open);

  double rateForCurrency(String curr) {
    switch (curr.toUpperCase()) {
      case 'USD':
        return _exchangeRates['USD'] ?? 7.0;
      case 'HKD':
        return _exchangeRates['HKD'] ?? 0.9;
      default:
        return 1.0;
    }
  }

  double getCurrencyRate(String curr) => rateForCurrency(curr);

  double convertToCny(double amount, String curr) {
    return amount * rateForCurrency(curr);
  }

  String normalizeMarketKey(String? market) {
    final key = (market ?? '').trim().toLowerCase();
    switch (key) {
      case 'a':
      case 'hk':
      case 'us':
      case 'fund':
        return key;
      default:
        return 'a';
    }
  }

  bool isMarketOpen(String? market) {
    return _marketOpenStatus[normalizeMarketKey(market)] ?? false;
  }

  bool isMarketTradingDay(String? market) {
    return _marketTradingDayStatus[normalizeMarketKey(market)] ?? false;
  }

  bool asBool(dynamic value) {
    if (value is bool) return value;
    if (value is num) return value != 0;
    if (value is String) {
      final lower = value.trim().toLowerCase();
      return lower == '1' || lower == 'true' || lower == 'yes';
    }
    return false;
  }

  bool hasMarketStatusPayload(dynamic raw) {
    final map = _asMap(raw);
    if (map.isEmpty) return false;
    final markets = map['markets'];
    if (markets is Map && markets.isNotEmpty) return true;
    return map.containsKey('a') ||
        map.containsKey('hk') ||
        map.containsKey('us') ||
        map.containsKey('fund');
  }

  bool inferTradingDay({required bool open, required String reason}) {
    if (open) return true;
    switch (reason.trim().toLowerCase()) {
      case 'holiday_or_weekend':
        return false;
      case 'off_hours':
      case 'open_session':
        return true;
      case 'override':
        return false;
      default:
        return open;
    }
  }

  ParsedMarketStatus parseMarketStatus(
    dynamic payload, {
    Map<String, bool>? openFallback,
  }) {
    final root = _asMap(payload);
    final dynamic marketsRaw = root['markets'] ?? payload;
    final markets = marketsRaw is Map
        ? Map<String, dynamic>.from(marketsRaw)
        : <String, dynamic>{};

    bool parseOpenNode(String key) {
      if (markets.isNotEmpty && markets.containsKey(key)) {
        final node = markets[key];
        if (node is Map) {
          return asBool(node['open']);
        }
        return asBool(node);
      }
      return openFallback?[key] ?? fallbackMarketOpenStatus[key]!;
    }

    bool parseTradingDayNode(String key, bool open) {
      if (markets.isNotEmpty && markets.containsKey(key)) {
        final node = markets[key];
        if (node is Map) {
          if (node.containsKey('trading_day')) {
            return asBool(node['trading_day']);
          }
          final reason = '${node['reason'] ?? ''}';
          if (reason.trim().isNotEmpty) {
            return inferTradingDay(open: open, reason: reason);
          }
          return open;
        }
        return asBool(node);
      }
      return open;
    }

    final open = {
      'a': parseOpenNode('a'),
      'hk': parseOpenNode('hk'),
      'us': parseOpenNode('us'),
      'fund': parseOpenNode('fund'),
    };
    final tradingDay = {
      'a': parseTradingDayNode('a', open['a'] ?? false),
      'hk': parseTradingDayNode('hk', open['hk'] ?? false),
      'us': parseTradingDayNode('us', open['us'] ?? false),
      'fund': parseTradingDayNode('fund', open['fund'] ?? false),
    };
    return ParsedMarketStatus(open: open, tradingDay: tradingDay);
  }

  Map<String, bool> parseMarketOpenFallback(dynamic raw) {
    final status = _asMap(raw);
    if (status.isEmpty) {
      return Map<String, bool>.from(fallbackMarketOpenStatus);
    }
    return {
      'a': asBool(status['a']),
      'hk': asBool(status['hk']),
      'us': asBool(status['us']),
      'fund': asBool(status['fund']),
    };
  }

  void applyParsedStatus(ParsedMarketStatus status, {bool notify = true}) {
    _marketOpenStatus = status.open;
    _marketTradingDayStatus = status.tradingDay;
    if (notify) {
      notifyListeners();
    }
  }

  void applySyncMarketStatus(
    dynamic rawStatuses, {
    dynamic rawOpenFallback,
    bool notify = true,
  }) {
    if (!hasMarketStatusPayload(rawStatuses) &&
        !hasMarketStatusPayload(rawOpenFallback)) {
      return;
    }
    final parsed = parseMarketStatus(
      rawStatuses,
      openFallback: parseMarketOpenFallback(rawOpenFallback),
    );
    applyParsedStatus(parsed, notify: notify);
  }

  void updateExchangeRates(Map<String, dynamic> rates, {bool notify = true}) {
    _exchangeRates = {
      'USD': (rates['USD'] as num?)?.toDouble() ?? 7.25,
      'HKD': (rates['HKD'] as num?)?.toDouble() ?? 0.93,
      'CNY': 1.0,
    };
    if (notify) {
      notifyListeners();
    }
  }

  Map<String, dynamic> serializeMarketStatusForCache() {
    return <String, dynamic>{
      'markets': {
        'a': {
          'open': _marketOpenStatus['a'] ?? false,
          'trading_day': _marketTradingDayStatus['a'] ?? false,
        },
        'hk': {
          'open': _marketOpenStatus['hk'] ?? false,
          'trading_day': _marketTradingDayStatus['hk'] ?? false,
        },
        'us': {
          'open': _marketOpenStatus['us'] ?? false,
          'trading_day': _marketTradingDayStatus['us'] ?? false,
        },
        'fund': {
          'open': _marketOpenStatus['fund'] ?? false,
          'trading_day': _marketTradingDayStatus['fund'] ?? false,
        },
      },
    };
  }

  ParsedMarketStatus currentMarketStatusSnapshot() {
    return ParsedMarketStatus(
      open: Map<String, bool>.from(_marketOpenStatus),
      tradingDay: Map<String, bool>.from(_marketTradingDayStatus),
    );
  }

  void resetMarketStatus({bool notify = true}) {
    _marketOpenStatus = Map<String, bool>.from(fallbackMarketOpenStatus);
    _marketTradingDayStatus = Map<String, bool>.from(
      fallbackMarketTradingDayStatus,
    );
    if (notify) {
      notifyListeners();
    }
  }

  Map<String, dynamic> _asMap(dynamic value) {
    if (value is Map<String, dynamic>) return value;
    if (value is Map) return Map<String, dynamic>.from(value);
    return <String, dynamic>{};
  }
}
