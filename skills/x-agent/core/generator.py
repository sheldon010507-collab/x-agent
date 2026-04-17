"""
generator.py - A/B/C 内容生成模块

- A类: 推文 (3条备选)
- B类: 视频脚本 (30秒分镜)
- C类: 智能评论 (3条备选)
- Niche 语气注入
- 风险评分
"""

from pathlib import Path
from typing import Dict, List

from .llm_router import LLMRouter


class ContentGenerator:
    def __init__(self, llm_router: LLMRouter, niche: str = "general"):
        self.llm_router = llm_router
        self.niche = niche
        self.voice_style = self._load_niche_voice(niche)

    def _load_niche_voice(self, niche: str) -> str:
        voice_file = Path(__file__).parent.parent / "niche_voices" / f"{niche}.txt"
        if voice_file.exists():
            return voice_file.read_text(encoding="utf-8")
        return f"Niche: {niche}\nTone: Professional and engaging"

    async def _generate_with_fallback(
        self, prompt: str, system: str, validator_fn, mock_fn, *mock_args
    ) -> Dict:
        try:
            result = await self.llm_router.generate_json(prompt, system=system)
            return validator_fn(result)
        except Exception:
            return mock_fn(*mock_args)

    async def generate_type_a(
        self, topic: str, summary: str = "", source: str = "", score: float = 50.0
    ) -> Dict:
        prompt = f"""请根据以下热点话题，生成 3 条不同角度的推文：

话题：{topic}
热点来源：{source}
热点评分：{score}/100
相关信息：{summary}

生成要求：
1. 每条推文控制在 280 字符以内
2. 包含 2-3 个相关 hashtag
3. 3 条推文角度分别为：Hot take / Data-Research / Interactive Poll

请严格按照以下 JSON 格式返回：
{{"tweets": [{{"angle": "Hot take", "content": "...", "hashtags": ["#tag1"]}}, {{"angle": "Data/Research", "content": "...", "hashtags": ["#tag1"]}}, {{"angle": "Interactive Poll", "content": "...", "hashtags": ["#tag1"]}}], "media_suggestion": "keyword1, keyword2"}}"""

        system = f"""你是 X 智能运营助手，专门为 {self.niche} 领域创作高质量的推文内容。
当前 Niche 的语气风格：
{self.voice_style}

请生成 3 条不同角度的推文，每条控制在 280 字符以内，包含 2-3 个相关 hashtag。
严格按照 JSON 格式返回。"""

        return await self._generate_with_fallback(
            prompt, system, self._validate_type_a, self._mock_type_a, topic
        )

    def _validate_type_a(self, result: Dict) -> Dict:
        if isinstance(result, dict) and "tweets" in result and isinstance(result["tweets"], list):
            return result
        return self._mock_type_a("Unknown")

    def _mock_type_a(self, topic: str) -> Dict:
        return {
            "tweets": [
                {"angle": "Hot take", "content": f"Unpopular opinion about {topic}: it's more relevant than you think.", "hashtags": ["#HotTake", "#Trending"]},
                {"angle": "Data/Research", "content": f"Data shows {topic} is gaining traction. Here's what the numbers say.", "hashtags": ["#Data", "#Research"]},
                {"angle": "Interactive Poll", "content": f"Quick poll: What's your take on {topic}? Vote below!", "hashtags": ["#Poll", "#Community"]},
            ],
            "media_suggestion": f"{topic}, trending, discussion",
        }

    async def generate_type_b(
        self, topic: str, summary: str = "", source: str = "", score: float = 50.0
    ) -> Dict:
        prompt = f"""请根据以下热点话题，生成一个 30 秒视频脚本：

话题：{topic}
热点来源：{source}
热点评分：{score}/100
相关信息：{summary}

请严格按照以下 JSON 格式返回：
{{"title": "视频标题", "angle": "创作切入点", "script": {{"hook": {{"time": "0-5s", "content": "开场钩子"}}, "body": {{"time": "5-20s", "content": "主体内容"}}, "cta": {{"time": "20-30s", "content": "CTA"}}}}, "caption": "配发文字(280字符内)", "hashtags": ["#tag1"], "media_suggestion": "keyword1, keyword2"}}"""

        system = f"""你是 X 智能运营助手，专门为 {self.niche} 领域创作短视频脚本。
当前 Niche 的语气风格：
{self.voice_style}
严格按照 JSON 格式返回。"""

        return await self._generate_with_fallback(
            prompt, system, self._validate_type_b, self._mock_type_b, topic
        )

    def _validate_type_b(self, result: Dict) -> Dict:
        if isinstance(result, dict) and "script" in result:
            return result
        return self._mock_type_b("Unknown")

    def _mock_type_b(self, topic: str) -> Dict:
        return {
            "title": f"Everything About {topic}",
            "angle": "Quick dive into the trend",
            "script": {
                "hook": {"time": "0-5s", "content": f"Want to know about {topic}?"},
                "body": {"time": "5-20s", "content": "Here's what you need to know..."},
                "cta": {"time": "20-30s", "content": "Follow for more!"},
            },
            "caption": f"Quick take on {topic}",
            "hashtags": ["#Trending", "#Video", "#Shorts"],
            "media_suggestion": f"{topic}, video, trending",
        }

    async def generate_comment(
        self, post_content: str, author: str = "", hashtags: List[str] = None
    ) -> Dict:
        hashtag_str = ", ".join(hashtags) if hashtags else ""
        prompt = f"""请根据以下帖子内容，生成 3 条不同的评论选项：

原帖内容：{post_content}
原帖作者：{author}
话题标签：{hashtag_str}

请严格按照以下 JSON 格式返回：
{{"comments": [{{"content": "评论内容...", "has_cta": false}}, {{"content": "评论内容...", "has_cta": true}}, {{"content": "评论内容...", "has_cta": false}}]}}"""

        system = f"""你是 X 智能运营助手，专门为 {self.niche} 领域创作自然、有吸引力的评论。
当前 Niche 的语气风格：
{self.voice_style}
每条评论控制在 120 字符以内，包含 emoji，以问题结尾。避免明显的机器人语气。"""

        return await self._generate_with_fallback(
            prompt, system, self._validate_comment, self._mock_comment
        )

    def _validate_comment(self, result: Dict) -> Dict:
        if isinstance(result, dict) and "comments" in result:
            return result
        return self._mock_comment()

    def _mock_comment(self) -> Dict:
        return {
            "comments": [
                {"content": "This is fire! What do you think?", "has_cta": False},
                {"content": "Love this perspective! Have you considered the alternative?", "has_cta": False},
                {"content": "Great insights! Check out my profile for more on this topic", "has_cta": True},
            ]
        }

    async def generate(self, topic: str, content_type: str = "a", niche: str = None) -> Dict:
        """统一生成入口"""
        if niche and niche != self.niche:
            self.niche = niche
            self.voice_style = self._load_niche_voice(niche)

        risk_score = self._calculate_risk_score(topic, content_type)

        try:
            if content_type == "a":
                result = await self.generate_type_a(topic)
                content = self._format_type_a(result)
            elif content_type == "b":
                result = await self.generate_type_b(topic)
                content = self._format_type_b(result)
            elif content_type == "c":
                result = await self.generate_comment(topic)
                content = self._format_comment(result)
            else:
                raise ValueError(f"Unknown content type: {content_type}")

            return {
                "content": content,
                "raw": result,
                "risk_score": risk_score,
                "type": content_type,
                "niche": self.niche,
            }
        except Exception as e:
            return {
                "content": f"Generation failed: {e}",
                "risk_score": 100,
                "type": content_type,
                "niche": self.niche,
            }

    def _calculate_risk_score(self, topic: str, content_type: str) -> int:
        score = 30
        sensitive_keywords = ["crypto", "onlyfans", "adult", "xxx", "gambl"]
        topic_lower = topic.lower()
        for kw in sensitive_keywords:
            if kw in topic_lower:
                score += 20
                break
        if content_type == "c":
            score += 15
        elif content_type == "a":
            score += 10
        if "adult" in self.niche.lower():
            score += 25
        elif "crypto" in self.niche.lower():
            score += 20
        return min(score, 100)

    def _format_type_a(self, result: Dict) -> str:
        if "tweets" in result:
            return "\n\n".join(
                [f"{i+1}. {t.get('content', t)}" for i, t in enumerate(result["tweets"][:3])]
            )
        return str(result)

    def _format_type_b(self, result: Dict) -> str:
        script = result.get("script", {})
        hook = script.get("hook", {}).get("content", "")
        body = script.get("body", {}).get("content", "")
        cta = script.get("cta", {}).get("content", "")
        return f"Title: {result.get('title', 'Untitled')}\n\nHook: {hook}\nBody: {body}\nCTA: {cta}"

    def _format_comment(self, result: Dict) -> str:
        comments = result.get("comments", [])
        return "\n\n".join(
            [f"{i+1}. {c.get('content', c)}" for i, c in enumerate(comments[:3])]
        )
