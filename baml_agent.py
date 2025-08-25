"""
BAML Pipecat Agent with Conversation Recording
"""

import asyncio
import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

from pipecat.frames.frames import TextFrame, StartFrame, EndFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.aggregators.llm_response import LLMFullResponseAggregator
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
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

# ================== MODIFIED BAML PROCESSOR ==================
class BAMLProcessor(FrameProcessor):
    """Custom processor that uses BAML for structured responses"""
    
    def __init__(self, recorder):
        super().__init__()
        self.recorder = recorder
        self.last_user_text = None
        
    async def process_frame(self, frame, direction: FrameDirection):
        # Capture user input from STT
        if (direction == FrameDirection.UPSTREAM and 
            isinstance(frame, TextFrame) and 
            hasattr(frame, 'metadata') and 
            frame.metadata.get('source') == 'stt'):
            
            self.last_user_text = frame.text
            self.recorder.record_user_input(frame.text)
            print(f"👤 User: {frame.text}")
        
        # Process agent responses with BAML
        elif (direction == FrameDirection.DOWNSTREAM and 
              isinstance(frame, TextFrame) and
              self.last_user_text):
            
            start_time = time.time()
            
            try:
                if BAML_AVAILABLE:
                    request = CustomerSupportRequest(
                        user_message=self.last_user_text,
                        context="customer support call"
                    )
                    response = await b.CustomerSupport(request)
                    structured_frame = TextFrame(response.message)
                    
                    # Record the interaction
                    latency = (time.time() - start_time) * 1000
                    self.recorder.record_agent_response(response.message, latency)
                    print(f"🤖 Agent: {response.message}")
                    print(f"⏱️  Latency: {latency:.0f}ms")
                    
                    await self.push_frame(structured_frame, direction)
                    self.last_user_text = None
                    return
                else:
                    # Fallback
                    await self.push_frame(frame, direction)
                    return
                
            except Exception as e:
                print(f"BAML processing error: {e}")
                await self.push_frame(frame, direction)
                return
        
        # Pass through other frames
        await self.push_frame(frame, direction)

# ================== MAIN FUNCTION ==================
async def main():
    # Check for required API keys
    required_keys = ["OPENAI_API_KEY", "DAILY_API_KEY", "CARTESIA_API_KEY", "DEEPGRAM_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        print(f"Missing required environment variables: {', '.join(missing_keys)}")
        sys.exit(1)

    print("Creating BAML Pipecat Agent with Recording...")
    print("=" * 50)

    # Create conversation recorder
    recorder = ConversationRecorder()
    
    # Create services
    llm = OpenAILLMService(model="gpt-4o-mini")
    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"), model="nova-2")
    tts = CartesiaTTSService(api_key=os.getenv("CARTESIA_API_KEY"), voice_id="79a125e8-cd45-4c13-8a67-188112f4dd22")
    
    # Create BAML processor with recorder
    baml_processor = BAMLProcessor(recorder)
    llm_aggregator = LLMFullResponseAggregator()
    
    # Create transport
    transport_params = DailyParams(audio_out_enabled=True, transcription_enabled=True, vad_enabled=VAD_AVAILABLE)
    if VAD_AVAILABLE and SileroVADAnalyzer:
        transport_params.vad_analyzer = SileroVADAnalyzer()
    
    transport = DailyTransport(
        room_url=os.getenv("DAILY_ROOM_URL"),
        token=os.getenv("DAILY_TOKEN"),
        bot_name="BAML_Agent",
        params=transport_params
    )
    
    # Create pipeline
    pipeline = Pipeline([
        transport.input(),
        stt,
        llm,
        baml_processor,
        tts,
        transport.output(),
        llm_aggregator
    ])
    
    # Create task
    task = PipelineTask(pipeline)
    
    # Set system message
    system_prompt = """You are a customer support agent. Your responses will be processed by BAML for structure.
    Provide helpful, accurate, and concise answers. Always confirm customer details before proceeding with any actions.
    Be professional and empathetic in your communication."""
    
    try:
        # Start recording a new call
        call_id = f"baml_call_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        recorder.start_new_call(call_id)
        
        # Create runner
        runner = PipelineRunner()
        
        # Queue start frame
        await task.queue_frame(StartFrame())
        
        # Run the task
        runner_task = asyncio.create_task(runner.run(task))
        
        print("Pipeline started successfully!")
        print("BAML Agent is now ready to process customer support requests.")
        print("Speak your test scenarios into the microphone...")
        print("Press Ctrl+C to stop and save the recording...")
        
        # Keep running
        try:
            await asyncio.sleep(3600)  # 1 hour timeout
        except asyncio.CancelledError:
            print("Shutting down...")
        
        # Cleanup
        await task.queue_frame(EndFrame())
        await runner_task
        recorder.save_call()
        
    except Exception as e:
        print(f"Error during pipeline execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await runner.cancel()
        print("Cleanup completed.")

if __name__ == "__main__":
    print("Starting BAML Pipecat Agent with Recording...")
    print("=" * 50)
    
    asyncio.run(main())
    
    print("=" * 50)
    print("BAML Agent execution completed.")