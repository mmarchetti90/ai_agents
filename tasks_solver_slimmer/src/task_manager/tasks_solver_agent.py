#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import json

from collections.abc import Callable
from datetime import datetime
from gc import collect as gc_collect
from src.models.generation_model import init_text_generation_model
from src.models.embedding_model import init_text_embedding_model
from src.tools import *
from sys import argv

### GLOBAL VARS ---------------------------- ###

CONFIG_FILE = 'config/config.task.solver.json'

### CLASSES AND FUNCTIONS ------------------ ###

def parse_config() -> dict:

    """
    Parsing config file containing global vars
    """

    with open(CONFIG_FILE) as opened_config_file:
    
        config_data = json.load(opened_config_file)

    return config_data

### ---------------------------------------- ###

class Manager:

    """
    Class for AI agent responsible for managing tasks execution
    """

    def __init__(
        self,
        generative_model: Callable,
        generative_model_checkpoint: str,
        embedding_model: Callable,
        embedding_model_checkpoint: str,
        device_map: str='cpu',
        max_new_tokens: int=1024,
        use_rag: bool=True,
        rag_similarity_function: str='cosine',
        max_rag_hits: int=10,
        history_log_dir: str='./'

    ) -> None:

        """
        Initializes the AI Agent

        Parameters
        ----------
        generative_model
            The LLM used to run the text generation tools
        generative_model_checkpoint
            Name or path of the checkpoint for the text generation tools
        embedding_model
            The model to be used for RAG
        embedding_model_checkpoint
            Name or path of the checkpoint for the RAG model
        device_map
            Device to use to run the models
            Default = 'cpu'
        max_new_tokens
            Maximum number of new tokens for the text generation tools
            Default = 1024
        use_rag
            Set to True to use a RAG to filter the info retrieved by function tools
        rag_similarity_function
            Similarity function for the RAG model
            Default = 'cosine'
        max_rag_hits
            Top relevant data hits
            Default = 10
        history_log_dir
            Where to store the history log
            Default = './'
        """

        self.init_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S").replace(' ', '_')

        self.text_generation_model = generative_model(generative_model_checkpoint, device_map)

        self.text_embedding_model = embedding_model(embedding_model_checkpoint, device_map, rag_similarity_function)

        self.max_new_tokens = max_new_tokens

        self.use_rag = use_rag

        self.max_rag_hits = max_rag_hits

        self.history_log_dir = history_log_dir

        self.history_log = self.init_history_log()

        self.tools = {}

        self.tools_description = []

        self.add_tool(self.empty_tool(), is_query_decomposer=True, log=False)

        self.add_tool(self.empty_tool(), is_task_assigner=True, log=False)

        self.add_tool(self.empty_tool(), is_rag=True, log=False)

        self.add_tool(self.empty_tool(), is_summarizer=True, log=False)

        self.final_answer = ''

    ### ------------------------------------ ###
    ### AGENT HISTORY                        ###
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

        if self.current_task not in history.keys():

            history[self.current_task] = {}

        history[self.current_task][action] = content
        
        with open(self.history_log, 'w') as history_out:
    
            json.dump(history, history_out, indent=4)

    ### ------------------------------------ ###

    def log_trace(self, trace_message: str) -> None:

        trace_timestamp = datetime.now().strftime("%H:%M:%S")

        timestamped_trace_message = f"[{trace_timestamp}] {trace_message}"

        print(timestamped_trace_message)

    ### ------------------------------------ ###
    ### QUERY PROCESSING                     ###
    ### ------------------------------------ ###

    def get_answer(self, query: str='', tasks_list: list[str]=[]) -> str:

        """
        Query-processing workflow
        Can either accept a query or a defined list of sequential tasks
        If the former, it will be broken down to a list of sequential tasks

        Parameters
        ----------
        query : str
            The query to be answered
        tasks_list : list[str]
            List of sequential tasks to be executed

        Returns
        -------
        str
            The final answer or last recorded processing message
        """

        self.log_trace(trace_message='Started processing')

        # Check input

        self.current_task = "task_decomposition"

        if not len(tasks_list) and query != '':

            self.log_trace(trace_message=f'Running query decomposition: {query}')

            self.log_history('original_query', query)

            tasks_list = self.decompose_query(query)

            self.log_trace(trace_message='\u2714 Query decomposition complete:')

            for task in tasks_list:

                self.log_trace(trace_message=f'  * {task}')

            self.log_history('proposed_tasks', tasks_list)

        elif len(tasks_list):

            self.log_history('proposed_tasks', tasks_list)

        else:

            return "ERROR: invalid input."

        # Assign tasks

        self.current_task = "task_assignment"

        self.log_trace(trace_message='Assigning tasks to tools')

        assigned_tasks = self.assign_tasks(tasks_list)

        self.log_trace(trace_message='\u2714 Tasks were assigned to tools:')

        for N,(task,tool_call) in enumerate(assigned_tasks):

            self.log_trace(trace_message=f'  * "{task}" assigned to {tool_call["tool"]}')

        self.log_history('assigned_tasks', assigned_tasks)

        # Execute tasks

        self.current_task = "task_execution"

        tasks_outputs = self.run_tasks(assigned_tasks)

        # Summarize tasks output
        
        self.current_task = "summarization"

        self.log_trace(trace_message='Summarizing tasks outputs')

        self.final_answer = self.summarize_tasks_outputs(tasks_outputs, query)

        self.log_trace(trace_message='\u2714 Summary completed')

        print(f'FINAL OUTPUT:\n{self.final_answer}')

        self.log_history('final_answer', self.final_answer)

        return self.final_answer

    ### ------------------------------------ ###
    ### QUERY DECOMPOSITION                  ###
    ### ------------------------------------ ###

    def decompose_query(self, query: str) -> list[str]:

        """
        Decomposing a query into a series of sequential tasks
        """

        tasks_list = []

        while not len(tasks_list):

            try:

                tasks_list = self.query_decomposer.forward(model=self.text_generation_model, query=query, max_new_tokens=self.max_new_tokens)

            except:

                tasks_list = []

        return tasks_list

    ### ------------------------------------ ###
    ### TASKS MANAGEMENT                     ###
    ### ------------------------------------ ###

    def assign_tasks(self, tasks_list: list[str]) -> list[str, dict]:

        """
        Assigning tasks to tools
        """

        tools_description = self.get_tools_description_dict(self.tools)

        tools_description_text = json.dumps(tools_description, indent=2)

        self.log_history('available_tools', tools_description)

        assigned_tasks = []

        while not len(assigned_tasks):

            try:

                assigned_tasks = self.task_assigner.forward(model=self.text_generation_model, tasks=tasks_list, tools_description=tools_description_text, max_new_tokens=self.max_new_tokens)

            except:

                assigned_tasks = []

        return assigned_tasks

    ### ------------------------------------ ###

    def run_tasks(self, assigned_tasks: list[str, dict]) -> list[str]:

        """
        Runs individual tasks with tool calls (functions or llms)
        """

        self.log_trace(trace_message='Running tasks:')

        observations = []

        for N,(task,tool_call) in enumerate(assigned_tasks):

            tool_name, tool_input = tool_call["tool"], tool_call["input"]

            self.log_trace(trace_message=f'  * Running task {N} - "{task}" with tool {tool_name}')

            try:

                if self.tools[tool_name].tool_type == 'function':

                    new_observation = self.tools[tool_name].forward(query=tool_input)

                    if self.use_rag:

                        new_observation = self.rag_filter.forward(model=self.text_embedding_model, query=task, data=new_observation, max_hits=self.max_rag_hits)

                        new_observation = str(new_observation)

                elif self.tools[tool_name].tool_type == 'llm':

                    new_observation = self.tools[tool_name].forward(model=self.text_generation_model, query=tool_input, context=observations[-1], max_new_tokens=self.max_new_tokens)

                else:

                    new_observation = ''

                if new_observation != '':

                    observations.append(new_observation)

                self.log_trace(trace_message=f'    \u2714 Task {N} completed')

                self.log_history(f'tasks_{N}', {'task' : task,
                                                'tool' : tool_name,
                                                'tool_input' : tool_input,
                                                'tool_output' : new_observation})
            except:

                self.log_trace(trace_message=f'    \u2717 Task {N} failed')

                continue

        return observations

    ### ------------------------------------ ###

    def summarize_tasks_outputs(self, tasks_outputs: list[str], context: str='') -> str:

        summary = self.summarizer.forward(model=self.text_generation_model, query="\n\n".join(tasks_outputs), context=context, max_new_tokens=self.max_new_tokens)

        if not len(summary):

            summary = tasks_outputs[-1]

        return summary

    ### ------------------------------------ ###
    ### TOOLS MANAGEMENT                     ###
    ### ------------------------------------ ###

    class empty_tool:

        """
        Mock tool that returns the query when run
        """

        def __init__(self):

            pass

        ### -------------------------------- ###

        def forward(self, query: str, *args, **kwargs) -> str:

            return query

    ### ------------------------------------ ###

    def add_tool(
        self,
        tool_call: Callable,
        is_query_decomposer: bool=False,
        is_task_assigner: bool=False,
        is_rag: bool=False,
        is_summarizer: bool=False,
        log: bool=True
    ) -> None:

        """
        Registers a tool to the agent

        Parameters
        ----------
        tool_call : Callable
            A class with the following attributes: name, description, inputs, output_type
            Must also have the following method: forward (runs the tool) 
        is_query_decomposer : bool
            Set to True to identify the tool for query decomposition
        is_task_assigner : bool
            Set to True to identify the tool for assigning tasks to tools
        is_rag : bool
            Set to True to identify the tool for filtering retrieved info
        is_summarizer : bool
            Set to True to identify the tool for summarizing tasks outputs
        log : bool
            Set to True to log the entry
        """

        if is_query_decomposer:

            self.query_decomposer = tool_call

            if log:

                self.log_trace(trace_message='Added tool: query_decomposer')

        elif is_task_assigner:

            self.task_assigner = tool_call

            if log:

                self.log_trace(trace_message='Added tool: task_assigner')

        elif is_rag:

            self.rag_filter = tool_call

            if log:

                self.log_trace(trace_message='Added tool: rag_filter')

        elif is_summarizer:

            self.summarizer = tool_call

            if log:

                self.log_trace(trace_message='Added tool: summarizer')

        else:

            self.tools[tool_call.name] = tool_call

            if log:

                self.log_trace(trace_message=f'Added tool: {tool_call.name}')

    ### ------------------------------------ ###

    @staticmethod
    def get_tools_description_dict(tools: dict) -> dict[str]:

        """
        Formats the tools information for the prompt

        Returns
        -------
        dict[str]
            Structured tools information
        """

        tools_description = []

        for tool_name,tool in tools.items():

            tool_data = {
                "type": tool.tool_type,
                "name": tool.name,
                "description": tool.description.strip(),
                "parameters": tool.inputs
            }

            tools_description.append(tool_data)

        return tools_description

### ---------------------------------------- ###

def run_query(query: str, tasks_list: list[str], config_vars: dict) -> str:

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

    # Agent init

    agent = Manager(
        generative_model=init_text_generation_model,
        generative_model_checkpoint=config_vars['TEXT_GENERATION_MODEL'],
        embedding_model=init_text_embedding_model,
        embedding_model_checkpoint=config_vars['TEXT_EMBEDDING_MODEL'],
        device_map=config_vars['DEVICE_MAP'],
        max_new_tokens=config_vars['MAX_NEW_TOKENS'],
        use_rag=config_vars['USE_RAG'],
        rag_similarity_function=config_vars['RAG_SIMILARITY_FUNCTION'],
        max_rag_hits=config_vars['MAX_RAG_HITS'],
        history_log_dir=config_vars['HISTORY_LOG_DIR']
    )

    # Add LLM tools

    tool_function = query_decomposition.query_decomposition
    max_tasks = config_vars['MAX_TASKS']
    agent.add_tool(tool_function(max_tasks), is_query_decomposer=True)
    
    tool_function = task_assigner.task_assigner
    agent.add_tool(tool_function(), is_task_assigner=True)

    tool_function = rag_filter.rag_filter
    agent.add_tool(tool_function(), is_rag=True)
    
    tool_function = data_summarizer.data_summarizer
    agent.add_tool(tool_function(), is_summarizer=True)
    
    tool_function = code_writer.code_writer
    agent.add_tool(tool_function())

    tool_function = creative_writer.creative_writer
    agent.add_tool(tool_function())

    # Add function tools

    tool_function = pubmed_search.pubmed_search
    agent.add_tool(tool_function())

    tool_function = wikipedia_search.wikipedia_search
    agent.add_tool(tool_function())

    # Run query

    answer = agent.get_answer(query, tasks_list)

    # Garbage collection

    del agent
    gc_collect()

    return answer

### ---------------------------------------- ###

if __name__ == '__main__':

    config_vars = parse_config()

    if '--query' in argv:

        query = argv[argv.index('--query') + 1]

        tasks_list = []

    elif '--tasks' in argv:

        query = ''

        tasks_list = [t for t in open(argv[argv.index('--tasks') + 1], 'r').read().split('\n') if len(t)]

    else:

        query = input('How may I help?\n')

        tasks_list = []

    answer = run_query(query, tasks_list, config_vars)
