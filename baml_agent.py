"""
BAML Pipecat Agent
"""

from pipecat import Agent
from pipecat.llss import OpenAI
from pipecat.tts import OpenAITTS
from pipecat.stt import OpenAISTT
from baml import PromptTemplate
import os

# BAML Structered Template
support_prompt = PromptTemplate(
    name="customer_support",
    template="""
    Role: Support Agent
    Task: Answer questions concisely and accurately.
    Always confirm customer details before proceeding.
    """
)

#Create BAML Agent
def create_baml_agent():
    llm = OpenAI(model="gpt-4o-mini")
    stt = OpenAISTT()
    tts = OpenAITTS()

    agent = Agent(
        name="BAML_Agent",
        llm=llm,
        stt=stt,
        tts=tts,
        system_prompt=support_prompt
    )
    return agent

if __name__ == "__main__":
    agent = create_baml_agent()
    agent.start()