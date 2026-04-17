#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

from collections.abc import Callable
from torch import no_grad as torch_no_grad

### CLASSES AND FUNCTIONS ------------------ ###

class query_decomposition:
    
    """
    Class for decomposing a query into a set of tasks
    """
    
    # Variables for guiding LMM choice

    tool_type = "llm"
    
    name = 'query_decomposition'
    
    description = """
    This is a tool that decomposes a query into subtasks for solving the query
    """
    
    inputs = {
        'query': {
            'type': 'string',
            'description': 'User-submitted query'
        },
        'context': {
            'type': 'string',
            'description': 'Context to guide the text generation'
        }
    }
    
    output_type = 'list of strings'
    
    ### ------------------------------------ ###
    
    def __init__(self, max_tasks: int=5):
        
        self.is_initialized = False # For compatibility with smolagents

        self.max_tasks = max_tasks

        self.output_block_tokens = ['<subtasks>', '</subtasks>']

        self.task_identifier = "TASK="

        self.prompt = f"""
<|im_start|>system
You are an expert at decomposing a complex task into subtasks.
[CONTEXT]
<im_end>
<|im_start|>user
Decompose the following query into at  most [N_MAX_TASKS] subtasks: [QUERY]
List the subtask within {self.output_block_tokens[0]} {self.output_block_tokens[1]} XML tags.
Each subtasks need to have the prefix "{self.task_identifier}".
/no_think
<im_end>
<|im_start|>assistant

"""
    
    ### ------------------------------------ ###
    
    @torch_no_grad()
    def forward(self, model: Callable, query: str, context: str='', max_new_tokens: int=512) -> list[str]:

        # Update prompt

        updated_prompt = self.prompt.replace('[N_MAX_TASKS]', str(self.max_tasks)).replace('[QUERY]', query)

        if context != '':

            updated_prompt = updated_prompt.replace('[CONTEXT]', f"Here's some context from previous tasks: {context}")

        else:

            updated_prompt = updated_prompt.replace('[CONTEXT]', '')

        # Run LLM

        llm_output = model(
            updated_prompt,
            return_full_text=False,
            max_new_tokens=max_new_tokens
        )[0]['generated_text']
        
        # Parse output

        tasks = self.parse_llm_output(llm_output, self.output_block_tokens, self.task_identifier)

        tasks = tasks[:self.max_tasks]

        return tasks

    ### ------------------------------------ ###

    @staticmethod
    def parse_llm_output(text: str, delimiters: list[str], task_identifier: str) -> list[str]:

        parsed_text = text.strip()

        # Check start token
        
        if '<|im_start|>assistant' in parsed_text:

            parsed_text = parsed_text.split('<|im_start|>assistant')[-1].strip()
        
        if delimiters[0] in parsed_text:
                
            parsed_text = parsed_text.split(delimiters[0])[-1].strip()
                
            if delimiters[1] in parsed_text:
                
                parsed_text = parsed_text.split(delimiters[1])[0].strip()

        # Parse bullets

        tasks = []

        for line in parsed_text.split('\n'):

            line = line.strip()

            line = line.replace(task_identifier.replace('=', ':'), task_identifier)

            if task_identifier in line:

                line = line[line.index(task_identifier) + len(task_identifier):].strip()

                tasks.append(line)

        return tasks
        
### ---------------------------------------- ###

if __name__ == '__main__':
    
    query = 'Download info about the "Dark Elf Trilogy" series by R. A. Salvatore, then list the books in publication order.'
    
    text_generator = query_decomposition()

    from src.models.generation_model import init_text_generation_model
    
    model = init_text_generation_model(model_checkpoint='Qwen/Qwen3-0.6B', device_map='cpu')

    output = text_generator.forward(model=model, query=query)

    with open('test_query_decomposition.txt', 'w') as out:
    
        out.write('\n'.join(output))
