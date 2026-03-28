#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import json

from collections.abc import Callable
from datetime import datetime
from typing import Any

### CLASSES -------------------------------- ###

class orchestrator:

    """
    Class for generating pipelines to complete tasks

    Parameters
    ----------
    config: dict
        Dictionary of configuration parameters
    llm: Callable
        llm class instance for running prompts
    memory: Callable
        memory_handler class instance
    """

    ### ------------------------------------ ###

    def __init__(
        self,
        config: dict,
        llm: Any,
        memory: Any
    ) -> None:

        """
        Initializes the AI Agent

        Parameters
        ----------
        config: dict
            Dictionary of configuration parameters
        llm: Callable
            llm class instance for running prompts
        memory: Callable
            memory_handler class instance
        """

        # Init
        self.interaction_counter = 0
        self.llm = llm
        self.memory = memory
        self.max_memory_size = config['MAX_MEMORY_SIZE']
        self.max_new_tokens = config['MAX_NEW_TOKENS']
        self.max_tool_retries = config['MAX_TOOL_RETRIES']

        # Init trace
        self.agent_trace = []
        self.log_trace(trace_message='Agent initialized')

        # Init storage for last produced outputs
        self.last_produced_outputs = {
            'str' : '',
            'dict' : {},
            'sqlite3.Connection' : None,
            'pd.DataFrame' : None,
            'plot' : None
        }

        # Trim memory
        self.memory.trim_memory(self.max_memory_size)

        # Adding LLM-based tools (innate functionalities)
        self.tools = {}
        for prompt_path in config['PROMPTS']:
            new_tool = self.llm_tool(prompt_path)
            self.add_tool(
                tool_call=new_tool,
                is_query_decomposer=(new_tool.name == 'query_decomposition'),
                is_task_assigner=(new_tool.name == 'task_assigner'),
                log=False
            )

        # Adding memory-based tool
        self.add_tool(
            tool_call=self.memory_search(self.memory, config['MAX_RAG_HITS'], config['RAG_SIMILARITY_THRESHOLD']),
            is_query_decomposer=False,
            is_task_assigner=False,
            log=False
        )

    ### ------------------------------------ ###
    ### AGENT HISTORY                        ###
    ### ------------------------------------ ###

    def log_trace(self, trace_message: str) -> None:

        trace_timestamp = datetime.now().strftime("%H:%M:%S")
        timestamped_trace_message = f"[{trace_timestamp}] {trace_message}"
        print(timestamped_trace_message)
        self.agent_trace.append(timestamped_trace_message.replace('\n', '  \n')) # So the newline will be recognized by st.chat_message

    ### ------------------------------------ ###
    ### TOOLS MANAGEMENT                     ###
    ### ------------------------------------ ###

    class empty_tool:

        """
        Mock tool that returns the query when run
        """

        ### -------------------------------- ###

        def __init__(self):

            pass

        ### -------------------------------- ###

        def forward(self, query: str, *args, **kwargs) -> str:

            return query

    ### ------------------------------------ ###

    class llm_tool:

        """
        Class for initializing LLM-based tools

        Parameters
        ----------
        prompt_path : str
            Path to markdown file describing the tool
        """

        ### -------------------------------- ###

        def __init__(self, prompt_path: str) -> None:

            raw = {
                entry.split('\n')[0].strip() : entry[entry.index('\n'):].replace('```', '').strip()
                for entry in open(prompt_path, 'r').read().strip().split('###')
                if len(entry)
            }
            self.tool_type = 'llm'
            self.name = raw['name']
            self.description = raw['description']
            self.inputs = json.loads(raw['expected_inputs'])
            self.prompt = raw['prompt']
            self.output_type = raw['output_type']

        ### -------------------------------- ###

        def forward(self, llm_engine: Callable[..., Any], query: str, context: str='', tools: str='', max_new_tokens: int=512) -> str:

            # Update prompt
            updated_prompt = self.prompt.replace('[QUERY]', query)
            if context != '':
                updated_prompt = updated_prompt.replace('[CONTEXT]', f"Here's some useful info: {context}")
            else:
                updated_prompt = updated_prompt.replace('[CONTEXT]', '')
            if tools != '':
                updated_prompt = updated_prompt.replace('[TOOLS]', tools)
            else:
                updated_prompt = updated_prompt.replace('[TOOLS]', '')

            # Run LLM
            parsed_llm_output = llm_engine.forward(prompt=updated_prompt, max_new_tokens=max_new_tokens)

            return parsed_llm_output

    ### ------------------------------------ ###

    class memory_search:

        """
        Class for initializing memory searches

        Parameters
        ----------
        memory: Callable
            memory_handler instance
        max_hits: int=5
            Maximum number of memories to return
        score_threshold: float=0.75
            Similarity threshold between context and memories
        """

        tool_type = 'function'
        name = 'memory_search'
        description = """
        This is a tool to retrieve memories relevant to a query
        """
        inputs = inputs = {
            'query': {
                'type': 'str',
                'description': 'Keywords to direct the memory search, comma-separated'
            }
        }
        output_type = 'str'

        ### -------------------------------- ###

        def __init__(self, memory: Any, max_hits: int=5, score_threshold: float=0.75) -> None:

            self.memory = memory
            self.max_hits = max_hits
            self.score_threshold = score_threshold

        ### -------------------------------- ###

        def forward(self, query: str) -> str:

            local_threshold = self.score_threshold
            while True:
                retrieved_memories = self.memory.retrieve_memory([query], self.max_hits, local_threshold)
                if len(retrieved_memories) > 0:
                    break
                else:
                    # Lowering the threshold and trying again
                    retrieved_memories = 'No relevant memories were found.'
                    local_threshold = local_threshold * 0.9
                    if local_threshold < 0.125:
                        break
            retrieved_memories = '\n'.join(retrieved_memories)

            return retrieved_memories

    ### ------------------------------------ ###

    def add_tool(
        self,
        tool_call: Any,
        is_query_decomposer: bool=False,
        is_task_assigner: bool=False,
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
            N.B. Tool is not added to the common pool
        is_task_assigner : bool
            Set to True to identify the tool for assigning tasks to tools
            N.B. Tool is not added to the common pool
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
        else:
            self.tools[tool_call.name] = tool_call
            if log:
                self.log_trace(trace_message=f'Added tool: {tool_call.name}')

    ### ------------------------------------ ###

    @staticmethod
    def get_tools_description_dict(tools: dict) -> list[dict]:

        """
        Formats the tools information for task_assigner prompt

        Returns
        -------
        dict[str]
            Structured tools information
        """

        tools_description = []
        for tool in tools.values():
            tool_data = {
                "type": tool.tool_type,
                "name": tool.name,
                "description": tool.description.strip(),
                "parameters": tool.inputs
            }
            tools_description.append(tool_data)
        return tools_description

    ### ------------------------------------ ###
    ### QUERY PROCESSING                     ###
    ### ------------------------------------ ###

    def process_query(self, query: str='') -> Any:

        """
        Query-processing workflow

        Parameters
        ----------
        query : str
            The query to be answered

        Returns
        -------
        str
            The answer to the query answer
        """

        # Return an empty string if the input is an empty string
        if not len(query):
            return ''

        # Add query to memory
        self.memory.log_memory(origin='user', content=query)

        # Analyze user query and decompose task into subtasks
        self.log_trace(trace_message='Started processing query')
        if query != '':
            self.log_trace(trace_message=f'Running query decomposition: {query}')
            tasks_list = self.decompose_query(query)
            tasks_list = self.check_tasks_list(tasks_list) # Quality check and rearrangement of tasks_list
            self.log_trace(trace_message='\u2714 Query decomposition complete:')
            for task in tasks_list:
                task_trace = f'  * {task["task_id"]} - {task["description"]}\n{" "*15}Dependent on tasks: {task["dependencies"]}'
                self.log_trace(trace_message=task_trace)
        else:
            return "ERROR: invalid input."

        # Assign tasks
        self.log_trace(trace_message='Assigning tasks to tools')
        assigned_tools = self.assign_tools(tasks_list)
        self.log_trace(trace_message='\u2714 Tasks were assigned to tools:')
        for task,tool_call in zip(tasks_list, assigned_tools):
            tool_trace = f'  * Task {task["task_id"]} assigned to tool "{tool_call["tool"]}"\n{" "*15}Reason: {tool_call["reason"]}'
            self.log_trace(trace_message=tool_trace)

        # Execute tasks
        tasks_outputs = self.run_tasks(tasks_list, assigned_tools)
        final_output = tasks_outputs[-1]

        # Add output to memory
        if type(final_output) == str:
            #self.memory.log_memory(origin='ai', content=final_output)
            # No need, the output would have already been added during self.run_tasks
            pass
        else:
            self.memory.log_memory(origin='ai', content=f'Returned {type(final_output)} object')

        # Update interaction_counter
        self.interaction_counter += 1

        # Check if memory needs a trim every 10 interactions
        if self.interaction_counter % 10 == 0:
            self.memory.trim_memory(self.max_memory_size)

        return final_output

    ### ------------------------------------ ###
    ### QUERY DECOMPOSITION                  ###
    ### ------------------------------------ ###

    def decompose_query(self, query: str) -> list[dict]:

        """
        Decomposing a query into a series of sequential tasks
        """

        tasks_list = []
        while not len(tasks_list):
            try:
                tasks_list = self.query_decomposer.forward(
                    llm_engine=self.llm,
                    query=query,
                    max_new_tokens=self.max_new_tokens
                )
                # Convert to dict
                try:
                    tasks_list = json.loads(tasks_list)
                    # Discard if required fields are missing
                    if any([field not in task.keys() for task in tasks_list for field in ['task_id', 'description', 'dependencies']]):
                        tasks_list = [] 
                except: 
                    tasks_list = []
            except:
                tasks_list = []
                self.log_trace(trace_message='Task failed...retrying')
        
        return tasks_list

    ### ------------------------------------ ###

    def check_tasks_list(self, tasks_list: list[dict]) -> list[dict]:

        """
        Deals with duplicate tasks ids and re-orders the list if there's dependencies issues
        """

        # Make sure task ids are unique
        tasks_ids = [task['task_id'] for task in tasks_list]
        not_unique = [tid for tid in set(tasks_ids) if tasks_ids.count(tid) > 1]
        if len(not_unique):
            for nu in not_unique:
                first_occurence_idx = tasks_ids.index(nu)
                while tasks_ids.count(nu) > 1:
                    duplicate_occurence_idx = tasks_ids[first_occurence_idx + 1:].index(nu) + first_occurence_idx + 1
                    new_idx = len(tasks_ids)
                    while str(new_idx) in tasks_ids:
                        new_idx += 1
                    new_idx = str(new_idx)
                    tasks_ids[duplicate_occurence_idx] = new_idx
        
        # Clean dependencies
        tasks_ids = [task['task_id'] for task in tasks_list]
        for N,task in enumerate(tasks_list):
            task_id = task['task_id']
            dependencies = [d.replace('task_id', '').replace(':', '').strip() for d in task['dependencies'] if d in tasks_ids and d != task_id]
            tasks_list[N]['dependencies'] = dependencies

        # Re-order to fix dependencies issues
        tasks_ids = [task['task_id'] for task in tasks_list]
        hierarchy = {}
        current_rank = -1
        while len(hierarchy) < len(tasks_list):
            for task in tasks_list:
                task_id = task['task_id']
                if task_id in hierarchy.keys():
                    continue
                dependencies = [d.replace('task_id', '').replace(':', '').strip() for d in task['dependencies']]
                if all([d in hierarchy.keys() for d in dependencies]):
                    current_rank += 1
                    hierarchy[task_id] = current_rank
                else:
                    continue
        reordered_tasks_list = [{} for _ in range(len(tasks_list))]
        for task in tasks_list:
            rank = hierarchy[task['task_id']]
            reordered_tasks_list[rank] = task

        return reordered_tasks_list

    ### ------------------------------------ ###
    ### TASKS MANAGEMENT                     ###
    ### ------------------------------------ ###

    def assign_tools(self, tasks_list: list[dict]) -> list[dict]:

        """
        Assigning tasks to tools
        """

        tools_description = self.get_tools_description_dict(self.tools)
        tools_description_text = json.dumps(tools_description, indent=2)
        assigned_tools = []
        while not len(assigned_tools):
            try:
                task_n = 0
                while len(assigned_tools) < len(tasks_list):

                    # Assign tool
                    query = tasks_list[task_n]['description']
                    new_assignment = self.task_assigner.forward(
                        llm_engine=self.llm,
                        query=query,
                        tools=tools_description_text,
                        max_new_tokens=self.max_new_tokens
                    )

                    # Convert to dict
                    try:
                        tool_info = json.loads(new_assignment)
                    except:
                        tool_info = json.loads("{'tool': 'none', 'reason': '', 'input': ''}")

                    # Check that tool call has required keys
                    if any(field not in tool_info.keys() for field in ["tool", "reason", "input"]):
                        continue

                    # Making sure a valid tool was chosen
                    if f'"name": "{tool_info["tool"]}"' in tools_description_text:
                        assigned_tools.append(tool_info)
                        task_n += 1
                    else:
                        continue
            except:
                assigned_tools = []
                self.log_trace(trace_message='Task failed...retrying')

        return assigned_tools

    ### ------------------------------------ ###

    def run_tasks(self, tasks_list: list[dict], assigned_tools: list[dict]) -> list[Any]:

        """
        Runs individual tasks with tool calls (functions or llms)
        """
        
        # Dict to convert data types shorthand to what you'd get from "type" command
        # Since input types are just descriptions, I can't use isinstance(<actual_output_type>, <input_type>)
        type_name_to_class_str = {
            'str' : "<class 'str'>",
            'dict' : "<class 'dict'>",
            'sqlite3.Connection' : "<class 'sqlite3.Connection'>",
            'pd.DataFrame' : "<class 'pandas.core.frame.DataFrame'>",
            'plot' : "<class 'matplotlib.figure.Figure'>"
        }

        # Running tasks
        self.log_trace(trace_message='Running tasks:')
        tasks_ids = [task['task_id'] for task in tasks_list]
        outputs = []
        for N,(task,tool_call) in enumerate(zip(tasks_list, assigned_tools)):

            # Extract task info
            task_id = task['task_id']
            tool_name = tool_call["tool"]
            self.log_trace(trace_message=f'  * Running task {N} - "{task["description"]}" with tool "{tool_name}"')

            # Check task dependencies
            dependencies = task['dependencies']
            if not len(outputs):
                # No previous outputs that can be used as inputs
                tool_input = tool_call["input"]
                context = ''
            elif not len(dependencies):
                # No dependencies, so the defined input will be used
                tool_input = tool_call["input"]
                context = (outputs[-1] if type(outputs[-1]) == str else '')
            else:
                # There are dependencies, so the output from a tool of the highest rank will be used as input (or context for llm tools)
                # N.B. Only outputs matching the input type will be considered
                expected_input_type = type_name_to_class_str[self.tools[tool_name].inputs['query']['type']]
                good_previous_outputs = []
                for d in dependencies:
                    d_output_type = str(type(outputs[tasks_ids.index(d)]))
                    if d_output_type == expected_input_type:
                        good_previous_outputs.append(d)
                if not len(good_previous_outputs):
                    # No matching outputs, so the defined input will be used
                    tool_input = tool_call["input"]
                    context = (outputs[-1] if type(outputs[-1]) == str else '')
                else:
                    # At least one dependency's output matches the current task's input type
                    if self.tools[tool_name].tool_type == 'function':
                        tool_input = outputs[tasks_ids.index(good_previous_outputs[-1])]
                    else:
                        tool_input = tool_call["input"]
                        context = outputs[tasks_ids.index(good_previous_outputs[-1])]

            # Run tool
            try_counter = 0
            while True:
                try:
                    if self.tools[tool_name].tool_type == 'function':
                        new_output = self.tools[tool_name].forward(query=tool_input)
                        new_output_type = self.tools[tool_name].output_type
                    elif self.tools[tool_name].tool_type == 'llm':
                        new_output = self.tools[tool_name].forward(llm_engine=self.llm, query=str(tool_input), context=context, max_new_tokens=self.max_new_tokens)
                        new_output_type = 'str'
                    else:
                        new_output = None
                        new_output_type = None
                    outputs.append(new_output)
                    if new_output_type in self.last_produced_outputs.keys():
                        self.last_produced_outputs[new_output_type] = new_output # pyright: ignore[reportArgumentType]
                    self.log_trace(trace_message=f'    \u2714 Task {N} completed')
                    break
                except:
                    try_counter += 1
                    if try_counter < self.max_tool_retries:
                        self.log_trace(trace_message=f'    \u2717 Task {N} failed, execution is retried.')
                    else:
                        self.log_trace(trace_message=f'    \u2717 Task {N} failed.')
                        outputs.append(None)
                        break

            # Add output to memory
            output_to_remember = outputs[-1]
            if tool_name == 'memory_search':
                continue
            elif isinstance(output_to_remember, str):
                self.memory.log_memory(origin='ai', content=output_to_remember)
            elif not isinstance(output_to_remember, type(None)):
                self.memory.log_memory(origin='ai', content=f'Returned {type(output_to_remember)} object')
            else:
                continue

        return outputs
