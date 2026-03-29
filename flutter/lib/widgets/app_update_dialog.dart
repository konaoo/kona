import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../config/theme.dart';
import '../models/app_version.dart';

class AppUpdateDialog extends StatelessWidget {
  final AppVersion version;
  final VoidCallback onClose;
  final VoidCallback onUpdate;

  const AppUpdateDialog({
    super.key,
    required this.version,
    required this.onClose,
    required this.onUpdate,
  });

  @override
  Widget build(BuildContext context) {
    final isLight = AppTheme.isLight;
    final notes = _buildNoteItems(version.releaseNotes);

    return Dialog(
      backgroundColor: Colors.transparent,
      insetPadding: const EdgeInsets.symmetric(horizontal: 28, vertical: 24),
      child: Container(
        constraints: const BoxConstraints(maxWidth: 360),
        decoration: BoxDecoration(
          color: isLight ? Colors.white : const Color(0xFF1E1B2E),
          borderRadius: BorderRadius.circular(28),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: isLight ? 0.24 : 0.34),
              blurRadius: 48,
              offset: const Offset(0, 18),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _HeroSection(isLight: isLight, onClose: onClose),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 14, 24, 28),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    '发现新版本 v${version.version}',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: isLight ? const Color(0xFF111111) : Colors.white,
                      fontSize: 21,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    '为了更好的使用体验，建议升级到最新版本。',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: isLight
                          ? const Color(0xFF555555)
                          : const Color(0xFF9A94B8),
                      fontSize: 13.5,
                      height: 1.6,
                    ),
                  ),
                  const SizedBox(height: 18),
                  ...notes.map(
                    (item) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: _FeatureItem(text: item, isLight: isLight),
                    ),
                  ),
                  const SizedBox(height: 14),
                  _PrimaryButton(onTap: onUpdate),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  List<String> _buildNoteItems(String raw) {
    final normalized = raw
        .replaceAll('\r\n', '\n')
        .replaceAll('•', '\n')
        .replaceAll('·', '\n')
        .trim();
    if (normalized.isEmpty) {
      return const [
        '修复已知问题，优化使用体验',
        '提升页面交互和操作流畅度',
        '增强稳定性与兼容性',
      ];
    }
    final lines = normalized
        .split('\n')
        .map((line) => line.trim())
        .where((line) => line.isNotEmpty)
        .map((line) => line.replaceFirst(RegExp(r'^[0-9]+\.\s*'), ''))
        .toList(growable: false);
    if (lines.isEmpty) {
      return const [
        '修复已知问题，优化使用体验',
        '提升页面交互和操作流畅度',
        '增强稳定性与兼容性',
      ];
    }
    return lines;
  }
}

class _HeroSection extends StatelessWidget {
  final bool isLight;
  final VoidCallback onClose;

  const _HeroSection({required this.isLight, required this.onClose});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 230,
      child: ClipRRect(
        borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
        child: Stack(
          children: [
            Positioned.fill(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: isLight
                      ? const Color(0xFFC4AAFF)
                      : const Color(0xFF2A2040),
                ),
              ),
            ),
            const Positioned.fill(child: _StarsLayer()),
            Positioned(
              top: 18,
              right: 18,
              child: GestureDetector(
                onTap: onClose,
                child: Container(
                  width: 28,
                  height: 28,
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: isLight ? 0.26 : 0.10),
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: Colors.white.withValues(alpha: isLight ? 0.34 : 0.16),
                    ),
                  ),
                  child: const Icon(
                    Icons.close,
                    size: 15,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
            Positioned(
              left: 0,
              right: 0,
              bottom: 32,
              child: Center(
                child: SvgPicture.string(
                  _rocketSvg,
                  width: 120,
                  height: 130,
                ),
              ),
            ),
            Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              child: SvgPicture.string(
                isLight ? _cloudLightSvg : _cloudDarkSvg,
                fit: BoxFit.fill,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StarsLayer extends StatelessWidget {
  const _StarsLayer();

  static const _dots = <({double left, double top, double size, double opacity})>[
    (left: 0.10, top: 0.18, size: 2.0, opacity: 0.74),
    (left: 0.22, top: 0.55, size: 1.5, opacity: 0.66),
    (left: 0.42, top: 0.08, size: 2.5, opacity: 0.84),
    (left: 0.68, top: 0.30, size: 1.8, opacity: 0.68),
    (left: 0.80, top: 0.12, size: 2.0, opacity: 0.76),
    (left: 0.88, top: 0.50, size: 1.5, opacity: 0.58),
    (left: 0.14, top: 0.72, size: 1.8, opacity: 0.62),
    (left: 0.58, top: 0.60, size: 2.0, opacity: 0.80),
    (left: 0.35, top: 0.40, size: 1.5, opacity: 0.60),
    (left: 0.76, top: 0.72, size: 2.2, opacity: 0.82),
  ];

  static const _crosses = <({double left, double top})>[
    (left: 0.08, top: 0.42),
    (left: 0.82, top: 0.28),
    (left: 0.92, top: 0.58),
    (left: 0.50, top: 0.75),
  ];

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        return Stack(
          children: [
            for (final dot in _dots)
              Positioned(
                left: constraints.maxWidth * dot.left,
                top: constraints.maxHeight * dot.top,
                child: Container(
                  width: dot.size,
                  height: dot.size,
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: dot.opacity),
                    shape: BoxShape.circle,
                  ),
                ),
              ),
            for (final cross in _crosses)
              Positioned(
                left: constraints.maxWidth * cross.left,
                top: constraints.maxHeight * cross.top,
                child: const _CrossStar(),
              ),
          ],
        );
      },
    );
  }
}

class _CrossStar extends StatelessWidget {
  const _CrossStar();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 10,
      height: 10,
      child: Stack(
        children: [
          Align(
            child: Container(
              width: 2,
              height: 10,
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.86),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          Align(
            child: Container(
              width: 10,
              height: 2,
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.86),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _FeatureItem extends StatelessWidget {
  final String text;
  final bool isLight;

  const _FeatureItem({required this.text, required this.isLight});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(top: 1),
          child: Text(
            '•',
            style: TextStyle(
              color: isLight
                  ? const Color(0xFF7C3AED)
                  : const Color(0xFF9D6AFF),
              fontSize: 20,
              height: 1,
            ),
          ),
        ),
        const SizedBox(width: 9),
        Expanded(
          child: Text(
            text,
            style: TextStyle(
              color: isLight
                  ? const Color(0xFF444444)
                  : const Color(0xFFC8C2E0),
              fontSize: 13.5,
              height: 1.5,
            ),
          ),
        ),
      ],
    );
  }
}

class _PrimaryButton extends StatelessWidget {
  final VoidCallback onTap;

  const _PrimaryButton({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF7C3AED), Color(0xFF9D6AFF)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(50),
      ),
      child: ElevatedButton(
        onPressed: onTap,
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.transparent,
          shadowColor: Colors.transparent,
          elevation: 0,
          padding: const EdgeInsets.symmetric(vertical: 15),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(50),
          ),
        ),
        child: const Text(
          '立即升级',
          style: TextStyle(
            color: Colors.white,
            fontSize: 15.5,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}

const String _cloudLightSvg = '''
<svg viewBox="0 0 320 70" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
  <path d="M0 70 Q20 40 60 50 Q80 28 120 42 Q145 15 185 36 Q210 18 250 38 Q275 22 300 42 Q312 32 320 46 L320 70 Z" fill="#FFFFFF"/>
</svg>
''';

const String _cloudDarkSvg = '''
<svg viewBox="0 0 320 70" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
  <path d="M0 70 Q20 40 60 50 Q80 28 120 42 Q145 15 185 36 Q210 18 250 38 Q275 22 300 42 Q312 32 320 46 L320 70 Z" fill="#1E1B2E"/>
</svg>
''';

const String _rocketSvg = '''
<svg width="120" height="130" viewBox="0 0 120 130" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="upper" x1="30" y1="10" x2="90" y2="70" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#E0D0F8"/>
      <stop offset="100%" stop-color="#C0A0E8"/>
    </linearGradient>
    <linearGradient id="lower" x1="30" y1="55" x2="90" y2="105" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#8055C8"/>
      <stop offset="100%" stop-color="#6038B0"/>
    </linearGradient>
    <linearGradient id="shadow" x1="40" y1="0" x2="110" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#000000" stop-opacity="0"/>
      <stop offset="100%" stop-color="#280A50" stop-opacity="0.22"/>
    </linearGradient>
    <linearGradient id="fin" x1="60" y1="65" x2="60" y2="115" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#7050C0"/>
      <stop offset="100%" stop-color="#4828A0"/>
    </linearGradient>
    <radialGradient id="port" cx="40%" cy="35%" r="65%">
      <stop offset="0%" stop-color="#3A3A5C"/>
      <stop offset="50%" stop-color="#1A1030"/>
      <stop offset="100%" stop-color="#0A0820"/>
    </radialGradient>
    <radialGradient id="glint" cx="35%" cy="28%" r="60%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.9"/>
      <stop offset="60%" stop-color="#FFFFFF" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="ex" cx="50%" cy="10%" r="80%">
      <stop offset="0%" stop-color="#D8C8F8" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="#B89DE0" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <ellipse cx="60" cy="115" rx="22" ry="9" fill="url(#ex)"/>
  <ellipse cx="60" cy="122" rx="15" ry="6" fill="url(#ex)" opacity="0.6"/>
  <ellipse cx="48" cy="120" rx="10" ry="5" fill="url(#ex)" opacity="0.4"/>
  <ellipse cx="72" cy="120" rx="10" ry="5" fill="url(#ex)" opacity="0.4"/>
  <path d="M42 72 C32 78 18 95 20 115 C26 105 34 96 40 88 L44 80 Z" fill="url(#fin)"/>
  <path d="M40 88 C34 97 28 107 22 114" stroke="#FFFFFF" stroke-opacity="0.15" stroke-width="2" fill="none" stroke-linecap="round"/>
  <path d="M78 72 C88 78 102 95 100 115 C94 105 86 96 80 88 L76 80 Z" fill="url(#fin)"/>
  <path d="M80 88 C86 97 92 107 98 114" stroke="#000000" stroke-opacity="0.2" stroke-width="2" fill="none" stroke-linecap="round"/>
  <path d="M60 5 C46 5 34 20 32 38 L32 90 C32 98 45 105 60 105 C75 105 88 98 88 90 L88 38 C86 20 74 5 60 5 Z" fill="url(#upper)"/>
  <path d="M32 65 L32 90 C32 98 45 105 60 105 C75 105 88 98 88 90 L88 65 Z" fill="url(#lower)"/>
  <path d="M60 5 C46 5 34 20 32 38 L32 90 C32 98 45 105 60 105 C75 105 88 98 88 90 L88 38 C86 20 74 5 60 5 Z" fill="url(#shadow)"/>
  <path d="M36 30 Q33 55 34 82" stroke="#FFFFFF" stroke-opacity="0.45" stroke-width="4" fill="none" stroke-linecap="round"/>
  <path d="M40 18 Q36 38 36 58" stroke="#FFFFFF" stroke-opacity="0.22" stroke-width="2.5" fill="none" stroke-linecap="round"/>
  <rect x="32" y="63" width="56" height="5" fill="#5028A0" fill-opacity="0.25"/>
  <line x1="32" y1="65" x2="88" y2="65" stroke="#FFFFFF" stroke-opacity="0.12" stroke-width="1"/>
  <circle cx="60" cy="46" r="18" fill="#140832" fill-opacity="0.4"/>
  <circle cx="60" cy="46" r="17" fill="none" stroke="#C8B4FF" stroke-opacity="0.35" stroke-width="2"/>
  <circle cx="60" cy="46" r="15.5" fill="#0A051E" fill-opacity="0.5"/>
  <circle cx="60" cy="46" r="14" fill="url(#port)"/>
  <ellipse cx="54" cy="39" rx="9" ry="7" fill="url(#glint)"/>
  <ellipse cx="67" cy="54" rx="3.5" ry="2.5" fill="#FFFFFF" fill-opacity="0.25" transform="rotate(-20 67 54)"/>
  <circle cx="51" cy="38" r="2.5" fill="#FFFFFF" fill-opacity="0.6"/>
  <circle cx="60" cy="46" r="9" fill="none" stroke="#6450B4" stroke-opacity="0.4" stroke-width="1"/>
  <ellipse cx="60" cy="104" rx="14" ry="4" fill="#1E0A46" fill-opacity="0.6"/>
  <ellipse cx="60" cy="104" rx="9" ry="2.5" fill="#0F0528" fill-opacity="0.8"/>
</svg>
''';
