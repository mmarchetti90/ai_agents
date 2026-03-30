# Text summarizer

AI agent for summarizing text

## Features

* Looped execution with streamlit interface
* Loads txt, pdf, or docx files
* Vectorizes and cluster senteces
* Summarizes clusters and extracts their topic

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
│   ├── data_summarizer.md
│   │
│   └── topic_extractor.md
│
├── requirements.txt
│
└── <b>src</b>
    │
    ├── __init__.py
    │
    ├── __main__.py
    │
    ├── <b>models</b>
    │   │
    │   ├── __init__.py
    │   │
    │   ├── embedder.py
    │   │
    │   └── llm.py
    │
    └── <b>pipeline</b>
        │
        ├── __init__.py
        │
        └── pipeline.py
</b>
</pre>