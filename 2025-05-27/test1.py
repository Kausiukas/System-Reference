from langchain_openai import ChatOpenAI

llm = ChatOpenAI()
response = llm.invoke("Hello, world!")
print(response)
