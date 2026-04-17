#!/usr/bin/env python3

"""
Unit test for the SkillsManager class with only subprocess.run calls
Run as "python -m unit_tests.skills_test_simple" from package root to avoid relative import issues
"""

### IMPORTS -------------------------------- ###

import yaml

from datetime import datetime
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

    # Load SkillsManager
    skills_manager_instance = SkillsManager(config_data['skills']['skills_dir'])
    log_trace(trace_message='Added skills')

    # Init task
    action = {
        "though": "I will load the script src/skills/read-code/scripts/read_code.py",
        "skill_name": "read-code",
        "skill_params": {
            "code_path": "src/skills/read-code/scripts/read_code.py"
        }
    }

    # Execute skill
    skill_exec_status, skill_outputs, skill_execution_log = skills_manager_instance.execute_skill(
        llm_call=None,
        skill_name=action['skill_name'],
        chat_context=[],
        **action['skill_params']
    )

    # Report
    log_trace(trace_message=f'Skill executions success: {skill_exec_status}')
    for log in skill_execution_log:
        log_trace(trace_message=log)
