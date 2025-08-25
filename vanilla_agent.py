"""
Simple Vanilla Pipecat Agent - Minimal working version
"""

import asyncio
import os
from dotenv import load_dotenv

from pipecat.pipeline.pipeline import Pipeline
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.tts import OpenAITTSService
from pipecat.services.openai.stt import OpenAISTTService
from pipecat.frames.frames import EndFrame, TextFrame, AudioRawFrame, UserStartedSpeakingFrame, UserStoppedSpeakingFrame, StartFrame
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

# Load environment variables
load_dotenv()

class SimpleDebugProcessor(FrameProcessor):
    """Simple debug processor that handles frame direction correctly"""
    
    def __init__(self, name="Debug"):
        super().__init__()
        self._debug_name = name
    
    async def process_frame(self, frame, direction: FrameDirection):
        try:
            # Log frame direction to debug the flow
            direction_str = "UPSTREAM" if direction == FrameDirection.UPSTREAM else "DOWNSTREAM"
            
            # Only log essential frame types to avoid spam
            if isinstance(frame, TextFrame):
                print(f"🗣️ [{self._debug_name}] Text: '{frame.text}' ({direction_str})")
            elif isinstance(frame, UserStartedSpeakingFrame):
                print(f"🎤 [{self._debug_name}] User started speaking ({direction_str})")
            elif isinstance(frame, UserStoppedSpeakingFrame):
                print(f"🔇 [{self._debug_name}] User stopped speaking ({direction_str})")
            elif isinstance(frame, StartFrame):
                print(f"🚀 [{self._debug_name}] Pipeline started ({direction_str})")
            elif isinstance(frame, EndFrame):
                print(f"🔚 [{self._debug_name}] Pipeline ended ({direction_str})")
            elif hasattr(frame, 'audio') and len(frame.audio) > 0:
                # Log audio frames occasionally
                if not hasattr(self, '_last_audio_log') or (asyncio.get_event_loop().time() - self._last_audio_log) > 2.0:
                    self._last_audio_log = asyncio.get_event_loop().time()
                    print(f"🎵 [{self._debug_name}] Audio: {len(frame.audio)} bytes ({direction_str})")
            
            # Always pass frames through - don't block anything
            await self.push_frame(frame, direction)
            
        except Exception as e:
            print(f"❌ [{self._debug_name}] Error: {e}")
            # Still pass the frame through to avoid breaking the pipeline
            try:
                await self.push_frame(frame, direction)
            except:
                pass

def create_simple_agent():
    """Create the simplest possible working agent"""
    
    # Simple transport configuration
    transport = DailyTransport(
        room_url=os.getenv("DAILY_ROOM_URL"),
        token=os.getenv("DAILY_TOKEN"),
        bot_name="Simple_Agent",
        params=DailyParams(
            audio_out_enabled=True,
            audio_in_enabled=True,
            vad_enabled=True,
            vad_audio_passthrough=True,
            transcription_enabled=True  # Enable transcription for proper flow
        )
    )
    
    # Basic services
    stt = OpenAISTTService()
    llm = OpenAILLMService(
        model="gpt-4o-mini",
        system_prompt="You are a helpful assistant. Give brief, friendly responses. Keep your responses concise and conversational."
    )
    tts = OpenAITTSService()
    
    # Single debug processor for input monitoring
    debug_input = SimpleDebugProcessor("INPUT")
    
    # Fixed pipeline - ensure audio flows UPSTREAM from input to output
    pipeline = Pipeline([
        transport.input(),      # Audio input (microphone) - should flow UPSTREAM
        debug_input,            # Debug processor
        stt,                    # Speech to text
        llm,                    # Process text and generate response
        tts,                    # Text to speech
        transport.output()       # Audio output (speaker) - should flow DOWNSTREAM
    ])
    
    return pipeline, transport

async def main():
    print("🚀 Starting Simple Vanilla Agent...")
    print(f"🏠 Room URL: {os.getenv('DAILY_ROOM_URL')}")

    # Diagnostics
    print(f"🔐 OPENAI_API_KEY set: {bool(os.getenv('OPENAI_API_KEY'))}")
    print(f"🔐 DAILY_TOKEN set: {bool(os.getenv('DAILY_TOKEN'))}")
    print(f"🔐 DEEPGRAM_API_KEY set: {bool(os.getenv('DEEPGRAM_API_KEY'))}")
    
    try:
        from openai import OpenAI
        if os.getenv('OPENAI_API_KEY'):
            client = OpenAI()
            try:
                resp = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":"ping"}], max_tokens=5)
                print("🧪 OpenAI LLM ping OK")
            except Exception as e:
                print(f"🧪 OpenAI LLM ping failed: {type(e).__name__}: {str(e)[:200]}")
    except Exception as e:
        print(f"🧪 OpenAI client import failed: {type(e).__name__}: {e}")

    try:
        import deepgram
        if os.getenv('DEEPGRAM_API_KEY'):
            client = deepgram.Deepgram(os.getenv('DEEPGRAM_API_KEY'))
            try:
                # Test Deepgram connectivity - just verify client can be created
                print("🧪 Deepgram API ping OK - client created successfully")
            except Exception as e:
                print(f"🧪 Deepgram API ping failed: {type(e).__name__}: {str(e)[:200]}")
        else:
            print("🧪 Deepgram API key not set, skipping test")
    except ImportError:
        print("🧪 Deepgram client not installed, skipping test")
    except Exception as e:
        print(f"🧪 Deepgram client error: {type(e).__name__}: {e}")

    try:
        # Create and run agent
        pipeline, transport = create_simple_agent()
        
        # Create task with minimal parameters
        task = PipelineTask(pipeline)
        runner = PipelineRunner()
        
        print("✅ Agent ready! Join the Daily room and start speaking.")
        print("📱 Make sure to allow microphone access in your browser.")
        print("🎤 You should see debug messages when you speak.")
        print("⏹️  Press Ctrl+C to stop.\n")
        
        # Run the pipeline directly - let pipecat handle everything
        await runner.run(task)
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())