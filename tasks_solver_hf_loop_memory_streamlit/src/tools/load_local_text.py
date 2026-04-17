#!/usr/bin/env python3

### CLASSES AND FUNCTIONS ------------------ ###

class load_local_text:
    
    """
    Load local text file
    """
    
    # Variables for guiding LMM choice

    tool_type = "function"
    name = 'load_local_text'
    description = """
    This is a tool that loads a local text file
    """
    inputs = {
        'query': {
            'type': 'str',
            'description': 'Path to the text file'
        }
    }
    output_type = 'str'
    
    ### ------------------------------------ ###
    
    def __init__(self):
        
        self.is_initialized = False # For compatibility with smolagents
    
    ### ------------------------------------ ###
    
    def forward(self, query: str) -> str:

        data = open(query, 'r').read()

        return data

### ---------------------------------------- ###

if __name__ == '__main__':
    
    # Create a file
    mock_file = 'mock.txt'
    with open(mock_file, 'w') as mock_input:
        mock_input.write(f'Success!\nNow please delete {mock_file}')

    # Execute
    loader = load_local_text()
    data = loader.forward(mock_file)
    print(data)
