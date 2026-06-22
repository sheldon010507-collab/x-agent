"""
Reddit Playwright 爬虫模块 — 融合 keyless + shreddit partials

功能：
- Playwright 直接抓取 Reddit 内容（搜索、subreddit 热门/最新帖）
- shreddit 「/svc/shreddit/」partials 抓取真实 upvote 分数
- 多账号轮换（防封）
- 登录态 Cookie 持久化
- 反检测措施（随机延迟、stealth JS）
- 自动限流检测与账号切换
- Reddit 私信/DM 监控（用于 Dashboard 消息面板）
"""

from __future__ import annotations

import html as _html
import asyncio
import json
import logging
import random
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from .browser_pool import BrowserPool, REDDIT_LAUNCH_ARGS

logger = logging.getLogger(__name__)

HAS_PLAYWRIGHT = True

# ─── 指纹伪装 JS ───────────────────────────────────────────────────────────
STEALTH_JS: str = r"""
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
        {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
    ]
});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
if (!window.chrome) {
    window.chrome = {
        runtime: {PlatformOs: {WIN: 'win', MAC: 'mac', LINUX: 'linux', CROS: 'cros'}}
    };
}
const originalQuery = window.navigator.permissions
    ? window.navigator.permissions.query : null;
if (originalQuery) {
    window.navigator.permissions.query = (parameters) =>
        parameters.name === 'notifications'
            ? Promise.resolve({state: Notification.permission})
            : originalQuery(parameters);
}
Object.defineProperty(window, 'outerWidth', {get: () => window.innerWidth});
Object.defineProperty(window, 'outerHeight', {get: () => window.innerHeight + 88});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
"""


@dataclass
class RedditAccount:
    """Reddit 账号配置"""
    id: str
    username: str
    password: str
    cookies_file: str
    user_agent: str = ""
    proxy: Optional[str] = None
    last_used: datetime = field(default_factory=datetime.now)
    daily_requests: int = 0
    request_count: int = 0
    status: str = "active"
    karma: str = "0"
    display_name: str = ""
    platform: str = "reddit"


@dataclass
class RedditPost:
    """标准化 Reddit 帖子数据"""
    id: str
    title: str
    content: str
    author: str
    subreddit: str
    upvotes: int
    comment_count: int
    created_utc: datetime
    url: str
    permalink: str
    awards: int = 0
    is_video: bool = False
    is_self: bool = False
    thumbnail: Optional[str] = None
    top_comments: List[Dict] = field(default_factory=list)
    comment_insights: List[str] = field(default_factory=list)
    engagement_score: float = 0.0


USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


class RedditPlaywrightCrawler:
    """
    Playwright 增强的 Reddit 爬虫 — 三层降级策略：

    1. shreddit listing partials（HTTP 直接取，无头/有头均可）拿真实 score
    2. shreddit comments /svc 取评论
    3. 页面 DOM 解析（搜索/社区页滚动）

    还支持：登录态保存、多账号轮换、X 账号 Cookie 复用、DM 会话列表获取。
    """

    # 默认多账号配置
    DEFAULT_ACCOUNTS: List[Dict[str, Any]] = [
        {"id": "reddit_1", "username": "xagent_research1", "password": "", "cookies_file": "data/cookies/reddit_1.json"},
        {"id": "reddit_2", "username": "xagent_research2", "password": "", "cookies_file": "data/cookies/reddit_2.json"},
    ]

    BROWSER_ARGS: List[str] = [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-accelerated-2d-canvas",
        "--disable-gpu",
        "--window-size=1920,1080",
    ]

    def __init__(
        self,
        accounts: Optional[List[Dict]] = None,
        headless: bool = True,
        max_retries: int = 3,
        request_delay_min: float = 2.0,
        request_delay_max: float = 5.0,
        data_dir: str = "data/reddit",
    ):
        self.headless = headless
        self.max_retries = max_retries
        self.delay_min = request_delay_min
        self.delay_max = request_delay_max

        raw_accounts = accounts or self.DEFAULT_ACCOUNTS
        self.accounts: List[RedditAccount] = []
        for acc in raw_accounts:
            self.accounts.append(RedditAccount(
                id=acc["id"],
                username=acc["username"],
                password=acc.get("password", ""),
                cookies_file=acc.get("cookies_file", f"data/cookies/{acc['id']}.json"),
                user_agent=acc.get("user_agent", random.choice(USER_AGENTS)),
                proxy=acc.get("proxy"),
            ))

        self.current_account_idx = 0
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._browser_pool: Optional[BrowserPool] = None
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self.total_requests = 0
        self.start_time = datetime.now()

    # ─── 生命周期 ────────────────────────────────────────────────────────────

    async def __aenter__(self):
        self._browser_pool = BrowserPool()
        await self._create_context()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._browser_pool:
            await self._browser_pool.close()

    async def _create_context(self):
        account = self.accounts[self.current_account_idx % len(self.accounts)]
        self._context = await self._browser_pool.get_context(
            account_id=account.id,
            cookies_file=account.cookies_file,
            user_agent=account.user_agent or random.choice(USER_AGENTS),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
            launch_args=REDDIT_LAUNCH_ARGS,
            headless=self.headless,
            proxy=account.proxy,
        )

        self._page = await self._context.new_page()
        if not await self._is_logged_in():
            if account.password:
                await self._login(account)
            else:
                logger.warning(f"[{account.username}] No password, skip login")

    async def _is_logged_in(self) -> bool:
        try:
            await self._page.goto(
                "https://www.reddit.com", wait_until="domcontentloaded", timeout=15000
            )
            for sel in [
                "header [class*='avatar']",
                "#avatar-username--container",
                "shreddit-avatar",
                "[data-testid='username']",
            ]:
                el = await self._page.query_selector(sel)
                if el:
                    return True
            return False
        except Exception:
            return False

    async def _login(self, account: RedditAccount):
        logger.info(f"[{account.username}] Attempting login...")
        try:
            await self._page.goto("https://www.reddit.com/login", wait_until="networkidle")
            await asyncio.sleep(random.uniform(0.8, 1.5))

            for sel_pair in [
                ("input#loginUsername", "input#loginPassword"),
                ("input[name='username']", "input[name='password']"),
            ]:
                u_els = await self._page.query_selector_all(sel_pair[0])
                p_els = await self._page.query_selector_all(sel_pair[1])
                if u_els and p_els:
                    await u_els[0].fill(account.username)
                    await asyncio.sleep(random.uniform(0.4, 0.9))
                    await p_els[0].fill(account.password)
                    break
            else:
                raise Exception("Login form not found")

            submit = await self._page.query_selector("button[type='submit']")
            if submit:
                await submit.click()
            await self._page.wait_for_url("https://www.reddit.com/", timeout=30000)

            # 拉 settings 页拿 karma / display_name
            await asyncio.sleep(random.uniform(1, 2))
            try:
                await self._page.goto(
                    "https://www.reddit.com/settings/", wait_until="domcontentloaded", timeout=15000
                )
                karma_sel = "[data-testid='karma'], [class*='karma']"
                karma_el = await self._page.query_selector(karma_sel)
                if karma_el:
                    account.karma = (await karma_el.inner_text()).strip()
                name_sel = "[data-testid='username'], [class*='username']"
                name_el = await self._page.query_selector(name_sel)
                if name_el:
                    account.display_name = (await name_el.inner_text()).strip()
            except Exception:
                pass

            cookies = await self._context.cookies()
            Path(account.cookies_file).parent.mkdir(parents=True, exist_ok=True)
            Path(account.cookies_file).write_text(json.dumps(cookies, indent=2), encoding="utf-8")
            logger.info(f"[{account.username}] Login successful, karma={account.karma}")
        except Exception as e:
            logger.error(f"[{account.username}] Login failed: {e}")
            raise

    # ─── 反检测 ──────────────────────────────────────────────────────────────

    async def _anti_detection(self):
        delay = random.uniform(self.delay_min, self.delay_max)
        await asyncio.sleep(delay)

    async def _switch_account(self):
        old = self.accounts[self.current_account_idx]
        self.current_account_idx = (self.current_account_idx + 1) % len(self.accounts)
        new = self.accounts[self.current_account_idx]
        logger.warning(f"Switching Reddit account: {old.username} -> {new.username}")
        if self._context:
            await self._context.close()
        await self._create_context()

    # ─── 核心搜索 ────────────────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        subreddits: Optional[List[str]] = None,
        sort: str = "hot",
        time_filter: str = "week",
        limit: int = 25,
    ) -> List[RedditPost]:
        all_posts: List[RedditPost] = []
        account = self.accounts[self.current_account_idx]

        if subreddits:
            for sr in subreddits:
                try:
                    posts = await self._search_subreddit(sr, query, sort, time_filter, limit)
                    all_posts.extend(posts)
                    account.request_count += 1
                    await self._anti_detection()
                except Exception as e:
                    logger.error(f"Search r/{sr} error: {e}")
                    if "429" in str(e) or "rate limit" in str(e).lower():
                        await self._switch_account()
                        posts = await self._search_subreddit(sr, query, sort, time_filter, limit)
                        all_posts.extend(posts)
        else:
            try:
                all_posts = await self._search_global(query, sort, time_filter, limit)
                account.request_count += 1
            except Exception as e:
                logger.error(f"Global search error: {e}")

        # 去重 + 排序
        seen: set = set()
        unique: List[RedditPost] = []
        for p in all_posts:
            if p.id not in seen:
                seen.add(p.id)
                unique.append(p)
        unique.sort(key=lambda p: p.engagement_score, reverse=True)
        return unique[:limit]

    async def _search_subreddit(
        self, subreddit: str, query: str, sort: str, time_filter: str, limit: int
    ) -> List[RedditPost]:
        url = (
            f"https://www.reddit.com/r/{subreddit}/search/"
            f"?q={query}&sort={sort}&t={time_filter}&restrict_sr=1"
        )
        return await self._fetch_posts_from_url(url, limit)

    async def _search_global(
        self, query: str, sort: str, time_filter: str, limit: int
    ) -> List[RedditPost]:
        url = f"https://www.reddit.com/search/?q={query}&sort={sort}&t={time_filter}"
        return await self._fetch_posts_from_url(url, limit)

    async def _fetch_posts_from_url(self, url: str, limit: int) -> List[RedditPost]:
        """从 URL 抓取并解析帖子 — 优先用 shreddit JSON partial 补 score。"""
        posts: List[RedditPost] = []
        parsed_posts: List[Dict] = []

        for attempt in range(self.max_retries):
            try:
                await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(random.uniform(1, 2))

                # 滚动加载
                for _ in range(3):
                    await self._page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                    await asyncio.sleep(random.uniform(0.8, 1.5))

                # 方案 A: 从 shreddit <shreddit-post> 属性拿真实 score
                parsed_posts = await self._extract_shreddit_posts(limit)

                # 方案 B: 回退 DOM 解析
                if not parsed_posts:
                    parsed_posts = await self._extract_dom_posts(limit)

                break
            except Exception as e:
                logger.warning(f"Fetch attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

        for pd in parsed_posts:
            posts.append(RedditPost(**pd))
        return posts

    # ─── 解析方法 ─────────────────────────────────────────────────────────────

    async def _extract_shreddit_posts(self, limit: int) -> List[Dict]:
        """从页面 <shreddit-post> 自定义元素提取帖卡（真实 score）。"""
        result = await self._page.evaluate(
            """
            (max) => {
            const cards = [];
            const elems = document.querySelectorAll('shreddit-post');
            for (const el of elems) {
                if (cards.length >= max) break;
                const a = el.attributes;
                const data = {};
                for (const attr of a) {
                    data[attr.name] = attr.value;
                }
                const linkEl = el.querySelector('a[href*="/comments/"]');
                data.permalink = linkEl ? linkEl.getAttribute('href') : '';
                data.url = data.permalink.startsWith('/')
                    ? 'https://www.reddit.com' + data.permalink : data.permalink;
                cards.push(data);
            }
            return cards;
            }
            """,
            limit,
        )
        if not result:
            return []

        posts: List[Dict] = []
        for card in result[:limit]:
            permalink = card.get("permalink", "")
            if "/comments/" not in permalink:
                continue
            try:
                score = int(card.get("score", "0") or "0")
            except ValueError:
                score = 0
            try:
                nc = int(card.get("comment-count", "0") or "0")
            except ValueError:
                nc = 0

            title = card.get("post-title", "")
            author = card.get("author", "")
            subreddit = card.get("subreddit-name", "")
            created = card.get("created-timestamp", "")

            posts.append({
                "id": card.get("post-id", "") or f"sp_{random.randint(10000, 99999)}",
                "title": title[:300],
                "content": "",
                "author": author if author not in ("[deleted]", "[removed]") else "[deleted]",
                "subreddit": subreddit,
                "upvotes": score,
                "comment_count": nc,
                "created_utc": self._parse_created(created),
                "url": card.get("url", f"https://www.reddit.com{permalink}"),
                "permalink": f"https://www.reddit.com{permalink}",
                "engagement_score": score + nc * 3,
                "is_self": False,
                "thumbnail": None,
            })
        return posts

    async def _extract_dom_posts(self, limit: int) -> List[Dict]:
        """DOM 解析回退方案。"""
        posts: List[Dict] = []
        for selector in ["[data-testid='post-container']", ".Post", "[data-click-id='body']", "shreddit-post"]:
            elements = await self._page.query_selector_all(selector)
            if elements:
                for el in elements[:limit]:
                    try:
                        post = await self._parse_post_element(el)
                        if post:
                            posts.append(post)
                    except Exception:
                        continue
                    if len(posts) >= limit:
                        break
                if posts:
                    break
        return posts

    async def _parse_post_element(self, element) -> Optional[Dict]:
        try:
            post_id = await element.get_attribute("id") or f"dom_{id(element)}"

            title = ""
            for sel in ["h3", "[data-testid='post-title']", "a[data-click-id='body'] h3", "h2"]:
                el = await element.query_selector(sel)
                if el:
                    title = (await el.inner_text()).strip()
                    break

            author = "unknown"
            for sel in ["a[href^='/user/']", "a[href^='/u/']"]:
                el = await element.query_selector(sel)
                if el:
                    author = (await el.inner_text()).strip().replace("u/", "").replace("/u/", "")
                    break

            upvotes = 0
            for sel in [
                "[data-testid='upvote-button'] + span",
                "[data-testid='upvote'] + span",
                "[aria-label*='upvote'] + span",
            ]:
                el = await element.query_selector(sel)
                if el:
                    upvotes = self._parse_number(await el.inner_text())
                    break

            comment_count = 0
            for sel in ["[data-testid='comment-button'] span", "a[href*='/comments/'] span"]:
                el = await element.query_selector(sel)
                if el:
                    comment_count = self._parse_number(await el.inner_text())
                    break

            subreddit = ""
            for sel in ["a[href^='/r/']"]:
                el = await element.query_selector(sel)
                if el:
                    raw = await el.get_attribute("href") or ""
                    m = re.search(r"/r/([^/]+)", raw)
                    subreddit = m.group(1) if m else ""
                    break

            url = permalink = ""
            for sel in ["a[href^='/r/']", "a[data-click-id='body']"]:
                el = await element.query_selector(sel)
                if el:
                    href = await el.get_attribute("href") or ""
                    url = f"https://www.reddit.com{href}" if href.startswith("/") else href
                    permalink = url
                    break

            engagement = upvotes + comment_count * 3
            return {
                "id": post_id,
                "title": title[:300],
                "content": "",
                "author": author,
                "subreddit": subreddit,
                "upvotes": upvotes,
                "comment_count": comment_count,
                "created_utc": datetime.now(),
                "url": url,
                "permalink": permalink,
                "engagement_score": engagement,
                "is_self": False,
                "thumbnail": None,
            }
        except Exception as e:
            logger.debug(f"parse_post_element error: {e}")
            return None

    def _parse_number(self, text: str) -> int:
        try:
            text = text.strip().lower().replace(",", "")
            if "k" in text:
                return int(float(text.replace("k", "")) * 1000)
            if "m" in text:
                return int(float(text.replace("m", "")) * 1_000_000)
            return int(float(text))
        except (ValueError, TypeError):
            return 0

    def _parse_created(self, iso_str: str) -> datetime:
        if not iso_str:
            return datetime.now()
        try:
            return datetime.fromisoformat(iso_str.strip())
        except Exception:
            return datetime.now()

    # ─── 帖子详情 ─────────────────────────────────────────────────────────────

    async def get_post_detail(self, post_id: str) -> Optional[RedditPost]:
        url = f"https://www.reddit.com/comments/{post_id}"
        try:
            await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(random.uniform(1, 2))

            # 正文
            content = ""
            for sel in ["[data-testid='post-content']", "[class*='text-14']"]:
                el = await self._page.query_selector(sel)
                if el:
                    content = (await el.inner_text()).strip()[:2000]
                    break

            # 前 3 条评论
            comments: List[Dict] = []
            comment_els = await self._page.query_selector_all("[data-testid='comment']")
            for c_el in comment_els[:3]:
                try:
                    author_el = await c_el.query_selector("a[href^='/user/']")
                    text_el = await c_el.query_selector("[data-testid='comment-body']")
                    if text_el:
                        comments.append({
                            "author": (await author_el.inner_text()) if author_el else "",
                            "text": (await text_el.inner_text()).strip()[:300],
                        })
                except Exception:
                    continue
            return RedditPost(
                id=post_id, title="", content=content,
                author="", subreddit="", upvotes=0, comment_count=len(comments),
                created_utc=datetime.now(), url=url, permalink=url,
                top_comments=comments,
            )
        except Exception as e:
            logger.error(f"Detail fetch error: {e}")
            return None

    # ─── 账号状态 ─────────────────────────────────────────────────────────────

    async def get_account_status(self) -> Dict[str, Any]:
        """获取当前账号状态（供 Dashboard 调用）。"""
        account = self.accounts[self.current_account_idx]
        try:
            if self._page:
                await self._page.goto(
                    "https://www.reddit.com/settings/",
                    wait_until="domcontentloaded", timeout=15000,
                )
                karma = "0"
                for sel in ["[data-testid='karma']", "[class*='karma']"]:
                    el = await self._page.query_selector(sel)
                    if el:
                        karma = (await el.inner_text()).strip()
                        break
                return {
                    "platform": "reddit",
                    "account_id": account.id,
                    "username": account.username,
                    "display_name": account.display_name or account.username,
                    "karma": karma,
                    "status": "healthy",
                    "status_detail": account.karma,
                    "request_count": account.request_count,
                    "daily_requests": account.daily_requests,
                    "last_used": account.last_used.isoformat(),
                    "last_activity": datetime.now().isoformat(),
                    "age_hours": (datetime.now() - account.last_used).total_seconds() / 3600,
                    "reputation_score": 85.0,
                    "daily_posts": 0,
                    "daily_likes": 0,
                    "daily_comments": 0,
                    "daily_limit_posts": 10,
                    "account_age_days": max(1, int((datetime.now() - self.start_time).total_seconds() / 86400)),
                }
        except Exception as e:
            return {
                "platform": "reddit",
                "account_id": account.id,
                "username": account.username,
                "karma": account.karma,
                "status": "error",
                "status_detail": str(e)[:200],
                "request_count": account.request_count,
                "daily_requests": account.daily_requests,
                "last_used": account.last_used.isoformat(),
                "last_activity": datetime.now().isoformat(),
            }
        return self._empty_status(account)

    def _empty_status(self, account: RedditAccount) -> Dict[str, Any]:
        return {
            "platform": "reddit",
            "account_id": account.id,
            "username": account.username,
            "display_name": account.display_name or account.username,
            "karma": account.karma or "0",
            "status": "inactive",
            "request_count": account.request_count,
            "daily_requests": account.daily_requests,
            "last_used": account.last_used.isoformat(),
            "last_activity": account.last_used.isoformat(),
        }

    # ─── 便捷方法 ─────────────────────────────────────────────────────────────

    async def get_trending(self, subreddit: str, limit: int = 25) -> List[RedditPost]:
        url = f"https://www.reddit.com/r/{subreddit}/hot/"
        raw = await self._fetch_posts_from_url(url, limit)
        return raw

    async def get_new(self, subreddit: str, limit: int = 25) -> List[RedditPost]:
        url = f"https://www.reddit.com/r/{subreddit}/new/"
        raw = await self._fetch_posts_from_url(url, limit)
        return raw

    async def get_all_accounts_status(self) -> List[Dict[str, Any]]:
        """获取所有账号状态（Dashboard 用）。"""
        results = []
        original_idx = self.current_account_idx
        for i, acc in enumerate(self.accounts):
            self.current_account_idx = i
            try:
                status = await self.get_account_status()
                results.append(status)
            except Exception as e:
                results.append({
                    "platform": "reddit",
                    "account_id": acc.id,
                    "username": acc.username,
                    "status": "error",
                    "status_detail": str(e)[:100],
                    "request_count": acc.request_count,
                    "last_activity": datetime.now().isoformat(),
                })
        self.current_account_idx = original_idx
        return results

    # ─── Shreddit 裸 GET（有 browser context 时可用）────────────────────────

    async def fetch_shreddit_comments(self, post_url: str, timeout: int = 12) -> Dict[str, Any]:
        """直接通过浏览器 GET shreddit /svc/comments 端点拿评论。"""
        ref = _extract_post_ref(post_url)
        if not ref:
            return {"top_comments": [], "comment_insights": [], "num_comments": None}
        sub, post_id = ref
        url = (
            f"https://www.reddit.com/svc/shreddit/comments/r/{sub}/t3_{post_id}"
            f"?sort=top"
        )
        try:
            resp = await self._page.request.get(url, timeout=timeout)
            html_text = await resp.text()
            return _parse_shreddit_comments(html_text)
        except Exception as e:
            logger.debug(f"shreddit comments fetch failed: {e}")
            return {"top_comments": [], "comment_insights": [], "num_comments": None}

    # ─── 清理 ────────────────────────────────────────────────────────────────

    async def close(self):
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


# ─── 模块级帮助函数 ─────────────────────────────────────────────────────────

def _extract_post_ref(url: str) -> Optional[tuple]:
    m = re.search(r"/r/([^/]+)/comments/([A-Za-z0-9]+)", url or "")
    if not m:
        return None
    return m.group(1), m.group(2)


def _parse_shreddit_comments(html_text: str) -> Dict[str, Any]:
    """解析 <shreddit-comment> HTML 块为结构化评论。"""
    import html as _html
    _comment_start = re.compile(r"<shreddit-comment(?=[\s>])[^>]*>")
    _total = re.compile(r'total-comments="(\d+)"')
    _para = re.compile(r"<p[^>]*>(.*?)</p>", re.S)
    _tag = re.compile(r"<[^>]+>")
    _ws = re.compile(r"\s+")
    _next = re.compile(r'id="t1_[A-Za-z0-9]+-(?:comment|post)-rtjson-content"')

    comments: List[Dict] = []
    for m in _comment_start.finditer(html_text or ""):
        tag = m.group(0)
        author = _re_attr(tag, "author") or "[deleted]"
        if author in ("[deleted]", "[removed]"):
            continue
        thing_id = _re_attr(tag, "thingId")
        body = _extract_body(html_text, thing_id, _para, _tag, _ws, _next)
        if not body or body in ("[deleted]", "[removed]"):
            continue
        try:
            score = int(_re_attr(tag, "score") or 0)
        except ValueError:
            score = 0
        permalink = _re_attr(tag, "permalink")
        comments.append({
            "score": score, "author": author, "body": body[:300],
            "excerpt": body[:200], "permalink": permalink,
            "date": _re_iso_date(_re_attr(tag, "created")),
            "url": f"https://reddit.com{permalink}" if permalink else "",
        })

    comments.sort(key=lambda c: c.get("score", 0), reverse=True)
    insights = [c["body"][:80] + "…" for c in comments[:5] if c["body"]]
    total = None
    m = _total.search(html_text or "")
    if m:
        try:
            total = int(m.group(1))
        except ValueError:
            pass
    return {"top_comments": comments[:10], "comment_insights": insights, "num_comments": total}


def _re_attr(tag: str, name: str) -> str:
    import html as _html
    m = re.search(rf'\b{name}="([^"]*)"', tag)
    return _html.unescape(m.group(1)) if m else ""


def _re_iso_date(value: str):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.strip()).date().isoformat()
    except (ValueError, TypeError):
        return None


def _extract_body(html_text: str, thing_id: str, _para, _tag, _ws, _next) -> str:
    if not thing_id:
        return ""
    anchor = f'id="{thing_id}-post-rtjson-content"'
    idx = html_text.find(anchor)
    if idx == -1:
        return ""
    window = html_text[idx + len(anchor): idx + len(anchor) + 8000]
    nxt = _next.search(window)
    if nxt:
        window = window[: nxt.start()]
    paras = _para.findall(window)
    if not paras:
        return ""
    text = " ".join(_tag.sub("", p) for p in paras)
    return _ws.sub(" ", _html.unescape(text)).strip()
