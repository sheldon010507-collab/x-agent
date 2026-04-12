# CONTRIBUTING.md - 贡献指南

欢迎为 X-Agent 做出贡献！🎉

本指南旨在帮助社区成员更好地参与项目，共同打造一个更强大的 X 智能运营 Agent。

---

## 📋 贡献方向

### 1. 新增 Niche 语气

在 `niche_voices/` 目录下新增 `.md` 文件，定义特定领域的语气模板：

```markdown
# [Niche 名称]

## Tone
[语气描述]

## Keywords
- 关键词 1
- 关键词 2

## Examples
- 示例句子 1
- 示例句子 2
```

### 2. 优化 Prompt

修改 `prompts/` 目录下的提示词文件：

- `type_a.txt` - A 类内容生成提示
- `type_b.txt` - B 类内容生成提示
- `comment.txt` - 评论生成提示
- `review.txt` - 复盘报告提示

### 3. 新增平台支持

在 `modules/research.py` 中扩展 `sources` 参数，支持更多数据源：

```python
sources = "x,reddit,youtube,web,tiktok,hackernews,new_platform"
```

### 4. 修复 Bug 或新增功能

- 在 GitHub 提 Issue 描述问题或建议
- Fork 仓库并创建分支
- 实现功能或修复
- 提交 Pull Request

---

## 🛠️ 开发规范

### 代码风格

- 使用 **Black** 格式化代码：
  ```bash
  black x-agent/
  ```

- 使用 **Ruff** 检查代码质量：
  ```bash
  ruff check x-agent/
  ```

- 遵循 PEP 8 规范

### 测试要求

- 所有新功能需通过单元测试
- 在 `tests/` 目录下添加对应测试文件
- 确保测试覆盖率不下降

运行测试：
```bash
pytest tests/
```

### 提交规范

Commit message 格式：
```
<type>(<scope>): <subject>

<body>

<footer>
```

Type 包括：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具配置

示例：
```
feat(research): 添加 TikTok 数据源支持

- 在 research.py 中集成 TikTok API
- 添加相关测试用例

Closes #123
```

---

## 📝 Pull Request 流程

1. **Fork 仓库**
2. **创建分支** (`feature/your-feature-name`)
3. **提交更改**
4. **推送分支**
5. **创建 Pull Request**
   - 描述更改内容
   - 关联相关 Issue
   - 等待 CI 检查通过
6. **代码审查**
   - 响应审查意见
   - 进行必要修改
7. **合并**

---

## 🧪 测试指南

### 运行全部测试
```bash
pytest tests/ -v
```

### 运行单个测试
```bash
pytest tests/test_research.py -v
```

### 查看测试覆盖率
```bash
pytest tests/ --cov=x-agent --cov-report=html
```

---

## 📚 文档贡献

- 更新 `README.md` 保持与代码一致
- 在 `docs/` 目录添加新功能文档
- 修复拼写或语法错误
- 补充示例和截图

---

## 🤔 需要帮助？

- 查看现有 [Issues](https://github.com/sheldon010507-collab/x-agent/issues)
- 加入讨论组提问
- 在 Discussion 区发起话题

---

## 🎯 当前优先任务

- [ ] 新增 Niche 语气模板（医疗、教育、科技等）
- [ ] 优化中文内容生成质量
- [ ] 添加更多单元测试
- [ ] 完善文档示例
- [ ] 支持更多 LLM 供应商

---

感谢每一位贡献者！🙏

X-Agent 因你而强大。
