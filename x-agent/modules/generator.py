"""
generator.py - 内容生成模块 (v3)
实现：
- A 类：AI 全自动推文（3 条备选）
- B 类：30 秒视频脚本（拍摄脚本）
- C 类：智能评论（带 emoji + 问题结尾）
集成 niche_voices 注入机制
输出配图建议关键词
"""
import asyncio
from typing import Dict, List, Optional
from pathlib import Path
from .llm_router import LLMRouter, get_llm_router
import logging

logger = logging.getLogger(__name__)


class ContentGenerator:
    """
    内容生成器
    
    支持三种内容类型：
    - A 类：AI 自动推文（Hot take / Data / Interactive Poll）
    - B 类：拍摄脚本（30 秒分镜）
    - C 类：智能评论（自然、带 emoji、问题结尾）
    """
    
    def __init__(self, llm_router: LLMRouter = None, niche: str = 'general'):
        """
        初始化生成器
        
        Args:
            llm_router: LLM 路由实例（可选，默认使用全局实例）
            niche: Niche 领域
        """
        self.llm_router = llm_router
        self.niche = niche
        self.voice_style = self._load_niche_voice(niche)
    
    def _get_llm_router(self):
        """获取 LLM 路由器（延迟导入）"""
        if self.llm_router is None:
            try:
                from .llm_router import get_llm_router
                self.llm_router = get_llm_router()
            except:
                # 如果没有配置，返回 None，使用模拟数据
                self.llm_router = None
        return self.llm_router
    
    def _load_niche_voice(self, niche: str) -> str:
        """
        加载 Niche 语气文件
        
        Args:
            niche: Niche 名称
        
        Returns:
            str: 语气文件内容
        """
        # 尝试多个可能的位置
        possible_paths = [
            Path(__file__).parent.parent / 'niche_voices' / f'{niche}.txt',
            Path(__file__).parent / '../niche_voices' / f'{niche}.txt',
            Path.cwd() / 'niche_voices' / f'{niche}.txt',
        ]
        
        for voice_file in possible_paths:
            if voice_file.exists():
                return voice_file.read_text(encoding='utf-8')
        
        # 如果没有找到，使用通用语气
        return self._get_default_voice(niche)
    
    def _get_default_voice(self, niche: str) -> str:
        """获取默认语气"""
        default_voices = {
            'adult': "Tone: cheeky, playful, suggestive, confident. Use emojis sparingly but effectively. Style: bold and direct.",
            'ai_tools': "Tone: geeky, efficient, cutting-edge, informative. Style: data-driven, unpopular opinions welcome.",
            'beauty': "Tone: friendly, authentic, detailed, sisterly. Style: honest reviews, 'girlies' energy, emoji-rich.",
            'fitness': "Tone: motivational, data-driven, challenging, community-focused. Style: 'no excuses', results-oriented.",
            'crypto': "Tone: FOMO, alpha-focused, community trust. Style: 'not financial advice but...', early adopter mentality.",
            'humor': "Tone: absurd, self-deprecating, meme-literate. Style: 'me: *does thing* also me:' format.",
            'general': "Tone: Professional and engaging. Style: Clear, concise, and audience-appropriate."
        }
        
        return default_voices.get(niche, default_voices['general'])
    
    async def generate_type_a(self, topic: str, summary: str = '', source: str = '', 
                              score: float = 50.0, niche: str = None) -> Dict:
        """
        生成 A 类推文（3 条备选）
        
        Args:
            topic: 话题
            summary: 热点摘要
            source: 来源
            score: 热点评分
            niche: Niche 领域（可选，覆盖默认）
        
        Returns:
            Dict: 包含 3 条推文的 JSON
                {
                    "tweets": [
                        {"angle": "Hot take", "content": "...", "hashtags": ["#tag1"]},
                        ...
                    ],
                    "media_suggestion": "keyword1, keyword2"
                }
        """
        current_niche = niche or self.niche
        voice = self._load_niche_voice(current_niche)
        
        prompt = self._build_type_a_prompt(topic, summary, source, score)
        
        router = self._get_llm_router()
        if router:
            try:
                result = await router.generate_json(
                    [{"role": "user", "content": prompt}],
                    system=f"""你是 X 智能运营助手，专门为 {current_niche} 领域创作高质量的推文内容。
                    
当前 Niche 的语气风格：
{voice}

请生成 3 条不同角度的推文，每条控制在 280 字符以内，包含 2-3 个相关 hashtag。
严格按照 JSON 格式返回。"""
                )
                return self._validate_type_a_result(result, topic)
            except Exception as e:
                logger.error(f"A 类生成失败：{e}")
        
        return self._mock_type_a_result(topic)
    
    def _build_type_a_prompt(self, topic: str, summary: str, source: str, score: float) -> str:
        """构建 A 类生成 Prompt"""
        return f"""请根据以下热点话题，生成 3 条不同角度的推文：

话题：{topic}
热点来源：{source}
热点评分：{score}/100
相关信息：{summary or '无'}

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
    
    def _validate_type_a_result(self, result: Dict, topic: str = 'Unknown') -> Dict:
        """验证 A 类生成结果"""
        if not isinstance(result, dict):
            return self._mock_type_a_result(topic)
        
        if 'tweets' not in result or not isinstance(result['tweets'], list):
            return self._mock_type_a_result(topic)
        
        # 确保每条推文都有必需字段
        validated_tweets = []
        for tweet in result['tweets']:
            if not isinstance(tweet, dict):
                continue
            
            validated_tweet = {
                'angle': tweet.get('angle', 'General'),
                'content': tweet.get('content', ''),
                'hashtags': tweet.get('hashtags', [])
            }
            
            # 确保 hashtags 是列表
            if isinstance(validated_tweet['hashtags'], str):
                validated_tweet['hashtags'] = [validated_tweet['hashtags']]
            
            validated_tweets.append(validated_tweet)
        
        # 如果结果为空，使用模拟数据
        if not validated_tweets:
            return self._mock_type_a_result(topic)
        
        result['tweets'] = validated_tweets
        
        # 确保有 media_suggestion
        if 'media_suggestion' not in result:
            result['media_suggestion'] = f"{topic}, trending, discussion"
        
        return result
    
    def _mock_type_a_result(self, topic: str) -> Dict:
        """模拟 A 类结果"""
        return {
            'tweets': [
                {
                    'angle': 'Hot take',
                    'content': f"Unpopular opinion about {topic}: it's more relevant than you think. 🤔",
                    'hashtags': ['#HotTake', '#Trending']
                },
                {
                    'angle': 'Data/Research',
                    'content': f"Data shows {topic} is gaining traction. Here's what the numbers say 📊",
                    'hashtags': ['#Data', '#Research']
                },
                {
                    'angle': 'Interactive Poll',
                    'content': f"Quick poll: What's your take on {topic}? Vote below! 👇",
                    'hashtags': ['#Poll', '#Community']
                }
            ],
            'media_suggestion': f"{topic}, trending, discussion"
        }
    
    async def generate_type_b(self, topic: str, summary: str = '', source: str = '', 
                              score: float = 50.0, niche: str = None) -> Dict:
        """
        生成 B 类视频脚本（30 秒分镜）
        
        Args:
            topic: 话题
            summary: 热点摘要
            source: 来源
            score: 热点评分
            niche: Niche 领域
        
        Returns:
            Dict: 视频脚本 JSON
        """
        current_niche = niche or self.niche
        voice = self._load_niche_voice(current_niche)
        
        prompt = self._build_type_b_prompt(topic, summary, source, score)
        
        router = self._get_llm_router()
        if router:
            try:
                result = await router.generate_json(
                    [{"role": "user", "content": prompt}],
                    system=f"""你是 X 智能运营助手，专门为 {current_niche} 领域创作短视频脚本。
                    
当前 Niche 的语气风格：
{voice}

请生成一个 30 秒视频脚本，包含清晰的开场钩子、主体内容和 CTA。
严格按照 JSON 格式返回。"""
                )
                return self._validate_type_b_result(result, topic)
            except Exception as e:
                logger.error(f"B 类生成失败：{e}")
        
        return self._mock_type_b_result(topic)
    
    def _build_type_b_prompt(self, topic: str, summary: str, source: str, score: float) -> str:
        """构建 B 类生成 Prompt"""
        return f"""请根据以下热点话题，生成一个 30 秒视频脚本：

话题：{topic}
热点来源：{source}
热点评分：{score}/100
相关信息：{summary or '无'}

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
    
    def _validate_type_b_result(self, result: Dict, topic: str = 'Unknown') -> Dict:
        """验证 B 类生成结果"""
        if not isinstance(result, dict):
            return self._mock_type_b_result(topic)
        
        # 确保 script 存在
        if 'script' not in result or not isinstance(result['script'], dict):
            return self._mock_type_b_result(topic)
        
        # 验证 script 结构
        script = result['script']
        if 'hook' not in script or 'body' not in script or 'cta' not in script:
            return self._mock_type_b_result(topic)
        
        # 确保有 media_suggestion
        if 'media_suggestion' not in result:
            result['media_suggestion'] = f"{topic}, video, trending"
        
        # 确保有 hashtags
        if 'hashtags' not in result:
            result['hashtags'] = ['#Trending', '#Video', '#Shorts']
        
        return result
    
    def _mock_type_b_result(self, topic: str) -> Dict:
        """模拟 B 类结果"""
        return {
            'title': f'Everything About {topic}',
            'angle': 'Quick dive into the trend',
            'script': {
                'hook': {'time': '0-5s', 'content': f'Want to know about {topic}?'},
                'body': {'time': '5-20s', 'content': "Here's what you need to know..."},
                'cta': {'time': '20-30s', 'content': 'Follow for more!'}
            },
            'caption': f'Quick take on {topic} 🎬',
            'hashtags': ['#Trending', '#Video', '#Shorts'],
            'media_suggestion': f'{topic}, video, trending',
            'best_posting_time': '19:00 UK'
        }
    
    async def generate_comment(self, post_content: str, author: str = '', 
                               hashtags: List[str] = None, niche: str = None) -> Dict:
        """
        生成智能评论（3 条备选）
        
        Args:
            post_content: 原帖内容
            author: 原作者
            hashtags: 话题标签
            niche: Niche 领域
        
        Returns:
            Dict: 评论列表
        """
        current_niche = niche or self.niche
        voice = self._load_niche_voice(current_niche)
        
        hashtag_str = ', '.join(hashtags) if hashtags else ''
        prompt = f"""请根据以下帖子内容，生成 3 条不同的评论选项：

原帖内容：{post_content}
原帖作者：{author or '未知'}
话题标签：{hashtag_str or '无'}

生成要求：
1. 每条评论控制在 120 字符以内
2. 必须包含 emoji
3. 以问题结尾（提升回复率）
4. 30% 概率自然带 CTA
5. 避免明显的机器人语气
6. 符合 {current_niche} 领域的交流风格

请严格按照以下 JSON 格式返回：
{{
  "comments": [
    {{"content": "评论内容...", "has_cta": false}},
    {{"content": "评论内容...", "has_cta": true}},
    {{"content": "评论内容...", "has_cta": false}}
  ]
}}"""
        
        router = self._get_llm_router()
        if router:
            try:
                result = await router.generate_json(
                    [{"role": "user", "content": prompt}],
                    system=f"""你是 X 智能运营助手，专门为 {current_niche} 领域创作自然、有吸引力的评论。

当前 Niche 的语气风格：
{voice}

请生成 3 条不同的评论选项，确保自然、真实、有吸引力。"""
                )
                return self._validate_comment_result(result)
            except Exception as e:
                logger.error(f"评论生成失败：{e}")
        
        return self._mock_comment_result()
    
    def _validate_comment_result(self, result: Dict) -> Dict:
        """验证评论生成结果"""
        if not isinstance(result, dict):
            return self._mock_comment_result()
        
        if 'comments' not in result or not isinstance(result['comments'], list):
            return self._mock_comment_result()
        
        # 验证每条评论
        validated_comments = []
        for comment in result['comments']:
            if not isinstance(comment, dict):
                continue
            
            validated_comment = {
                'content': comment.get('content', ''),
                'has_cta': comment.get('has_cta', False)
            }
            validated_comments.append(validated_comment)
        
        if not validated_comments:
            return self._mock_comment_result()
        
        result['comments'] = validated_comments
        return result
    
    def _mock_comment_result(self) -> Dict:
        """模拟评论结果"""
        return {
            'comments': [
                {'content': 'This is fire! 🔥 What do you think?', 'has_cta': False},
                {'content': 'Love this perspective 💡 Have you considered the alternative?', 'has_cta': False},
                {'content': 'Great insights! 👏 Check out my profile for more on this topic', 'has_cta': True}
            ]
        }
    
    def set_niche(self, niche: str):
        """
        切换 Niche
        
        Args:
            niche: 新的 Niche 领域
        """
        self.niche = niche
        self.voice_style = self._load_niche_voice(niche)


# ============ 便捷函数 ============

async def generate_content(content_type: str, topic: str, summary: str = '', 
                           niche: str = 'general', llm_router: LLMRouter = None) -> Dict:
    """
    便捷函数：生成内容
    
    Args:
        content_type: 'a' | 'b' | 'comment'
        topic: 话题
        summary: 摘要
        niche: Niche 领域
        llm_router: LLM 路由器
    
    Returns:
        Dict: 生成的内容
    """
    generator = ContentGenerator(llm_router, niche)
    
    if content_type == 'a':
        return await generator.generate_type_a(topic, summary)
    elif content_type == 'b':
        return await generator.generate_type_b(topic, summary)
    elif content_type == 'comment':
        return await generator.generate_comment(topic)
    else:
        raise ValueError(f"Unknown content type: {content_type}")


# ============ 测试代码 ============
if __name__ == '__main__':
    async def test_generator():
        # 测试 A 类生成
        generator = ContentGenerator(niche='ai_tools')
        
        print("测试 A 类生成...")
        result_a = await generator.generate_type_a(
            topic='AI breakthrough',
            summary='New model achieves unprecedented performance',
            source='Twitter',
            score=85.0
        )
        print(f"A 类结果：{result_a}")
        
        print("\n测试 B 类生成...")
        result_b = await generator.generate_type_b(
            topic='AI breakthrough',
            summary='New model achieves unprecedented performance',
            source='Twitter',
            score=85.0
        )
        print(f"B 类结果：{result_b}")
        
        print("\n测试评论生成...")
        result_c = await generator.generate_comment(
            post_content='Just launched my new AI product!',
            author='tech_ceo',
            hashtags=['#AI', '#Launch']
        )
        print(f"评论结果：{result_c}")
    
    # asyncio.run(test_generator())
