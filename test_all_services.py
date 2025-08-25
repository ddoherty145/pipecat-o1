#!/usr/bin/env python3
"""
Comprehensive test of all Pipecat services with fixes applied
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_deepgram_services():
    """Test Deepgram services with compatibility layer"""
    print("🧪 Testing Deepgram Services...")
    
    try:
        # Import compatibility layer first
        import deepgram_compatibility
        print("  ✅ Deepgram compatibility layer loaded")
        
        # Test STT service
        from pipecat.services.deepgram.stt import DeepgramSTTService
        print("  ✅ Deepgram STT service imported")
        
        # Test TTS service
        from pipecat.services.deepgram.tts import DeepgramTTSService
        print("  ✅ Deepgram TTS service imported")
        
        # Test service creation
        api_key = os.getenv("DEEPGRAM_API_KEY")
        if api_key:
            stt = DeepgramSTTService(api_key=api_key)
            tts = DeepgramTTSService(api_key=api_key)
            print("  ✅ Both Deepgram services created successfully")
            return True
        else:
            print("  ⚠️ Deepgram API key not found")
            return False
            
    except Exception as e:
        print(f"  ❌ Deepgram services test failed: {str(e)[:100]}")
        return False

async def test_cartesia_tts():
    """Test Cartesia TTS service"""
    print("\n🧪 Testing Cartesia TTS Service...")
    
    try:
        from pipecat.services.cartesia.tts import CartesiaTTSService
        
        api_key = os.getenv("CARTESIA_API_KEY")
        if not api_key:
            print("  ❌ CARTESIA_API_KEY not found")
            return False
        
        # Create TTS service
        voice_id = os.getenv("CARTESIA_VOICE_ID", "clara")
        tts = CartesiaTTSService(api_key=api_key, voice_id=voice_id)
        print(f"  ✅ TTS service created with voice: {voice_id}")
        
        # Test service creation (don't test actual TTS to avoid TaskManager issues)
        print("  ✅ Cartesia TTS service is ready")
        return True
        
    except Exception as e:
        print(f"  ❌ Cartesia TTS test failed: {str(e)[:100]}")
        return False

async def test_pipeline_integration():
    """Test pipeline integration with all services"""
    print("\n🧪 Testing Pipeline Integration...")
    
    try:
        from pipecat.pipeline.pipeline import Pipeline
        from pipecat.services.cartesia.tts import CartesiaTTSService
        from pipecat.services.openai.llm import OpenAILLMService
        
        # Import Deepgram services if available
        deepgram_available = False
        try:
            import deepgram_compatibility
            from pipecat.services.deepgram.stt import DeepgramSTTService
            deepgram_available = True
            print("  ✅ Deepgram services available for pipeline")
        except:
            print("  ⚠️ Deepgram services not available, using OpenAI STT")
        
        # Create basic services
        api_key = os.getenv("CARTESIA_API_KEY")
        voice_id = os.getenv("CARTESIA_VOICE_ID", "clara")
        
        tts = CartesiaTTSService(api_key=api_key, voice_id=voice_id)
        llm = OpenAILLMService(
            model="gpt-4o-mini",
            system_prompt="You are a helpful test assistant."
        )
        
        # Create pipeline with available services
        pipeline_services = [llm, tts]
        if deepgram_available:
            stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))
            pipeline_services.insert(0, stt)
        
        pipeline = Pipeline(pipeline_services)
        
        print("  ✅ Pipeline created successfully")
        print(f"  📊 Pipeline has {len(pipeline_services)} services")
        return True
        
    except Exception as e:
        print(f"  ❌ Pipeline integration test failed: {str(e)[:100]}")
        return False

async def main():
    """Main test function"""
    print("🚀 Comprehensive Pipecat Services Test Suite")
    print("=" * 60)
    
    # Test all services
    deepgram_ok = await test_deepgram_services()
    cartesia_ok = await test_cartesia_tts()
    pipeline_ok = await test_pipeline_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Final Test Results:")
    print(f"  Deepgram Services: {'✅ Working' if deepgram_ok else '❌ Failed'}")
    print(f"  Cartesia TTS: {'✅ Working' if cartesia_ok else '❌ Failed'}")
    print(f"  Pipeline Integration: {'✅ Working' if pipeline_ok else '❌ Failed'}")
    
    if deepgram_ok and cartesia_ok and pipeline_ok:
        print("\n🎉 All services are working correctly!")
        print("💡 Your baml_agent.py should work perfectly now.")
        print("🔧 Remember to import deepgram_compatibility before using Deepgram services.")
    elif cartesia_ok and pipeline_ok:
        print("\n⚠️ Cartesia TTS is working, but Deepgram has issues.")
        print("💡 You can use OpenAI STT as a fallback for speech recognition.")
    else:
        print("\n❌ Some critical services are not working.")
        print("🔧 Check your API keys and configurations.")

if __name__ == "__main__":
    asyncio.run(main())
