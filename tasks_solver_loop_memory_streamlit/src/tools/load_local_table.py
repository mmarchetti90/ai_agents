#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import pandas as pd

### CLASSES AND FUNCTIONS ------------------ ###

class load_local_table:
    
    """
    Load local table
    """
    
    # Variables for guiding LMM choice
    tool_type = "function"
    name = 'load_local_table'
    description = """
    This is a tool that loads local table with pandas
    """
    inputs = {
        'query': {
            'type': 'str',
            'description': 'Path to the data'
        }
    }
    output_type = 'pd.DataFrame'
    
    ### ------------------------------------ ###
    
    def __init__(self):
        
        self.is_initialized = False # For compatibility with smolagents
    
    ### ------------------------------------ ###
    
    def forward(self, query: str) -> pd.DataFrame:
        
        sep = (
            ',' if query.replace('.gz', '').endswith('.csv') else
            '\t' if query.replace('.gz', '').endswith('.tsv') else
            ','
        )
        data = pd.read_csv(query, sep=sep)

        return data
