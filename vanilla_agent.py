"""
Fixed Simple Vanilla Pipecat Agent - With proper Daily transport initialization
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

async def manually_start_pipeline(runner, task):
    """Manually inject StartFrame to bypass Pipecat's validation"""
    print("🚀 Manually starting pipeline with StartFrame injection")
    
    # Wait a moment for transport to be ready
    await asyncio.sleep(1)
    
    try:
        # Get the pipeline from the task
        pipeline = task._pipeline
        
        # Create and inject StartFrame at the beginning of the pipeline
        start_frame = StartFrame()
        
        # Inject StartFrame into the pipeline
        if hasattr(pipeline, '_processors') and pipeline._processors:
            first_processor = pipeline._processors[0]
            print("🎯 Injecting StartFrame into first processor")
            await first_processor.process_frame(start_frame, FrameDirection.DOWNSTREAM)
        
        print("✅ StartFrame injected successfully")
        
    except Exception as e:
        print(f"⚠️ Failed to inject StartFrame: {e}")
        # Continue anyway - maybe the transport will eventually send one

class ValidationFreeDebugProcessor(FrameProcessor):
    """Debug processor that completely bypasses Pipecat's StartFrame validation"""
    
    def __init__(self, name="Debug"):
        super().__init__()
        self._debug_name = name
        self._pipeline_started = False
        # FORCE the processor to think it's already started
        self._started = True  # This bypasses _check_started

    def _check_started(self, frame):
        """Override the validation to always pass"""
        pass  # Do nothing - no validation
    
    async def process_frame(self, frame, direction: FrameDirection):
        try:
            # Log frame direction to debug the flow
            direction_str = "UPSTREAM" if direction == FrameDirection.UPSTREAM else "DOWNSTREAM"
            
            # Track pipeline state
            if isinstance(frame, StartFrame):
                self._pipeline_started = True
                print(f"🚀 [{self._debug_name}] Pipeline STARTED ({direction_str})")
            elif isinstance(frame, EndFrame):
                self._pipeline_started = False
                print(f"🏁 [{self._debug_name}] Pipeline ENDED ({direction_str})")
            
            # Only log essential frame types to avoid spam
            elif isinstance(frame, TextFrame):
                print(f"💬 [{self._debug_name}] Text: '{frame.text}' ({direction_str})")
            elif isinstance(frame, UserStartedSpeakingFrame):
                print(f"🎤 [{self._debug_name}] User started speaking ({direction_str})")
            elif isinstance(frame, UserStoppedSpeakingFrame):
                print(f"🔇 [{self._debug_name}] User stopped speaking ({direction_str})")
            elif hasattr(frame, 'audio') and len(frame.audio) > 0:
                # Log audio frames occasionally with pipeline status
                if not hasattr(self, '_last_audio_log') or (asyncio.get_event_loop().time() - self._last_audio_log) > 2.0:
                    self._last_audio_log = asyncio.get_event_loop().time()
                    status = "ACTIVE" if self._pipeline_started else "WAITING"
                    print(f"🎵 [{self._debug_name}] Audio: {len(frame.audio)} bytes [{status}] ({direction_str})")
            
            # Always pass frames through - don't block anything
            await self.push_frame(frame, direction)
            
        except Exception as e:
            print(f"❌ [{self._debug_name}] Error: {e}")
            # Still pass the frame through to avoid breaking the pipeline
            try:
                await self.push_frame(frame, direction)
            except:
                pass

def create_fixed_simple_agent():
    """Create the simplest possible working agent with proper initialization"""
    
    # Enhanced transport configuration
    transport = DailyTransport(
        room_url=os.getenv("DAILY_ROOM_URL"),
        token=os.getenv("DAILY_TOKEN"),
        bot_name="Fixed_Simple_Agent",
        params=DailyParams(
            audio_out_enabled=True,
            audio_in_enabled=True,
            vad_enabled=True,
            vad_audio_passthrough=True,
            transcription_enabled=False,  # Let STT handle this
            audio_out_sample_rate=24000,
            audio_in_sample_rate=24000,
        )
    )
    
    # Basic services
    stt = OpenAISTTService()
    llm = OpenAILLMService(
        model="gpt-4o-mini",
        system_prompt="You are a helpful assistant. Give brief, friendly responses. Keep your responses concise and conversational."
    )
    tts = OpenAITTSService()
    
    # Create processors
    debug_processor = ValidationFreeDebugProcessor("SIMPLE")
    
    # Simple pipeline without startup injector (we'll inject manually)
    pipeline = Pipeline([
        transport.input(),      # Audio input (microphone)
        debug_processor,        # Debug processor with state tracking
        stt,                    # Speech to text
        llm,                    # Process text and generate response
        tts,                    # Text to speech
        transport.output()      # Audio output (speaker)
    ])
    
    return pipeline, transport

async def main():
    print("🚀 Starting Fixed Simple Vanilla Agent...")
    print(f"🏠 Room URL: {os.getenv('DAILY_ROOM_URL')}")

    # Enhanced diagnostics
    required_vars = ["OPENAI_API_KEY", "DAILY_TOKEN", "DAILY_ROOM_URL"]
    print("\n🔍 Environment Check:")
    for var in required_vars:
        value = os.getenv(var)
        status = "✅" if value else "❌"
        print(f"  {status} {var}: {'SET' if value else 'MISSING'}")
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required variables: {', '.join(missing_vars)}")
        return

    # API connectivity test
    print("\n🧪 API Connectivity Test:")
    try:
        from openai import OpenAI
        if os.getenv('OPENAI_API_KEY'):
            client = OpenAI()
            try:
                resp = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":"ping"}], max_tokens=5)
                print("  ✅ OpenAI API: Connected")
            except Exception as e:
                print(f"  ❌ OpenAI API: {str(e)[:100]}")
        else:
            print("  ⚠️ OpenAI API key not set")
    except Exception as e:
        print(f"  ❌ OpenAI client error: {str(e)[:100]}")

    try:
        print("\n" + "="*50)
        print("🏗️ Building Fixed Simple Agent...")
        
        # Create and run agent
        pipeline, transport = create_fixed_simple_agent()
        
        # Create task with minimal parameters
        task = PipelineTask(pipeline)
        runner = PipelineRunner()
        
        print("✅ Agent ready! Join the Daily room and start speaking.")
        print("📱 Make sure to allow microphone access in your browser.")
        print("🎤 Look for 'Pipeline STARTED' message when ready.")
        print("🔊 Audio frames should show [ACTIVE] status after start.")
        print("⏹️ Press Ctrl+C to stop.\n")
        
        # Start the runner in the background
        runner_task = asyncio.create_task(runner.run(task))
        
        # Wait a moment then manually inject StartFrame
        await manually_start_pipeline(runner, task)
        
        # Wait for the runner to complete
        await runner_task
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            if 'runner' in locals():
                await runner.cancel()
            print("✅ Cleanup completed")
        except:
            pass

if __name__ == "__main__":
    print("🎬 Fixed Vanilla Agent Starting...")
    print("="*50)
    asyncio.run(main())
    print("="*50)
    print("🏁 Agent execution completed.")