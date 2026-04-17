#!/usr/bin/env python3

"""
UI Structure
------------
2 columns
  * left_col with 2 text sources
    * User query
    * AI agent trace
  * right_col with 3 tabs
    * 'Summary' for agent genereated summary
    * 'Clustering stats' for a plot of clustering quality
    * 'Clusters' for a graphical visualization of clusters if text were compressed to 1 page
"""

### IMPORTS -------------------------------- ###

import json
import streamlit as st

from src.models.llm import llm
from src.models.embedder import embedder
from src.pipeline.pipeline import pipeline
from typing import Any

### GLOBAL VARS ---------------------------- ###

CONFIG_FILE = 'config/config.json'

### FUNCTIONS ------------------------------ ###

def parse_config() -> dict:

    """
    Parsing config file containing global vars
    """

    with open(CONFIG_FILE) as opened_config_file:
        config_data = json.load(opened_config_file)

    return config_data

### --------------------------------------- ###

@st.cache_resource
def load_pipeline(config_data: dict) -> Any:

    # Init models
    llm_instance = llm(
        model_checkpoint=config_data['TEXT_GENERATION_MODEL'],
        device_map=config_data['DEVICE_MAP']
    )
    embedder_instance = embedder(
        model_checkpoint=config_data['TEXT_EMBEDDING_MODEL'],
        device_map=config_data['DEVICE_MAP'],
        similarity_fn_name=config_data['RAG_SIMILARITY_FUNCTION']
    )

    # Init LLM agent
    pipeline_instance = pipeline(
        config=config_data,
        llm=llm_instance,
        text_embedder=embedder_instance
    )

    return pipeline_instance

### ---------------------------------------- ###

def run_agent(agent: Any) -> None:

    """
    Runs the agent and updates the session state
    """

    with st.spinner('Processing...', show_time=True):
        _ = agent.process_query(st.session_state.new_query)
        st.session_state.agent_trace = agent.agent_trace
        st.session_state.summary_report = agent.output['summary_report']
        st.session_state.clustering_stats_plot = agent.output['clustering_stats_plot']
        st.session_state.clusters_plot = agent.output['clusters_plot']

### ---------------------------------------- ###

def terminate() -> None:

    """
    Terminates the app
    """

    st.stop()
    gc_collect()
    sys_exit()

### MAIN ---------------------------------- ###

if __name__ == '__main__':

    # Parse config file
    config_data = parse_config()

    # Init pipeline
    pipeline_instance = load_pipeline(config_data)

    # Init session_state vars
    if 'new_query' not in st.session_state:
        st.session_state.new_query = ''
    if 'agent_trace' not in st.session_state:
        st.session_state.agent_trace = pipeline_instance.agent_trace
    if 'summary_report' not in st.session_state:
        st.session_state.summary_report = ''
    if 'clustering_stats_plot' not in st.session_state:
        st.session_state.clustering_stats_plot = None
    if 'clusters_plot' not in st.session_state:
        st.session_state.clusters_plot = None
    
    # Run agent
    if st.session_state.new_query in ['quit', 'exit', 'terminate', 'kill']:
        terminate()
    else:
        try:
            run_agent(agent=pipeline_instance)
        except Exception as error:
            st.session_state.summary_report = f'ERROR:\n{error}'
        
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
        'Paste text or path to document:',
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
    for at in st.session_state.agent_trace:
        with left_container_sub_2.chat_message('ai'):
            st.text(at)

    # right_col structure
    text_tab, plot_1_tab, plot_2_tab = right_col.tabs(['Summary', 'Clustering stats', 'Clusters'])

    # Populate right col
    if st.session_state.summary_report != '':
        text_tab.markdown(st.session_state.summary_report)
    if st.session_state.clustering_stats_plot is not None:
        plot_1_tab.pyplot(st.session_state.clustering_stats_plot, width=512)
    if st.session_state.clusters_plot is not None:
        plot_2_tab.pyplot(st.session_state.clusters_plot, width=512)
