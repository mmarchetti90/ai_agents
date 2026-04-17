#!/bin/bash python3

### IMPORTS -------------------------------- ###

from sys import argv

### CLASSES AND FUNCTIONS ------------------ ###

def load_snippet(code_path: str) -> str:

    # Read text
    code_snippet = open(code_path, "r").read()

    return code_snippet

### MAIN ----------------------------------- ###

if __name__ == "__main__":
    
    # Parse command line arguments
    code_path = argv[argv.index("--path") + 1]
    
    # Load code snippet
    code_snippet = load_snippet(code_path)

    # Print to stdout
    language = (
        'python' if code_path.endswith('.py') else
        'bash' if code_path.endswith('.py') else
        'javascript' if code_path.endswith('.js') else
        'typescript' if code_path.endswith('.ts') else
        'nextflow' if code_path.endswith('.nf') else
        'R' if code_path.endswith('.R') else
        ''
    )
    print(f'```{language}\n{code_snippet}```')
