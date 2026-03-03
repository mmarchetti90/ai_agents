#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

from collections.abc import Callable
from torch import no_grad as torch_no_grad

### CLASSES AND FUNCTIONS ------------------ ###

class code_writer:

    """
    Class for writing code
    """
    
    # Variables for guiding LMM choice

    tool_type = "llm"
    
    name = 'code_writer'
    
    description = """
    This is a tool that writes Python code
    """
    
    inputs = {
        'query': {
            'type': 'string',
            'description': 'Description of code to generate'
        },
        'context': {
            'type': 'string',
            'description': 'Context to guide the text generation'
        }
    }
    
    output_type = 'string'
    
    ### ------------------------------------ ###
    
    def __init__(self):
        
        self.is_initialized = False # For compatibility with smolagents

        self.output_block_tokens = ['<code>', '</code>']

        self.prompt = f"""
<|im_start|>system
You are an expert Python programmer.
[CONTEXT]
<im_end>
<|im_start|>user
[QUERY]
Wrap the code within {self.output_block_tokens[0]} {self.output_block_tokens[1]} XML tags.
/no_think
<im_end>
<|im_start|>assistant

"""
    
    ### ------------------------------------ ###
    
    @torch_no_grad()
    def forward(self, model: Callable, query: str, context: str='', max_new_tokens: int=512) -> str:

        # Update prompt

        updated_prompt = self.prompt.replace('[QUERY]', query)

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

        parsed_llm_output = self.parse_llm_output(llm_output, self.output_block_tokens)

        return parsed_llm_output

    ### ------------------------------------ ###

    @staticmethod
    def parse_llm_output(text: str, delimiters: list[str]) -> str:

        parsed_text = text.strip()

        # Check start token
        
        if '<|im_start|>assistant' in parsed_text:

            parsed_text = parsed_text.split('<|im_start|>assistant')[-1].strip()
        
        if delimiters[0] in parsed_text:
                
            parsed_text = parsed_text.split(delimiters[0])[-1].strip()
                
            if delimiters[1] in parsed_text:
                
                parsed_text = parsed_text.split(delimiters[1])[0].strip()

        return parsed_text
        
### ---------------------------------------- ###

if __name__ == '__main__':
    
    query = "Write a funtion that returns the sum of a list of numbers."

    text_generator = code_writer()

    from src.models.generation_model import init_text_generation_model
    
    model = init_text_generation_model(model_checkpoint='Qwen/Qwen3-0.6B', device_map='cpu')

    output = text_generator.forward(model=model, query=query)

    with open('test_code_writer.txt', 'w') as out:
    
        out.write(output)
