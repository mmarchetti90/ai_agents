#!/usr/bin/env python3

"""
Entrypoint for agent harness
"""

### IMPORTS -------------------------------- ###

import yaml

from datetime import datetime
from src.agent.agent import SavvyAgent
from sys import argv

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
┏━┳━━━━┳━━━━┳━━━━┳━━━━┳━━━━┳━━━━┓
┃ ┗━━┛ ┗━━┛ ┗━━┛ ┗━━┛ ┗━━┛ ┗━━┛ ┃
┃ >>>>>> SAVVY ASSISTANT <<<<<< ┃
┃ ┏━━┓ ┏━━┓ ┏━━┓ ┏━━┓ ┏━━┓ ┏━━┓ ┃
┗━━━━┻━━━━┻━━━━┻━━━━┻━━━━┻━━━━┻━┛
"""
    print(header.strip())

### MAIN ----------------------------------- ###

if __name__ == "__main__":
    
    # Parse config file
    config_data = parse_config()

    # Override knowledge_dir
    if '--knowledge_dir' in argv:
        config_data['knowledge']['knowledge_dir'] = argv[argv.index('--knowledge_dir') + 1]

    # Header art
    print_header_art()

    # Init coding agent
    agent_instance = SavvyAgent(config_data)

    # Loop execution
    iteration = -1
    while True:

        # New user query
        iteration += 1
        print('-' * 40)
        print(f'## Iteration {iteration}')
        user_query = input('### How can I help?\n(Type "quit" to terminate, "update_knowledge" if you modified the knowledge base)\n')

        # Run or terminate
        if user_query.lower() in ['quit', 'exit', 'terminate', 'kill']:
            print('### Exiting coding agent...')
            print('-' * 40)
            break
        elif user_query.lower() in ['update_knowledge']:
            print('### Updating knowledge base...')
            agent_instance.knowledge.update_knowledge_db()
            agent_instance.log_trace(trace_message='Updated knowledge base')
            for ku in agent_instance.knowledge.updates:
                agent_instance.log_trace(trace_message=f'  * {ku}')
            print('-' * 40)
        else:
            agent_answer = agent_instance.forward(user_query)
            print(agent_answer)
            print('-' * 40)
    
    # Save session trace (if desired)
    if config_data['agent']['save_session_trace']:
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(f'trace_{timestamp}.txt', 'w') as trace_out:
            trace_out.write('\n'.join(agent_instance.agent_trace))
