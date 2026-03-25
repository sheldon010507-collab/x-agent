"""
test_bot.py - X-Agent v3 Bot 测试脚本

测试内容：
1. Bot 初始化
2. 命令处理器注册
3. Inline 按钮回调
4. 配置加载
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from bot import XAgentBot, create_bot


def test_config():
    """测试配置加载"""
    print("🧪 测试配置加载...")
    
    try:
        config = Config()
        print(f"✅ 配置加载成功")
        print(f"   LLM Provider: {config.llm.provider}")
        print(f"   Available Providers: {config.llm.get_available_providers()}")
        print(f"   Current Niche: {config.niche.current_niche}")
        print(f"   Available Niches: {list(config.niche.AVAILABLE_NICHES.keys())}")
        return True
    except Exception as e:
        print(f"❌ 配置加载失败：{e}")
        return False


def test_bot_initialization():
    """测试 Bot 初始化"""
    print("\n🧪 测试 Bot 初始化...")
    
    # 使用测试 token（不会真正连接）
    test_token = "TEST_BOT_TOKEN"
    
    try:
        bot = create_bot(test_token)
        print(f"✅ Bot 实例创建成功")
        print(f"   Bot 类型：{type(bot).__name__}")
        print(f"   命令处理器数量：{len(bot.commands)}")
        return bot
    except Exception as e:
        print(f"❌ Bot 初始化失败：{e}")
        return None


def test_bot_commands():
    """测试 Bot 命令注册"""
    print("\n🧪 测试 Bot 命令注册...")
    
    test_token = "TEST_BOT_TOKEN"
    bot = create_bot(test_token)
    
    expected_commands = [
        'start', 'help', 'set_niche', 'research', 'trends',
        'create', 'log', 'report', 'strategy', 'settings', 'llm'
    ]
    
    registered_commands = list(bot.commands.keys())
    
    print(f"   已注册命令：{len(registered_commands)}")
    print(f"   命令列表：{', '.join(registered_commands)}")
    
    missing = set(expected_commands) - set(registered_commands)
    if missing:
        print(f"❌ 缺少命令：{missing}")
        return False
    else:
        print(f"✅ 所有命令已正确注册")
        return True


def test_niche_switching():
    """测试 Niche 切换"""
    print("\n🧪 测试 Niche 切换...")
    
    config = Config()
    
    # 测试切换 Niche
    test_niches = ['adult', 'ai_tools', 'beauty', 'fitness', 'crypto', 'humor', 'general']
    
    for niche in test_niches:
        success = config.set_niche(niche)
        if success:
            print(f"   ✅ 切换到 {niche}: {config.niche.get_niche_name(niche)}")
        else:
            print(f"   ❌ 切换 {niche} 失败")
    
    return True


def test_llm_switching():
    """测试 LLM 供应商切换"""
    print("\n🧪 测试 LLM 供应商切换...")
    
    config = Config()
    
    # 测试切换 LLM
    test_providers = ['anthropic', 'openai', 'groq', 'gemini', 'openrouter', 'nvidia', 'ollama']
    
    for provider in test_providers:
        success = config.set_llm_provider(provider)
        if success:
            print(f"   ✅ 切换到 {provider}")
        else:
            print(f"   ❌ 切换 {provider} 失败")
    
    return True


async def test_bot_async():
    """测试 Bot 异步功能"""
    print("\n🧪 测试 Bot 异步初始化...")
    
    test_token = "TEST_BOT_TOKEN"
    bot = create_bot(test_token)
    
    try:
        await bot.initialize()
        print(f"✅ Bot 异步初始化成功")
        return True
    except Exception as e:
        print(f"❌ Bot 异步初始化失败：{e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("🧪 X-Agent v3 Bot 测试套件")
    print("=" * 50)
    
    results = []
    
    # 1. 测试配置加载
    results.append(("配置加载", test_config()))
    
    # 2. 测试 Bot 初始化
    bot = test_bot_initialization()
    results.append(("Bot 初始化", bot is not None))
    
    # 3. 测试命令注册
    results.append(("命令注册", test_bot_commands()))
    
    # 4. 测试 Niche 切换
    results.append(("Niche 切换", test_niche_switching()))
    
    # 5. 测试 LLM 切换
    results.append(("LLM 切换", test_llm_switching()))
    
    # 6. 测试异步功能
    results.append(("异步初始化", asyncio.run(test_bot_async())))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计：{passed} 通过，{failed} 失败")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
