#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import json

from src.memory.memory_handler import memory_handler
from src.models.llm import llm
from src.models.embedder import embedder
from src.tools import *
from src.orchestrator.orchestrator import orchestrator
from src.user_interface.user_interface import user_interface

### GLOBAL VARS ---------------------------- ###

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
        memory_path=config_data['MEMORY_PATH'],
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

    # Init UI instance
    ui_instance = user_interface(
        agent=orchestrator_instance
	)
    
    # Starting interface
    ui_instance.render_ui()
