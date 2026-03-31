# AI agents

Collection of Ai agents built for fun and personal use.

## Contents

* **projects_summarizer** : tool for creating a summary of projects in a directory.

* **react** : ReAct agent capable of tool selection.

* **tasks_solver_customizable** : agent capable of decomposing a query into subtasks, then selecting tools (functions or LLMs) for each task.

* **tasks_solver_slimmer** : as above, but using the same model for each LLM tool.

* **tasks_solver_loop_memory_streamlit** : as above, but now tasks have a hierarchy and dependencies, the agent has access to vectorized memory stored in a SQLite database, and streamlit is used to provide a UI and looping execution

* **text_summarizer** : agent for text summarization capable of clustering sentences and extracting relevant topics. Works on short text and scientific papers alike.