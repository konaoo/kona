"""
Web 门户 / SPA 入口 / 静态资源 / 兼容跳转处理函数
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from flask import jsonify, make_response, redirect, send_from_directory


def create_web_entry_handlers(
    *,
    web_app_dist_dir_getter: Callable[[], Path],
    web_admin_dist_dir_getter: Callable[[], Path],
    base_dir: Path,
):
    def _is_long_cache_asset(path: str) -> bool:
        normalized = (path or "").strip().lower()
        if not normalized:
            return False

        if normalized in {"index.html", "manifest.json"}:
            return False

        suffix = Path(normalized).suffix.lower()
        if suffix in {".html", ".json"}:
            return False
        return suffix in {".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".webp", ".ico", ".map", ".woff", ".woff2", ".ttf"}

    def _serve_web_asset(web_dir: Path, asset_path: str = ""):
        index_file = web_dir / "index.html"
        if not index_file.exists():
            return jsonify({"error": "Web bundle not found"}), 404

        normalized_path = (asset_path or "").strip().lstrip("/")
        target_file = web_dir / normalized_path if normalized_path else index_file

        if normalized_path and target_file.exists() and target_file.is_file():
            response = make_response(send_from_directory(str(web_dir), normalized_path))
            if _is_long_cache_asset(normalized_path):
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            else:
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            return response

        response = make_response(send_from_directory(str(web_dir), "index.html"))
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    def serve_index_route():
        return _serve_web_asset(web_app_dist_dir_getter())

    def serve_web_app_route(asset_path: str = ""):
        return _serve_web_asset(web_app_dist_dir_getter(), asset_path)

    def serve_web_admin_route(asset_path: str = ""):
        return _serve_web_asset(web_admin_dist_dir_getter(), asset_path)

    def serve_web_assets_route(asset_path: str):
        return _serve_web_asset(web_app_dist_dir_getter(), f"assets/{asset_path}")

    def redirect_assets_route():
        return redirect('/app/invest', code=302)

    def redirect_test_route():
        return redirect('/app', code=302)

    def serve_compare_page():
        with open(base_dir / 'static_compare.html', 'r', encoding='utf-8') as file:
            return file.read()

    def serve_direct_test_page():
        with open(base_dir / 'direct_test.html', 'r', encoding='utf-8') as file:
            return file.read()

    return {
        "index": serve_index_route,
        "web_app": serve_web_app_route,
        "web_admin": serve_web_admin_route,
        "web_assets": serve_web_assets_route,
        "assets_redirect": redirect_assets_route,
        "test_redirect": redirect_test_route,
        "compare_page": serve_compare_page,
        "direct_test_page": serve_direct_test_page,
    }
