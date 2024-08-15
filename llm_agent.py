from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_core.messages import HumanMessage


class LLMAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model='gpt-4o')

    def render_system_message(self, content):
        system_message = SystemMessage(content=content)
        assert isinstance(system_message, SystemMessage)
        return system_message

    def render_human_message(self, content):
        return HumanMessage(content=content)

    async def __call__(self, system_message, human_message):
        messages = [
            self.render_system_message(content=system_message),
            self.render_human_message(content=human_message)
        ]
        response = await self.llm.ainvoke(input=messages)
        return response.content
