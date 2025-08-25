"""
BAML Pipecat Agent for current pipecat version 
"""

import asyncio
import os
import sys
from typing import AsyncGenerator
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

# Try to import VAD analyzer - handle different versions
try:
    # Newer version import
    from pipecat.processors.vad.silero import SileroVADAnalyzer
    VAD_AVAILABLE = True
except ImportError:
    try:
        # Older version import
        from pipecat.vad.silero import SileroVADAnalyzer
        VAD_AVAILABLE = True
    except ImportError:
        print("Warning: SileroVADAnalyzer not available. VAD will be disabled.")
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

class BAMLProcessor(FrameProcessor):
    """Custom processor that uses BAML for structured responses"""
    
    def __init__(self):
        # FIX: Call parent constructor properly
        super().__init__()
        # Initialize any needed attributes
        self._process_queue = asyncio.Queue()
    
    async def process_frame(self, frame, direction: FrameDirection):
        # Only process text frames going downstream
        if direction == FrameDirection.DOWNSTREAM and isinstance(frame, TextFrame):
            try:
                if BAML_AVAILABLE:
                    # Create BAML request
                    request = CustomerSupportRequest(
                        user_message=frame.text,
                        context="customer support call"
                    )
                    
                    # Use BAML function for structured response
                    response = await b.CustomerSupport(request)
                    
                    # Create new frame with BAML response
                    structured_frame = TextFrame(response.message)
                    await self.push_frame(structured_frame, direction)
                    return
                else:
                    # Fallback: just use the original text
                    print("BAML not available, using fallback response")
                    await self.push_frame(frame, direction)
                    return
                
            except Exception as e:
                print(f"BAML processing error: {e}")
                # Fall back to original frame
                await self.push_frame(frame, direction)
                return
        
        # Pass through other frames unchanged
        await self.push_frame(frame, direction)

async def main():
    # Check for required API keys
    required_keys = ["OPENAI_API_KEY", "DAILY_API_KEY", "CARTESIA_API_KEY", "DEEPGRAM_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        print(f"Missing required environment variables: {', '.join(missing_keys)}")
        sys.exit(1)

    print("Creating BAML Pipecat Agent...")
    print("=" * 50)

    # Create services
    print("Creating services...")
    llm = OpenAILLMService(
        model="gpt-4o-mini"
    )
    
    stt = DeepgramSTTService(
        api_key=os.getenv("DEEPGRAM_API_KEY"),
        model="nova-2"
    )
    
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="79a125e8-cd45-4c13-8a67-188112f4dd22"
    )
    
    print("Services created successfully!")
    
    # Create BAML processor
    baml_processor = BAMLProcessor()
    
    # Create aggregator
    llm_aggregator = LLMFullResponseAggregator()
    
    # Create transport with conditional VAD
    transport_params = DailyParams(
        audio_out_enabled=True,
        transcription_enabled=True,
        vad_enabled=VAD_AVAILABLE,
    )
    
    # Add VAD analyzer if available
    if VAD_AVAILABLE and SileroVADAnalyzer:
        transport_params.vad_analyzer = SileroVADAnalyzer()
    
    transport = DailyTransport(
        room_url=os.getenv("DAILY_ROOM_URL"),
        token=os.getenv("DAILY_TOKEN"),
        bot_name="BAML_Agent",
        params=transport_params
    )
    
    print("Transport created successfully!")
    
    # BAML-structured system prompt
    system_prompt = """You are a customer support agent. Your responses will be processed by BAML for structure.
    Provide helpful, accurate, and concise answers. Always confirm customer details before proceeding with any actions.
    Be professional and empathetic in your communication."""
    
    # Create pipeline with BAML processor
    print("Creating pipeline...")
    pipeline = Pipeline([
        transport.input(),
        stt,
        llm,
        baml_processor,     # BAML processing after LLM
        tts,
        transport.output(),
        llm_aggregator
    ])
    
    print("Pipeline created successfully!")
    
    # Create task
    task = PipelineTask(pipeline)
    
    print("Pipeline task created!")
    
    # Set initial messages - using the new approach
    # Instead of LLMMessagesFrame, we'll set the system message directly on the LLM service
    try:
        # Try the new way to set system message
        llm.set_system_message(system_prompt)
        print("System message set on LLM service")
    except AttributeError:
        print("Warning: set_system_message not available, using fallback")
        # Fallback: you might need to handle this differently

    try:
        print("Starting pipeline...")
        
        # Create runner
        runner = PipelineRunner()
        
        # Queue start frame
        await task.queue_frame(StartFrame())
        
        # Run the task in the background
        runner_task = asyncio.create_task(runner.run(task))
        
        print("Pipeline started successfully!")
        print("BAML Agent is now ready to process customer support requests.")
        print("Press Ctrl+C to stop...")
        
        # Keep the pipeline running until interrupted
        try:
            await asyncio.sleep(3600)  # Run for 1 hour or until interrupted
        except asyncio.CancelledError:
            print("Shutting down...")
        
        # Send an EndFrame to gracefully stop
        await task.queue_frame(EndFrame())
        
        # Wait for the task to finish
        await runner_task
        
        print("Pipeline completed successfully!")
        
    except Exception as e:
        print(f"Error during pipeline execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        print("Cleaning up...")
        await runner.cancel()
        print("Cleanup completed.")

if __name__ == "__main__":
    print("Starting BAML Pipecat Agent...")
    print("=" * 50)
    
    asyncio.run(main())
    
    print("=" * 50)
    print("BAML Agent execution completed.")