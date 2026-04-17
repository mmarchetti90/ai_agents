#!/usr/bin/env python3

"""
Unit test for the user_interface class
Run as "python -m streamlit run unit_tests/interface_test.py" from package root to avoid relative import issues
"""

### IMPORTS -------------------------------- ###

import pandas as pd
import seaborn as sns

from datetime import datetime
from matplotlib import pyplot as plt
from src.user_interface.user_interface import user_interface
from time import sleep
from typing import Any

### CLASSES -------------------------------- ###

class fake_agent:

    def __init__(self):

        self.agent_trace = []
        self.iteration_count = 0
        self.last_produced_outputs = {
            'str' : '',
            'pd.DataFrame' : None,
            'plot' : None
        }
        self.code_execution_warning = False
        self.code_execution_ok_to_proceed = False
        self.log_trace(trace_message='Agent initialized.')

    ### ------------------------------------ ###

    def log_trace(self, trace_message: str) -> Any:

        trace_timestamp = datetime.now().strftime("%H:%M:%S")
        timestamped_trace_message = f"[{trace_timestamp}] {trace_message}"
        self.agent_trace.append(timestamped_trace_message)
    
    ### ------------------------------------ ###

    def process_query(self, query: str='') -> Any:

        sleep(3) # Giving time to the spinner
        if not len(query):
            return ''

        # Init final_output
        self.final_output = None

        # Log processing start
        self.log_trace(trace_message=f'Started processing query: {query}')

        # Init new iteration
        self.iteration_count += 1
        suffix = (
            'st' if str(self.iteration_count).endswith('1') else
            'nd' if str(self.iteration_count).endswith('2') else
            'rd' if str(self.iteration_count).endswith('3') else
            'th'
        )
        self.log_trace(trace_message=f"I'm thinking... for the {self.iteration_count}{suffix} time!")
        sleep(0.05)

        # Generating text
        text = f'Text output {self.iteration_count}'
        self.last_produced_outputs['str'] = text

        # Generating a dataframe every other loop
        if self.iteration_count % 2 == 0:
            self.log_trace(trace_message="Loading data")
            df = self.init_dataframe()
            self.last_produced_outputs['pd.DataFrame'] = df
            sleep(0.05)
        else:
            df = None
            self.last_produced_outputs['pd.DataFrame'] = df
        
        # Generating a plot every other time the dataframe is generated
        if self.iteration_count % 4 == 0 and df is not None:
            self.log_trace(trace_message="Plotting data")
            fig = self.init_fig(df, 'x', 'y')
            self.last_produced_outputs['plot'] = fig
            sleep(0.05)
        else:
            fig = None
            self.last_produced_outputs['plot'] = fig
        
        # Generating a final output
        sleep(0.05)
        final_output = 'Done thinking'

        # Store final_output
        self.final_output = final_output

        return final_output

    ### ------------------------------------ ###

    @staticmethod
    def init_logs() -> list[str]:

        log = [
            "I'm thinking...",
            "Thinking some more",
            "And more",
            "I have a headache now..."
        ]

        return log

    ### ----------------------------------- ###

    @staticmethod
    def init_dataframe(n: int=20) -> pd.DataFrame:

        df = pd.DataFrame({
            'x' : list(range(n)),
            'y' : [x**2 for x in range(n)]
        })

        return df

    ### ----------------------------------- ###

    @staticmethod
    def init_fig(df: pd.DataFrame, varx: str, vary: str) -> Any:

        fig, ax = plt.subplots()
        sns.scatterplot(df, x=varx, y=vary, ax=ax)

        return fig

### MAIN ---------------------------------- ###

if __name__ == '__main__':

    # Init fake agent
    fake_agent_instance = fake_agent()

    # Init UI instance
    ui_instance = user_interface(
        agent=fake_agent_instance
	)
    
    # Starting interface
    ui_instance.render_ui()
