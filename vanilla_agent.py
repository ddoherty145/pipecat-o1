"""
Vanilla Pipecat Agent for fair comparison with BAML agent
"""

import asyncio
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv

from pipecat.pipeline.pipeline import Pipeline
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.tts import OpenAITTSService
from pipecat.services.openai.stt import OpenAISTTService
from pipecat.frames.frames import StartFrame, EndFrame, TextFrame
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.transports.services.daily import DailyParams, DailyTransport

# Load environment variables
load_dotenv()

class ConversationRecorder:
    def __init__(self):
        self.conversation = []
        self.current_call_id = None
        
    def start_new_call(self, call_id):
        self.current_call_id = call_id
        self.conversation = []
        
    def record_interaction(self, user_text, agent_text, latency_ms):
        self.conversation.append({
            "user": user_text,
            "agent": agent_text,
            "latency_ms": latency_ms,
            "timestamp": datetime.now().isoformat()
        })
        
    def save_call(self):
        if self.current_call_id and self.conversation:
            filename = f"evaluation/sample_calls/vanilla_{self.current_call_id}.json"
            os.makedirs("evaluation/sample_calls", exist_ok=True)
            
            call_data = {
                "call_id": self.current_call_id,
                "agent_type": "vanilla",
                "conversation": self.conversation
            }
            
            with open(filename, "w") as f:
                json.dump(call_data, f, indent=2)

def create_vanilla_agent():
    """Create vanilla agent with Daily transport"""
    
    # Create transport
    transport = DailyTransport(
        room_url=os.getenv("DAILY_ROOM_URL"),
        token=os.getenv("DAILY_TOKEN"),
        bot_name="Vanilla_Agent",
        params=DailyParams(
            audio_out_enabled=True,
            transcription_enabled=True,
            vad_enabled=False
        )
    )
    
    # Create services
    llm = OpenAILLMService(
        model="gpt-4o-mini",
        system_prompt="You are a helpful assistant for basic customer support calls."
    )
    
    stt = OpenAISTTService()
    tts = OpenAITTSService()
    
    # Create pipeline
    pipeline = Pipeline([
        transport.input(),
        stt,
        llm,
        tts,
        transport.output()
    ])
    
    return pipeline, transport

async def main():
    """Main function to run the vanilla agent"""
    
    # Check required keys
    required_keys = ["OPENAI_API_KEY", "DAILY_API_KEY", "DAILY_ROOM_URL", "DAILY_TOKEN"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        print(f"Missing environment variables: {', '.join(missing_keys)}")
        return
    
    print("Creating Vanilla Pipecat Agent...")
    
    # Create recorder
    recorder = ConversationRecorder()
    
    # Create agent
    agent, transport = create_vanilla_agent()
    task = PipelineTask(agent)
    
    try:
        # Start recording
        call_id = f"call_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        recorder.start_new_call(call_id)
        
        # Start pipeline
        runner = PipelineRunner()
        await task.queue_frame(StartFrame())
        runner_task = asyncio.create_task(runner.run(task))
        
        print("Vanilla agent ready! Join the Daily room to test.")
        print("Press Ctrl+C when done to save recording.")
        
        # Keep running
        await asyncio.sleep(3600)
        
    except asyncio.CancelledError:
        print("Shutting down...")
    finally:
        # Cleanup
        await task.queue_frame(EndFrame())
        await runner_task
        recorder.save_call()
        await runner.cancel()
        print("Cleanup completed.")

if __name__ == "__main__":
    asyncio.run(main())