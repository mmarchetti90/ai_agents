#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import json

### CLASSES AND FUNCTIONS ------------------ ###

class SkillBase:

    """
    Base class for storing skills and their implementations

    Parameters
    ----------
    skill_dir: str
        Directory where skill is located
    """

    ### ------------------------------------ ###

    def __init__(self, skill_dir: str) -> None:

        # Store skill_dir (needed for scripts execution)
        self.skill_dir = skill_dir
            
        # Read md file
        md_path = f'{skill_dir}/SKILL.md'
        md_raw = open(md_path, 'r').read()

        # Parse md contents
        self.parse_md(md_content=md_raw)

    ### ------------------------------------ ###

    def parse_md(self, md_content: str) -> None:

        # Read name and description from markdown file
        self.name = md_content.split('---')[1].strip().split('\n')[0].replace('name:', '').strip()
        self.description = md_content.split('---')[1].strip().split('\n')[0].replace('description:', '').strip()

        # Read inputs, purpose, directions, and workflow
        sections = {
            section.split('\n')[0].strip() : '\n'.join([row.strip() for row in section.split('\n')[1:]]).strip()
            for section in md_content.split('##')[1:]
        }
        self.inputs = json.loads(sections['Inputs'].replace('```json', '').replace('```', '').strip())
        self.default_inputs = json.loads(sections['Default inputs'].replace('```json', '').replace('```', '').strip())
        self.purpose = sections['Purpose'].strip()
        self.directions = sections['Directions'].strip()
        self.workflow = {i : w.replace(f'{i+1}. ', '') for i,w in enumerate(sections['Workflow'].split('\n'))}
        self.completion_message = sections['Completion message'].strip()
