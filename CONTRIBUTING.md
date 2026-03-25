# Contributing to X-Agent

感谢你考虑为 X-Agent 做贡献！

## 如何贡献

### 报告 Bug
1. 在 [Issues](https://github.com/sheldon010507-collab/x-agent/issues) 中搜索是否已有相关问题
2. 如果没有，创建新 Issue，包含：
   - 清晰的标题
   - 复现步骤
   - 期望行为
   - 实际行为
   - 环境信息（Python版本、操作系统等）

### 提交功能请求
1. 在 Issues 中创建新 Issue
2. 标签为 `enhancement`
3. 描述功能需求和使用场景

### 提交代码

#### 开发环境设置
```bash
# Fork 仓库后
git clone https://github.com/你的用户名/x-agent.git
cd x-agent

# 创建分支
git checkout -b feature/你的功能名

# 安装开发依赖
pip install -r requirements.txt
pip install pytest pytest-asyncio
```

#### 代码规范
- 遵循 PEP 8 风格指南
- 添加类型注解
- 编写文档字符串
- 添加单元测试

#### 提交 PR
1. 确保所有测试通过：`pytest tests/`
2. 提交代码：`git commit -m "feat: 描述你的改动"`
3. 推送到你的 Fork：`git push origin feature/你的功能名`
4. 创建 Pull Request

#### Commit 消息格式
- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 其他改动

## 行为准则
- 尊重所有贡献者
- 建设性的讨论和反馈
- 欢迎不同背景的贡献者

## 许可证
通过提交代码，你同意你的贡献将在 MIT 许可证下授权。

---

感谢你的贡献！ 🎉
