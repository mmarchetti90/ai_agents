#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import sqlite3

### CLASSES AND FUNCTIONS ------------------ ###

class load_local_sql:
    
    """
    Load local SQLite database
    """
    
    # Variables for guiding LMM choice
    tool_type = "function"
    name = 'load_local_sql'
    description = """
    This is a tool that loads a local SQLite database
    """
    inputs = {
        'query': {
            'type': 'str',
            'description': 'Path to the database'
        }
    }
    output_type = 'sqlite3.Connection'
    
    ### ------------------------------------ ###
    
    def __init__(self):
        
        self.is_initialized = False # For compatibility with smolagents
    
    ### ------------------------------------ ###
    
    def forward(self, query: str) -> sqlite3.Connection:
        
        data = sqlite3.connect(query)
        
        return data
