"""
快讯页面与快讯接口路由
"""
from __future__ import annotations

from flask import Blueprint, jsonify, redirect, request


def create_news_blueprint(news_fetcher):
    bp = Blueprint("news_routes", __name__)

    @bp.route("/news")
    def news_page():
        """旧快讯页入口兼容跳转。"""
        return redirect("/app/news", code=302)

    @bp.route("/api/news/latest")
    def get_latest_news():
        """获取最新快讯 API。"""
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 30, type=int)
        since_id = request.args.get("since_id", "", type=str).strip()

        safe_page = max(1, page)
        safe_page_size = max(1, min(200, page_size))

        if since_id:
            items = news_fetcher.fetch_since(since_id=since_id, limit=safe_page_size)
            return jsonify(
                {
                    "items": items,
                    "page": 1,
                    "page_size": safe_page_size,
                    "has_more": False,
                    "since_id": since_id,
                    "latest_id": news_fetcher.latest_id(),
                }
            )

        data = news_fetcher.fetch_latest(page=safe_page, page_size=safe_page_size)
        return jsonify(
            {
                "items": data,
                "page": safe_page,
                "page_size": safe_page_size,
                "has_more": len(data) >= safe_page_size,
                "latest_id": news_fetcher.latest_id(),
            }
        )

    return bp
