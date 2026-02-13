/// 资产操作统一结果（新增/编辑/删除）
class AssetActionResult {
  final bool ok;
  final String? message;
  final Map<String, dynamic>? data;

  const AssetActionResult({required this.ok, this.message, this.data});

  const AssetActionResult.success({this.data}) : ok = true, message = null;

  const AssetActionResult.failure(this.message, {this.data}) : ok = false;
}
