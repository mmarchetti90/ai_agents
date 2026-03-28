#!/usr/bin/env python3

"""
Unit test for the orchestrator class
The test checks initialization, tool calling, and output generation only, not all possible input ouput combinations
Run as "python -m unit_tests.orchestrator_test" from package root to avoid relative import issues
"""

### IMPORTS -------------------------------- ###

import json

from os import remove as os_remove
from src.memory.memory_handler import memory_handler
from src.models.llm import llm
from src.models.embedder import embedder
from src.tools import *
from src.orchestrator.orchestrator import orchestrator

### GLOBAL VARS ---------------------------- ###

MEMORY_PATH = 'memory/test.db'

CONFIG_FILE = 'config/config.json'

### FUNCTIONS ------------------------------ ###

def parse_config() -> dict:

    """
    Parsing config file containing global vars
    """

    with open(CONFIG_FILE) as opened_config_file:
        config_data = json.load(opened_config_file)

    return config_data

### MAIN ---------------------------------- ###

if __name__ == '__main__':

    # Parse config file
    config_data = parse_config()

    # Init models
    llm_instance = llm(
        model_checkpoint=config_data['TEXT_GENERATION_MODEL'],
        device_map=config_data['DEVICE_MAP']
    )
    embedder_instance = embedder(
        model_checkpoint=config_data['TEXT_EMBEDDING_MODEL'],
        device_map=config_data['DEVICE_MAP'],
        similarity_fn_name=config_data['RAG_SIMILARITY_FUNCTION']
    )

    # Init memory
    memory_instance = memory_handler(
        memory_path=MEMORY_PATH,
        text_embedder=embedder_instance
    )

    # Init LLM agent
    orchestrator_instance = orchestrator(
        config=config_data,
        llm=llm_instance,
        memory=memory_instance
    )

    # Adding function tools
    tool_function = execute_code.execute_code # pyright: ignore[reportUndefinedVariable]
    orchestrator_instance.add_tool(tool_function())
    tool_function = load_local_sql.load_local_sql # pyright: ignore[reportUndefinedVariable]
    orchestrator_instance.add_tool(tool_function())
    tool_function = load_local_table.load_local_table # pyright: ignore[reportUndefinedVariable]
    orchestrator_instance.add_tool(tool_function())
    tool_function = load_local_text.load_local_text # pyright: ignore[reportUndefinedVariable]
    orchestrator_instance.add_tool(tool_function())
    tool_function = pubmed_search.pubmed_search # pyright: ignore[reportUndefinedVariable]
    orchestrator_instance.add_tool(tool_function())
    tool_function = wikipedia_search.wikipedia_search # pyright: ignore[reportUndefinedVariable]
    orchestrator_instance.add_tool(tool_function())

    # Quering the orchestrator_instance
    query_1 = "Download info about Drizzt Do'Urden from Wikipedia, summarize the information, then write a short story about Drizzt fighting to escape the Underdark."
    query_2 = "Search your memory for references to Drizzt Do'Urden, summarize the data, then use the summarized data to tell me the birth place of Drizzt Do'Urden"
    print('#' * 40)
    #print('### QUERY TEST 1:')
    #print(f'  * {query_1}')
    #output_1 = orchestrator_instance.process_query(query_1)
    #print(f'### FINAL OUTPUT 1:\n{output_1}')
    print('### QUERY TEST 2:')
    print(f'  * {query_2}')
    output_2 = orchestrator_instance.process_query(query_2)
    print(f'### FINAL OUTPUT 1:\n{output_2}')
    print('#' * 40)

    # Deleting test database
    os_remove(MEMORY_PATH)
