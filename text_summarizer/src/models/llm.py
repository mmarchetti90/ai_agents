#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

from collections.abc import Callable
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

class llm:

    """
    Class for running a LLM
    
    Parameters
    ----------
    model_checkpoint: str
        Name of the model checkpoint to use
    device_map: str='auto'
        Device to be used for inference

    Methods
    -------
    init_model(model_checkpoint: str, device_map: str='auto') -> Callable
        Initializes the model to be used for inference
        Ran automatically at initialization
    forward(prompt: str, max_new_tokens: int=512) -> str
        Runs inference
    """
    
    ### ------------------------------------ ###
    
    def __init__(
        self,
        model_checkpoint: str,
        device_map: str='auto'
    ) -> None:

        self.output_block_tokens = ['<output>', '</output>']

        self.model = self.init_model(model_checkpoint, device_map)

    ### ------------------------------------ ###

    def init_model(
        self,
        model_checkpoint: str,
        device_map: str='auto'
    ) -> Callable:

        """
        Initializes the model to be used for inference
        
        Parameters
        ----------
        model_checkpoint: str
            Name of the model checkpoint to use
        device_map: str='auto'
            Device to be used for inference
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

        model_pipeline = TextGenerationPipeline(
            model,
            tokenizer,
            framework="pt",
            task="text-generation"
        )

        return model_pipeline
    
    ### ------------------------------------ ###
    
    @torch_no_grad()
    def forward(
        self,
        prompt: str,
        max_new_tokens: int=512
    ) -> str:

        """
        Runs inference

        Parameters
        ----------
        prompt: str
            Prompt to be fed to the llm
        max_new_tokens: int=512
            Maximum number of new tokens
        """

        # Run LLM

        raw_llm_output = self.model(
            prompt,
            return_full_text=False,
            max_new_tokens=max_new_tokens
        )[0]['generated_text']
        
        # Parse output

        parsed_llm_output = raw_llm_output.strip()

        if '<|im_start|>assistant' in parsed_llm_output:

            parsed_llm_output = parsed_llm_output.split('<|im_start|>assistant')[-1].strip()
        
        if self.output_block_tokens[0] in parsed_llm_output:
                
            parsed_llm_output = parsed_llm_output.split(self.output_block_tokens[0])[-1].strip()
                
            if self.output_block_tokens[1] in parsed_llm_output:
                
                parsed_llm_output = parsed_llm_output.split(self.output_block_tokens[1])[0].strip()

        return parsed_llm_output
        
### ---------------------------------------- ###

if __name__ == '__main__':
    
    prompt = f"""
<|im_start|>system
You are a creative writer of fictional stories.
You love science fiction.
<im_end>
<|im_start|>user
Tell me a three sentence horror story.
Wrap the story within <output> </output> XML tags.
/no_think
<im_end>
<|im_start|>assistant

"""

    model_checkpoint, device_map ='Qwen/Qwen3.5-0.8B', 'cpu'

    llm_instance = llm(model_checkpoint, device_map)

    output = llm_instance.forward(prompt=prompt)

    with open('llm_test.txt', 'w') as out:
    
        out.write(output)
