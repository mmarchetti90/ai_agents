#!/usr/bin/env python3

"""
Unit test for the MemoryHandler class
Run as "python -m unit_tests.memory_test" from package root to avoid relative import issues
"""

### IMPORTS -------------------------------- ###

import yaml

from datetime import datetime
from os import remove as os_remove
from src.memory_handler.memory_handler import MemoryHandler
from time import sleep

### GLOBAL VARS ---------------------------- ###

MEMORY_PATH = 'memory_test.db'
SCORE_THRESHOLD = 0.7
CONFIG_FILE = 'config/config.yaml'

### FUNCTIONS ------------------------------ ###

def parse_config() -> dict:

    """
    Parsing config file containing global vars
    """

    with open(CONFIG_FILE) as opened_config_file:
        config_data = yaml.safe_load(opened_config_file)

    return config_data

### ---------------------------------------- ###

def log_trace(trace_message: str) -> None:

        """
        Logs a time-stamped trace message to the console and appends it to the log

        Parameters
        ----------
        trace_message: str
            The message to log
        """

        trace_timestamp = datetime.now().strftime("%H:%M:%S")
        timestamped_trace_message = f"[{trace_timestamp}] {trace_message}"
        print(timestamped_trace_message)

### MAIN ---------------------------------- ###

if __name__ == '__main__':

    # Parse config file
    config_data = parse_config()
    log_trace(trace_message='Loaded config')

    # Init memory handler
    memory_instance = MemoryHandler(
        MEMORY_PATH,
        config_data['memory']['checkpoint']
    )
    log_trace(trace_message='Added memory')
    
    # Adding memories
    log_trace(trace_message='Adding memories:')
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
        memory_instance.log_memory(origin='assistant', content=mta)
        log_trace(trace_message=f'  * {mta}')
        sleep(sleep_time)
    log_trace(f'All done: new memory count is {memory_instance.memory_count}')
    
    # Removing 2 oldest memories
    log_trace(trace_message='Removing the 2 oldest memories')
    max_memories = memory_instance.memory_count - 2
    memory_instance.trim_memory(max_memories)
    log_trace(trace_message=f'All done: new memory count is {memory_instance.memory_count}')

    # Retrieving memories relevant to a tag
    context = ["Tolkien's Middle Earth."]
    log_trace(trace_message=f'Retrieving memories relevant to the following context: "{context[0]}"')
    retrieved_memories = memory_instance.retrieve_memory(context=context, max_hits=5, score_threshold=SCORE_THRESHOLD)
    log_trace(trace_message='Retrieved the following:')
    for rm in retrieved_memories:
        log_trace(trace_message=f'  * {rm}')

    # Deleting test database
    os_remove(MEMORY_PATH)
