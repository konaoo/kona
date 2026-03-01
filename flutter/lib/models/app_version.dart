class AppVersion {
  final String version;
  final int buildNumber;
  final String releaseNotes;
  final String downloadUrl;
  final bool forceUpdate;

  const AppVersion({
    required this.version,
    required this.buildNumber,
    required this.releaseNotes,
    required this.downloadUrl,
    required this.forceUpdate,
  });

  factory AppVersion.fromJson(Map<String, dynamic> json) {
    return AppVersion(
      version: json['version'] as String? ?? '1.0.0',
      buildNumber: json['buildNumber'] as int? ?? 1,
      releaseNotes: json['releaseNotes'] as String? ?? '更新内容',
      downloadUrl: json['downloadUrl'] as String? ?? '',
      forceUpdate: json['forceUpdate'] as bool? ?? false,
    );
  }
}
