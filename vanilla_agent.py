"""
Vanilla Pipecat Agent using the new pipeline architecture
"""

import asyncio
import os
from dotenv import load_dotenv

from pipecat.pipeline.pipeline import Pipeline
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.tts import OpenAITTSService
from pipecat.services.openai.stt import OpenAISTTService
from pipecat.frames.frames import StartFrame, EndFrame, TextFrame
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask

# Load environment variables
load_dotenv()

def create_vanilla_agent():
    """Create a vanilla pipecat agent using the new pipeline architecture"""
    
    # Create the services
    llm = OpenAILLMService(
        model="gpt-4o-mini",
        system_prompt="You are a helpful assistant for basic customer support calls."
    )
    
    stt = OpenAISTTService()
    tts = OpenAITTSService()
    
    # Create the pipeline connecting the services
    # The flow is: STT -> LLM -> TTS
    pipeline = Pipeline([stt, llm, tts])
    
    return pipeline

async def main():
    """Main function to run the agent"""
    print("Creating vanilla agent pipeline...")
    
    # Create the agent pipeline
    agent = create_vanilla_agent()
    
    print("Pipeline created successfully!")
    print("Services linked: STT → LLM → TTS")
    
    # Create a pipeline task
    task = PipelineTask(agent)
    
    print("Pipeline task created!")
    
    try:
        # Start the pipeline with a StartFrame
        print("Starting pipeline...")
        
        # Create and run the task properly
        runner = PipelineRunner()
        
        # Queue the start frame
        await task.queue_frame(StartFrame())
        
        # Run the task in the background
        runner_task = asyncio.create_task(runner.run(task))
        
        print("Pipeline started successfully!")
        print("Pipeline is now ready to process audio/text frames.")
        
        # Send a test text frame
        print("Sending test message...")
        await task.queue_frame(TextFrame("Hello, how are you?"))
        
        # Wait a moment to show the pipeline is running
        await asyncio.sleep(5)
        
        # Send an EndFrame to gracefully stop
        print("Stopping pipeline...")
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
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key in a .env file or environment variable.")
        print("\nYou can set it temporarily with:")
        print("export OPENAI_API_KEY='your_actual_api_key'")
        exit(1)
    
    print("Starting Vanilla Pipecat Agent...")
    print("=" * 40)
    
    # Run the async main function
    asyncio.run(main())
    
    print("=" * 40)
    print("Agent execution completed.")