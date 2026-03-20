const int kAssetNameChineseLimit = 10;
const String kAssetNameEllipsis = '....';

final RegExp _assetNameChinesePattern = RegExp(
  r'[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]',
);

String formatAssetDisplayName(
  String? rawName, {
  int maxChineseChars = kAssetNameChineseLimit,
  String ellipsis = kAssetNameEllipsis,
}) {
  final text = (rawName ?? '').trim();
  if (text.isEmpty || maxChineseChars <= 0) return text;

  final maxUnits = maxChineseChars * 2;
  var usedUnits = 0;
  var codeUnitOffset = 0;

  for (final rune in text.runes) {
    final char = String.fromCharCode(rune);
    final charUnits = _assetNameChinesePattern.hasMatch(char) ? 2 : 1;
    if (usedUnits + charUnits > maxUnits) {
      return '${text.substring(0, codeUnitOffset)}$ellipsis';
    }
    codeUnitOffset += char.length;
    usedUnits += charUnits;
  }

  return text;
}
