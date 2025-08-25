"""
Vinalla Pipcat Agent
"""

from pipecat import Agent
from pipecat.llss import OpenAI
from pipecat.tts import OpenAITTS
from pipecat.stt import OpenAISTT

def create_anilla_agent():
    llm = OpenAI(model="gpt-4o-mini")
    stt = OpenAISTT()
    tts = OpenAITTS()

    agent = Agent(
        name="VanillaAgent",
        llm=llm,
        stt=stt,
        tts=tts,
        system_prompt="You are a helpful assistant for basic customer support calls."
    )
    return agent

if __name__ == "__main__":
    agent = create_anilla_agent()
    agent.start()