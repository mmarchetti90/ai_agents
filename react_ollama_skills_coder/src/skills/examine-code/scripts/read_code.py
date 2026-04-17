#!/bin/bash python3

### IMPORTS -------------------------------- ###

from sys import argv

### CLASSES AND FUNCTIONS ------------------ ###

def load_snippet(code_path: str, element: str, element_type: str) -> str:

    # Read text
    code_snippet = open(code_path, "r").read()

    # Extract element (mostly geared for python code)
    get_indent_level = lambda line: len(line) - len(line.lstrip())
    if element != 'all':
        if element_type == 'class':
            element = f'class {element}'
        elif element_type == 'function':
            element = f'def {element}'
        else:
            pass
        code_snippet_sub = []
        element_indent = -1
        capture_following_lines = False
        for code_line in code_snippet.split('\n'):
            code_line = code_line.expandtabs(4)
            if not len(code_line.strip()):
                # Empty line
                continue
            elif element in code_line:
                # Capture line since it contains the element
                code_snippet_sub.append(code_line)
                element_indent = get_indent_level(code_line)
                capture_following_lines = True
            elif capture_following_lines:
                # Check if the following line has higher level of indent
                line_indent = get_indent_level(code_line)
                if line_indent > element_indent:
                    # Capture following line and append it to the last element captured
                    code_snippet_sub[-1] += '\n' + code_line
                else:
                    # Following line has a same or lower level of indent, so capture is stopped
                    element_indent = -1
                    capture_following_lines = False
            else:
                continue
        code_snippet = '\n\n'.join(code_snippet_sub)

    return code_snippet

### MAIN ----------------------------------- ###

if __name__ == "__main__":
    
    # Parse command line arguments
    code_path = argv[argv.index("--path") + 1]
    if '--element' in argv:
        element = argv[argv.index("--element") + 1]
    else:
        element = 'all'
    if '--element_type' in argv:
        element_type = argv[argv.index("--element_type") + 1]
    else:
        element_type = 'other'
    
    # Load code snippet
    code_snippet = load_snippet(code_path, element, element_type)

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
