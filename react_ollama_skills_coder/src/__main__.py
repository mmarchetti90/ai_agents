#!/usr/bin/env python3

"""
Entrypoint for agent harness
"""

### IMPORTS -------------------------------- ###

import yaml

from datetime import datetime
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

### ---------------------------------------- ###

def print_header_art():

    header = """
┏━┳━━━━┳━━━━┳━━━━┳━━━━┳━━━━┳━━━━┳━━━━┓
┃ ┗━━┛ ┗━━┛ ┗━━┛ ┗━━┛ ┗━━┛ ┗━━┛ ┗━━┛ ┃
┃ >>>>>>>> CODING ASSISTANT <<<<<<<< ┃
┃ ┏━━┓ ┏━━┓ ┏━━┓ ┏━━┓ ┏━━┓ ┏━━┓ ┏━━┓ ┃
┗━━━━┻━━━━┻━━━━┻━━━━┻━━━━┻━━━━┻━━━━┻━┛
"""
    print(header.strip())

### MAIN ----------------------------------- ###

if __name__ == "__main__":
    
    # Parse config file
    config_data = parse_config()

    # Header art
    print_header_art()

    # Init coding agent
    agent_instance = CodingAgent(config_data)

    # Loop execution
    while True:

        # New user query
        print('-' * 40)
        user_query = input('### How can I help?\n')

        # Run or terminate
        if user_query.lower() in ['quit', 'exit', 'terminate', 'kill']:
            print('### Exiting coding agent...')
            print('-' * 40)
            break
        else:
            print('-' * 40)
            _ = agent_instance.process_query(user_query)
    
    # Save session trace (if desired)
    if config_data['agent']['save_session_trace']:
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(f'trace_{timestamp}.txt', 'w') as trace_out:
            trace_out.write('\n'.join(agent_instance.agent_trace))
