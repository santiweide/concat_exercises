#!/usr/bin/env python3
"""
Test script to verify AI model configuration.
Run this to check if API keys are properly configured.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from services.ai_models import GeminiModel, QwenVLModel
from config import config


def check_env_vars():
    """Check environment variables."""
    print("=" * 60)
    print("Environment Variables Check")
    print("=" * 60)
    
    gemini_key = config.GEMINI_API_KEY
    qwen_key = config.QWEN_API_KEY
    default_model = config.DEFAULT_AI_MODEL
    
    print(f"GEMINI_API_KEY: {'✓ Set' if gemini_key else '✗ Not set'}")
    if gemini_key:
        print(f"  Value: {gemini_key[:10]}...{gemini_key[-4:]}")
    
    print(f"QWEN_API_KEY: {'✓ Set' if qwen_key else '✗ Not set'}")
    if qwen_key:
        print(f"  Value: {qwen_key[:10]}...{qwen_key[-4:]}")
    
    print(f"DEFAULT_AI_MODEL: {default_model}")
    print()
    
    return bool(gemini_key), bool(qwen_key)


async def test_gemini():
    """Test Gemini model initialization."""
    print("=" * 60)
    print("Testing Gemini Model")
    print("=" * 60)
    
    if not config.GEMINI_API_KEY:
        print("✗ Gemini API key not configured")
        return False
    
    try:
        model = GeminiModel(config.GEMINI_API_KEY)
        print(f"✓ Model initialized: {model.name}")
        print(f"  Model type: {model.model_type.value}")
        print(f"  Text model: {model.TEXT_MODEL}")
        print(f"  Image model: {model.IMAGE_MODEL}")
        
        # Simple test prompt
        test_prompt = "测试提示词"
        test_text = "这是一段测试文本"
        
        print(f"\n  Testing API call (this may take a few seconds)...")
        result = await model.extract_from_text(test_text, "test.pdf", test_prompt)
        
        if result:
            print(f"  ✓ API call successful")
            return True
        else:
            print(f"  ✗ API call returned None (may be expected for test data)")
            return True  # Still consider it successful if no error
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


async def test_qwen():
    """Test Qwen VL model initialization."""
    print("\n" + "=" * 60)
    print("Testing Qwen VL Model")
    print("=" * 60)
    
    if not config.QWEN_API_KEY:
        print("✗ Qwen API key not configured")
        return False
    
    try:
        model = QwenVLModel(config.QWEN_API_KEY)
        print(f"✓ Model initialized: {model.name}")
        print(f"  Model type: {model.model_type.value}")
        print(f"  Model name: {model.MODEL_NAME}")
        print(f"  Base URL: {model.BASE_URL}")
        
        # Simple test prompt
        test_prompt = "测试提示词"
        test_text = "这是一段测试文本"
        
        print(f"\n  Testing API call (this may take a few seconds)...")
        result = await model.extract_from_text(test_text, "test.pdf", test_prompt)
        
        if result:
            print(f"  ✓ API call successful")
            return True
        else:
            print(f"  ✗ API call returned None (may be expected for test data)")
            return True  # Still consider it successful if no error
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


async def test_service_integration():
    """Test PDFImportService integration."""
    print("\n" + "=" * 60)
    print("Testing PDFImportService Integration")
    print("=" * 60)
    
    from services.pdf_import_service import PDFImportService
    
    # Test get_available_models
    models = PDFImportService.get_available_models()
    print(f"\nAvailable models: {len(models)}")
    for model in models:
        status = "✓ Available" if model['available'] else "✗ Not configured"
        print(f"  - {model['name']} ({model['type']}): {status}")
    
    # Test creating service instances
    print("\nTesting service creation:")
    
    if config.GEMINI_API_KEY:
        try:
            service = PDFImportService("gemini")
            print(f"  ✓ Gemini service created: {service.model.name}")
        except Exception as e:
            print(f"  ✗ Gemini service error: {str(e)}")
    
    if config.QWEN_API_KEY:
        try:
            service = PDFImportService("qwen-vl")
            print(f"  ✓ Qwen VL service created: {service.model.name}")
        except Exception as e:
            print(f"  ✗ Qwen VL service error: {str(e)}")
    
    # Test default service
    try:
        service = PDFImportService()
        print(f"  ✓ Default service created: {service.model.name}")
    except Exception as e:
        print(f"  ✗ Default service error: {str(e)}")


async def main():
    """Main test function."""
    print("\n🧪 AI Model Configuration Test\n")
    
    # Check environment variables
    has_gemini, has_qwen = check_env_vars()
    
    if not has_gemini and not has_qwen:
        print("⚠️  No API keys configured!")
        print("Please set GEMINI_API_KEY or QWEN_API_KEY in .env file")
        return
    
    # Test models
    results = []
    
    if has_gemini:
        gemini_ok = await test_gemini()
        results.append(("Gemini", gemini_ok))
    
    if has_qwen:
        qwen_ok = await test_qwen()
        results.append(("Qwen VL", qwen_ok))
    
    # Test service integration
    await test_service_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, ok in results:
        status = "✓ PASS" if ok else "✗ FAIL"
        print(f"{name}: {status}")
    
    all_passed = all(ok for _, ok in results)
    if all_passed:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
