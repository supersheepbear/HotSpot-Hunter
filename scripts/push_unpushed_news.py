#!/usr/bin/env python3
# coding=utf-8
"""
手动推送未推送的重要新闻
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app.storage.local import LocalStorageBackend
from app.utils.notification_config_loader import load_notification_config
from app.utils.config_loader import load_ai_config
from app.utils.analysis_config_loader import load_analysis_config


def main():
    """主函数"""
    print("=" * 60)
    print("手动推送未推送的重要新闻")
    print("=" * 60)
    print()

    # 初始化存储后端
    storage = LocalStorageBackend(data_dir="output")

    # 获取当前月份的数据库连接
    date = datetime.now().strftime("%Y-%m-%d")
    conn = storage._get_connection(date)
    cursor = conn.cursor()

    # 查询未推送的 critical/high 级别新闻
    cursor.execute("""
        SELECT title, platform_id, importance, url, rank
        FROM news_items
        WHERE importance IN ('critical', 'high')
        AND (has_been_pushed = 0 OR has_been_pushed IS NULL)
        ORDER BY
            CASE importance
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
            END,
            rank ASC
    """)

    results = cursor.fetchall()

    if not results:
        print("✅ 没有未推送的重要新闻")
        return

    print(f"📰 发现 {len(results)} 条未推送的重要新闻")
    print()

    # 构建新闻列表
    important_news = []
    for title, platform_id, importance, url, rank in results:
        # 获取平台名称
        cursor.execute("SELECT name FROM platforms WHERE id = ?", (platform_id,))
        platform_result = cursor.fetchone()
        platform_name = platform_result[0] if platform_result else platform_id

        important_news.append({
            "title": title,
            "platform_id": platform_id,
            "platform_name": platform_name,
            "rank": rank or 0,
            "importance": importance,
            "url": url or "",
        })

    # 显示前 10 条
    print("前 10 条新闻：")
    for i, news in enumerate(important_news[:10], 1):
        print(f"{i}. [{news['importance']}] {news['title'][:60]}... ({news['platform_name']})")

    if len(important_news) > 10:
        print(f"... 还有 {len(important_news) - 10} 条")
    print()

    # 加载配置
    analysis_config = load_analysis_config()
    max_push = analysis_config.get("push", {}).get("max_push_per_run", 300)

    if len(important_news) > max_push:
        print(f"⚠️  新闻数量 ({len(important_news)}) 超过限制 ({max_push})，将只推送前 {max_push} 条")
        important_news = important_news[:max_push]

    # 推送新闻
    print(f"🚀 开始推送 {len(important_news)} 条新闻...")
    print()

    from app.notification.important_news_sender import send_important_news_to_all_channels

    notification_config = load_notification_config()
    ai_config = load_ai_config()

    results = send_important_news_to_all_channels(
        important_news=important_news,
        notification_config=notification_config,
        get_time_func=lambda: datetime.now(),
        split_content_func=None,
        ai_config=ai_config,
    )

    # 输出推送结果
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)

    print()
    print(f"📊 推送完成：{success_count}/{total_count} 个渠道成功")
    for channel, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {channel}")

    # 如果推送成功，标记为已推送
    if success_count > 0:
        from app.utils.helpers import normalize_title_for_dedup

        for news in important_news:
            title = news["title"]
            normalized_title = normalize_title_for_dedup(title)

            # 标记所有平台的相同标题新闻为已推送
            cursor.execute("""
                UPDATE news_items
                SET has_been_pushed = 1,
                    normalized_title = CASE
                        WHEN normalized_title = '' OR normalized_title IS NULL THEN ?
                        ELSE normalized_title
                    END
                WHERE normalized_title = ?
                OR (
                    (normalized_title = '' OR normalized_title IS NULL) AND
                    REPLACE(REPLACE(title, ' ', ''), '　', '') = REPLACE(REPLACE(?, ' ', ''), '　', '')
                )
            """, (normalized_title, normalized_title, title))

        conn.commit()
        print()
        print(f"✅ 已标记 {len(important_news)} 条新闻为已推送")

    conn.close()
    print()
    print("=" * 60)
    print("完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
