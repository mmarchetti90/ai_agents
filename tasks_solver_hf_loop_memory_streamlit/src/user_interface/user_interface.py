#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import streamlit as st

from gc import collect as gc_collect
from sys import exit as sys_exit
from time import sleep
from typing import Any

### CLASSES -------------------------------- ###

class user_interface:

    """
    Class for managing streamlit UI

    UI Structure
    ------------
    2 columns
      * left_col with 2 text sources
        * User query
        * AI agent trace
      * right_col with 3 tabs
        * 'Agent reply' for agent genereated reply
        * 'Data' for pd.DataFrame
        * 'Plots' for matplotlib plots

    Parameters
    ----------
    agent: Any,
        AI agent instance
    Methods
    -------
    render_ui
        Renders the UI
    terminate
        Terminates the app
    """

    ### ------------------------------------ ###

    def __init__(
            self,
            agent: Any
        ) -> None:
        
        # Init self and session_state vars
        if 'agent' not in st.session_state:
            st.session_state.agent = agent
        if 'new_query' not in st.session_state:
            st.session_state.new_query = ''

    ### ------------------------------------ ###

    def render_ui(self) -> Any:

        """
        Renders the UI
        """
        
        # Run agent
        if st.session_state.new_query in ['quit', 'exit', 'terminate', 'kill']:
            self.terminate()
        else:
            self.run_agent()
        
        # Wide layout
        st.set_page_config(layout="wide")

        # Main layout has 2 columns
        # left_col displays the input query prompt and the log_messages, each in a separate container
        # right_col displays 2 tabs for data and plots
        main_container = st.container(horizontal=True, border=True)
        left_col, right_col = main_container.container(border=True, width=768), main_container.container(border=True)

        # left_col structure
        left_container_sub_1, left_container_sub_2 = left_col.container(border=True), left_col.container(border=True, height=512)

        # Populate left_container_sub_1
        _ = left_container_sub_1.text_input(
            'Input query:',
            placeholder='Type "exit" to terminate session.',
            key='new_query'
        )

        # Reduce padding for trace
        st.html("""
<style>
.stChatMessage {
    padding-top: 0;
    padding-bottom: 0;
}
</style>
""")

        # Populate left_container_sub_2
        for at in st.session_state.agent.agent_trace:
            with left_container_sub_2.chat_message('ai'):
                st.write(at)

        # right_col structure
        text_tab, data_tab, plot_tab = right_col.tabs(['Agent reply', 'Data', 'Plots'])

        # Populate right col
        if st.session_state.agent.last_produced_outputs['str'] is not None:
            text_tab.write(st.session_state.agent.last_produced_outputs['str'])
        if st.session_state.agent.last_produced_outputs['pd.DataFrame'] is not None:
            data_tab.dataframe(st.session_state.agent.last_produced_outputs['pd.DataFrame'], width='content')
        if st.session_state.agent.last_produced_outputs['plot'] is not None:
            plot_tab.pyplot(st.session_state.agent.last_produced_outputs['plot'], width=512)

    ### ------------------------------------ ###

    def run_agent(self) -> None:

        with st.spinner('Processing...', show_time=True):
            _ = st.session_state.agent.process_query(st.session_state.new_query)

    ### ------------------------------------ ###

    def terminate(self) -> None:

        """
        Terminates the app
        """

        st.stop()
        gc_collect()
        sys_exit()
