System Architecture Overview
The AI assistant is built on a modular, multi-layered architecture. At a high level, it consists of a User
Interface, a central Assistant Core that coordinates various Agents, and supporting modules for
knowledge storage, external AI models, logging, and testing. The diagram below illustrates the top-level
architecture, grouping components by functionality:

```mermaid
graph TD
    UI[User Interface (Streamlit GUI)] --> Core[Assistant Core & Agents]
    Core --> VectorStore[Vector Store]
    Core --> KnowledgeBase[Knowledge Base]
    Core --> LLMAPI[LLM API Providers]
    Core --> Logging[Logging & Memory]
    Core --> Testing[Test Framework]
    VectorStore --> ChromaDB[(ChromaDB Embeddings DB)]
    KnowledgeBase --> LocalFiles[(Local Document Storage)]
    LLMAPI --> OpenAI[(OpenAI/Codex API)]
    LLMAPI --> LocalLLM[(Local LLM API)]
```

UI: The front-end is a Streamlit-based web interface that allows user interaction. It supports a real-time
chat, document uploads, system status displays, and checklist management . The UI captures user
inputs (queries, uploaded documents, etc.) and displays the assistant’s outputs.

Assistant Core: The core is the brain of the system. It receives input from the UI and delegates tasks to
specialized Agents for processing. It manages query analysis, context gathering, and orchestrating
responses. This is also where chain-of-thought reasoning and progress visualization are handled. The core
uses a BaseAgent class providing common utilities that many agents inherit .

Agents: Multiple specialized agents handle different domains and tasks. For example, BusinessCaseAgent,
CodeAnalysisAgent, DocumentAnalysisAgent (domain-specific analysis agents) and system-level agents
like DevOpsAgent, TestAgent, LLMAgent, CodexAgent, and GUIAgent. Each agent’s role is described in
detail in the next section.

Vector Store: A semantic vector database is used for embedding and retrieving documents or code
snippets relevant to queries . The implementation uses ChromaDB for storing embeddings, enabling
similarity search over documents. When a query comes in, the assistant can search this vector store for
relevant context to include in prompts.

Knowledge Base: A local knowledge base manages source documents and files . It handles file
indexing, content chunking, and metadata. New documents can be added (for example, via the UI), and the
content is chunked and embedded into the vector store for later retrieval. (In code, this might correspond
to a local_knowledge_base.py module and works in tandem with the vector store.)

LLM API Providers: These are external AI model endpoints used by the assistant. By default, the system
integrates with OpenAI’s GPT models (and Codex for code) . The design also allows using local or
alternative LLM providers – an LLMProvider abstraction supports multiple backends (e.g. OpenAI, local
models via Ollama, etc.) . This layer handles sending prompts to the model and obtaining completions.

Logging & Memory: The assistant includes logging, reasoning trace, and memory modules. A Reasoning
Logger records the chain-of-thought or intermediate steps for visualization and debugging . An Error
Handler captures errors/exceptions and logs them for review . The system also maintains Task Memory
to keep context of past actions – e.g. recent tasks, code changes, or conversational history . This
memory can be used to find related past tasks or to enrich the context for new queries.

Testing Framework: For development workflows, the assistant can generate and run tests on code. A Test
Generator module creates test cases and a Test Framework interface (supporting Pytest, Unittest, etc.)
executes them . Results are analyzed by a ResultAnalyzer to identify failures and suggest fixes . This
testing component is mainly utilized by the DevOps and Test agents to ensure code quality.

The overall data flow can be summarized as follows: When a user submits a query or task, the UI passes it
to the Assistant Core, which may use the Vector Store to fetch relevant context and then call an LLM API
to generate a response . The response is then returned to the UI for display. If the query involves
document analysis or code operations, specialized agents and tools (like the vector store, knowledge base,
or test runner) come into play as described below
