# AI data analyst agent

AI agent for tasks decomposition

## Features

* Looped execution
* Tool calling
* Vectorized memory stored in a SQLite database
* Streamlit interface

## Package structure

<pre>
<b>root</b>
│
├── README.md
│
├── <b>config</b>
│   │
│   └── config.json
│
├── makefile
│
├── <b>memory</b>
│   │
│   └── memory.db
│
├── <b>prompts</b>
│   │
│   ├── code_writer.md
│   │
│   ├── conversationalist.md
│   │
│   ├── creative_writer.md
│   │
│   ├── data_miner.md
│   │
│   ├── data_summarizer.md
│   │
│   ├── final_answer.md
│   │
│   ├── query_decomposition.md
│   │
│   └── task_assigner.md
│
├── requirements.txt
│
├── <b>src</b>
│   │
│   ├── __init__.py
│   │
│   ├── __main__.py
│   │
│   ├── <b>memory</b>
│   │   │
│   │   ├── __init__.py
│   │   │
│   │   └── memory_handler.py
│   │
│   ├── <b>models</b>
│   │   │
│   │   ├── __init__.py
│   │   │
│   │   ├── embedder.py
│   │   │
│   │   └── llm.py
│   │
│   ├── <b>orchestrator</b>
│   │   │
│   │   ├── __init__.py
│   │   │
│   │   └── orchestrator.py
│   │
│   ├── <b>tools</b>
│   │   │
│   │   ├── __init__.py
│   │   │
│   │   ├── execute_code.py
│   │   │
│   │   ├── load_local_sql.py
│   │   │
│   │   ├── load_local_table.py
│   │   │
│   │   ├── load_local_text.py
│   │   │
│   │   ├── pubmed_search.py
│   │   │
│   │   └── wikipedia_search.py
│   │
│   └── <b>user_interface</b>
│       │
│       ├── __init__.py
│       │
│       └── user_interface.py
│
└── <b>unit_tests</b>
    │
    ├── __init__.py
    │
    ├── interface_test.py
    │
    ├── memory_test.py
    │
    └── orchestrator_test.py
</b>
</pre>