# coding=utf-8
"""
AI新闻撰写器

将新闻列表整合成易读的摘要，替代传统的链接列表推送
"""

import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from app.ai.analyzer import AIAnalyzer
from app.utils.config_loader import load_ai_config, load_analysis_config


@dataclass
class NewsDigest:
    """新闻摘要数据类"""
    content: str  # 摘要正文
    topics: List[Dict[str, Any]]  # 按主题分组的内容
    source_links: List[Dict[str, str]]  # 来源链接列表
    news_count: int  # 处理的新闻数量
    success: bool  # 是否成功
    error: str  # 错误信息


class AINewsWriter:
    """AI新闻撰写器"""

    def __init__(
        self,
        ai_config: Optional[Dict[str, Any]] = None,
        writing_config: Optional[Dict[str, Any]] = None,
        get_time_func=None,
        debug: bool = False,
    ):
        """
        初始化AI新闻撰写器

        Args:
            ai_config: AI配置（API Key等）
            writing_config: 撰写配置
            get_time_func: 获取时间的函数
            debug: 是否开启调试模式
        """
        # 加载AI配置
        if ai_config is None:
            ai_config = load_ai_config()
        self.ai_config = ai_config

        # 加载撰写配置
        if writing_config is None:
            analysis_config = load_analysis_config()
            writing_config = analysis_config.get("ai_writing", {})
        self.writing_config = writing_config

        # 时间函数
        if get_time_func is None:
            from datetime import datetime
            get_time_func = lambda: datetime.now()
        self.get_time_func = get_time_func

        self.debug = debug

        # 创建AI分析器（复用其API调用能力）
        self.analyzer = AIAnalyzer(
            ai_config=ai_config,
            analysis_config={"LANGUAGE": "Chinese"},
            get_time_func=get_time_func,
            debug=debug,
        )

    def generate_digest(
        self,
        news_items: List[Dict[str, Any]],
        style: Optional[str] = None,
    ) -> NewsDigest:
        """
        生成新闻摘要

        Args:
            news_items: 新闻列表，每项包含 title, url, source, category 等
            style: 撰写风格，覆盖配置中的默认值

        Returns:
            NewsDigest 对象
        """
        if not news_items:
            return NewsDigest(
                content="暂无重要新闻",
                topics=[],
                source_links=[],
                news_count=0,
                success=True,
                error="",
            )

        # 获取配置
        style = style or self.writing_config.get("style", "news_anchor")
        max_news = self.writing_config.get("max_news_per_digest", 50)
        output_lang = self.writing_config.get("output_language", "zh")
        include_sources = self.writing_config.get("include_sources", True)
        group_by_topic = self.writing_config.get("group_by_topic", True)

        # 限制新闻数量
        news_items = news_items[:max_news]

        try:
            # 构建提示词
            prompt = self._build_prompt(news_items, style, output_lang, group_by_topic)

            # 调用AI API
            response = self.analyzer._call_ai_api(prompt)

            # 解析响应
            digest = self._parse_response(response, news_items, include_sources)

            return digest

        except Exception as e:
            error_msg = str(e)
            print(f"[AI撰写] 生成摘要失败: {error_msg}")
            return NewsDigest(
                content="",
                topics=[],
                source_links=[],
                news_count=len(news_items),
                success=False,
                error=error_msg,
            )

    def _build_prompt(
        self,
        news_items: List[Dict[str, Any]],
        style: str,
        output_lang: str,
        group_by_topic: bool,
    ) -> str:
        """构建AI提示词"""

        # 风格说明
        style_instructions = {
            "news_anchor": """你是一位专业的新闻主播，用流畅、专业的语言播报新闻。
- 语气正式但不生硬，像在做新闻联播
- 突出事件的重要性和影响
- 用简洁的过渡语串联不同主题""",

            "analyst": """你是一位资深的新闻分析师，提供深度解读。
- 不仅报道事实，还要分析背后的原因和影响
- 指出事件之间的关联性
- 提供专业的观点和预测""",

            "brief": """你是一位高效的信息整理专家，提供精炼的新闻简报。
- 用最少的字数传达最多的信息
- 每条新闻用一句话概括
- 按重要性排序，突出关键信息""",
        }

        style_desc = style_instructions.get(style, style_instructions["news_anchor"])

        # 语言说明
        lang_desc = "中文" if output_lang == "zh" else "English"

        # 构建新闻列表
        news_text = self._format_news_for_prompt(news_items)

        # 主题分组说明
        topic_instruction = ""
        if group_by_topic:
            topic_instruction = """
请按以下主题分组整理新闻（如果该主题有相关新闻）：
- 【中美关系】中美两国相关的政治、经济、外交新闻
- 【国际局势】其他国际关系、地缘政治、战争冲突
- 【经济金融】股市、货币政策、企业动态、投资并购
- 【科技前沿】AI、芯片、互联网、科技公司动态
- 【社会民生】国内社会新闻、民生政策、公共事件

每个主题用【主题名】作为标题，下面是该主题的新闻综述。
如果某个主题没有相关新闻，就跳过该主题。"""

        prompt = f"""{style_desc}

请用{lang_desc}撰写一份新闻摘要。
{topic_instruction}

要求：
1. 将相关的新闻整合在一起，用流畅的叙述串联
2. 去除重复信息（同一事件的多个来源只保留核心信息）
3. 突出因果关系和事件影响
4. 控制总字数在800-1200字之间
5. 不要使用链接，只输出纯文本摘要

以下是需要整理的新闻列表：

{news_text}

请直接输出摘要内容，不要加任何前缀说明。"""

        return prompt

    def _format_news_for_prompt(self, news_items: List[Dict[str, Any]]) -> str:
        """将新闻列表格式化为提示词中的文本"""
        lines = []
        for i, item in enumerate(news_items, 1):
            title = item.get("title", "")
            source = item.get("source", "")
            category = item.get("category", "")

            # 清理标题
            import re
            clean_title = re.sub(r'<[^>]+>', '', title)
            clean_title = ' '.join(clean_title.split())

            line = f"{i}. {clean_title}"
            if source:
                line += f" ({source})"
            if category:
                line += f" [分类: {category}]"
            lines.append(line)

        return "\n".join(lines)

    def _parse_response(
        self,
        response: str,
        news_items: List[Dict[str, Any]],
        include_sources: bool,
    ) -> NewsDigest:
        """解析AI响应"""

        content = response.strip()

        # 提取主题（如果有）
        topics = self._extract_topics(content)

        # 构建来源链接列表
        source_links = []
        if include_sources:
            for item in news_items:
                url = item.get("url", "")
                title = item.get("title", "")
                source = item.get("source", "")
                if url:
                    source_links.append({
                        "title": title[:50] + "..." if len(title) > 50 else title,
                        "url": url,
                        "source": source,
                    })

        return NewsDigest(
            content=content,
            topics=topics,
            source_links=source_links,
            news_count=len(news_items),
            success=True,
            error="",
        )

    def _extract_topics(self, content: str) -> List[Dict[str, Any]]:
        """从内容中提取主题分组"""
        import re

        topics = []
        # 匹配【主题名】格式
        pattern = r'【([^】]+)】'
        matches = list(re.finditer(pattern, content))

        for i, match in enumerate(matches):
            topic_name = match.group(1)
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            topic_content = content[start:end].strip()

            topics.append({
                "name": topic_name,
                "content": topic_content,
            })

        return topics


def generate_news_digest(
    news_items: List[Dict[str, Any]],
    ai_config: Optional[Dict[str, Any]] = None,
    writing_config: Optional[Dict[str, Any]] = None,
) -> NewsDigest:
    """
    便捷函数：生成新闻摘要

    Args:
        news_items: 新闻列表
        ai_config: AI配置
        writing_config: 撰写配置

    Returns:
        NewsDigest 对象
    """
    writer = AINewsWriter(
        ai_config=ai_config,
        writing_config=writing_config,
    )
    return writer.generate_digest(news_items)
