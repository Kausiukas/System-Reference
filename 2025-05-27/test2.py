import os
from langchain_openai import ChatOpenAI

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "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"
os.environ["LANGCHAIN_PROJECT"] = "2025-05-27"

llm = ChatOpenAI()
print(llm.invoke("Test trace for LangSmith").content)
