# coding=utf-8
"""
重要新闻推送模块

当新增新闻的重要性评级为 critical 或 high 时，自动推送到所有配置的渠道
"""

from typing import List, Dict, Optional, Callable
from datetime import datetime


def _categorize_news(stats: List[Dict]) -> Dict[str, List[Dict]]:
    """
    根据关键词将新闻分类

    Args:
        stats: 新闻统计数据

    Returns:
        分类后的新闻字典
    """
    categories = {
        "政治外交": [],
        "经济金融": [],
        "科技创新": [],
        "社会民生": [],
        "国际关系": [],
        "自然灾害": [],
        "其他": []
    }

    # 关键词映射
    keyword_map = {
        "政治外交": ["政策", "外交", "政府", "国务院", "会议", "法律", "政治"],
        "经济金融": ["经济", "金融", "股市", "投资", "银行", "货币", "贸易", "GDP", "财报", "上市", "融资"],
        "科技创新": ["科技", "AI", "人工智能", "芯片", "技术", "互联网", "软件", "硬件", "创新", "研发"],
        "社会民生": ["社会", "教育", "医疗", "就业", "民生", "安全", "事故"],
        "国际关系": ["国际", "战争", "冲突", "制裁", "协议", "峰会"],
        "自然灾害": ["地震", "台风", "洪水", "灾害", "疫情", "火灾"]
    }

    for stat in stats:
        titles = stat.get("titles", [])
        word = stat.get("word", "")

        # 根据关键词判断分类
        categorized = False
        for category, keywords in keyword_map.items():
            if any(kw in word or any(kw in title.get("title", "") for title in titles) for kw in keywords):
                categories[category].extend(titles)
                categorized = True
                break

        # 如果没有匹配到分类，放入"其他"
        if not categorized:
            categories["其他"].extend(titles)

    # 移除空分类
    return {k: v for k, v in categories.items() if v}


def send_important_news_to_all_channels(
    important_news: List[Dict],
    notification_config: Dict,
    get_time_func: Optional[Callable] = None,
    split_content_func: Optional[Callable] = None,
) -> Dict[str, bool]:
    """
    推送重要新闻到所有配置的渠道
    
    Args:
        important_news: 重要新闻列表，每个元素包含：
            - title: 新闻标题
            - platform_name: 平台名称
            - platform_id: 平台ID
            - rank: 排名
            - importance: 重要性评级 ('critical' 或 'high')
            - url: 新闻链接（可选）
        notification_config: 推送通知配置字典
        get_time_func: 获取当前时间的函数
        split_content_func: 内容分批函数
    
    Returns:
        Dict[str, bool]: 每个渠道的发送结果
    """
    if not important_news:
        return {}
    
    # 获取当前时间
    if get_time_func:
        now = get_time_func()
    else:
        now = datetime.now()
    
    # 将重要新闻转换为 report_data 格式
    report_data = _convert_important_news_to_report_data(important_news)
    
    # 创建 NotificationDispatcher
    from app.notification import NotificationDispatcher
    
    # 如果没有提供 split_content_func，使用默认实现
    if split_content_func is None:
        # 导入内容渲染和分批函数
        from app.notification.renderer import (
            render_feishu_content,
            render_dingtalk_content,
        )
        from app.notification.batch import truncate_to_bytes

        def default_split_func(
            report_data: Dict,
            channel: str,
            update_info: Optional[Dict] = None,
            max_bytes: int = 4000,
            mode: str = "daily",
            **kwargs
        ) -> List[str]:
            """默认的内容分批函数"""
            # 根据渠道选择渲染函数
            if channel == "feishu":
                content = render_feishu_content(report_data, update_info, mode)
            elif channel == "dingtalk":
                content = render_dingtalk_content(report_data, update_info, mode)
            else:
                # 其他渠道使用简单的文本格式（Discord, Telegram等）
                content = ""

                # 处理 stats 中的重要新闻
                if report_data.get("stats"):
                    # stats 已经在 _convert_important_news_to_report_data 中按类别分组
                    # 直接使用，不需要再次调用 _categorize_news

                    # 统计总数
                    total_count = sum(len(stat.get("titles", [])) for stat in report_data["stats"])

                    # 标题
                    content += "━━━━━━━━━━━━━━\n"
                    content += f"📰 重要新闻 ({total_count}条)\n"
                    content += "━━━━━━━━━━━━━━\n\n"

                    # 按分类输出（stats 中每个元素就是一个类别）
                    for stat in report_data["stats"]:
                        category_name = stat.get("word", "")  # 例如 "🔴 政治外交"
                        news_list = stat.get("titles", [])

                        if not news_list:
                            continue

                        content += f"{category_name}\n"

                        for title_info in news_list:
                            title = title_info.get("title", "")
                            source = title_info.get("source_name", "")
                            url = title_info.get("url", "")

                            if url:
                                content += f"• {title} <{url}> | {source}\n"
                            else:
                                content += f"• {title} | {source}\n"

                        content += "\n"

                # 处理 new_titles（如果有）
                elif report_data.get("new_titles"):
                    content += "📰 重要新闻推送\n\n"
                    for platform_id, titles in report_data["new_titles"].items():
                        platform_name = report_data.get("id_to_name", {}).get(platform_id, platform_id)
                        content += f"【{platform_name}】\n"
                        for title_info in titles[:10]:
                            title = title_info.get("title", "")
                            content += f"• {title}\n"
                        content += "\n"

            # 分批处理
            if not content:
                return []

            content_bytes = content.encode('utf-8')
            if len(content_bytes) <= max_bytes:
                return [content]

            # 需要分批
            batches = []
            current_batch = ""
            current_size = 0

            for line in content.split('\n'):
                line_bytes = (line + '\n').encode('utf-8')
                line_size = len(line_bytes)

                if current_size + line_size > max_bytes:
                    if current_batch:
                        batches.append(current_batch)
                    current_batch = line + '\n'
                    current_size = line_size
                else:
                    current_batch += line + '\n'
                    current_size += line_size

            if current_batch:
                batches.append(current_batch)

            return batches

        split_content_func = default_split_func
    
    dispatcher = NotificationDispatcher(
        config=notification_config,
        get_time_func=get_time_func or (lambda: datetime.now()),
        split_content_func=split_content_func,
    )
    
    # 使用 dispatcher 推送到所有渠道
    report_type = f"重要新闻推送 ({len(important_news)} 条)"
    
    # 设置显示区域配置（只显示重要新闻，不显示其他内容）
    display_regions_config = {
        "HOTLIST": True,  # 显示热榜（重要新闻）
        "RSS": False,  # 不显示RSS
        "AI_ANALYSIS": False,  # 不显示AI分析
        "STANDALONE": False,  # 不显示独立展示区
    }
    
    # 更新配置中的显示区域设置（临时覆盖）
    original_display = notification_config.get("DISPLAY", {})
    notification_config["DISPLAY"] = {
        "REGIONS": display_regions_config
    }
    
    results = dispatcher.dispatch_all(
        report_data=report_data,
        report_type=report_type,
        mode="incremental",  # 增量模式
    )
    
    # 恢复原始配置
    notification_config["DISPLAY"] = original_display
    
    return results


def _convert_important_news_to_report_data(important_news: List[Dict]) -> Dict:
    """
    将重要新闻列表转换为 report_data 格式

    Args:
        important_news: 重要新闻列表

    Returns:
        report_data 格式的字典
    """
    # 关键词映射（用于分类）- 包含中英文关键词
    keyword_map = {
        "政治外交": [
            # 中文
            "政策", "外交", "政府", "国务院", "会议", "法律", "政治", "部长", "官员", "党",
            "防务", "预算", "税", "增值税", "立法", "议会", "选举", "投票", "民主党", "共和党",
            # 英文
            "government", "policy", "election", "vote", "congress", "senate", "minister"
        ],
        "经济金融": [
            # 中文
            "经济", "金融", "股市", "投资", "银行", "货币", "贸易", "GDP", "财报", "上市",
            "融资", "交付", "销量", "出口", "进口", "半导体", "订单", "市值", "估值",
            # 英文
            "economy", "finance", "stock", "market", "investment", "trade", "export", "import"
        ],
        "科技创新": [
            # 中文
            "科技", "AI", "人工智能", "芯片", "技术", "互联网", "软件", "硬件", "创新", "研发",
            "卫星", "数据", "算法", "模型", "开源", "GitHub", "microsoft", "anthropics", "BitNet",
            "歼-20", "战机", "无人机", "机器人", "自动驾驶", "光合", "能源",
            # 英文
            "AI", "technology", "software", "hardware", "algorithm", "model", "bot", "botnet",
            "Wikipedia", "WhatsApp", "GPS", "autonomous", "drone", "prompt injection", "social media"
        ],
        "社会民生": [
            # 中文
            "社会", "教育", "医疗", "就业", "民生", "安全", "事故", "诊疗", "中毒", "死亡",
            "入狱", "犯罪", "案件", "毒药", "附片", "救心丸",
            # 英文
            "health", "education", "safety", "dies", "death", "smallpox", "eradicate"
        ],
        "国际关系": [
            # 中文
            "国际", "战争", "冲突", "制裁", "协议", "峰会", "伊朗", "以色列", "加沙", "乌克兰",
            "俄", "美国", "欧盟", "印度", "谈判", "军演", "袭击", "停火",
            # 英文
            "international", "war", "conflict", "Iran", "Israel", "Gaza", "Ukraine", "Russia"
        ],
        "自然灾害": [
            # 中文
            "地震", "台风", "洪水", "灾害", "疫情", "火灾", "崩塌", "矿难",
            # 英文
            "disaster", "earthquake", "flood", "typhoon", "pandemic"
        ],
        "体育赛事": [
            # 中文
            "澳网", "冠军", "夺冠", "比赛", "运动", "球", "赛", "莱巴金娜", "萨巴伦卡",
            "大满贯", "决赛", "网球",
            # 英文
            "sport", "champion", "game", "match", "tennis", "Australian Open"
        ],
    }

    # 按类别分组新闻
    categorized_news = {category: [] for category in keyword_map.keys()}
    categorized_news["其他"] = []

    for news in important_news:
        title = news.get("title", "")
        categorized = False

        # 根据标题内容判断分类
        for category, keywords in keyword_map.items():
            if any(kw in title for kw in keywords):
                categorized_news[category].append(news)
                categorized = True
                break

        # 如果没有匹配到分类，放入"其他"
        if not categorized:
            categorized_news["其他"].append(news)

    # 构建 stats（按类别分组）
    stats = []

    # 类别图标映射
    category_icons = {
        "政治外交": "🔴",
        "经济金融": "💰",
        "科技创新": "💻",
        "社会民生": "👥",
        "国际关系": "🌍",
        "自然灾害": "⚠️",
        "体育赛事": "🏆",
        "其他": "📌"
    }

    for category, news_list in categorized_news.items():
        if not news_list:
            continue

        icon = category_icons.get(category, "📌")

        # 调试日志：显示每个类别的新闻数量
        print(f"[重要新闻分类] {icon} {category}: {len(news_list)} 条")
        for news in news_list:
            print(f"  - {news.get('title', '')[:50]}...")

        stats.append({
            "word": f"{icon} {category}",
            "count": len(news_list),
            "titles": [
                {
                    "title": news.get("title", ""),
                    "source_name": news.get("platform_name", ""),
                    "url": news.get("url", ""),
                    "mobile_url": news.get("url", ""),
                    "ranks": [news.get("rank", 0)],
                    "rank_threshold": 10,
                    "time_display": "",
                    "count": 1,
                    "is_new": True,
                }
                for news in news_list
            ],
        })

    # 构建 id_to_name 映射
    id_to_name = {}
    for news in important_news:
        platform_id = news.get("platform_id", "")
        platform_name = news.get("platform_name", "")
        if platform_id and platform_name:
            id_to_name[platform_id] = platform_name

    return {
        "stats": stats,
        "new_titles": [],
        "failed_ids": [],
        "id_to_name": id_to_name,
        "total_new_count": len(important_news),
    }


# 保留旧函数名以保持兼容性（已废弃，使用 send_important_news_to_all_channels）
def send_important_news_to_feishu(
    important_news: List[Dict],
    webhook_url: str,
    get_time_func=None,
) -> bool:
    """
    推送重要新闻到飞书（已废弃，请使用 send_important_news_to_all_channels）
    
    此函数保留仅为向后兼容，实际会调用新的多渠道推送函数
    """
    import requests
    
    if not important_news:
        return False
    
    if not webhook_url:
        print("[重要新闻推送] 未配置飞书 Webhook URL，跳过推送")
        return False
    
    # 获取当前时间
    if get_time_func:
        now = get_time_func()
    else:
        now = datetime.now()
    
    # 构建消息内容
    importance_labels = {
        "critical": "🔴 关键",
        "high": "🟠 重要",
    }
    
    content_parts = []
    content_parts.append("📰 重要新闻推送")
    content_parts.append(f"更新时间：{now.strftime('%Y-%m-%d %H:%M:%S')}")
    content_parts.append("")  # 空行
    
    for idx, news in enumerate(important_news, 1):
        title = news.get("title", "")
        platform_name = news.get("platform_name", "")
        rank = news.get("rank", 0)
        importance = news.get("importance", "")
        url = news.get("url", "")
        
        importance_label = importance_labels.get(importance, importance)
        
        # 构建新闻条目
        news_lines = []
        news_lines.append(f"{idx}. {importance_label} | {title}")
        
        # 添加平台和排名信息
        info_parts = []
        if platform_name:
            info_parts.append(f"平台: {platform_name}")
        if rank > 0:
            info_parts.append(f"排名: #{rank}")
        if info_parts:
            news_lines.append("   " + " | ".join(info_parts))
        
        # 添加链接
        if url:
            news_lines.append(f"   链接: {url}")
        
        content_parts.extend(news_lines)
        content_parts.append("")  # 空行分隔
    
    full_content = "\n".join(content_parts)
    
    # 构建飞书消息 payload
    payload = {
        "msg_type": "text",
        "content": {
            "text": full_content,
        },
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(webhook_url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                print(f"[重要新闻推送] 成功推送 {len(important_news)} 条重要新闻到飞书")
                return True
            else:
                error_msg = result.get("msg") or result.get("StatusMessage", "未知错误")
                print(f"[重要新闻推送] 推送失败，错误：{error_msg}")
                return False
        else:
            print(f"[重要新闻推送] 推送失败，状态码：{response.status_code}")
            print(f"[重要新闻推送] 响应内容：{response.text}")
            return False
    except Exception as e:
        print(f"[重要新闻推送] 推送出错：{e}")
        import traceback
        traceback.print_exc()
        return False
    """
    推送重要新闻到飞书
    
    Args:
        important_news: 重要新闻列表，每个元素包含：
            - title: 新闻标题
            - platform_name: 平台名称
            - rank: 排名
            - importance: 重要性评级 ('critical' 或 'high')
            - url: 新闻链接（可选）
        webhook_url: 飞书 Webhook URL
        get_time_func: 获取当前时间的函数
    
    Returns:
        bool: 发送是否成功
    """
    if not important_news:
        return False
    
    if not webhook_url:
        print("[重要新闻推送] 未配置飞书 Webhook URL，跳过推送")
        return False
    
    # 获取当前时间
    if get_time_func:
        now = get_time_func()
    else:
        now = datetime.now()
    
    # 构建消息内容
    importance_labels = {
        "critical": "🔴 关键",
        "high": "🟠 重要",
    }
    
    content_parts = []
    content_parts.append("📰 重要新闻推送")
    content_parts.append(f"更新时间：{now.strftime('%Y-%m-%d %H:%M:%S')}")
    content_parts.append("")  # 空行
    
    for idx, news in enumerate(important_news, 1):
        title = news.get("title", "")
        platform_name = news.get("platform_name", "")
        rank = news.get("rank", 0)
        importance = news.get("importance", "")
        url = news.get("url", "")
        
        importance_label = importance_labels.get(importance, importance)
        
        # 构建新闻条目
        news_lines = []
        news_lines.append(f"{idx}. {importance_label} | {title}")
        
        # 添加平台和排名信息
        info_parts = []
        if platform_name:
            info_parts.append(f"平台: {platform_name}")
        if rank > 0:
            info_parts.append(f"排名: #{rank}")
        if info_parts:
            news_lines.append("   " + " | ".join(info_parts))
        
        # 添加链接
        if url:
            news_lines.append(f"   链接: {url}")
        
        content_parts.extend(news_lines)
        content_parts.append("")  # 空行分隔
    
    full_content = "\n".join(content_parts)
    
    # 构建飞书消息 payload
    payload = {
        "msg_type": "text",
        "content": {
            "text": full_content,
        },
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(webhook_url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                print(f"[重要新闻推送] 成功推送 {len(important_news)} 条重要新闻到飞书")
                return True
            else:
                error_msg = result.get("msg") or result.get("StatusMessage", "未知错误")
                print(f"[重要新闻推送] 推送失败，错误：{error_msg}")
                return False
        else:
            print(f"[重要新闻推送] 推送失败，状态码：{response.status_code}")
            print(f"[重要新闻推送] 响应内容：{response.text}")
            return False
    except Exception as e:
        print(f"[重要新闻推送] 推送出错：{e}")
        import traceback
        traceback.print_exc()
        return False
