# X (Twitter) 浏览器自动化设置指南

## 概览

X-Agent 使用 **Playwright 无头浏览器自动化** 来实现 X (Twitter) 自动发帖、评论、点赞等功能。

**关键特点**：
- ✅ 免费（无需 $100/月 的 X API 费用）
- ✅ 无头浏览器（自动化，无需人工干预）
- ⚠️ 风险：X 2026 年风控很强，容易封号
- 🔐 安全：登录状态本地保存，不上传服务器

---

## 安装依赖

### 1. 安装 Python 包

```bash
cd x-agent/x-agent
pip install -r requirements.txt
```

这会自动安装 `playwright>=1.40.0`

### 2. 安装 Playwright 浏览器驱动

```bash
playwright install chromium
```

或者安装所有浏览器（可选）：

```bash
playwright install
```

### 3. 验证安装

```bash
python -c "from playwright.async_api import async_playwright; print('✅ Playwright 已安装')"
```

---

## 初始化 X 登录

### 方式 A：通过 Python CLI（推荐）

创建 `login_x.py`：

```python
import asyncio
from x_agent.modules.x_automation import create_x_automation

async def main():
    automation = await create_x_automation()

    # 请输入你的 X 账号凭证
    email = input("邮箱或用户名: ")
    password = input("密码: ")

    success = await automation.login(email, password)

    if success:
        print("✅ 登录成功！Session 已保存到: ~/.x-agent/sessions/x_auth_state.json")
        print("⚠️ 请妥善保管此文件，它包含你的登录状态")
    else:
        print("❌ 登录失败，请检查邮箱和密码")

    await automation.close()

if __name__ == "__main__":
    asyncio.run(main())
```

运行：

```bash
python login_x.py
```

### 方式 B：通过 Telegram Bot

当你首次运行 X-Agent 时：

```bash
python main.py
```

在 Telegram 中发送：

```
/xconfigure
```

Bot 会提示你输入 X 账号和密码，然后保存 session。

---

## 文件位置

登录后，session 会保存到：

```
~/.x-agent/
└── sessions/
    └── x_auth_state.json    # 登录状态（包含 cookies）
```

**⚠️ 安全提示**：
- 不要将此文件上传到 GitHub
- 不要在公共计算机上使用此文件
- 如果账号被封，删除此文件并用新账号重新登录

---

## 环境变量配置

在 `.env` 中配置防封参数：

```bash
# 防封配置
DELAY_MIN=10            # 最小延迟（秒）
DELAY_MAX=40            # 最大延迟（秒）
MAX_POSTS_PER_DAY=10    # 每日最多发帖数
MAX_COMMENTS_PER_DAY=15 # 每日最多评论数
MAX_LIKES_PER_DAY=30    # 每日最多点赞数
```

---

## 使用流程

### 1. Telegram Bot 生成内容

```
/create a
```

Bot 会生成 A 类推文（3 条备选）

### 2. 人工确认

点击 Inline 按钮：

```
✅ 人工确认发布
```

会弹出二次确认对话框

### 3. 自动发帖到 X

确认后，内容自动发布到 X！

```
POST https://x.com/...
```

### 4. 查看状态

```
/status
```

显示当前发帖数、评论数、点赞数等

---

## 防封机制

### 1. 随机延迟

每次操作前随机延迟 10-40 秒（从 `.env` 配置）

```python
delay = random.uniform(DELAY_MIN, DELAY_MAX)
await asyncio.sleep(delay)
```

### 2. 内容变体

自动添加不同 emoji 和短语，避免被检测为重复内容

```python
content = "新推文内容"
# 自动变成：
# "新推文内容 🔥"
# "新推文内容 Interesting."
# "新推文内容 💭"
```

### 3. 每日上限

内置每日操作限额，防止一次性操作过多导致封号

```bash
# .env
MAX_POSTS_PER_DAY=10
MAX_COMMENTS_PER_DAY=15
MAX_LIKES_PER_DAY=30
```

### 4. 必须的人工确认

**所有内容发布都需要人工二次确认**，无自动发布路径

```
生成内容 → ✅ 人工确认 → ⚠️ 二次确认 → 发布
```

---

## 常见问题

### Q: Session 过期了怎么办？

A: 重新运行 `login_x.py` 或在 Telegram 中使用 `/xconfigure` 重新登录

### Q: 怎样查看当前有多少条推文已发布？

A: 在 Telegram 中发送 `/status`，会显示今日发帖数、评论数等

### Q: 能否只评论，不发帖？

A: 可以。在 `.env` 中设置：

```bash
# 仅启用评论自动化
AUTO_COMMENT_ENABLED=true
AUTO_POST_ENABLED=false
AUTO_LIKE_ENABLED=false
```

### Q: 账号被封了怎么办？

A:
1. 删除 `~/.x-agent/sessions/x_auth_state.json`
2. 用新账号或不同邮箱重新注册 X
3. 重新运行 `login_x.py` 保存新 session
4. **建议用小号测试，不要用主账号**

### Q: 为什么发帖失败？

常见原因：
1. Session 过期 → 重新登录
2. X 账号被限制 → 检查 X 应用设置
3. 网络问题 → 检查网络连接
4. 浏览器崩溃 → 检查内存使用

查看日志：

```bash
tail -f ~/.x-agent/x_agent.log
```

---

## 架构图

```
Telegram Bot
    ↓
ContentGenerator (A/B/C 类内容)
    ↓
人工确认（Inline 按钮）
    ↓
二次确认对话框
    ↓
X 自动化 (x_automation.py)
    ↓
Playwright 浏览器
    ↓
X.com
```

---

## 性能指标

| 操作 | 平均耗时 | 备注 |
|------|---------|------|
| 发帖 | 5-10 秒 | 含随机延迟 |
| 评论 | 5-10 秒 | 含随机延迟 |
| 点赞 | 2-5 秒 | 延迟较短 |
| 转发 | 5-10 秒 | 含随机延迟 |

---

## 故障排查

### 浏览器无法启动

```bash
# 确保 Chromium 已安装
playwright install chromium

# 检查权限
chmod 755 ~/.local/share/ms-playwright/chromium-*/chrome-linux/chrome
```

### Session 加载失败

```bash
# 删除过期的 session
rm ~/.x-agent/sessions/x_auth_state.json

# 重新登录
python login_x.py
```

### 网络超时

增加超时时间（在 `x_automation.py` 中修改）：

```python
await self.page.goto(url, wait_until="networkidle", timeout=30000)  # 30 秒
```

---

## 下一步

1. ✅ 安装依赖：`pip install -r requirements.txt`
2. ✅ 安装浏览器：`playwright install chromium`
3. ✅ 初始登录：`python login_x.py`
4. ✅ 启动 Bot：`python main.py`
5. ✅ Telegram 测试：`/create a` 然后 `/status`

祝你使用愉快！如有问题，查看日志文件或参考常见问题部分。
