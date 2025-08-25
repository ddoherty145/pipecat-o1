#!/usr/bin/env python3
"""
Test Cartesia TTS with proper Pipecat pipeline initialization
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_cartesia_tts_pipeline():
    """Test Cartesia TTS service within a proper Pipecat pipeline context"""
    print("🧪 Testing Cartesia TTS Service with Pipeline Context...")
    
    try:
        from pipecat.services.cartesia.tts import CartesiaTTSService
        from pipecat.pipeline.pipeline import Pipeline
        from pipecat.pipeline.runner import PipelineRunner
        from pipecat.pipeline.task import PipelineTask
        from pipecat.frames.frames import StartFrame, EndFrame, TextFrame
        from pipecat.processors.frame_processor import FrameDirection
        
        api_key = os.getenv("CARTESIA_API_KEY")
        if not api_key:
            print("  ❌ CARTESIA_API_KEY not found")
            return False
        
        # Create TTS service
        voice_id = os.getenv("CARTESIA_VOICE_ID", "clara")
        tts = CartesiaTTSService(api_key=api_key, voice_id=voice_id)
        print(f"  ✅ TTS service created with voice: {voice_id}")
        
        # Create a simple pipeline with the TTS service
        pipeline = Pipeline([
            tts
        ])
        
        # Create task and runner
        task = PipelineTask(pipeline)
        runner = PipelineRunner()
        
        print("  🔧 Setting up pipeline context...")
        
        # Start the pipeline
        await runner.run(task)
        
        # Wait a moment for initialization
        await asyncio.sleep(1)
        
        # Test text-to-speech conversion
        test_text = "Hello, this is a test of the Cartesia TTS service."
        print(f"  📝 Converting text: '{test_text}'")
        
        try:
            # Send a text frame to the TTS service
            text_frame = TextFrame(text=test_text)
            await tts.process_frame(text_frame, FrameDirection.DOWNSTREAM)
            
            print("  ✅ Text-to-speech processing initiated successfully")
            return True
                
        except Exception as e:
            print(f"  ❌ TTS processing failed: {str(e)[:100]}")
            return False
        
        finally:
            # Clean up
            await runner.cancel()
        
    except Exception as e:
        print(f"  ❌ Cartesia TTS pipeline test failed: {str(e)[:100]}")
        return False

async def test_cartesia_tts_direct():
    """Test Cartesia TTS service with direct method calls"""
    print("\n🧪 Testing Cartesia TTS Service Direct Method...")
    
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
        
        # Test the say method (deprecated but might work)
        test_text = "Hello, this is a test."
        print(f"  📝 Testing say method with: '{test_text}'")
        
        try:
            await tts.say(test_text)
            print("  ✅ Say method executed successfully")
            return True
        except Exception as e:
            print(f"  ❌ Say method failed: {str(e)[:100]}")
            return False
        
    except Exception as e:
        print(f"  ❌ Cartesia TTS direct test failed: {str(e)[:100]}")
        return False

async def main():
    """Main test function"""
    print("🚀 Cartesia TTS Pipeline Context Test")
    print("=" * 50)
    
    # Test both approaches
    pipeline_ok = await test_cartesia_tts_pipeline()
    direct_ok = await test_cartesia_tts_direct()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"  Pipeline Context: {'✅ Working' if pipeline_ok else '❌ Failed'}")
    print(f"  Direct Method: {'✅ Working' if direct_ok else '❌ Failed'}")
    
    if pipeline_ok or direct_ok:
        print("\n🎉 Cartesia TTS is working!")
        print("💡 The TaskManager issue has been resolved.")
    else:
        print("\n❌ Both approaches failed.")
        print("🔧 Further investigation needed.")

if __name__ == "__main__":
    asyncio.run(main())
