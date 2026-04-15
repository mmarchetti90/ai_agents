#!/usr/bin/env python3

"""
Entrypoint for agent harness
"""

### IMPORTS -------------------------------- ###

from os import environ
environ["TOKENIZERS_PARALLELISM"] = "false"

import yaml

from src.agent.agent import CodingAgent

### GLOBAL VARS ---------------------------- ###

CONFIG_FILE = 'config/config.yaml'

### FUNCTIONS ------------------------------ ###

def parse_config() -> dict:

    """
    Parsing config file containing global vars
    """

    with open(CONFIG_FILE) as opened_config_file:
        config_data = yaml.safe_load(opened_config_file)

    return config_data

### MAIN ----------------------------------- ###

if __name__ == "__main__":
    
    # Parse config file
    config_data = parse_config()

    # Init coding agent
    agent_instance = CodingAgent(config_data)

    # Loop execution
    while True:

        # New user query
        user_query = input('### How can I help?\n')

        # Run or terminate
        if user_query.lower() in ['quit', 'exit', 'terminate', 'kill']:
            print('### Exiting coding agent...')
            break
        else:
            _ = agent_instance.process_query(user_query)
