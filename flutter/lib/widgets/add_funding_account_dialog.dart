import 'package:flutter/material.dart';

import 'add_asset_dialog.dart';

Future<int?> showAddFundingAccountDialog({
  required BuildContext context,
  BuildContext? hostContext,
  String initialCurrency = 'CNY',
  bool lockCurrency = false,
  bool forceAssetTypeCash = false,
}) {
  final effectiveLock = lockCurrency || forceAssetTypeCash;
  final allowedTypes = forceAssetTypeCash
      ? <String>{'cash'}
      : <String>{'cash', 'other'};

  return showGeneralDialog<int>(
    context: context,
    barrierDismissible: true,
    barrierLabel: '添加资金账户',
    barrierColor: const Color(0xA6000000),
    transitionDuration: const Duration(milliseconds: 220),
    pageBuilder: (_, __, ___) {
      return AddAssetDialog(
        hostContext: hostContext ?? context,
        fixedAssetType: forceAssetTypeCash ? 'cash' : null,
        allowedAssetTypes: allowedTypes,
        initialCashCurrency: initialCurrency,
        lockCashCurrency: effectiveLock,
        returnCreatedAssetId: true,
      );
    },
    transitionBuilder: (_, animation, __, child) {
      final curved = CurvedAnimation(
        parent: animation,
        curve: Curves.easeOutBack,
      );
      return FadeTransition(
        opacity: animation,
        child: ScaleTransition(
          scale: Tween<double>(begin: 0.93, end: 1.0).animate(curved),
          child: child,
        ),
      );
    },
  );
}
