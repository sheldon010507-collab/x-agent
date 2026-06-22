"""
http.py — 通用 HTTP 客户端

提供统一 UA / proxy / gzip / 超时的 GET 文本能力，避免各 fetcher 重复造轮子。
"""

from __future__ import annotations

import gzip
import logging
import time
from typing import Optional
from urllib.parse import quote

from .config import HTTP_PROXY, USER_AGENT

try:
    import aiohttp  # type: ignore

    HAS_AIOHTTP = True
except ImportError:  # pragma: no cover - 测试环境可能没装
    HAS_AIOHTTP = False

try:
    import httpx  # type: ignore

    HAS_HTTPX = True
except ImportError:  # pragma: no cover
    HAS_HTTPX = False

logger = logging.getLogger(__name__)


async def get_text_async(
    url: str,
    timeout: float = 15.0,
    accept: Optional[str] = None,
    max_retries: int = 2,
) -> Optional[str]:
    """异步取文本，自动解 gzip，失败返回 None（不抛异常）。"""
    if not HAS_AIOHTTP:
        return None

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": accept or "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    proxy = HTTP_PROXY

    last_err: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    proxy=proxy,
                ) as resp:
                    if resp.status == 429:
                        wait = float(resp.headers.get("Retry-After", "2"))
                        logger.warning(f"429 for {url}, sleep {wait}s")
                        await _sleep(wait)
                        continue
                    if resp.status >= 400:
                        logger.debug(f"HTTP {resp.status} for {url}")
                        return None
                    body = await resp.read()
                    if resp.headers.get("Content-Encoding", "").lower() == "gzip":
                        body = gzip.decompress(body)
                    return body.decode("utf-8", errors="replace")
        except Exception as e:  # pragma: no cover - 网络错误时
            last_err = e
            logger.debug(f"get_text_async ({url}) attempt {attempt} failed: {e}")
            await _sleep(0.5 * (2**attempt))

    logger.debug(f"get_text_async gave up on {url}: {last_err}")
    return None


def get_text(
    url: str,
    timeout: float = 15.0,
    accept: Optional[str] = None,
    max_retries: int = 2,
) -> Optional[str]:
    """同步取文本（兜底，依赖 httpx）。"""
    if not HAS_HTTPX:
        logger.debug("httpx not installed; cannot use sync get_text")
        return None
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": accept or "*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    proxy = HTTP_PROXY

    with httpx.Client(timeout=timeout, proxy=proxy, follow_redirects=True) as client:
        last_err: Optional[Exception] = None
        for attempt in range(max_retries + 1):
            try:
                resp = client.get(url, headers=headers)
                if resp.status_code == 429:
                    wait = float(resp.headers.get("Retry-After", "2"))
                    time.sleep(wait)
                    continue
                if resp.status_code >= 400:
                    return None
                body = resp.content
                if resp.headers.get("content-encoding", "").lower() == "gzip":
                    body = gzip.decompress(body)
                return body.decode("utf-8", errors="replace")
            except Exception as e:
                last_err = e
                time.sleep(0.5 * (2**attempt))
        logger.debug(f"get_text gave up on {url}: {last_err}")
        return None


async def _sleep(seconds: float) -> None:
    import asyncio

    await asyncio.sleep(seconds)


def url_encode(text: str) -> str:
    return quote(text, safe="")
