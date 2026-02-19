#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import json

from collections.abc import Callable
from datetime import datetime
from src.agent_model.agent_model import init_text_generation_model
from src.embedding_model.embedding_model import init_text_embedding_model
from src.tools.pubmed_search import pubmed_search
from src.tools.wikipedia_search import wikipedia_search
from torch import no_grad as torch_no_grad

### GLOBAL VARS ---------------------------- ###

CONFIG_FILE = 'data/config/config.react.json'

### CLASSES AND FUNCTIONS ------------------ ###

def parse_config():

    """
    Parsing config file containing global vars
    """

    with open(CONFIG_FILE) as opened_config_file:
    
        config_data = json.load(opened_config_file)

    return config_data

### ---------------------------------------- ###

class ai_agent:

    """
    Class for AI agent responsible for running queries and handling tools
    ReAct architecture supplemented by RAG for filtering tool-retrieved data
    """

    def __init__(
        self,
        agent_model: Callable,
        agent_model_checkpoint: str,
        embedding_model: Callable,
        embedding_model_checkpoint: str,
        base_prompt_path: str,
        rag_similarity_function: str='cosine',
        max_rag_hits: int=10,
        use_rag: bool=True,
        device_map: str='cpu',
        max_iterations: int=5,
        max_new_tokens: int=1024,
        trace_log_dir: str='./',
        history_log_dir: str='./'

    ) -> None:

        """
        Initializes the AI Agent

        Parameters
        ----------
        agent_model
            The LLM used to run the agent
        agent_model_checkpoint
            Name or path of the checkpoint for the agent model
        embedding_model
            The model to be used for RAG
        embedding_model_checkpoint
            Name or path of the checkpoint for the RAG model
        base_prompt_path
            Path to the base prompt
        rag_similarity_function
            Similarity function for the RAG model
            Default = 'cosine'
        max_rag_hits
            Top relevant data hits
            Default = 10
        use_rag
            Set to True to use a RAG to filter the info retrieved by the tools
        device_map
            Device to use to run the models
            Default = 'cpu'
        max_iterations
            Maximum number of agent iterations 
            Default = 5
        max_new_tokens
            Maximum number of new tokens for the agent model
            Default = 1024
        trace_log_dir
            Where to store the trace log
            Default = './'
        history_log_dir
            Where to store the history log
            Default = './'
        """

        self.init_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S").replace(' ', '_')

        self.text_generation_model = agent_model(agent_model_checkpoint, device_map)

        self.text_embedding_model = embedding_model(embedding_model_checkpoint, device_map, rag_similarity_function)

        self.use_rag = use_rag

        self.max_rag_hits = max_rag_hits

        self.tools = {}
        
        self.messages_log = []

        self.query = ''
        
        self.max_iterations = max_iterations

        self.max_new_tokens = max_new_tokens

        self.current_iteration = 0
        
        self.prompt_template = self.load_prompt_template(base_prompt_path)

        self.trace_log_dir = trace_log_dir

        self.trace_log = self.init_trace_log()

        self.history_log_dir = history_log_dir

        self.history_log = self.init_history_log()

        self.last_thought = ''

        self.last_observations = 'Nothing yet. Use a tool to get relevant information.'

        self.tool_used = False

    ### ------------------------------------ ###
    ### PROMPT LOADING AND EDITING           ###
    ### ------------------------------------ ###

    @staticmethod
    def load_prompt_template(base_prompt_path) -> str:

        """
        Loads the base prompt template
        """

        prompt = open(base_prompt_path, 'r').read()

        return prompt

    ### ------------------------------------ ###

    def update_prompt(self) -> str:

        """
        Updates the prompt template with query, history, and tools
        """

        prompt_updated = self.prompt_template

        prompt_updated = prompt_updated.replace('[QUERY]', self.query)

        prompt_updated = prompt_updated.replace('[THOUGHTS]', self.last_thought if self.last_thought != "Didn't think" else "")

        prompt_updated = prompt_updated.replace('[OBSERVATIONS]', self.last_observations)

        prompt_updated = prompt_updated.replace('[TOOLS]', self.tools_prompt_text(self.tools))

        tool_names = ','.join(list(self.tools.keys())) + ', or NONE'

        prompt_updated = prompt_updated.replace('[TOOL_NAMES]', tool_names)

        return prompt_updated

    ### ------------------------------------ ###
    ### AGENT HISTORY                        ###
    ### ------------------------------------ ###

    def init_trace_log(self) -> str:

        """
        Inits the trace log of LLM responses

        Returns
        -------
        str
            Trace file path
        """

        trace_file_path = f'{self.trace_log_dir}/ai_assistant_trace_{self.init_timestamp}.json'

        empty_json = json.loads('{}')

        with open(trace_file_path, 'w') as trace_out:
    
            json.dump(empty_json, trace_out, indent=4)

        return trace_file_path

    ### ------------------------------------ ###

    def init_history_log(self) -> str:

        """
        Inits the history of past actions and observations

        Returns
        -------
        str
            Trace file path
        """

        history_file_path = f'{self.history_log_dir}/ai_assistant_history_{self.init_timestamp}.json'

        empty_json = json.loads('{}')

        with open(history_file_path, 'w') as history_out:
    
            json.dump(empty_json, history_out, indent=4)

        return history_file_path

    ### ------------------------------------ ###

    def log_trace(self, llm_response: dict) -> None:

        """
        Logs the JSON responses from the LLM.

        Parameters
        ----------
        llm_response : dict
            The JSON formatted LLM response
        """
        
        with open(self.trace_log, 'r') as trace_in:
    
            trace = json.load(trace_in)

        trace[f'iteration_{self.current_iteration}'] = llm_response
        
        with open(self.trace_log, 'w') as trace_out:
        
            json.dump(trace, trace_out, indent=4)

    ### ------------------------------------ ###

    def log_history(self, action: str, content: str) -> str:

        """
        Logs the most recent action and observations

        Parameters
        ----------
        action : str
            The action that was taken (e.g. what tool was run)
        content : str
            The result of the action
        """
        
        with open(self.history_log, 'r') as history_in:
    
            history = json.load(history_in)

        if f'iteration_{self.current_iteration}' not in history.keys():

            history[f'iteration_{self.current_iteration}'] = {}

        history[f'iteration_{self.current_iteration}'][action] = content
        
        with open(self.history_log, 'w') as history_out:
    
            json.dump(history, history_out, indent=4)

    ### ------------------------------------ ###
    ### THINK/DECIDE/ACT LOOP                ###
    ### ------------------------------------ ###

    def get_answer(self, query: str) -> str:

        """
        Query-processing workflow

        Parameters
        ----------
        query : str
            The query to be answered

        Returns
        -------
        str
            The final answer or last recorded processing message
        """

        self.query = query

        self.think()
        
        return self.final_answer

    ### ------------------------------------ ###

    def think(self) -> None:

        """
        Iteratively processes the current query with LLM-driven actions
        """

        self.current_iteration += 1

        if self.current_iteration > self.max_iterations:

            out_of_tries_answer = "I'm sorry, but I couldn't find a good answer. Here's what I've learnt so far: " + self.last_thought

            self.log_trace({
                'though' : 'Reached maximum iterations. Stopping.',
                'answer' : out_of_tries_answer
            })

            self.final_answer = out_of_tries_answer
            
            return

        else:

            prompt = self.update_prompt()
            
            self.log_history('prompt', prompt)

            thought, tool, answer = self.run_llm(prompt)

            self.decide(thought, tool, answer)

    ### ------------------------------------ ###

    def decide(self, thought:str, tool: list[str], answer: str) -> None:

        """
        Parses the agent's response, deciding what to do next

        Parameters
        ----------
        agent_response : str
            The response generated by the LLM during the "think" process
        """

        ### TESTING
        """
        if tool[0].lower() == 'none' and answer.lower() != 'none' and self.current_iteration > 1:

            self.final_answer = answer

            return

        else:

            tool_name = tool[0]

            if self.current_iteration == 1 and tool_name not in self.tools.keys():

                # Default to wikipedia_search if no tool was selected during the first iteration
                tool_name = 'wikipedia_search'

            tool_input = tool[-1] if tool[-1] != 'NONE' else self.query

            self.act(tool_name, tool_input)
        """

        try:

            #if answer.lower() != 'none' and self.current_iteration > 1:
            #if (tool[0].lower() == 'none' or self.tool_used) and answer.lower() != 'none' and self.current_iteration > 1:
            if tool[0].lower() == 'none' and answer.lower() != 'none' and self.current_iteration > 1:

                self.final_answer = answer

                return

            else:

                tool_name = tool[0]

                if self.current_iteration == 1 and tool_name not in self.tools.keys():

                    # Default to wikipedia_search if no tool was selected during the first iteration
                    tool_name = 'wikipedia_search'

                tool_input = tool[-1] if tool[-1] != 'NONE' else self.query

                self.act(tool_name, tool_input)

        except:

            self.log_history('warning', 'I encountered an error in processing. Let me try again.')
            
            self.think()

    ### ------------------------------------ ###

    def act(self, tool_name: str, tool_query: str) -> None:

        """
        Executes the selected tool

        Parameters
        ----------
        tool_name : str
            The tool to be used
        tool_query : str
            The tool's input
        """

        if tool_name in self.tools.keys():

            tool_retrieved_info = self.tools[tool_name].forward(tool_query)

            self.log_history('tool_use', tool_name)

            if self.use_rag:

                new_observations = self.extract_tool_info(self.query, tool_retrieved_info)

            else:

                new_observations = tool_retrieved_info

            self.tool_used = True

            self.log_history('observations', new_observations)

            self.last_observations = str(new_observations)

            self.think()
        
        else:

            self.tool_used = False
            
            self.think()

    ### ------------------------------------ ###
    ### TOOLS MANAGEMENT                     ###
    ### ------------------------------------ ###

    def add_tool(self, tool_call: Callable) -> None:

        """
        Registers a tool to the agent

        Parameters
        ----------
        tool_call : Callable
            A class with the following attributes: name, description, inputs, output_type
            Must also have the following method: forward (runs the tool) 
        """

        self.tools[tool_call.name] = tool_call()

    ### ------------------------------------ ###

    @torch_no_grad()
    def extract_tool_info(self, original_query: str, new_info: str) -> str:

        # Split info into sentences

        new_info = [ni for ni in new_info.replace('\n', '. ').split('. ') if len(ni)]
        #new_info = [ni for ni in new_info.split('\n') if len(ni)]

        # Embed query and info

        query_embedding = self.text_embedding_model.encode(original_query)

        info_embedding = self.text_embedding_model.encode(new_info)

        # Compute similarity of info to query

        similarity = [
            (sentence, score)
            for sentence,score in zip(new_info,
                                      self.text_embedding_model.similarity(query_embedding, info_embedding).tolist()[0])
        ]

        similarity.sort(key=lambda s: s[1], reverse=True)

        # Extract top hits and structure as bullet-points

        relevant_info = '\n'.join([f'* {s[0]}' for s in similarity[:self.max_rag_hits]])

        return relevant_info

    ### ------------------------------------ ###

    @staticmethod
    def tools_prompt_text(tools: dict) -> str:

        """
        Formats the tools information for the prompt

        Returns
        -------
        str
            Structured tools information
        """

        text = []

        for tool_name,tool in tools.items():

            tool_text = []
            tool_text.append('{')
            tool_text.append(f'{" " * 2}"type": "{tool.tool_type}",')
            tool_text.append(f'{" " * 2}"name": "{tool.name}",')
            tool_text.append(f'{" " * 2}"description": "{tool.description.strip()}",')
            tool_text.append((" " * 2) + '"parameters": {')
            inputs_description = []
            for input_name,input_description in tool.inputs.items():
                
                new_input_description = '\n'.join([f'{" " * 4}"{input_name}": ' + '{',
                                                   f'{" " * 6}"type": "{input_description["type"]}",',
                                                   f'{" " * 6}"description": "{input_description["description"]}"',
                                                   (" " * 4) + '}'])
                inputs_description.append(new_input_description)
            inputs_description = ',\n'.join(inputs_description)
            tool_text.append(inputs_description)
            tool_text.append('  }')
            tool_text.append('}')

            tool_text = '\n'.join(tool_text)

            text.append(tool_text)

        text = '\n\n'.join(text)

        return text

    ### ------------------------------------ ###
    ### LLM MANAGEMENT                       ###
    ### ------------------------------------ ###

    @staticmethod
    def clean_llm_answer(answer):

        # Check start token
        
        if '<|im_start|>assistant' in answer:

            answer = answer.split('<|im_start|>assistant')[-1].strip()
        
        # Check possible delimiters to trim the answer
        
        delimiter_sets = [['<tool_call>', '</tool_call>'], ['```json', '```']]
        
        for delimiters in delimiter_sets:

            if delimiters[0] in answer:
                
                answer = answer.split(delimiters[0])[-1].strip()
                
                if delimiters[1] in answer:
                
                    answer = answer.split(delimiters[1])[0].strip()
        
        #cleaned_answer = answer.replace('{{', '{').replace('}}', '}')
        cleaned_answer = answer
        
        try:
            
            json_answer = json.loads(cleaned_answer)
            
        except:
            
            json_answer = json.loads('{}')

        return json_answer

    ### ------------------------------------ ###

    @staticmethod
    def parse_json_response(json_response):

        # Extract though

        if 'thought' in json_response:

            thought = json_response['thought']

        else:

            thought = "Didn't think"

        # Extract tool

        tool = []

        if 'tool' in json_response:

            for field in ['name', 'reason', 'input']:

                if field in json_response['tool']:

                    tool_info = json_response['tool'][field]

                else:

                    tool_info = 'NONE'

                tool.append(tool_info)

        # Extract answer

        if 'answer' in json_response:

            answer = json_response['answer']

        else:

            answer = 'NONE'

        return thought, tool, answer

    ### ------------------------------------ ###

    @torch_no_grad()
    def run_llm(self, prompt: str) -> str:

        llm_output = self.text_generation_model(
            prompt,
            return_full_text=False,
            max_new_tokens=self.max_new_tokens
        )[0]['generated_text']

        self.log_history('unfiltered_agent_output', llm_output)

        parsed_llm_output = self.clean_llm_answer(llm_output)

        self.log_trace(parsed_llm_output)

        thought, tool, answer = self.parse_json_response(parsed_llm_output)

        self.log_history('agent_thinking', thought)

        self.last_thought = thought

        return thought, tool, answer

### ---------------------------------------- ###

def run_query(query: str, config_vars: dict) -> str:

    """
    Sets up the agent, registers tools, and executes a query.

    Parameters
    ----------
    query : str
        The query to execute
    config_vars : dict
        Dictionary of configuration variables

    Returns
    -------
    str
        The Ai agent's final answer
    """

    # Model init

    agent_model = init_text_generation_model

    embedding_model = init_text_embedding_model

    # Agent init

    agent = ai_agent(
        agent_model=agent_model,
        agent_model_checkpoint=config_vars['TEXT_GENERATION_MODEL'],
        embedding_model=embedding_model,
        embedding_model_checkpoint=config_vars['TEXT_EMBEDDING_MODEL'],
        base_prompt_path=config_vars['BASE_PROMPT_PATH'],
        rag_similarity_function=config_vars['RAG_SIMILARITY_FUNCTION'],
        max_rag_hits=config_vars['MAX_RAG_HITS'],
        use_rag=config_vars['USE_RAG'],
        device_map=config_vars['DEVICE_MAP'],
        max_iterations=config_vars['MAX_ITERATIONS'],
        max_new_tokens=config_vars['MAX_NEW_TOKENS'],
        trace_log_dir=config_vars['TRACE_LOG_DIR'],
        history_log_dir=config_vars['HISTORY_LOG_DIR']
    )

    agent.add_tool(pubmed_search)

    agent.add_tool(wikipedia_search)

    # Run query

    answer = agent.get_answer(query)

    return answer

### ---------------------------------------- ###

if __name__ == '__main__':

    config_vars = parse_config()

    query = input('How may I help?\n')

    answer = run_query(query, config_vars)

    print("Here's my answer:")

    print(answer)
