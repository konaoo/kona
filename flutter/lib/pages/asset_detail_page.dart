import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import '../models/asset.dart';
import '../providers/app_state.dart';
import '../widgets/add_asset_dialog.dart';

/// 资产详情页面（现金/其他/负债统一样式）
class AssetDetailPage extends StatelessWidget {
  final String assetType; // cash | other | liability

  const AssetDetailPage({super.key, required this.assetType});

  static const _bg = Color(0xFF0D0E12);
  static const _surface2 = Color(0xFF1A1D25);
  static const _border = Color(0x0EFFFFFF);
  static const _text = Color(0xFFE4E5EA);
  static const _textMuted = Color(0xFF575D6E);
  static const _textSub = Color(0xFF8A92A3);
  static const _nameText = Color(0xFFEDF1FA);
  static const _amountText = Color(0xFFBCC4D3);
  static const _amountZero = Color(0xFFA9AFBD);
  static const _gold = Color(0xFFB79C66);

  TextStyle _dm({double? size, FontWeight? weight, Color? color}) {
    return GoogleFonts.dmSans(fontSize: size, fontWeight: weight, color: color);
  }

  TextStyle _mono({double? size, FontWeight? weight, Color? color}) {
    return GoogleFonts.jetBrainsMono(
      fontSize: size,
      fontWeight: weight,
      color: color,
    );
  }

  String _getTitle() {
    switch (assetType) {
      case 'cash':
        return '现金资产';
      case 'other':
        return '其他资产';
      case 'liability':
        return '我的负债';
      default:
        return '资产详情';
    }
  }

  List<Asset> _getAssets(AppState appState) {
    switch (assetType) {
      case 'cash':
        return appState.cashAssets;
      case 'other':
        return appState.otherAssets;
      case 'liability':
        return appState.liabilities;
      default:
        return [];
    }
  }

  double _bottomContentPadding(BuildContext context) {
    final safeBottom = MediaQuery.of(context).padding.bottom;
    const navBarHeight = 60.0;
    const fabRegion = 92.0;
    return 18 + navBarHeight + safeBottom + fabRegion;
  }

  ({String symbol, String unit, String value, bool isZero}) _displayAmount(
    Asset asset,
  ) {
    final curr = (asset.curr).toUpperCase();
    final absInt = math.max(0, asset.amount.abs().floor());
    final displayValue = _formatWithThousands(absInt);

    switch (curr) {
      case 'USD':
        return (
          symbol: r'$',
          unit: '美元',
          value: displayValue,
          isZero: absInt == 0,
        );
      case 'HKD':
        return (
          symbol: 'HK\$',
          unit: '港币',
          value: displayValue,
          isZero: absInt == 0,
        );
      case 'CNY':
      default:
        return (
          symbol: '¥',
          unit: '人民币',
          value: displayValue,
          isZero: absInt == 0,
        );
    }
  }

  String _formatWithThousands(int value) {
    final raw = value.toString();
    if (raw.length <= 3) return raw;
    final buffer = StringBuffer();
    for (var i = 0; i < raw.length; i++) {
      final posFromEnd = raw.length - i;
      buffer.write(raw[i]);
      if (posFromEnd > 1 && posFromEnd % 3 == 1) {
        buffer.write(',');
      }
    }
    return buffer.toString();
  }

  IconData _iconForAsset(Asset asset) {
    final text = asset.name.toLowerCase();
    final curr = asset.curr.toUpperCase();
    if (text.contains('银行')) return Icons.account_balance_outlined;
    if (text.contains('卡')) return Icons.credit_card_outlined;
    if (curr == 'USD' || text.contains('美元')) {
      return Icons.account_balance_wallet_outlined;
    }
    if (text.contains('现金') || text.contains('备用金')) {
      return Icons.payments_outlined;
    }
    return Icons.account_balance_outlined;
  }

  Widget _buildHeader(BuildContext context, int count) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 18, 18, 14),
      child: Row(
        children: [
          Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: () => Navigator.of(context).pop(),
              borderRadius: BorderRadius.circular(10),
              child: Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: _surface2,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: _border),
                ),
                alignment: Alignment.center,
                child: const Icon(
                  Icons.arrow_back_ios_new_rounded,
                  size: 16,
                  color: _text,
                ),
              ),
            ),
          ),
          Expanded(
            child: Center(
              child: Text(
                _getTitle(),
                style: _dm(size: 16, weight: FontWeight.w600, color: _text),
              ),
            ),
          ),
          SizedBox(
            width: 66,
            child: Align(
              alignment: Alignment.centerRight,
              child: Text(
                '$count 个账户',
                style: _dm(size: 11, color: _textMuted),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmpty() {
    return Container(
      margin: const EdgeInsets.only(top: 10),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 28),
      decoration: BoxDecoration(
        color: const Color(0xA81A1D25),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: const Color(0x24FFFFFF),
          style: BorderStyle.solid,
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            '暂无${_getTitle()}',
            style: _dm(size: 16, weight: FontWeight.w600, color: _text),
          ),
          const SizedBox(height: 6),
          Text('点击右下角 + 添加第一条资产', style: _dm(size: 12, color: _textMuted)),
        ],
      ),
    );
  }

  Widget _buildAssetCard(BuildContext context, Asset asset) {
    final amount = _displayAmount(asset);
    final amountValueColor = amount.isZero ? _amountZero : _amountText;
    final amountSymbolColor = amount.isZero ? _amountZero : _gold;
    final amountUnitColor = amount.isZero ? const Color(0xFF838A9A) : _textSub;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: () => _showEditDialog(context, asset),
        child: Ink(
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [Color(0xF51A1D25), Color(0xFA171A22)],
            ),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: const Color(0x0EFFFFFF)),
            boxShadow: const [
              BoxShadow(
                color: Color(0x47000000),
                blurRadius: 18,
                offset: Offset(0, 8),
              ),
            ],
          ),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(11),
                    border: Border.all(color: const Color(0x295B8DEF)),
                    gradient: const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [Color(0x245B8DEF), Color(0x0F4A7BE0)],
                    ),
                  ),
                  alignment: Alignment.center,
                  child: Icon(
                    _iconForAsset(asset),
                    size: 18,
                    color: const Color(0xFF739BF0),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        asset.name,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: _dm(
                          size: 15,
                          weight: FontWeight.w700,
                          color: _nameText,
                        ),
                      ),
                      const SizedBox(height: 5),
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          Text(
                            amount.symbol,
                            style: _mono(
                              size: 12,
                              weight: FontWeight.w500,
                              color: amountSymbolColor,
                            ),
                          ),
                          const SizedBox(width: 5),
                          Flexible(
                            child: Text(
                              amount.value,
                              overflow: TextOverflow.ellipsis,
                              style: _mono(
                                size: 13,
                                weight: FontWeight.w500,
                                color: amountValueColor,
                              ),
                            ),
                          ),
                          const SizedBox(width: 5),
                          Text(
                            amount.unit,
                            style: _dm(
                              size: 9,
                              weight: FontWeight.w500,
                              color: amountUnitColor,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _showAddDialog(BuildContext context) {
    showDialog(
      context: context,
      barrierDismissible: false,
      barrierColor: const Color(0x80000000),
      builder: (_) =>
          AddAssetDialog(fixedAssetType: assetType, hostContext: context),
    );
  }

  void _showEditDialog(BuildContext context, Asset asset) {
    showDialog(
      context: context,
      barrierDismissible: false,
      barrierColor: const Color(0x80000000),
      builder: (_) => AddAssetDialog(
        fixedAssetType: assetType,
        editingAsset: asset,
        hostContext: context,
        lockCashCurrency: true,
        allowDeleteInEdit: true,
        dialogTitleOverride: '编辑资产',
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      body: Container(
        decoration: const BoxDecoration(
          gradient: RadialGradient(
            center: Alignment(0.8, -1.1),
            radius: 1.1,
            colors: [Color(0x1F5B8DEF), Color(0x000D0E12)],
          ),
        ),
        child: SafeArea(
          bottom: false,
          child: Consumer<AppState>(
            builder: (context, appState, _) {
              final assets = _getAssets(appState);
              return Column(
                children: [
                  _buildHeader(context, assets.length),
                  Expanded(
                    child: ListView.separated(
                      padding: EdgeInsets.fromLTRB(
                        14,
                        8,
                        14,
                        _bottomContentPadding(context),
                      ),
                      itemCount: assets.isEmpty ? 1 : assets.length,
                      separatorBuilder: (_, index) =>
                          const SizedBox(height: 10),
                      itemBuilder: (context, index) {
                        if (assets.isEmpty) {
                          return _buildEmpty();
                        }
                        return _buildAssetCard(context, assets[index]);
                      },
                    ),
                  ),
                ],
              );
            },
          ),
        ),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.endFloat,
      floatingActionButton: FloatingActionButton.small(
        heroTag: 'add_asset_detail_$assetType',
        onPressed: () => _showAddDialog(context),
        backgroundColor: const Color(0xFF5B8DEF),
        child: const Icon(Icons.add, size: 20, color: Colors.white),
      ),
    );
  }
}
