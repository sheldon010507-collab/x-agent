"""
stealth.py - 反检测：清理 webdriver 痕迹、伪装 UA、随机化指纹
"""

import random
from typing import Dict


# 真实浏览器 UA 池
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
]

LOCALES = ["en-US", "en-GB"]
TIMEZONES = ["America/New_York", "Europe/London", "America/Los_Angeles"]


def random_context_options() -> Dict:
    """生成随机化的 browser context 选项"""
    return {
        "user_agent": random.choice(USER_AGENTS),
        "viewport": random.choice(VIEWPORTS),
        "locale": random.choice(LOCALES),
        "timezone_id": random.choice(TIMEZONES),
        "device_scale_factor": 1,
        "is_mobile": False,
        "has_touch": False,
        "java_script_enabled": True,
    }


# 通过 init script 清理 navigator.webdriver 等指纹
STEALTH_INIT_SCRIPT = """
// 隐藏 webdriver 标识
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

// 伪造 plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
        { name: 'Native Client', filename: 'internal-nacl-plugin' },
    ],
});

// 伪造 languages
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });

// 修复 chrome.runtime
window.chrome = window.chrome || {};
window.chrome.runtime = window.chrome.runtime || {};

// 伪装 permissions
const originalQuery = window.navigator.permissions && window.navigator.permissions.query;
if (originalQuery) {
    window.navigator.permissions.query = (parameters) =>
        parameters.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : originalQuery(parameters);
}

// 伪造 hardwareConcurrency
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
"""


async def apply_stealth(context):
    """应用 stealth 反检测脚本到 browser context"""
    await context.add_init_script(STEALTH_INIT_SCRIPT)
    # 尝试用 playwright_stealth 库（如果安装了）
    try:
        from playwright_stealth import stealth_async  # noqa: F401
        # 注意：playwright_stealth 应用在 page 级别，留给 manager 处理
    except ImportError:
        pass
