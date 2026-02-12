/// 资产操作统一结果（新增/编辑/删除）
class AssetActionResult {
  final bool ok;
  final String? message;

  const AssetActionResult({required this.ok, this.message});

  const AssetActionResult.success() : ok = true, message = null;

  const AssetActionResult.failure(this.message) : ok = false;
}
