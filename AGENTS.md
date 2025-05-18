# Agents, Modules, and Dependency Map

This document maps all major modules/files in the codebase to their responsible agent(s), lists their main functions/classes, and outlines key dependencies. Use this as a reference for maintainability, extensibility, and onboarding.

---

## 1. GUIAgent
**Responsibilities:** UI rendering, user interaction, progress visualization, chat, and recommendations.

- **streamlit_checklist_app.py**
  - *Functions/Classes:* `main`, `show_task_creation`, `show_patch_review`, `show_code_knowledge_base`, `show_test_generation_ui`, `show_prompt_chaining_ui`, `show_reasoning_trace_ui`, `show_interactive_code_review_ui`, `show_task_memory_ui`
  - *Depends on:* `checklist_reader.py`, `checklist_recommender.py`, `patch_reviewer.py`, `test_generator.py`, `result_analyzer.py`, `rollback_manager.py`, `impact_analyzer.py`, `llm_provider.py`, `test_framework.py`, `permission_manager.py`, `error_handler.py`, `prompt_engineering.py`, `security_checker.py`, `reasoning_logger.py`, `task_memory.py`

- **code_knowledge_base.py**
  - *Functions/Classes:* `CodeInspector`, `VectorCodeSearch`
  - *Depends on:* `os`, `ast`, (optional: ChromaDB)

---

## 2. DevOpsAgent
**Responsibilities:** Task management, incremental development, patch review, test generation, status updates, and system controls.

- **incremental_development.py**
  - *Functions/Classes:* `run_incremental_development`, `update_subtask_status`, `get_subtask_progress`, `check_dependencies`, `update_subtask_status_automatically`
  - *Depends on:* `change_plan_generator.py`, `checklist_reader.py`, `threading`, `json`

- **task_creator.py**
  - *Functions/Classes:* `TaskCreator`
  - *Depends on:* `openai`, `os`, `json`

- **manual_trigger.py**
  - *Functions/Classes:* `ManualTrigger`
  - *Depends on:* `threading`, `json`

- **patch_reviewer.py**
  - *Functions/Classes:* `PatchReviewer`, `check_syntax`, `validate_diff`, `suggest_improvements`, `review_code`
  - *Depends on:* `ast`, `difflib`, `prompt_engineering.py`

- **rollback_manager.py**
  - *Functions/Classes:* `RollbackManager`
  - *Depends on:* `os`, `shutil`, `datetime`

- **impact_analyzer.py**
  - *Functions/Classes:* `ImpactAnalyzer`
  - *Depends on:* `ast`, `os`

- **test_generator.py**
  - *Functions/Classes:* `TestGenerator`, `generate_tests`, `analyze_coverage`, `save_tests`, `run_tests`, `discover_and_run_tests`
  - *Depends on:* `prompt_engineering.py`, `llm_provider.py`, `test_framework.py`, `unittest`, `pytest`, `os`, `subprocess`

- **test_framework.py**
  - *Functions/Classes:* `TestFrameworkBase`, `PytestFramework`, `UnittestFramework`, `NoseFramework`, `TestFrameworkRegistry`
  - *Depends on:* `subprocess`

- **security_checker.py**
  - *Functions/Classes:* `run_flake8`, `run_pylint`, `run_bandit`, `run_all_checks`
  - *Depends on:* `subprocess`, `tempfile`, `os`

---

## 3. LLMAgent
**Responsibilities:** LLM abstraction, prompt engineering, code/test generation, review, and explainability.

- **llm_provider.py**
  - *Functions/Classes:* `LLMProviderBase`, `OpenAIProvider`, `LocalLLMProvider`, `OllamaProvider`, `LLMRegistry`
  - *Depends on:* `os`, `openai` (optional), local LLM APIs

- **prompt_engineering.py**
  - *Functions/Classes:* `PROMPT_TEMPLATES`, `get_prompt`, `prompt_chain`
  - *Depends on:* None

- **reasoning_logger.py**
  - *Functions/Classes:* `ReasoningLogger`
  - *Depends on:* `json`, `threading`, `os`

---

## 4. TestAgent
**Responsibilities:** Test generation, execution, analysis, and result reporting.

- **test_generator.py** (see above)
- **result_analyzer.py**
  - *Functions/Classes:* `ResultAnalyzer`, `parse_test_results`, `analyze_failures`, `generate_fix_suggestions`
  - *Depends on:* `pytest`, `json`, `re`

---

## 5. Permission & User Management

- **permission_manager.py**
  - *Functions/Classes:* `PermissionManager`
  - *Depends on:* `json`, `threading`, `os`

---

## 6. Error Handling & Logging

- **error_handler.py**
  - *Functions/Classes:* `log_error`, `error_catcher`, `retry_on_error`, `get_error_logs`
  - *Depends on:* `logging`, `traceback`, `threading`, `json`, `os`

---

## 7. Memory & Context

- **task_memory.py**
  - *Functions/Classes:* `TaskMemory`, `add_task`, `add_code_change`, `get_recent_tasks`, `find_related_tasks`
  - *Depends on:* `json`, `threading`, `os`

---

## 8. Other/Shared Utilities

- **checklist_reader.py** — Checklist parsing and lookup
- **checklist_recommender.py** — Task recommendation logic
- **change_plan_generator.py** — Change plan generation for tasks

---

## 5. CodexAgent
**Responsibilities:** OpenAI Codex integration for code generation, review, test generation, debugging, and patch workflows.

### Integration Goals and Use Cases

**Goals:**
- Seamlessly integrate OpenAI Codex into the multi-agent AI assistant to enhance automation, code quality, and developer productivity.
- Enable Codex to function as both a dedicated agent (CodexAgent) and as a tool for other agents (e.g., DevOpsAgent, LLMAgent, TestAgent).
- Support human-in-the-loop workflows, ensuring user oversight for critical or non-trivial changes.

**Primary Use Cases:**
1. **Code Generation**
   - Generate new functions, classes, or modules based on user requirements or agent requests.
   - Scaffold boilerplate code for new features or integrations.
2. **Code Review and Improvement**
   - Analyze existing code and suggest improvements for readability, performance, or security.
   - Provide inline comments and refactoring suggestions.
3. **Test Case Generation**
   - Automatically generate unit, integration, or end-to-end tests for new or existing code.
   - Suggest edge cases and coverage improvements.
4. **Debugging Assistance**
   - Analyze error messages, stack traces, or failing tests and suggest possible fixes.
   - Propose code changes to resolve detected issues.
5. **Patch Review and Application**
   - Review code patches generated by agents or users.
   - Support workflows for edit, apply, or reject patches with user approval.
6. **Documentation and Example Generation**
   - Generate or update docstrings, README sections, and usage examples for new or modified code.

**Workflow Boundaries:**
- All non-trivial code changes generated by Codex require user review and approval before application.
- Codex can be invoked directly by users or by other agents as a tool, depending on the integration approach.
- Automated actions (e.g., test generation, code suggestions) are logged and can be reviewed or rolled back as needed.

---

**Legend:**
- *Functions/Classes* — Main public functions and classes in the module
- *Depends on* — Key modules/files or external dependencies

**This map is intended to help developers and maintainers quickly understand the agent/module structure and dependencies.**

## Codex Integration

### Overview
Codex is integrated as a dedicated agent (CodexAgent) within the multi-agent AI assistant. It is responsible for code generation, code review, test case generation, and debugging assistance.

### Responsibilities
- Generate code for new features or functions.
- Provide code review and improvement suggestions.
- Generate test cases.
- Assist in debugging.

### Integration Points
- CodexAgent collaborates with existing agents (GUIAgent, DevOpsAgent, LLMAgent, TestAgent) to provide code-related functionalities.
- It can be used as a tool by other agents or as a standalone agent in the LangGraph swarm.

### Usage
- CodexAgent can be invoked through the Streamlit UI or programmatically.
- Ensure the OpenAI API key is set in your `.env` file and the required dependencies are installed. 