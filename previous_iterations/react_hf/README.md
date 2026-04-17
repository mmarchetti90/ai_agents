# Personal AI agent

Toy ReAct AI agent built from scratch using **HuggingFace transformers** library.

## Main functionality

Answer questions about a topic by:

1. Downloading relevant info from PubMed or Wikipedia.

2. Use RAG to filter retrieved info.

2. Use the info to answer the query.

## Tools

* **pubmed_searh** : custom tool to query PubMed to fetch articles abstracts relevant to a query

* **wikipedia_search** : custom tool to query Wikipedia and extract info relevant to a query

## Notes

- This tool was inspired by this great [**tutorial**](https://github.com/arunpshankar/react-from-scratch/tree/88ad3659a8a10110ad8cbf8f587a52f9854da696).
