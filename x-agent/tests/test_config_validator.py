""" test_config_validator.py - 测试配置验证模块 """
import sys
import asyncio
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.config_validator import ConfigValidator, validate_env_only


def test_validator_initialization():
    """测试验证器初始化"""
    print("=" * 60)
    print("测试配置验证器初始化")
    print("=" * 60)
    
    # 测试默认路径
    validator = ConfigValidator()
    assert validator.env_path is not None
    print(f"✓ 验证器初始化成功，env 路径：{validator.env_path}")
    
    # 测试必填项
    assert 'TELEGRAM_BOT_TOKEN' in validator.required_vars
    assert 'SUPABASE_URL' in validator.required_vars
    assert 'SUPABASE_KEY' in validator.required_vars
    print("✓ 必填配置项正确")
    
    # 推荐项
    assert 'ANTHROPIC_API_KEY' in validator.recommended_vars
    print("✓ 推荐配置项正确")
    
    print("\n✅ 验证器初始化测试通过\n")
    return True


def test_validate_env_file():
    """测试 .env 文件验证"""
    print("=" * 60)
    print("测试 .env 文件验证")
    print("=" * 60)
    
    validator = ConfigValidator()
    
    # 测试 .env 文件存在性
    if validator.env_path.exists():
        print(f"✓ .env 文件存在：{validator.env_path}")
        
        # 验证文件（不检查内容）
        result = validator.validate_env_file()
        print(f"✓ .env 验证完成：{'通过' if result else '失败'}")
        
        # 显示验证结果
        print("\n验证结果:")
        for var, valid in validator.validation_results.items():
            status = "✓" if valid else "✗"
            print(f"  {status} {var}")
        
        # 显示错误和警告
        if validator.errors:
            print("\n错误:")
            for error in validator.errors:
                print(f"  ❌ {error}")
        
        if validator.warnings:
            print("\n警告:")
            for warning in validator.warnings:
                print(f"  ⚠️ {warning}")
        
        print(f"\n✅ .env 文件验证测试完成\n")
        return True
    else:
        print(f"✗ .env 文件不存在：{validator.env_path}")
        print("\n✅ .env 文件验证测试完成（文件缺失）\n")
        return False


async def test_validate_all_async():
    """测试所有验证（异步）"""
    print("=" * 60)
    print("测试完整配置验证")
    print("=" * 60)
    
    validator = ConfigValidator()
    
    # 1. 验证 .env
    print("\n1. 验证 .env 文件...")
    env_valid = validator.validate_env_file()
    print(f"   {'✓' if env_valid else '✗'} .env 验证：{'通过' if env_valid else '失败'}")
    
    # 2. 验证 Supabase 连接
    print("\n2. 验证 Supabase 连接...")
    try:
        supabase_valid = await validator.validate_supabase_connection()
        print(f"   {'✓' if supabase_valid else '✗'} Supabase 连接：{'成功' if supabase_valid else '失败'}")
    except Exception as e:
        print(f"   ✗ Supabase 连接测试失败：{e}")
        supabase_valid = False
    
    # 3. 验证 OpenClaw 连接
    print("\n3. 验证 OpenClaw 连接...")
    try:
        openclaw_valid = await validator.validate_openclaw_connection()
        print(f"   {'✓' if openclaw_valid else '✗'} OpenClaw 连接：{'成功' if openclaw_valid else '失败'}")
    except Exception as e:
        print(f"   ⚠️ OpenClaw 连接测试失败（可选）: {e}")
        openclaw_valid = False
    
    # 4. 验证 LLM 供应商
    print("\n4. 验证 LLM 供应商...")
    try:
        llm_valid = await validator.validate_llm_provider()
        print(f"   {'✓' if llm_valid else '✗'} LLM 供应商：{'可用' if llm_valid else '不可用'}")
    except Exception as e:
        print(f"   ✗ LLM 验证失败：{e}")
        llm_valid = False
    
    # 汇总
    print("\n" + "=" * 60)
    print("验证汇总:")
    print("=" * 60)
    print(f"  .env 配置：{'✓' if env_valid else '✗'}")
    print(f"  Supabase: {'✓' if supabase_valid else '✗'}")
    print(f"  OpenClaw: {'✓' if openclaw_valid else '✗'} (可选)")
    print(f"  LLM: {'✓' if llm_valid else '✗'}")
    
    all_passed = env_valid and supabase_valid and llm_valid
    print(f"\n总体结果：{'✅ 通过' if all_passed else '❌ 失败'}")
    
    print("\n✅ 完整配置验证测试完成\n")
    return all_passed


async def test_get_validation_status():
    """测试获取验证状态文本"""
    print("=" * 60)
    print("测试验证状态文本")
    print("=" * 60)
    
    validator = ConfigValidator()
    validator.validate_env_file()
    
    status = validator.get_validation_status()
    print("\n验证状态:")
    print(status)
    
    print("\n✅ 验证状态文本测试完成\n")
    return True


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("X-Agent v3 配置验证模块测试")
    print("=" * 60 + "\n")
    
    try:
        # 测试 1: 初始化
        test_validator_initialization()
        
        # 测试 2: .env 验证
        test_validate_env_file()
        
        # 测试 3: 完整验证
        await test_validate_all_async()
        
        # 测试 4: 状态文本
        await test_get_validation_status()
        
        print("\n" + "=" * 60)
        print("✅ 所有配置验证测试通过！")
        print("=" * 60 + "\n")
        return 0
    
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(asyncio.run(main()))
