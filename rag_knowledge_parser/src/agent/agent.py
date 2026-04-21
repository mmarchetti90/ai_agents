#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

from datetime import datetime
from ollama import chat as OllamaChat
from ollama import ChatResponse
from src.knowledge_handler.knowledge_handler import KnowledgeHandler

### CLASSES AND FUNCTIONS ------------------ ###

class SavvyAgent:

    """
    Class for managing the agent loop

    Parameters
    ----------
    config : dict
        Configuration dictionary containing all necessary parameters
    
    Methods
    -------
    forward(self, query: str) -> str
        Query processing workflow
    """

    ### ------------------------------------ ###

    def __init__(self, config: dict) -> None:

        # Init trace log
        self.agent_trace = []
        self.log_trace(trace_message='Initializing agent')

        # Init LLM
        self.model_checkpoint = config['llm']['checkpoint']
        self.think_mode = config['llm']['think_mode']
        self.context_window = config['llm']['context_window']
        self.max_new_tokens = config['llm']['max_new_tokens']
        self.log_trace(trace_message='Added LLM params')
        
        # Init agent knowledge
        self.knowledge = KnowledgeHandler(
            config['knowledge']['knowledge_dir'],
            config['knowledge']['checkpoint']
        )
        self.max_retrieved_info = config['knowledge']['max_retrieved_info']
        self.knowledge_score_threshold = config['knowledge']['score_threshold']
        self.log_trace(trace_message='Added knowledge base')
        for ku in self.knowledge.updates:
            self.log_trace(trace_message=f'  * {ku}')

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
          * Relevant knowledge
          * User query
        
        Parameters
        ----------
        query: str
            The user query
        """

        agent_instructions = """
You are an expert at answering questions based on provided knowledge.
You will be given a question by the user. Follow these instructions to answer it:
* Analyze the question and think about what kind of information is needed to answer it.
* Check your knowledge base for relevant information.
* Always base your answer on the provided knowledge and your own reasoning.
"""

        # Init chat messages
        self.chat = [
            {'role' : 'system', 'content' : agent_instructions}
        ]

        # Get data from knowledge base
        useful_data = self.knowledge.retrieve_data(
            context=[query],
            max_hits=self.max_retrieved_info,
            score_threshold=self.knowledge_score_threshold
        )
        useful_data = '\n'.join(useful_data)

        # Add data to chat
        useful_data = {'role' : 'system', 'content' : f'This is a compendium of useful data to answer the question:\n{useful_data}'}
        self.chat.append(useful_data)

        # Add user query
        self.chat.append({'role' : 'user', 'content' : query})
    
    ### ------------------------------------ ###
    ### QUESTION ANSWERING                   ###
    ### ------------------------------------ ###

    def forward(self, query: str) -> str:

        """
        Query-processing workflow

        Parameters
        ----------
        query : str
            The query to be answered

        Returns
        -------
        str
            The answer to the query
        """
        
        # Process query
        if not len(query) or not isinstance(query, str):
            return "Sorry, I didn't understand your question."
        else:
            self.init_chat(query)
            agent_response = self.llm_inference(chat=self.chat, tools=[],
                model_checkpoint=self.model_checkpoint,
                think_mode=self.think_mode,
                context_window=self.context_window,
                max_new_tokens=self.max_new_tokens
            )
            return agent_response

    ### ------------------------------------ ###
    ### LLM INFERENCE                        ###
    ### ------------------------------------ ###

    @staticmethod
    def llm_inference(chat: list[dict], tools: list[dict]=[], model_checkpoint: str='Qwen3.5:4b', think_mode: bool=True, context_window: int=2048, max_new_tokens: int=512) -> str:

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

        # Check for explicit think toggle
        if '/no_think' in chat[-1]['content']:
            chat[-1]['content'] = chat[-1]['content'].replace('/no_think', '').strip()
            think_mode = False
        elif '/think' in chat[-1]['content']:
            chat[-1]['content'] = chat[-1]['content'].replace('/think', '').strip()
            think_mode = True
        else:
            pass

        # Inference
        response: ChatResponse = OllamaChat(
            model=model_checkpoint,
            messages=chat,
            tools=tools,
            think=think_mode,
            options={
                'num_ctx': context_window,
                'num_predict': max_new_tokens
            }
        )

        # Clean output
        llm_output = response.message.content or response.message.thinking
        llm_output = llm_output if isinstance(llm_output, str) else 'Sorry, something went wrong.'

        return llm_output
