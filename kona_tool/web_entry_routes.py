"""
Web 门户 / SPA 入口 / 兼容跳转 / 测试页路由
"""
from __future__ import annotations

from flask import Blueprint


def create_web_entry_blueprint(
    *,
    index_handler,
    web_app_handler,
    web_admin_handler,
    web_assets_handler,
    assets_redirect_handler,
    test_redirect_handler,
    compare_page_handler,
    direct_test_page_handler,
):
    bp = Blueprint("web_entry_routes", __name__)

    @bp.route("/")
    def index():
        return index_handler()

    @bp.route("/app")
    @bp.route("/app/")
    @bp.route("/app/<path:asset_path>")
    def web_app_route(asset_path: str = ""):
        return web_app_handler(asset_path)

    @bp.route("/admin")
    @bp.route("/admin/")
    @bp.route("/admin/<path:asset_path>")
    def web_admin_route(asset_path: str = ""):
        return web_admin_handler(asset_path)

    @bp.route("/assets/<path:asset_path>")
    def web_assets(asset_path: str):
        return web_assets_handler(asset_path)

    @bp.route("/assets")
    def assets():
        return assets_redirect_handler()

    @bp.route("/test")
    def test_page():
        return test_redirect_handler()

    @bp.route("/compare")
    def compare_page():
        return compare_page_handler()

    @bp.route("/direct_test")
    def direct_test_page():
        return direct_test_page_handler()

    return bp
