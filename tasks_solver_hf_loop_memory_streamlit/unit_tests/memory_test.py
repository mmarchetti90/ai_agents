#!/usr/bin/env python3

"""
Unit test for the memory_handler class
Run as "python -m unit_tests.memory_test" from package root to avoid relative import issues
"""

### IMPORTS -------------------------------- ###

import json

from os import remove as os_remove
from src.memory.memory_handler import memory_handler
from src.models.embedder import embedder
from time import sleep

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

    # Init model
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
    # Adding memories
    print('Adding memories:')
    sleep_time = 3
    memories_to_add = [
        "Middle Earth is home to many races, including dwarves, humans, and elves.",
        "Luke Skywalker is a central character in Star Wars.",
        "Captain America is a known Marvel superhero.",
        "Sauron waged war in Middle Earth.",
        "Eru Ilúvatar is the core deity in Tolkien's works.",
        "Bilbo Baggins had a great adventure in Middle Earth.",
        "Tattoine is a remote planet in the Star Wars universe."
    ]
    for mta in memories_to_add:
        memory_instance.log_memory(origin='user', content=mta)
        print(f'  * {mta}')
        sleep(sleep_time)
    print(f'All done: new memory count is {memory_instance.memory_count}')
    
    # Removing 2 oldest memories
    print('Removing the 2 oldest memories')
    max_memories = memory_instance.memory_count - 2
    memory_instance.trim_memory(max_memories)
    print(f'All done: new memory count is {memory_instance.memory_count}')

    # Retrieving memories relevant to a tag
    context = ["Tolkien's Middle Earth."]
    print(f'Retrieving memories relevant to the following context: "{context[0]}"')
    retrieved_memories = memory_instance.retrieve_memory(context=context, max_hits=5, score_threshold=0.7)
    print('Retrieved the following:')
    for rm in retrieved_memories:
        print(f'  * {rm}')

    # Deleting test database
    os_remove(MEMORY_PATH)
