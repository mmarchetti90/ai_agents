#!/usr/bin/env python3

### CLASSES AND FUNCTIONS ------------------ ###

class execute_code:
    
    """
    Class for executing code snippets
    """
    
    # Variables for guiding LMM choice
    tool_type = "function"
    name = 'execute_code'
    description = """
    This is a tool that execute python code snippets
    """
    inputs = {
        'query': {
            'type': 'str',
            'description': 'Code snippet to be executed'
        }
    }
    output_type = 'dict'
    
    ### ------------------------------------ ###
    
    def __init__(self):
        
        self.is_initialized = False # For compatibility with smolagents
    
    ### ------------------------------------ ###
    
    def forward(self, query: str) -> dict:
        
        # Attempt execution
        try:
            new_vars = {}
            exec(query, globals(), new_vars)
            return new_vars
        except:
            return {}

### ---------------------------------------- ###

if __name__ == '__main__':
    
    query = "x=3\ny=5\nz=x+y"
    new_vars = execute_code().forward(query)
    if len(new_vars):
        print('Execution success')
        for nv_name,nv_value in new_vars.items():
            print(f'{nv_name}: {nv_value}')
    else:
        print('Execution failed')
