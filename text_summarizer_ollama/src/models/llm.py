#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

from collections.abc import Callable
from ollama import chat as OllamaChat
from ollama import ChatResponse

### CLASSES AND FUNCTIONS ------------------ ###

class LLM:

    """
    Class for running a LLM
    
    Parameters
    ----------
    model_checkpoint: str
        Name of the model checkpoint to use
    max_new_tokens: int=512
        Maximum number of new tokens

    Methods
    -------
    forward(prompt: str, max_new_tokens: int=512) -> str
        Runs inference
    """
    
    ### ------------------------------------ ###
    
    def __init__(
        self,
        model_checkpoint: str,
        max_new_tokens: int=512
    ) -> None:

        self.output_block_tokens = ['<output>', '</output>']
        self.model_checkpoint = model_checkpoint
        self.max_new_tokens = max_new_tokens
    
    ### ------------------------------------ ###
    
    def forward(
        self,
        chat: list[dict],
        tools: list[str]=[],
        think=False
    ) -> str:

        """
        Runs inference

        Parameters
        ----------
        chat: list[dict]
            Prompt chat to be fed to the llm
        """

        # Run LLM
        raw_llm_output: ChatResponse = OllamaChat(
            model=self.model_checkpoint,
            messages=chat,
            tools=tools,
            think=think,
            options={
                'num_ctx': 4096,
                'num_predict': self.max_new_tokens
            }
        )

        # Parse response
        parsed_llm_output = raw_llm_output.message.content or raw_llm_output.message.thinking
        parsed_llm_output = parsed_llm_output if isinstance(parsed_llm_output, str) else ''
        parsed_llm_output = parsed_llm_output.strip()
        if '<|im_start|>assistant' in parsed_llm_output:
            parsed_llm_output = parsed_llm_output.split('<|im_start|>assistant')[-1].strip()
        if self.output_block_tokens[0] in parsed_llm_output:
            parsed_llm_output = parsed_llm_output.split(self.output_block_tokens[0])[-1].strip()
            if self.output_block_tokens[1] in parsed_llm_output:
                parsed_llm_output = parsed_llm_output.split(self.output_block_tokens[1])[0].strip()
    
        return parsed_llm_output
        
### ---------------------------------------- ###

if __name__ == '__main__':
    
    chat = [
        {'role' : 'system', 'content' : 'You are a creative writer of science fiction stories.'},
        {'role' : 'user', 'content' : 'Tell me a three sentence horror story. /no_think'}
    ]

    model_checkpoint, max_new_tokens ='qwen3.5:4b', 512
    llm_instance = LLM(model_checkpoint, max_new_tokens)
    output = llm_instance.forward(chat=chat)

    with open('llm_test.txt', 'w') as out:
        out.write(output)
