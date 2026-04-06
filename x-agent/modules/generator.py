"""
generator.py - 内容生成模块

【V0 Final】此版本为生产级开源版本

功能：
- A类推文生成
- B类视频脚本
- C类智能评论
- Niche语气注入

版本：V0 Final
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional

from .llm_router import LLMRouter


class ContentGenerator:
    """内容生成器"""

    def __init__(self, llm_router: LLMRouter, niche: str = "general"):
        """
        初始化生成器

        Args:
            llm_router: LLM 路由实例
            niche: Niche 领域
        """
        self.llm_router = llm_router
        self.niche = niche
        self.voice_style = self._load_niche_voice(niche)

    def _load_niche_voice(self, niche: str) -> str:
        """
        加载 Niche 语气文件

        Args:
            niche: Niche 名称

        Returns:
            str: 语气文件内容
        """
        voice_file = Path(__file__).parent.parent / "niche_voices" / f"{niche}.txt"

        if voice_file.exists():
            return voice_file.read_text(encoding="utf-8")
        else:
            # 使用通用语气
            return f"Niche: {niche}\nTone: Professional and engaging"

    async def _generate_with_fallback(
        self, prompt: str, system: str, validator_fn, mock_fn, *mock_args
    ) -> Dict:
        """通用生成流程：调用 LLM → 验证 → fallback"""
        try:
            result = await self.llm_router.generate_json(prompt, system=system)
            return validator_fn(result)
        except Exception:
            return mock_fn(*mock_args)

    async def generate_type_a(
        self, topic: str, summary: str = "", source: str = "", score: float = 50.0
    ) -> Dict:
        """
        生成 A 类推文（3 条备选）

        Args:
            topic: 话题
            summary: 热点摘要
            source: 来源
            score: 热点评分

        Returns:
            Dict: 包含 3 条推文的 JSON
        """
        prompt = self._build_type_a_prompt(topic, summary, source, score)
        system = f"""你是 X 智能运营助手，专门为 {self.niche} 领域创作高质量的推文内容。
当前 Niche 的语气风格：
{self.voice_style}

请生成 3 条不同角度的推文，每条控制在 280 字符以内，包含 2-3 个相关 hashtag。
严格按照 JSON 格式返回。"""
        return await self._generate_with_fallback(
            prompt, system, self._validate_type_a_result, self._mock_type_a_result, topic
        )

    def _build_type_a_prompt(self, topic: str, summary: str, source: str, score: float) -> str:
        """构建 A 类生成 Prompt"""
        return f"""请根据以下热点话题，生成 3 条不同角度的推文：

话题：{topic}
热点来源：{source}
热点评分：{score}/100
相关信息：{summary}

生成要求：
1. 每条推文控制在 280 字符以内
2. 包含 2-3 个相关 hashtag
3. 3 条推文角度分别为：
   - Hot take（独特观点）
   - Data/Research（数据驱动）
   - Interactive Poll（互动投票）

请严格按照以下 JSON 格式返回：
{{
  "tweets": [
    {{
      "angle": "Hot take",
      "content": "推文内容...",
      "hashtags": ["#tag1", "#tag2"]
    }},
    {{
      "angle": "Data/Research",
      "content": "推文内容...",
      "hashtags": ["#tag1", "#tag2"]
    }},
    {{
      "angle": "Interactive Poll",
      "content": "推文内容...",
      "hashtags": ["#tag1", "#tag2"]
    }}
  ],
  "media_suggestion": "keyword1, keyword2, keyword3"
}}"""

    def _validate_type_a_result(self, result: Dict) -> Dict:
        """验证 A 类生成结果"""
        if not isinstance(result, dict):
            return self._mock_type_a_result("Unknown")

        if "tweets" not in result or not isinstance(result["tweets"], list):
            return self._mock_type_a_result("Unknown")

        return result

    def _mock_type_a_result(self, topic: str) -> Dict:
        """模拟 A 类结果"""
        return {
            "tweets": [
                {
                    "angle": "Hot take",
                    "content": f"Unpopular opinion about {topic}: it's more relevant than you think. 🤔",
                    "hashtags": ["#HotTake", "#Trending"],
                },
                {
                    "angle": "Data/Research",
                    "content": f"Data shows {topic} is gaining traction. Here's what the numbers say 📊",
                    "hashtags": ["#Data", "#Research"],
                },
                {
                    "angle": "Interactive Poll",
                    "content": f"Quick poll: What's your take on {topic}? Vote below! 👇",
                    "hashtags": ["#Poll", "#Community"],
                },
            ],
            "media_suggestion": f"{topic}, trending, discussion",
        }

    async def generate_type_b(
        self, topic: str, summary: str = "", source: str = "", score: float = 50.0
    ) -> Dict:
        """
        生成 B 类视频脚本（30 秒分镜）

        Args:
            topic: 话题
            summary: 热点摘要
            source: 来源
            score: 热点评分

        Returns:
            Dict: 视频脚本 JSON
        """
        prompt = self._build_type_b_prompt(topic, summary, source, score)
        system = f"""你是 X 智能运营助手，专门为 {self.niche} 领域创作短视频脚本。
当前 Niche 的语气风格：
{self.voice_style}

请生成一个 30 秒视频脚本，包含清晰的开场钩子、主体内容和 CTA。
严格按照 JSON 格式返回。"""
        return await self._generate_with_fallback(
            prompt, system, self._validate_type_b_result, self._mock_type_b_result, topic
        )

    def _build_type_b_prompt(self, topic: str, summary: str, source: str, score: float) -> str:
        """构建 B 类生成 Prompt"""
        return f"""请根据以下热点话题，生成一个 30 秒视频脚本：

话题：{topic}
热点来源：{source}
热点评分：{score}/100
相关信息：{summary}

生成要求：
1. 视频时长严格控制在 30 秒
2. 包含清晰的开场钩子（0-5 秒）
3. 主体内容要有信息量（5-20 秒）
4. 包含明确的 CTA（20-30 秒）
5. 提供配图/视频建议关键词

请严格按照以下 JSON 格式返回：
{{
  "title": "视频标题",
  "angle": "一句话创作切入点",
  "script": {{
    "hook": {{
      "time": "0-5s",
      "content": "开场钩子内容"
    }},
    "body": {{
      "time": "5-20s",
      "content": "主体内容"
    }},
    "cta": {{
      "time": "20-30s",
      "content": "核心卖点 + CTA"
    }}
  }},
  "caption": "配发 X 的文字内容（280 字符内）",
  "hashtags": ["#tag1", "#tag2", "#tag3"],
  "media_suggestion": "keyword1, keyword2, keyword3",
  "best_posting_time": "建议发布时间（UK 时间）"
}}"""

    def _validate_type_b_result(self, result: Dict) -> Dict:
        """验证 B 类生成结果"""
        if not isinstance(result, dict) or "script" not in result:
            return self._mock_type_b_result("Unknown")
        return result

    def _mock_type_b_result(self, topic: str) -> Dict:
        """模拟 B 类结果"""
        return {
            "title": f"Everything About {topic}",
            "angle": "Quick dive into the trend",
            "script": {
                "hook": {"time": "0-5s", "content": f"Want to know about {topic}?"},
                "body": {"time": "5-20s", "content": "Here's what you need to know..."},
                "cta": {"time": "20-30s", "content": "Follow for more!"},
            },
            "caption": f"Quick take on {topic} 🎬",
            "hashtags": ["#Trending", "#Video", "#Shorts"],
            "media_suggestion": f"{topic}, video, trending",
            "best_posting_time": "19:00 UK",
        }

    async def generate_comment(
        self, post_content: str, author: str = "", hashtags: List[str] = None
    ) -> Dict:
        """
        生成智能评论（3 条备选）

        Args:
            post_content: 原帖内容
            author: 原作者
            hashtags: 话题标签

        Returns:
            Dict: 评论列表
        """
        prompt = self._build_comment_prompt(post_content, author, hashtags)
        system = f"""你是 X 智能运营助手，专门为 {self.niche} 领域创作自然、有吸引力的评论。
当前 Niche 的语气风格：
{self.voice_style}

请生成 3 条不同的评论选项，每条评论：
1. 控制在 120 字符以内
2. 必须包含 emoji
3. 以问题结尾（提升回复率）
4. 30% 概率自然带 CTA
5. 避免明显的机器人语气

请严格按照以下 JSON 格式返回：
{{
  "comments": [
    {{
      "content": "评论内容...",
      "has_cta": false
    }},
    {{
      "content": "评论内容...",
      "has_cta": true
    }},
    {{
      "content": "评论内容...",
      "has_cta": false
    }}
  ]
}}"""
        return await self._generate_with_fallback(
            prompt, system, self._validate_comment_result, self._mock_comment_result
        )

    def _build_comment_prompt(self, post_content: str, author: str, hashtags: List[str]) -> str:
        """构建评论生成 Prompt"""
        hashtag_str = ", ".join(hashtags) if hashtags else ""
        return f"""请根据以下帖子内容，生成 3 条不同的评论选项：

原帖内容：{post_content}
原帖作者：{author}
话题标签：{hashtag_str}"""

    def _validate_comment_result(self, result: Dict) -> Dict:
        """验证评论生成结果"""
        if not isinstance(result, dict) or "comments" not in result:
            return self._mock_comment_result()
        return result

    def _mock_comment_result(self) -> Dict:
        """模拟评论结果"""
        return {
            "comments": [
                {"content": "This is fire! 🔥 What do you think?", "has_cta": False},
                {
                    "content": "Love this perspective 💡 Have you considered the alternative?",
                    "has_cta": False,
                },
                {
                    "content": "Great insights! 👏 Check out my profile for more on this topic",
                    "has_cta": True,
                },
            ]
        }

    def set_niche(self, niche: str):
        """切换 Niche"""
        self.niche = niche
        self.voice_style = self._load_niche_voice(niche)

    async def generate(self, topic: str, content_type: str = "a", niche: str = None) -> Dict:
        """
        统一生成入口 - V0 Final

        Args:
            content_type: 'a' | 'b' | 'c'
            topic: 话题
            niche: Niche 领域（可选，默认使用当前设置）

        Returns:
            Dict: 包含 content 和 risk_score
        """
        if niche and niche != self.niche:
            self.set_niche(niche)

        # 计算 risk_score（基于话题敏感度和内容类型）
        risk_score = self._calculate_risk_score(topic, content_type)

        try:
            if content_type == "a":
                result = await self.generate_type_a(topic)
                content = self._format_type_a_content(result)
            elif content_type == "b":
                result = await self.generate_type_b(topic)
                content = self._format_type_b_content(result)
            elif content_type == "c":
                result = await self.generate_comment(topic)
                content = self._format_comment_content(result)
            else:
                raise ValueError(f"Unknown content type: {content_type}")

            return {
                "content": content,
                "risk_score": risk_score,
                "type": content_type,
                "niche": self.niche,
            }
        except Exception as e:
            return {
                "content": f"生成失败: {str(e)}",
                "risk_score": 100,
                "type": content_type,
                "niche": self.niche,
            }

    def _calculate_risk_score(self, topic: str, content_type: str) -> int:
        """
        计算风险评分 (0-100)

        风险因素：
        - 敏感关键词
        - 内容类型（C类评论风险更高）
        - Niche 领域（成人用品风险较高）
        """
        score = 30  # 基础分

        # 敏感关键词检查
        sensitive_keywords = ["crypto", "onlyfans", "adult", "xxx", "gambl"]
        topic_lower = topic.lower()
        for kw in sensitive_keywords:
            if kw in topic_lower:
                score += 20
                break

        # 内容类型风险
        if content_type == "c":  # 评论风险较高
            score += 15
        elif content_type == "a":  # 推文中等
            score += 10

        # Niche 风险
        if "adult" in self.niche.lower():
            score += 25
        elif "crypto" in self.niche.lower():
            score += 20

        return min(score, 100)

    def _format_type_a_content(self, result: Dict) -> str:
        """格式化 A 类推文"""
        if "tweets" in result:
            tweets = result["tweets"]
            return "\n\n".join([f"{i+1}. {t.get('content', t)}" for i, t in enumerate(tweets[:3])])
        return str(result)

    def _format_type_b_content(self, result: Dict) -> str:
        """格式化 B 类脚本"""
        script = result.get("script", {})
        hook = script.get("hook", {}).get("content", "")
        body = script.get("body", {}).get("content", "")
        cta = script.get("cta", {}).get("content", "")
        return f"🎬 标题: {result.get('title', 'Untitled')}\n\n🎣 钩子: {hook}\n📝 主体: {body}\n📢 CTA: {cta}"

    def _format_comment_content(self, result: Dict) -> str:
        """格式化评论"""
        comments = result.get("comments", [])
        return "\n\n".join([f"{i+1}. {c.get('content', c)}" for i, c in enumerate(comments[:3])])

    async def generate_trend_analysis(self, research_result: Dict, date: str = None) -> str:
        """
        生成趋势分析 Markdown 报告

        Args:
            research_result: 研究结果（包含 platform_data、summary、risk_score 等）
            date: 报告日期（可选）

        Returns:
            str: Markdown 格式的趋势分析报告
        """
        from datetime import datetime

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        # 提取关键数据
        platform_data = research_result.get("platform_data", {})
        summary = research_result.get("summary", "")

        # 构建分析提示
        trends_info = []
        total_posts = 0
        for platform, data in platform_data.items():
            if isinstance(data, dict) and isinstance(data.get("posts"), list):
                posts = data["posts"][:5]  # 取前 5 条
                total_posts += len(posts)
                platform_trends = [p.get("title", "")[:60] for p in posts]
                trends_info.append(f"**{platform.upper()}**:\n" + "\n".join(f"- {t}" for t in platform_trends))

        trends_text = "\n\n".join(trends_info)

        prompt = f"""请根据以下多平台的实时趋势数据，生成一份专业的 Markdown 格式趋势分析报告。

【数据总览】
- 报告日期：{date}
- 总话题数：{total_posts}
- 数据来源：{', '.join(platform_data.keys())}

【平台热点数据】
{trends_text}

【LLM 初步总结】
{summary}

请按以下结构生成 Markdown 报告：
1. 趋势概览（一句话总结当日热点特征）
2. 热度排行 TOP 5（列出热度最高的5个话题，包含热度指标）
3. 平台汇聚性分析（分析话题在多个平台的流行程度）
4. 投资机会（基于趋势的潜在商机或运营机会）
5. 相关话题推荐（基于趋势的衍生话题建议）

报告要求：
- 语言简洁专业
- 使用数据支持观点
- 突出关键洞察
- Markdown 格式规范"""

        try:
            report = await self.llm_router.chat([
                {"role": "system", "content": "你是专业的数据分析师和趋势研究员。生成高质量的 Markdown 分析报告。"},
                {"role": "user", "content": prompt}
            ])
            return report
        except Exception as e:
            # 返回备用报告格式
            return f"""# 📊 趋势分析报告 [{date}]

## 🔥 趋势概览
- 总话题数：{total_posts}
- 数据来源：{', '.join(platform_data.keys())}
- AI 总结：{summary[:100]}...

## 📈 平台热点分布
{trends_text}

## ⚠️ 报告生成失败
由于 LLM 服务不可用，以上为基础数据展示。错误：{str(e)}
"""


async def generate_content(
    content_type: str, topic: str, summary: str = "", niche: str = "general"
) -> Dict:
    """
    便捷函数：生成内容

    Args:
        content_type: 'a' | 'b' | 'comment'
        topic: 话题
        summary: 摘要
        niche: Niche 领域

    Returns:
        Dict: 生成的内容
    """
    llm_router = LLMRouter()
    generator = ContentGenerator(llm_router, niche)

    if content_type == "a":
        return await generator.generate_type_a(topic, summary)
    elif content_type == "b":
        return await generator.generate_type_b(topic, summary)
    elif content_type == "comment":
        return await generator.generate_comment(topic)
    else:
        raise ValueError(f"Unknown content type: {content_type}")
