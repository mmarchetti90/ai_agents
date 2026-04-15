#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import json

from collections.abc import Callable
from os import listdir
from re import findall
from src.skills_manager.skill_base import SkillBase
from subprocess import run as subprocess_run

### CLASSES AND FUNCTIONS ------------------ ###

class SkillsManager:

    """
    Class for managing skills and their execution

    Parameters
    ----------
    skills_dir: str
        Directory where skills are located
    """

    ### ------------------------------------ ###

    def __init__(self, skills_dir: str) -> None:
        
        self.load_skills(skills_dir)

    ### ------------------------------------ ###

    def load_skills(self, skills_dir: str) -> dict:

        """
        Loads all skills from the specified directory and stores them as a dict

        Parameters
        ----------
        skill_dir: str
            Main directory where skills are stored
        
        Returns
        -------
        dict
            Dictionary of skills
        """

        # Load and parse SKILL.md files
        self.skills = {}
        for skill_subdir in listdir(skills_dir):
            # Find and load SKILL.md
            skill_path = f'{skills_dir}/{skill_subdir}'
            try:
                new_skill = SkillBase(skill_path)
                self.skills[new_skill.name] = new_skill
            except:
                continue

    ### ------------------------------------ ###

    def get_skills_descriptions(self, exclude: list[str]=[]) -> dict:

        """
        Creates a dictionary of skills descriptions and expected inputs

        Parameters
        ----------
        exclude: list[str]
            List of skill to mask from the description

        Returns
        -------
        dict
            Dictionary of skills descriptions and expected inputs
        """

        skills_description = [
            {
                'name' : s.name,
                'description' : s.description,
                'inputs' : s.inputs
            }
            for s in self.skills.values()
            if s.name not in exclude
        ]

        return skills_description

    ### ------------------------------------ ###

    def execute_skill(self, llm_call: Callable, skill_name: str, chat_context: list[dict]=[], **kwargs) -> tuple[bool, list[str], list[str]]:

        """
        Attempts to execute a skill using the provided LLM call and/or running scripts
        Parameters
        ----------
        llm_call: Callable
            Function that calls the LLM
        skill_name: str
            Name of the skill to execute
        chat_context: list[dict]
            Chat context to pass to the LLM call
        """

        execution_log = []
        self.skill_outputs = []
        if skill_name in self.skills.keys():

            # Init skill chat
            self.skill_chat = [
                {'role' : 'system', 'content' : self.skills[skill_name].purpose},
                {'role' : 'system', 'content' : f'Here are some directions to guide your task:\n{self.skills[skill_name].directions}'}
            ]
            if len(chat_context):
                self.skill_chat += chat_context

            # Run workflow
            for task_n,task in self.skills[skill_name].workflow.items():
                execution_log.append(f'  * Executing task {task_n + 1}...')
                try:
                    if task.startswith('RUN'):
                        self.subprocess_action(task, skill_name, **kwargs)
                    else:
                        self.llm_action(llm_call, task, **kwargs)
                    execution_log.append('    \u2714 Execution complete')
                    success = True
                except:
                    execution_log.append('    \u2717 Execution failed')
                    success = False
                    break

        else:
            
            execution_log.append('  \u2717 ERROR: skill not found')
            success = False
        
        if success:
            execution_log.append(self.skills[skill_name].completion_message.replace('<previous_output>', self.skill_outputs[-1]))
        else:
            execution_log.append('Skill execution failed')
    
        return success, self.skill_outputs, execution_log
    
    ### ------------------------------------ ###

    def subprocess_action(self, task: str, skill_name: str, **kwargs):

        """
        Executes workflow step using subprocess.run
        """

        # Extract instructions for subprocess.run
        instructions = json.loads(task.split('```')[1])

        # Parse command
        scripts_dir_path = f'{self.skills[skill_name].skill_dir}/scripts/'
        for i,a in enumerate(instructions['args']):
            # Anatomize 'scripts' directory
            if 'script' in a:
                instructions['args'][i] = instructions['args'][i].replace('scripts/', scripts_dir_path)
            # Anatomize previous output
            if '<previous_output>' in a:
                instructions['args'][i] = instructions['args'][i].replace('<previous_output>', f'"{self.skill_outputs[-1]}"')
            # Anatomize skill inputs
            for skill_arg in self.skills[skill_name].inputs.keys():
                if f'<{skill_arg}>' in a:
                    try:
                        instructions['args'][i] = instructions['args'][i].replace(f'<{skill_arg}>', kwargs[skill_arg])
                    except:
                        instructions['args'][i] = instructions['args'][i].replace(f'<{skill_arg}>', self.skills[skill_name].default_inputs[skill_arg])
        
        # Run command
        if 'stdout' in instructions['kwargs']:
            # With stdout redirection
            if instructions['kwargs']['stdout'][1:-1] in kwargs.keys():
                skill_arg = instructions['kwargs']['stdout'][1:-1]
                stdout_target = kwargs[skill_arg]
            elif instructions['kwargs']['stdout'][1:-1] in self.skills[skill_name].default_inputs.keys():
                skill_arg = instructions['kwargs']['stdout'][1:-1]
                stdout_target = self.skills[skill_name].default_inputs[skill_arg]
            else:
                stdout_target = instructions['kwargs']['stdout']
            with open(stdout_target, 'w') as stdout:
                instructions['kwargs']['stdout'] = stdout
                command_run = subprocess_run(instructions['args'], **instructions['kwargs'])
        else:
            # No stdout redirection
            command_run = subprocess_run(instructions['args'], **instructions['kwargs'])
        
        # Command output
        if instructions['capture'] == 'none':
            command_output = ''
        elif instructions['capture'] == "stdout":
            command_output = command_run.stdout
        elif instructions['capture'] == "stderr":
            command_output = command_run.stderr
        else:
            command_output = command_run.stdout + '\n' + command_run.stderr
        self.skill_outputs.append(command_output)
        
        # Update chat
        if instructions['message'] != '':
            self.skill_chat.append({'role' : 'agent', 'content' : instructions['message']})
        if command_output != '':
            self.skill_chat.append({'role' : 'agent', 'content' : command_output})

    ### ------------------------------------ ###

    def llm_action(self, llm_call: Callable, task: str, **kwargs):

        """
        Executes workflow step using LLM
        """

        # Find arguments and replace them with their values
        task_args = findall('<[^ ]*>', task)
        for ta in task_args:
            if ta == '<previous_output>':
                task = task.replace(ta, f'"{self.skill_outputs[-1]}"')
            else:
                try:
                    task = task.replace(ta, kwargs[ta[1:-1]])
                except:
                    continue
        
        # LLM task
        self.skill_chat.append({'role' : 'user', 'content' : task})

        # Run LLM
        llm_response = llm_call(self.skill_chat)
        if '/no_think' in task:
            for token in ['<think>', '</think>']:
                if token in llm_response:
                    llm_response = llm_response.split(token)[-1].strip()
        self.skill_outputs.append(llm_response)

        # Update chat
        self.skill_chat.append({'role' : 'agent', 'content' : llm_response})
