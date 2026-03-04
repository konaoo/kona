import 'dart:async';
import 'package:flutter/material.dart';
import '../config/theme.dart';

enum TopToastType { success, error, info }

class TopToast {
  static OverlayEntry? _entry;
  static Timer? _timer;

  static void showSuccess(BuildContext context, String message) {
    _show(
      context,
      message: message,
      type: TopToastType.success,
      duration: const Duration(milliseconds: 1800),
    );
  }

  static void showError(BuildContext context, String message) {
    _show(
      context,
      message: message,
      type: TopToastType.error,
      duration: const Duration(milliseconds: 2500),
    );
  }

  static void showInfo(BuildContext context, String message) {
    _show(
      context,
      message: message,
      type: TopToastType.info,
      duration: const Duration(milliseconds: 2000),
    );
  }

  static void showAction(
    BuildContext context, {
    required String message,
    required String actionLabel,
    required VoidCallback onAction,
    TopToastType type = TopToastType.info,
    Duration duration = const Duration(seconds: 15),
  }) {
    _show(
      context,
      message: message,
      type: type,
      duration: duration,
      actionLabel: actionLabel,
      onAction: () {
        _removeCurrent();
        onAction();
      },
    );
  }

  static void _show(
    BuildContext context, {
    required String message,
    required TopToastType type,
    required Duration duration,
    String? actionLabel,
    VoidCallback? onAction,
  }) {
    _timer?.cancel();
    _removeCurrent();

    final overlay = Overlay.of(context, rootOverlay: true);

    final Color bgColor;
    final IconData icon;
    switch (type) {
      case TopToastType.success:
        bgColor = AppTheme.success;
        icon = Icons.check_circle_outline;
        break;
      case TopToastType.error:
        bgColor = AppTheme.danger;
        icon = Icons.error_outline;
        break;
      case TopToastType.info:
        bgColor = AppTheme.accent;
        icon = Icons.info_outline;
        break;
    }

    _entry = OverlayEntry(
      builder: (ctx) {
        final topPadding = MediaQuery.of(ctx).padding.top;
        return Positioned(
          top: topPadding + 10,
          left: 16,
          right: 16,
          child: Material(
            color: Colors.transparent,
            child: _ToastCard(
              message: message,
              icon: icon,
              bgColor: bgColor,
              actionLabel: actionLabel,
              onAction: onAction,
            ),
          ),
        );
      },
    );

    overlay.insert(_entry!);
    _timer = Timer(duration, _removeCurrent);
  }

  static void _removeCurrent() {
    _entry?.remove();
    _entry = null;
    _timer?.cancel();
    _timer = null;
  }
}

class _ToastCard extends StatelessWidget {
  final String message;
  final IconData icon;
  final Color bgColor;
  final String? actionLabel;
  final VoidCallback? onAction;

  const _ToastCard({
    required this.message,
    required this.icon,
    required this.bgColor,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: bgColor.withValues(alpha: 0.95),
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.18),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          Icon(icon, color: Colors.white, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          if (actionLabel != null && actionLabel!.isNotEmpty && onAction != null)
            TextButton(
              onPressed: onAction,
              style: TextButton.styleFrom(
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 8),
                minimumSize: const Size(0, 32),
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              child: Text(
                actionLabel!,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
        ],
      ),
    );
  }
}
