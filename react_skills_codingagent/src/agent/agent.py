#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import json

from collections.abc import Callable
from datetime import datetime
from src.memory_handler.memory_handler import MemoryHandler
from src.skills_manager.skills_manager import SkillsManager
#from torch import float16 as torch_float16
#from torch.cuda import is_available as cuda_is_available
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TextGenerationPipeline
)
from typing import Any

### CLASSES AND FUNCTIONS ------------------ ###

class CodingAgent:

    """
    Class for managing the agent loop

    Parameters
    ----------
    config : dict
        Configuration dictionary containing all necessary parameters
    
    Methods
    -------
    process_query(self, query: str) -> str
        Query processing workflow
    """

    ### ------------------------------------ ###

    def __init__(self, config: dict) -> None:

        # Loop-affecting vars
        self.max_iterations = config['agent']['max_iterations']
        self.max_messages_in_memory = config['agent']['max_useful_chat_messages']
        
        # Init trace log
        self.agent_trace = []
        self.log_trace(trace_message='Initializing agent')

        # Init LLM
        self.llm_call = self.init_llm_model(
            config['model']['checkpoint'],
            config['model']['device_map'],
            config['model']['max_new_tokens']
        )
        self.no_think_mode = config['model']['no_think_mode']
        self.log_trace(trace_message='Added LLM engine')

        # Init skills manager
        self.skills_manager = SkillsManager(config['skills']['skills_dir'])
        self.log_trace(trace_message='Added skills')
        
        # Init agent memory
        self.memory = MemoryHandler(
            config['memory']['memory_path'],
            config['memory']['checkpoint'],
            config['memory']['device_map'],
            config['memory']['similarity_fn_name']
        )
        self.memory_score_threshold = config['memory']['score_threshold']
        self.log_trace(trace_message='Added memory')

    ### ------------------------------------ ###
    ### LLM MODEL                            ###
    ### ------------------------------------ ###

    @staticmethod
    def init_llm_model(model_checkpoint: str, device_map: str='auto', max_new_tokens: int=2048) -> Callable:

        """
        Initializes the LLM

        Parameters
        ----------
        model_checkpoint: str
            Checkpoint to use
        device_map: str='auto'
            Device to use for inference
        max_new_tokens: int=2048
            Max new tokens to generate
        
        Returns
        -------
        Callable
            Lambda functions for generating text given a list of chat messages
        """

        # Tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)

        # Init model
        """
        # BitsAndBytesConfig has issues on Mac Silicon
        # So, might as well use a quantized model from HuggingFace
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
        llm = AutoModelForCausalLM.from_pretrained(
            model_checkpoint,
            use_safetensors=True,
            low_cpu_mem_usage=True,
            device_map=device_map
        )

        # Init text generator
        llm_pipeline = TextGenerationPipeline(
            llm,
            tokenizer,
            framework="pt",
            task="text-generation"
        )

        # Init lambda function for text generation
        llm_call = lambda chat: llm_pipeline(chat, max_new_tokens=max_new_tokens)[0]['generated_text'][-1]['content']

        return llm_call

    ### ------------------------------------ ###

    @staticmethod
    def clean_llm_response(llm_response: str) -> dict:

        """
        Cleans the agent response

        Parameters
        ----------
        llm_response: str
            Agent response to be cleaned
        
        Returns
        -------
        dict
            Cleaned agent response
        """

        # Extract relevant part of the response
        if '<skill>' in llm_response:
            llm_response = llm_response.split('<skill>')[-1].strip()
            if '</skill>' in llm_response:
                llm_response = llm_response.split('</skill>')[0].strip()

        # Convert to dict
        required_skill_call_fields = ["though", "skill_name", "skill_params"]
        try:
            parsed_response = json.loads(llm_response.strip())
            parsed_response = {key : val.strip() if isinstance(val, str) else val for key,val in parsed_response.items()}
            if not all(field in parsed_response.keys() for field in required_skill_call_fields):
                return parsed_response, False
            else:
                return parsed_response, True
        except:
            return {}, False

    ### ------------------------------------ ###
    ### TRACE LOG                            ###
    ### ------------------------------------ ###

    def log_trace(self, trace_message: str) -> None:

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
        self.agent_trace.append(timestamped_trace_message)
    
    ### ------------------------------------ ###
    ### CHAT INIT                            ###
    ### ------------------------------------ ###

    def init_chat(self, query: str) -> None:

        """
        Inits the chat messages with
          * The initial system prompt
          * List of available skills
          * Relevant past messages (short-term memory)
          * User query
        
        Parameters
        ----------
        query: str
            The user query
        """

        # Init chat messages
        self.chat_history = [
            {'role' : 'system', 'content' : 'You are an expert AI coding assistant'},
            {'role' : 'system', 'content' : f"Here's a list of skills available to you:\n{self.skills_manager.get_skills_descriptions()}"}
        ]

        # Add instructions for skill calling
        skill_call_message = """
        {
            "though" : "Your reasoning",
            "skill_name" : "The name of skill assigned to the task or DONE if you answered the query",
            "skill_params" : "Dictionary of skills parameters"
        }
        """
        skill_call_message = f'Call skills using the following JSON format within <skill> </skill> XML tags:\n<skill>{skill_call_message}</skill>'
        self.chat_history.append({'role' : 'system', 'content' : skill_call_message})

        # Update chat with relevant messages
        useful_messages = [c['content'] for c in self.chat_history if c['role'] not in ['system', 'user']][-self.max_messages_in_memory:]
        useful_messages += self.memory.retrieve_memory(
            context=query,
            max_hits=self.max_messages_in_memory,
            score_threshold=self.memory_score_threshold
        )
        useful_messages = [{'role' : 'agent', 'content' : content} for content in list(set(useful_messages))]
        self.chat_history += useful_messages

        # Add user query
        self.chat_history.append({'role' : 'user', 'content' : query})

    ### ------------------------------------ ###
    ### THINK/DECIDE/ACT LOOP                ###
    ### ------------------------------------ ###

    def process_query(self, query: str) -> str:

        """
        Query-processing workflow

        Parameters
        ----------
        query : str
            The query to be answered

        Returns
        -------
        str
            The answer to the query or the last recorded processing message
        """

        # Init iterations counter and resets the query answer
        self.current_iteration = 0
        self.query_answer = ''

        # Process query
        if self.no_think_mode:
            query = query if '/no_think' in query else query + ' /no_think' # For Qwen models
        if not len(query) or not isinstance(query, str):
            return "Sorry, I didn't understand your question."
        else:
            self.query = query
            self.memory.log_memory(origin='user', content=query)
            self.init_chat(query)
            self.think()
            self.log_trace(trace_message=self.query_answer)
            return self.query_answer
    
    ### ------------------------------------ ###

    def think(self) -> None:

        """
        Iteratively processes the current query with LLM-driven actions
        """

        # Update iterations counter
        self.current_iteration += 1

        # Call LLM or provide a final answer if no more iterations are needed
        if self.current_iteration > self.max_iterations:
            out_of_iterations_message = "I'm sorry, but I couldn't find a good answer."
            self.query_answer = out_of_iterations_message
            self.chat_history.append({'role' : 'agent', 'content' : out_of_iterations_message})
            self.memory.log_memory(origin='agent', content=self.chat_history[-1]['content'])
        else:
            agent_response = self.llm_call(self.chat_history)
            print(agent_response) ### TESTING
            self.memory.log_memory(origin='agent', content=agent_response)
            self.decide(agent_response)

    ### ------------------------------------ ###

    def decide(self, agent_response: dict) -> None:

        """
        Parses the agent's response, deciding what to do next
        """

        # Extract relevant information from the response
        action, response_qc = self.clean_llm_response(agent_response)
        
        # Process response
        if not response_qc:
            self.log_trace(trace_message='I encounter an error. Retrying.')
            self.think()
        elif action['skill_name'].upper() == 'DONE':
            self.query_answer = action['thought']
            self.chat_history.append({'role' : 'agent', 'content' : self.query_answer})
            self.memory.log_memory(origin='agent', content=self.chat_history[-1]['content'])
        elif action['skill_name'] not in self.skills_manager.skills.keys():
            self.log_trace(trace_message=f'Skill "{action["skill_name"]} not valid. Skipping.')
            self.think()
        else:
            self.log_trace(trace_message=f'Using skill "{action["skill_name"]}"')
            self.act(action)

    ### ------------------------------------ ###

    def act(self, action: dict) -> str:

        """
        Executes skills
        """

        # Execute the skill
        skill_exec_status, skill_outputs, skill_execution_log = self.skills_manager.execute_skill(
            llm_call=self.llm_call,
            skill_name=action['skill_name'],
            chat_context=[c for c in self.chat_history if c['role'] in ['user', 'agent']],
            **action['skill_params']
        )
        
        # Log the skill execution
        for log in skill_execution_log:
            self.log_trace(trace_message=log)

        # Log the action execution in chat and memory
        if skill_exec_status:
            # Update chat and memory
            self.chat_history.append({'role' : 'agent', 'content' : 'I used the skill "{action["skill_name"]}".'})
            self.memory.log_memory(origin='agent', content=self.chat_history[-1]['content'])
            self.chat_history.append({'role' : 'agent', 'content' : skill_execution_log[-1]})
            self.memory.log_memory(origin='agent', content=self.chat_history[-1]['content'])
        else:
            # Update chat and memory
            self.chat_history.append({'role' : 'agent', 'content' : f"I couldn't use the skill, here's the execution log:\n{''.join(skill_execution_log)}"})
            self.memory.log_memory(origin='agent', content=self.chat_history[-1]['content'])
        
        # Next think cycle
        self.think()
