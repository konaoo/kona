#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLUTTER_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${FLUTTER_DIR}"

LOGO_PATH="assets/images/logo.png"
ABOUT_LIGHT_PATH="assets/images/about_logo_light.png"
ABOUT_DARK_PATH="assets/images/about_logo_dark_small.png"
SPLASH_PATH="android/app/src/main/res/drawable-nodpi/splash_screen.png"
ANDROID_12_STYLE="android/app/src/main/res/values-v31/styles.xml"
ANDROID_12_NIGHT_STYLE="android/app/src/main/res/values-night-v31/styles.xml"
IOS_PROJECT_FILE="ios/Runner.xcodeproj/project.pbxproj"
UNREFERENCED_IOS_ICONS=(
  "ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-50x50@1x.png"
  "ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-50x50@2x.png"
  "ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-57x57@1x.png"
  "ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-57x57@2x.png"
  "ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-72x72@1x.png"
  "ios/Runner/Assets.xcassets/AppIcon.appiconset/Icon-App-72x72@2x.png"
)

if [[ ! -f "${LOGO_PATH}" ]]; then
  echo "Missing ${LOGO_PATH}"
  exit 1
fi

if [[ ! -f "${SPLASH_PATH}" ]]; then
  echo "Missing ${SPLASH_PATH}"
  exit 1
fi

if [[ ! -f "${ANDROID_12_STYLE}" || ! -f "${ANDROID_12_NIGHT_STYLE}" ]]; then
  echo "Missing Android 12+ splash style files"
  exit 1
fi

echo "Syncing about page logos from ${LOGO_PATH}"
cp "${LOGO_PATH}" "${ABOUT_LIGHT_PATH}"
cp "${LOGO_PATH}" "${ABOUT_DARK_PATH}"

echo "Generating launcher icons from ${LOGO_PATH}"
flutter pub get
dart run flutter_launcher_icons

if [[ -f "${IOS_PROJECT_FILE}" ]]; then
  perl -0pi -e 's/ASSETCATALOG_COMPILER_GENERATE_SWIFT_ASSET_SYMBOL_EXTENSIONS = AppIcon;/ASSETCATALOG_COMPILER_GENERATE_SWIFT_ASSET_SYMBOL_EXTENSIONS = YES;/g' "${IOS_PROJECT_FILE}"
fi

for icon_path in "${UNREFERENCED_IOS_ICONS[@]}"; do
  rm -f "${icon_path}"
done

echo "Launcher icons generated."
echo "Splash image remains managed by ${SPLASH_PATH}."
echo "Android 12+ splash behavior is controlled by values-v31 styles and splash_transparent_icon.xml."
