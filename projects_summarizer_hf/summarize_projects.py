#!/usr/bin/env python3

"""
This script parses project folders in search of ReadME.txt files.
It then uses the folder name and the ReadME.txt to create a summary of all projects.
N.B. The project folder must follow the following naming convention:
<date>_<project_supervisor>_<tag>
with:
    <date> : date in <year><month><day> format (e.g. 20261231)
    <project_supervisor> : name of Principal Investigator for the project (could also be just a project id of sorts)
    <tag> : most relevant tag for the project (e.g. RNASeq, WGS, etc)
e.g. 20261231_Smith_RNASeq
"""

### IMPORTS -------------------------------- ###

from collections.abc import Callable
from datetime import datetime
from gc import collect as gc_collect
from os import listdir
from os.path import exists
from sys import argv
from torch import no_grad as torch_no_grad
#from torch import float16 as torch_float16
#from torch.cuda import is_available as cuda_is_available
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TextGenerationPipeline
)

### CLASSES AND FUNCTIONS ------------------ ###

def init_text_generation_model(model_checkpoint: str, device_map: str='auto'):

    """
    Initialize the LLM
    """

    # Tokenizer
    
    tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)

    # Init model

    """
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch_float16
    ) if cuda_is_available else None

    model = AutoModelForCausalLM.from_pretrained(
        model_checkpoint,
        use_safetensors=True,
        low_cpu_mem_usage=True,
        quantization_config=quantization_config,
        device_map=device_map
    )
    """

    model = AutoModelForCausalLM.from_pretrained(
        model_checkpoint,
        use_safetensors=True,
        low_cpu_mem_usage=True,
        device_map=device_map
    )

    # Init text generator

    text_generator = TextGenerationPipeline(
        model,
        tokenizer,
        framework="pt",
        task="text-generation"
    )

    return text_generator

### ---------------------------------------- ###

class project_descriptor:

    """
    Class for creating a project summary
    """
    
    # Variables for guiding LMM choice

    tool_type = "llm"
    
    name = 'data_summarizer'
    
    description = """
    This is a tool that summarizes text
    """
    
    inputs = {
        'query': {
            'type': 'string',
            'description': 'Input data to summarize'
        },
        'context': {
            'type': 'string',
            'description': 'Context to guide the text generation'
        }
    }
    
    output_type = 'string'
    
    ### ------------------------------------ ###
    
    def __init__(self, model_checkpoint: Callable, device_map: str='cpu'):
        
        self.is_initialized = False # For compatibility with smolagents

        self.model = init_text_generation_model(model_checkpoint, device_map)

        self.output_block_tokens = ['<summary>', '</summary>']

        self.prompt = f"""
<|im_start|>system
You are an expert at extracting key points from a provided text.
[CONTEXT]
<im_end>
<|im_start|>user
Extract key information from following data: [QUERY]
Report the key information as bullet points wrapped within {self.output_block_tokens[0]} {self.output_block_tokens[1]} XML tags.
/no_think
<im_end>
<|im_start|>assistant

"""
    
    ### ------------------------------------ ###
    
    @torch_no_grad()
    def forward(self, query: str, context: str='', max_new_tokens: int=512) -> str:

        # Update prompt

        updated_prompt = self.prompt.replace('[QUERY]', query)

        if context != '':

            updated_prompt = updated_prompt.replace('[CONTEXT]', f"Here's some context to guide the summary generation: {context}")

        else:

            updated_prompt = updated_prompt.replace('[CONTEXT]', '')

        # Run LLM

        llm_output = self.model(
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

def create_summary(overwrite: bool=False):

    entries_separator = '-' * 40

    # Load old summary file

    summary_file = 'projects_summary.md'

    if exists(summary_file):

        old_summary = open(summary_file, 'r').read().split(entries_separator)

        old_summary = [entry.strip() for entry in old_summary if len(entry.strip())][1:]

        old_summary = {entry.split('\n')[0].replace('# PROJECT ID: ', '') : entry for entry in old_summary}

    else:

        old_summary = dict()

    # Find projects

    print("# Finding projects to summarize")

    standard_readme = 'ReadME.txt'

    projects = [p for p in listdir() if exists(f'{p}/{standard_readme}')]

    projects_n = len(projects)

    print(f'  * Found {projects_n} projects')

    # Init summary generator

    print("# Init LLM model")

    model_checkpoint = 'Qwen/Qwen3-0.6B'

    device_map = 'cpu'

    summarizer = project_descriptor(model_checkpoint, device_map)

    # Create summary

    print("# Summarizing projects")

    summary_format = f"""
{entries_separator}
# PROJECT ID: [PROJECT_ID]
## DATE: [DATE]
## PI: [PI]
## TAG: [TAG]
## DESCRIPTION:
[DESCRIPTION]
{entries_separator}
"""

    summary = []

    for N,p in enumerate(projects):

        print(f'  * Summarizing project {N + 1} / {projects_n} : {p}')

        if not overwrite and p in old_summary.keys():

            structured_p_summary = '\n' + entries_separator + '\n' + old_summary[p] + '\n' + entries_separator

            print('    \u2714 Summary already exists, skipping')

        else:

            # Extract date, PI, and tag

            try:

                date, pi, *tag = p.split('_')

                tag = tag[0] if len(tag) else ""

            except:

                print('    \u2717 Folder name is unconventional, skipping')

                continue

            # Read project notes

            notes = open(f'{p}/{standard_readme}', 'r').read()

            if '### Notes' in notes:

                notes = notes.replace('### Notes:', '### Notes').split('### Notes')[-1]

            # Summarize project notes

            p_summary = ''

            while not len(p_summary):

                try:

                    p_summary = summarizer.forward(query=notes)

                except:

                    p_summary = ''

            # Format summary

            structured_p_summary = summary_format

            structured_p_summary = structured_p_summary.replace('[PROJECT_ID]', p)
            structured_p_summary = structured_p_summary.replace('[DATE]', date)
            structured_p_summary = structured_p_summary.replace('[PI]', pi)
            structured_p_summary = structured_p_summary.replace('[TAG]', tag)
            structured_p_summary = structured_p_summary.replace('[DESCRIPTION]', p_summary)

            print(f'    \u2714 Summary complete')

        summary.append(structured_p_summary)

    # Sort by project date

    summary.sort(key = lambda entry: entry.split('\n')[2].replace('## DATE: ', ''))

    # Add header and join as string

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S").replace(' ', '_')

    summary_header = '\n'.join([entries_separator, f'UPDATED: {timestamp}', entries_separator])

    summary = '\n'.join([summary_header] + summary)

    # Save summary to file

    with open(summary_file, 'w') as summary_out:

        summary_out.write(summary)

### ---------------------------------------- ###

if __name__ == '__main__':

    overwrite_toggle = ('--overwrite' in argv)

    create_summary(overwrite_toggle)

    gc_collect()
