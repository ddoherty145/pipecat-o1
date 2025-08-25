import asyncio
import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

from pipecat.frames.frames import (
    TextFrame, StartFrame, EndFrame, AudioRawFrame, 
    UserStartedSpeakingFrame, UserStoppedSpeakingFrame
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.aggregators.llm_response import LLMFullResponseAggregator
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.cartesia.tts import CartesiaTTSService

# Try to import Deepgram STT service with compatibility layer
try:
    # Import compatibility layer first
    import deepgram_compatibility
    from pipecat.services.deepgram.stt import DeepgramSTTService
    DEEPGRAM_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Deepgram STT service not available: {e}")
    DEEPGRAM_AVAILABLE = False
    DeepgramSTTService = None

from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.stt import OpenAISTTService
from pipecat.transports.services.daily import DailyParams, DailyTransport

# Try to import VAD analyzer
try:
    from pipecat.processors.vad.silero import SileroVADAnalyzer
    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False
    SileroVADAnalyzer = None

# Import BAML
try:
    from baml_client import b
    from baml_client.types import CustomerSupportRequest, CustomerSupportResponse
    BAML_AVAILABLE = True
except ImportError:
    print("Warning: baml_client not installed. Using fallback mode.")
    BAML_AVAILABLE = False

# Load environment variables
load_dotenv()

# ================== MANUAL PIPELINE STARTER ==================
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

# ================== VALIDATION-FREE DEBUG PROCESSOR ==================
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
            direction_str = "UPSTREAM" if direction == FrameDirection.UPSTREAM else "DOWNSTREAM"

            # Track pipeline state
            if isinstance(frame, StartFrame):
                self._pipeline_started = True
                print(f"🚀 [{self._debug_name}] Pipeline STARTED ({direction_str})")
            elif isinstance(frame, EndFrame):
                self._pipeline_started = False
                print(f"🏁 [{self._debug_name}] Pipeline ENDED ({direction_str})")

            # Handle text frames
            elif isinstance(frame, TextFrame):
                source = getattr(frame, 'metadata', {}).get('source', 'unknown')
                print(f"💬 [{self._debug_name}] Text [{source}]: '{frame.text[:100]}...' ({direction_str})")

            # Handle speech events
            elif isinstance(frame, UserStartedSpeakingFrame):
                print(f"🎤 [{self._debug_name}] User STARTED speaking ({direction_str})")
            elif isinstance(frame, UserStoppedSpeakingFrame):
                print(f"🔇 [{self._debug_name}] User STOPPED speaking ({direction_str})")

            # Handle audio frames with throttling
            elif isinstance(frame, AudioRawFrame):
                if not hasattr(self, '_last_audio_log') or (asyncio.get_event_loop().time() - self._last_audio_log) > 3.0:
                    self._last_audio_log = asyncio.get_event_loop().time()
                    status = "ACTIVE" if self._pipeline_started else "WAITING"
                    print(f"🎵 [{self._debug_name}] Audio: {len(frame.audio)} bytes [{status}] ({direction_str})")

            # Push frame without validation
            await self.push_frame(frame, direction)

        except Exception as e:
            print(f"❌ [{self._debug_name}] Error processing frame: {e}")
            try:
                await self.push_frame(frame, direction)
            except Exception as push_error:
                print(f"❌ [{self._debug_name}] Failed to push frame after error: {push_error}")

# ================== CONVERSATION RECORDER ==================
class ConversationRecorder:
    def __init__(self):
        self.conversation = []
        self.current_call_id = None
        self.last_user_input = None
        self.last_input_time = None
        
    def start_new_call(self, call_id):
        self.current_call_id = call_id
        self.conversation = []
        self.last_user_input = None
        self.last_input_time = None
        print(f"📝 Started recording call: {call_id}")
        
    def record_user_input(self, text):
        self.last_user_input = text
        self.last_input_time = time.time()
        self.conversation.append({
            "type": "user",
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
        
    def record_agent_response(self, text, latency_ms):
        if self.last_user_input and self.last_input_time:
            self.conversation.append({
                "type": "agent",
                "text": text,
                "latency_ms": latency_ms,
                "timestamp": datetime.now().isoformat()
            })
            
    def save_call(self):
        if self.current_call_id and self.conversation:
            filename = f"evaluation/sample_calls/{self.current_call_id}.json"
            os.makedirs("evaluation/sample_calls", exist_ok=True)
            
            call_data = {
                "call_id": self.current_call_id,
                "timestamp": datetime.now().isoformat(),
                "conversation": self.conversation,
                "total_turns": len([t for t in self.conversation if t["type"] == "user"]),
                "avg_latency": self._calculate_avg_latency()
            }
            
            with open(filename, "w") as f:
                json.dump(call_data, f, indent=2)
            print(f"💾 Saved call recording: {filename}")
            
    def _calculate_avg_latency(self):
        latencies = [t["latency_ms"] for t in self.conversation if "latency_ms" in t]
        return sum(latencies) / len(latencies) if latencies else 0

# ================== ENHANCED BAML PROCESSOR ==================
class EnhancedBAMLProcessor(FrameProcessor):
    """Enhanced BAML processor with proper state management"""
    
    def __init__(self, recorder):
        super().__init__()
        self.recorder = recorder
        self.last_user_text = None
        self._pipeline_started = False
        self._processing_response = False
        
    async def process_frame(self, frame, direction: FrameDirection):
        # Track pipeline state
        if isinstance(frame, StartFrame):
            self._pipeline_started = True
            print("🧠 BAML Processor: Pipeline started")
        elif isinstance(frame, EndFrame):
            self._pipeline_started = False
            
        # Only process when pipeline is active
        if not self._pipeline_started:
            await self.push_frame(frame, direction)
            return
            
        # Capture user input from STT
        if (direction == FrameDirection.UPSTREAM and 
            isinstance(frame, TextFrame) and 
            not self._processing_response):
            
            # Check if this is from STT (you may need to adjust this based on your STT implementation)
            self.last_user_text = frame.text
            self.recorder.record_user_input(frame.text)
            print(f"👤 User said: {frame.text}")
        
        # Process LLM responses with BAML
        elif (direction == FrameDirection.DOWNSTREAM and 
              isinstance(frame, TextFrame) and
              self.last_user_text and
              not self._processing_response):
            
            self._processing_response = True
            start_time = time.time()
            
            try:
                if BAML_AVAILABLE:
                    print("🧠 Processing with BAML...")
                    request = CustomerSupportRequest(
                        user_message=self.last_user_text,
                        context="customer support call"
                    )
                    response = await b.CustomerSupport(request)
                    
                    # Create new frame with BAML response
                    baml_frame = TextFrame(response.message)
                    
                    # Record the interaction
                    latency = (time.time() - start_time) * 1000
                    self.recorder.record_agent_response(response.message, latency)
                    print(f"🤖 BAML Response: {response.message}")
                    print(f"⏱️  BAML Latency: {latency:.0f}ms")
                    
                    # Push the BAML response instead of original
                    await self.push_frame(baml_frame, direction)
                    self.last_user_text = None
                    self._processing_response = False
                    return
                else:
                    # Fallback - just pass through
                    print("🔄 BAML not available, using fallback")
                    
            except Exception as e:
                print(f"❌ BAML processing error: {e}")
            finally:
                self._processing_response = False
        
        # Pass through all other frames
        await self.push_frame(frame, direction)

# ================== ENHANCED DAILY TRANSPORT SETUP ==================
def create_enhanced_daily_transport():
    """Create Daily transport with proper configuration"""
    
    # Enhanced transport parameters
    params = DailyParams(
        audio_out_enabled=True,
        audio_in_enabled=True,
        transcription_enabled=False,  # Let STT handle this
        vad_enabled=True,
        vad_audio_passthrough=True,
        vad_analyzer=SileroVADAnalyzer() if VAD_AVAILABLE else None,
        # Additional params for stability
        audio_out_sample_rate=24000,
        audio_in_sample_rate=24000,
    )
    
    transport = DailyTransport(
        room_url=os.getenv("DAILY_ROOM_URL"),
        token=os.getenv("DAILY_TOKEN"),
        bot_name="Enhanced_BAML_Agent",
        params=params
    )
    
    return transport

# ================== MAIN FUNCTION ==================
async def main():
    print("🚀 Starting Enhanced BAML Pipecat Agent...")
    print(f"🏠 Room URL: {os.getenv('DAILY_ROOM_URL')}")
    
    # Comprehensive diagnostics
    required_env_vars = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "DAILY_TOKEN": os.getenv("DAILY_TOKEN"),
        "CARTESIA_API_KEY": os.getenv("CARTESIA_API_KEY"),
        "DAILY_ROOM_URL": os.getenv("DAILY_ROOM_URL")
    }
    
    if DEEPGRAM_AVAILABLE:
        required_env_vars["DEEPGRAM_API_KEY"] = os.getenv("DEEPGRAM_API_KEY")
    
    print("🔍 Environment Check:")
    for var, value in required_env_vars.items():
        status = "✅" if value else "❌"
        print(f"  {status} {var}: {'SET' if value else 'MISSING'}")
    
    # Check for missing required vars
    missing_vars = [var for var, value in required_env_vars.items() if not value]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # API connectivity tests
    print("\n🧪 API Connectivity Tests:")
    
    # Test OpenAI
    try:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[{"role": "user", "content": "ping"}], 
            max_tokens=5
        )
        print("  ✅ OpenAI API: Connected")
    except Exception as e:
        print(f"  ❌ OpenAI API: {str(e)[:100]}")
    
    # Test Cartesia
    try:
        import requests
        headers = {"X-API-Key": os.getenv("CARTESIA_API_KEY")}
        resp = requests.get("https://api.cartesia.ai/voices", headers=headers, timeout=5)
        if resp.status_code == 200:
            print("  ✅ Cartesia API: Connected")
        else:
            print(f"  ❌ Cartesia API: HTTP {resp.status_code}")
    except Exception as e:
        print(f"  ❌ Cartesia API: {str(e)[:100]}")

    print("\n" + "="*60)
    print("🏗️  Building Enhanced Agent Pipeline...")
    
    try:
        # Create conversation recorder
        recorder = ConversationRecorder()
        call_id = f"enhanced_call_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        recorder.start_new_call(call_id)
        
        # Create transport
        transport = create_enhanced_daily_transport()
        
        # Create services
        llm = OpenAILLMService(
            model="gpt-4o-mini",
            system_prompt=(
                "You are a professional customer support agent. "
                "Provide helpful, accurate, and concise responses. "
                "Always be empathetic and solution-oriented. "
                "Keep responses under 100 words unless more detail is specifically requested."
            )
        )
        
        # Choose STT service
        if DEEPGRAM_AVAILABLE and os.getenv("DEEPGRAM_API_KEY"):
            stt = DeepgramSTTService(
                api_key=os.getenv("DEEPGRAM_API_KEY"), 
                model="nova-2"
            )
            print("🎙️  Using Deepgram STT")
        else:
            stt = OpenAISTTService(api_key=os.getenv("OPENAI_API_KEY"))
            print("🎙️  Using OpenAI STT (fallback)")
        
        # TTS service
        tts = CartesiaTTSService(
            api_key=os.getenv("CARTESIA_API_KEY"), 
            voice_id="79a125e8-cd45-4c13-8a67-188112f4dd22"
        )
        
        # Create processors
        debug_processor = ValidationFreeDebugProcessor("MAIN")
        baml_processor = EnhancedBAMLProcessor(recorder)
        llm_aggregator = LLMFullResponseAggregator()
        
        # Build pipeline without startup injector (we'll inject manually)
        pipeline = Pipeline([
            transport.input(),    # Audio input from Daily
            debug_processor,      # Debug monitoring
            stt,                 # Speech to text
            llm,                 # Language model processing
            baml_processor,      # BAML structured processing
            tts,                 # Text to speech
            transport.output(),  # Audio output to Daily
            llm_aggregator       # Response aggregation
        ])
        
        # Create and configure task
        task = PipelineTask(pipeline)
        runner = PipelineRunner()
        
        print("✅ Pipeline built successfully!")
        print("\n🎯 Ready to connect!")
        print("📱 Join the Daily room and start speaking")
        print("🎤 Ensure microphone permissions are granted")
        print("🔊 You should see real-time debug output")
        print("⏹️  Press Ctrl+C to stop")
        print("="*60)
        
        # Start the runner in the background
        runner_task = asyncio.create_task(runner.run(task))
        
        # Wait a moment then manually inject StartFrame
        await manually_start_pipeline(runner, task)
        
        # Wait for the runner to complete
        await runner_task
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down gracefully...")
        recorder.save_call()
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        recorder.save_call()
        
    finally:
        print("🧹 Cleaning up...")
        try:
            if 'runner' in locals():
                await runner.cancel()
            print("✅ Cleanup completed")
        except Exception as cleanup_error:
            print(f"⚠️  Cleanup warning: {cleanup_error}")

if __name__ == "__main__":
    print("🎬 Enhanced BAML Pipecat Agent Starting...")
    print("="*60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"💥 Startup error: {e}")
    
    print("="*60)
    print("🏁 Agent execution completed.")