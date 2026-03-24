import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class ProfileIcons {
  // Theme Toggle
  static Widget themeIcon() => _buildIcon(
        '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12 3v3M12 18v3M4.9 4.9l2.2 2.2M16.9 16.9l2.2 2.2M3 12h3M18 12h3M4.9 19.1l2.2-2.2M16.9 7.1l2.2-2.2" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="12" r="4.2" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        const Color(0xFF5B8DEF),
        const Color(0x595B8DEF),
        const [Color(0x475B8DEF), Color(0x1F4A7BE0)],
      );

  // Password
  static Widget passwordIcon() => _buildIcon(
        '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><rect height="10" rx="2.5" width="16" x="4" y="10" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M8 10V7.8a4 4 0 1 1 8 0V10" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="15" r="1.2" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        const Color(0xFFD4AF64),
        const Color(0x57D4AF64),
        const [Color(0x3BD4AF64), Color(0x1AD4AF64)],
      );

  // Biometrics
  static Widget biometricsIcon() => _buildIcon(
        '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12 3c4 0 7 3 7 7v2c0 5-3 9-7 9s-7-4-7-9v-2c0-4 3-7 7-7z" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M8 11h8M8.5 14.5h7" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        const Color(0xFF3ECF82),
        const Color(0x573ECF82),
        const [Color(0x383ECF82), Color(0x1A28B084)],
      );

  // Check Update
  static Widget updateIcon() => _buildIcon(
        '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M20 5v6h-6" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M4 19v-6h6" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M6.5 9.5A7 7 0 0 1 18 8l2 3" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M17.5 14.5A7 7 0 0 1 6 16l-2-3" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        const Color(0xFF6F88EC),
        const Color(0x576F88EC),
        const [Color(0x3D6F88EC), Color(0x1A5C70DC)],
      );

  // About Us
  static Widget aboutIcon() => _buildIcon(
        '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="9" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 10v6" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="7.5" r="1" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        const Color(0xFF888FA0),
        const Color(0x578CA3BC),
        const [Color(0x388CA3BC), Color(0x148CA3BC)],
      );

  // Group
  static Widget groupIcon() => _buildIcon(
        '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><circle cx="8" cy="10" r="2.5" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="16" cy="10" r="2.5" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M3.5 18c.8-2.4 2.5-3.8 4.5-3.8s3.7 1.4 4.5 3.8" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M11.5 18c.8-2.4 2.5-3.8 4.5-3.8s3.7 1.4 4.5 3.8" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        const Color(0xFF7FCD7C),
        const Color(0x577FCD7C),
        const [Color(0x3D7FCD7C), Color(0x145CB05A)],
      );

  static Widget _buildIcon(String svgString, Color iconColor, Color borderColor, List<Color> gradientColors) {
    return Container(
      width: 30,
      height: 30,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(9),
        border: Border.all(color: borderColor),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: gradientColors,
        ),
      ),
      alignment: Alignment.center,
      child: SvgPicture.string(
        svgString,
        width: 16,
        height: 16,
        colorFilter: ColorFilter.mode(iconColor, BlendMode.srcIn),
      ),
    );
  }
}
