#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

from datetime import datetime
from ollama import chat as OllamaChat
from ollama import ChatResponse
from src.memory_handler.memory_handler import MemoryHandler
from src.skills_manager.skills_manager import SkillsManager

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
        self.llm_call = lambda chat, tools, think: self.llm_inference(
            chat=chat,
            tools=tools,
            model_checkpoint=config['model']['checkpoint'],
            think_mode=think,
            context_window=config['model']['context_window'],
            max_new_tokens=config['model']['max_new_tokens']
        )
        self.think_mode = config['model']['think_mode']
        self.log_trace(trace_message='Added LLM engine')

        # Init skills manager
        self.skills_manager = SkillsManager(config['skills']['skills_dir'])
        self.log_trace(trace_message='Added skills')
        
        # Init agent memory
        self.memory = MemoryHandler(
            config['memory']['memory_path'],
            config['memory']['checkpoint']
        )
        self.memory_score_threshold = config['memory']['score_threshold']
        self.log_trace(trace_message='Added memory')

    ### ------------------------------------ ###
    ### LLM MODEL                            ###
    ### ------------------------------------ ###

    @staticmethod
    def llm_inference(chat: list[dict], tools: list[dict]=[], model_checkpoint: str='Qwen3.5:4b', think_mode: bool=True, context_window: int=2048, max_new_tokens: int=512) -> ChatResponse:

        """
        Runs LLM inference

        Parameters
        ----------
        model_checkpoint: str
            Checkpoint to use
        think_mode: str='auto'
            Toggle for thinking mode
        max_new_tokens: int=2048
            Max new tokens to generate
        
        Returns
        -------
        ChatResponse
            Ollama ChatResponse object
        """

        response: ChatResponse = OllamaChat(
            model=model_checkpoint,
            messages=chat,
            tools=tools,
            think=think_mode,
            options={
                'num_ctx': 4096,
                'num_predict': max_new_tokens
            }
        )

        return response

    ### ------------------------------------ ###

    @staticmethod
    def clean_llm_response(response: ChatResponse) -> dict:

        """
        Parses a ChatResponse object and extract response and tools
        """

        try:
            action = {
                "thought" : response.message.content or response.message.thinking,
                "skill_name" : response.message.tool_calls[0].function.name.replace('_', '-') if response.message.tool_calls is not None else None,
                "skill_params" : response.message.tool_calls[0].function.arguments if response.message.tool_calls is not None else None
            }
            return action, True
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

        agent_instructions = """
You are an expert AI coding assistant
You will be given a task by the user. Follow these instructions to complete the task:
* Analyze the task and plan your next action carefully.
* If you completed the task, call the task_completed tool.
* Always choose the correct tool for the current task.

When deciding your next action, do the following:
* Think about the task and the step you took to complete it.
* Observe the results of your previous actions and consider their outcome.
* If you remeber already completing the same task in the past, report the past outcome.
* Decide on the next action, either use a tool or ask for more information.
"""

        # Init chat messages
        self.chat_history = [
            {'role' : 'system', 'content' : agent_instructions}
        ]

        # Get recent messages from this query session (short-term memory)
        recent_memories = [c['content'] for c in self.chat_history if c['role'] not in ['system', 'user']][-self.max_messages_in_memory:]

        # Get messages from previous sessions (long-term memory)
        # N.B. have to be filtered to remove recent_memories duplicates
        far_memories = self.memory.retrieve_memory(
            context=query,
            max_hits=self.max_messages_in_memory,
            score_threshold=self.memory_score_threshold
        )
        far_memories = [m for m in far_memories if m not in recent_memories]

        # Add memories to chat, specifying them as memories
        memories = [{'role' : 'assistant', 'content' : f'This is a memory of something I did in the past:\n{m}'} for m in recent_memories + far_memories]
        self.chat_history += memories

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
            out_of_iterations_message = "Agent iterations limit reached. Terminating."
            self.query_answer = out_of_iterations_message
            self.chat_history.append({'role' : 'assistant', 'content' : out_of_iterations_message})
            self.memory.log_memory(origin='assistant', content=self.chat_history[-1]['content'])
        else:
            agent_response = self.llm_call(chat=self.chat_history, tools=self.skills_manager.get_skills_calls(), think=self.think_mode)
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
            # Error, retrying
            self.log_trace(trace_message='I encountered an error. Retrying.')
            self.think()
        elif action['skill_name'] is None or action['skill_name'] == 'task-completed':
            # No skill selected, asking for more info or task is done
            self.query_answer = action['thought']
            try:
                self.query_answer += "\n" + action['skill_params']['completion_message']
                self.query_answer += "\n" + action['skill_params']['task_output']
            except:
                pass
            if self.query_answer:
                self.chat_history.append({'role' : 'assistant', 'content' : self.query_answer})
                self.memory.log_memory(origin='assistant', content=self.chat_history[-1]['content'])
            else:
                self.query_answer = 'Task completed.'
        elif action['skill_name'] not in self.skills_manager.skills.keys():
            # Skill invalid, retrying
            self.log_trace(trace_message=f'Skill "{action["skill_name"]}" not valid. Skipping.')
            self.think()
        else:
            # Skill valid, executing
            self.memory.log_memory(origin='assistant', content=action['thought'])
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
            chat_context=[c for c in self.chat_history if c['role'] in ['user', 'assistant']],
            **action['skill_params']
        )
        
        # Log the skill execution
        for log in skill_execution_log:
            self.log_trace(trace_message=log)

        # Log the action execution in chat and memory
        if skill_exec_status:
            # Update chat and memory
            self.chat_history.append({'role' : 'assistant', 'content' : f'I used the skill "{action["skill_name"]}".'})
            self.memory.log_memory(origin='assistant', content=self.chat_history[-1]['content'])
            self.chat_history.append({'role' : 'assistant', 'content' : skill_execution_log[-1]})
            self.memory.log_memory(origin='assistant', content=self.chat_history[-1]['content'])
        else:
            # Update chat and memory
            self.chat_history.append({'role' : 'assistant', 'content' : f"I couldn't use the skill, here's the execution log:\n{''.join(skill_execution_log)}"})
            self.memory.log_memory(origin='assistant', content=self.chat_history[-1]['content'])
        
        # Next think cycle
        self.think()
