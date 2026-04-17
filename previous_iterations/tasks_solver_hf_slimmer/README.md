# Tasks solver AI agent

Toy Agent agent built for fun using **HuggingFace transformers** library.

## Main functionality

1. Decomposes a query into tasks (skipped if a list of tasks is provided as input).

2. Assigns tasks to tools.

3. Runs individual tasks.

4. Summarizes tasks outputs to provide a final output.

## Tools

### LLMs

* **query_decomposition** : decomposes a query into tasks

* **task_assigner** : assigns tasks to tools

* **rag_filter** : filters retrieved data for relevance to the query

* **data_summarizer** : summarizes tasks outputs given the original query as context

* **code_writer** : writes code given a query and context

* **creative_writer** : writes text given a query and context

### Functions

* **pubmed_searh** : fetches articles abstracts relevant to a query from PubMed

* **wikipedia_search** : extracts info relevant to a query from Wikipedia
