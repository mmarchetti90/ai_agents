# AI agents

Collection of AI agents built for fun and personal use.\
None of these were built with AI :satisfied:

## Contents

### Summarizers

* **projects_summarizer_hf**:\
A tool for creating a summary of projects in a directory.\
Uses HF transformers.

* **text_summarizer_hf**:\
Agent for text summarization capable of clustering sentences and extracting relevant topics.\
Streamlit interface.\
Works on short text and scientific papers alike.\
Uses HF transformers.

### Task solvers

* **tasks_solver_customizable**:\
Basic agent capable of decomposing a query into subtasks, then selecting tools (functions or LLMs) for each task.\
Each LLM tool can have a separate model.\
Uses HF transformers.

* **tasks_solver_slimmer**:\
As above, but using the same model for each LLM tool.\
Uses HF transformers.

* **tasks_solver_loop_memory_streamlit**:\
As above, but now tasks have a hierarchy and dependencies, the agent has access to vectorized memory stored in a SQLite database, and streamlit is used to provide a UI and looping execution
Streamlit implementation needs fixing (i.e. caching the agent as in text_summarizer_hf).\
Uses HF transformers.

### ReAct agents

* **react_hf**:\
Basic ReAct agent capable of tool selection.\
Uses HF transformers.

* **react_hf_skills_coder**:\
More complex ReAct coding agent with memory and skills calling.\
Geared towards coding.\
Uses HF transformers.

* **react_ollama_skills_coder**:\
Improved memory and skills handling.\
Better loop thanks to a specialized skill for terminating a loop.\
Geared towards coding.\
Uses Ollama for inference with larger quantized models.\
(Model quantization with HF transformers on Mac silicon doesn't work)
