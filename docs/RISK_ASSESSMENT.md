# X-Agent Risk Assessment

Updated: 2026-06-22

## 1. Account Enforcement Risk

- Frequent posting, liking, commenting, or retweeting can trigger platform automation defenses.
- Repeated AI-generated wording can be classified as spam.
- Sensitive niches, including adult, political, medical, and financial topics, require stricter review.
- Multi-account rotation can increase correlation risk if timing, content, or browser fingerprints are similar.

Controls:
- Manual approval is required before publishing generated content.
- Daily limits should remain conservative per account and per action type.
- Browser automation should use cooldowns and avoid burst behavior.

## 2. API and Automation Limits

- X, Reddit, Google Trends, TikTok, and YouTube can rate-limit or block automated access.
- Playwright scraping can fail when page structure, login flow, or anti-automation checks change.
- Mock fallback data can hide upstream collection failures if not surfaced in reports.

Controls:
- Track source failures and mock fallbacks explicitly.
- Prefer read-only collection without login where possible.
- Keep retry/backoff bounded.

## 3. Legal and Platform Policy Risk

- Content must comply with platform terms and local law.
- Adult content needs age-gating, jurisdiction checks, and careful wording.
- Reused images, videos, and post text may create copyright or privacy issues.

Controls:
- Keep human review in the publish path.
- Store citations and source URLs for generated content.
- Avoid publishing private messages or personal data.

## 4. Data Leakage Risk

- API keys, Telegram tokens, X credentials, cookies, and browser session files are sensitive.
- Compose files, docs, logs, screenshots, and test fixtures can accidentally leak secrets.

Controls:
- Store secrets only in `.env` or a secret manager.
- Rotate any credential that was committed or shared.
- Never put real tokens in documentation examples.

## 5. Misoperation Risk

- A wrong account, wrong niche, or wrong publish target can cause reputational damage.
- API endpoints that trigger posting or engagement must not be public without authentication.

Controls:
- Require `XAGENT_API_KEY` for action endpoints.
- Keep publish confirmation two-step.
- Log action, account, target URL, and operator-visible status for each run.
