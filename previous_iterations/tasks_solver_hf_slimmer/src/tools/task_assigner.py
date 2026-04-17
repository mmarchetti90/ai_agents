#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import json

from collections.abc import Callable
from torch import no_grad as torch_no_grad

### CLASSES AND FUNCTIONS ------------------ ###

class task_assigner:
    
    """
    Class for decomposing a query into a set of tasks
    """
    
    # Variables for guiding LMM choice

    tool_type = "llm"
    
    name = 'task_assigner'
    
    description = """
    This is a tool that assigns a tool to a query
    """
    
    inputs = {
        'query': {
            'type': 'string',
            'description': 'User-submitted query'
        },
        'tools_description': {
            'type': 'string',
            'description': 'JSON-formatted string describing available tools'
        },
        'context': {
            'type': 'string',
            'description': 'Context to guide the text generation'
        }
    }
    
    output_type = 'list of strings'
    
    ### ------------------------------------ ###
    
    def __init__(self):
        
        self.is_initialized = False # For compatibility with smolagents

        self.output_block_tokens = ['<tool_call>', '</tool_call>']

        self.prompt = f"""
<|im_start|>system
You are an expert at assigning tools to specific tasks.
[CONTEXT]
The tool calls available to you are described within <tools> </tools> XML tags:
<tools>
[TOOLS]
</tools>
<im_end>
<|im_start|>user
Assign a tool to the following query: [QUERY]

Call the tool using the following JSON format within {self.output_block_tokens[0]} {self.output_block_tokens[1]} XML tags as follows:
{self.output_block_tokens[0]}
{{
  "tool": "Name of the tool you choose to use ([TOOL_NAMES]). Choose NONE if you're ready to answer.",
  "reason": "Short explanation of why you chose this tool.",
  "input": "Specific input for the tool."
}}
{self.output_block_tokens[1]}
/no_think
<im_end>
<|im_start|>assistant

"""
    
    ### ------------------------------------ ###
    
    @torch_no_grad()
    def forward(self, model: Callable, tasks: list[str], tools_description: str, context: str='', max_new_tokens: int=512) -> list[str, dict]:

        """
        # Tool descriptions should be a string in this format
        {
          "type": "function",
          "name": "tool_1",
          "description": "This tool does something",
          "parameters": {
            "parameter_1": {
              "type": "string",
              "description": "What the parameters is"
            }
          }
        }
        {
          "type": "function",
          "name": "tool_2",
          "description": "This tool does something",
          "parameters": {
            "parameter_1": {
              "type": "string",
              "description": "What the parameters is"
            },
            "parameter_2": {
              "type": "string",
              "description": "What the parameters is"
            }
          }
        }
        """

        assigned_tasks = []

        task_n = 0

        while len(assigned_tasks) < len(tasks):

            query = tasks[task_n]

            # Update prompt

            updated_prompt = self.prompt.replace('[QUERY]', query).replace('[TOOLS]', tools_description)

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

            #print(llm_output) ### TESTING
            
            # Parse output

            tool_info = self.parse_llm_output(llm_output, self.output_block_tokens)

            # Check that tool call has required keys

            if any(field not in tool_info.keys() for field in ["tool", "reason", "input"]):

                continue

            # Making sure a valid tool was chosen
            
            if f'"name": "{tool_info["tool"]}"' in tools_description:

                assigned_tasks.append((query, tool_info))

                task_n += 1

            else:

                continue

        return assigned_tasks

    ### ------------------------------------ ###

    @staticmethod
    def parse_llm_output(text: str, delimiters: list[str]) -> dict[str]:

        parsed_text = text.strip()

        # Check start token
        
        if '<|im_start|>assistant' in parsed_text:

            parsed_text = parsed_text.split('<|im_start|>assistant')[-1].strip()
        
        if delimiters[0] in parsed_text:
                
            parsed_text = parsed_text.split(delimiters[0])[-1].strip()
                
            if delimiters[1] in parsed_text:
                
                parsed_text = parsed_text.split(delimiters[1])[0].strip()
        
        #parsed_text = parsed_text.replace('{{', '{').replace('}}', '}')
        
        try:
            
            json_answer = json.loads(parsed_text)
            
        except:
            
            json_answer = json.loads({'tool': 'none', 'reason': '', 'input': ''})

        return json_answer
        
### ---------------------------------------- ###

if __name__ == '__main__':
    
    query = [
        "Who is Drizzt Do'Urden?",
        "Get the most updated data on the role of EGFR in cancer"
    ]

    tools_description = '{\n  \"type\": \"function\",\n  \"name\": \"pubmed_literature_search\",\n  \"description\": \"This is a tool that downloads scientific research abtracts from PubMed and is best used to find up-to-date reseach data\",\n  \"parameters\": {\n    \"query\": {\n      \"type\": \"string\",\n      \"description\": \"String of space-separated keywords\"\n    }\n  }\n}\n\n{\n  \"type\": \"function\",\n  \"name\": \"wikipedia_search\",\n  \"description\": \"This is a tool that downloads extracts from Wikipedia and is best used to retrieve general knowledge about a subject\",\n  \"parameters\": {\n    \"query\": {\n      \"type\": \"string\",\n      \"description\": \"String of space-separated keywords\"\n    }\n  }\n}'
    
    text_generator = task_assigner()

    from src.models.generation_model import init_text_generation_model
    
    model = init_text_generation_model(model_checkpoint='Qwen/Qwen3-0.6B', device_map='cpu')

    output = text_generator.forward(model=model, query=query)

    with open('test_task_assignment.txt', 'w') as out:
    
        out.write('\n'.join([f'{task}: {tool}' for (task,tool) in output]))
