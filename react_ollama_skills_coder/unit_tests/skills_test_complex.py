#!/usr/bin/env python3

"""
Unit test for the SkillsManager class with llm and subprocess.run calls
Run as "python -m unit_tests.skills_test_complex" from package root to avoid relative import issues
"""

### IMPORTS -------------------------------- ###

import yaml

from datetime import datetime
from src.agent.agent import CodingAgent
from src.skills_manager.skills_manager import SkillsManager

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

### MAIN ----------------------------------- ###

if __name__ == "__main__":

    # Parse config file
    config_data = parse_config()
    log_trace(trace_message='Loaded config')

    # Init LLM call
    llm_call = lambda chat, tools, think: CodingAgent.llm_inference(
        chat=chat,
        tools=tools,
        model_checkpoint=config_data['model']['checkpoint'],
        think_mode=think,
        context_window=config_data['model']['context_window'],
        max_new_tokens=config_data['model']['max_new_tokens']
    )
    log_trace(trace_message='Added LLM engine')

    # Load SkillsManager
    skills_manager_instance = SkillsManager(config_data['skills']['skills_dir'])
    log_trace(trace_message='Added skills')

    # Init task
    action = {
        "though": "I will load and comment the load_snippet function from script src/skills/examine-code/scripts/read_code.py",
        "skill_name": "examine-code",
        "skill_params": {
            "code_path": "src/skills/examine-code/scripts/read_code.py",
            "element": "load_snippet",
            "element_type": "function"
        }
    }

    # Execute skill
    skill_exec_status, skill_outputs, skill_execution_log = skills_manager_instance.execute_skill(
        llm_call=llm_call,
        skill_name=action['skill_name'],
        chat_context=[],
        **action['skill_params']
    )

    # Report
    log_trace(trace_message=f'Skill executions success: {skill_exec_status}')
    for log in skill_execution_log:
        log_trace(trace_message=log)
