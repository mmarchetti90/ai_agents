---
name: read-code
description: Reads a code snippet and returns it as a string
---

## Inputs

```json
{
  "code_path" : "Path to the code file to be read (e.g. 'src/main.py')"
}
```

## Default inputs

```json
{
  "code_path" : "src/main.py"
}
```

## Mock function

```python
def read_code(code_path: str):
  """
  Reads a code snippet and returns it as a string

  Args:
    code_path: Path to the code file to be read (e.g. 'src/main.py').
  Returns:
    str: The loaded code snippet
  """

  output = ""

  return output
```

## Purpose

Reads a code snippet and returns it as a string.

## Directions

- Do not execute the code snippet

## Workflow

1. RUN ```{"message": "Code snippet was loaded", "args": ["python", "scripts/read_code.py", "--path", "<code_path>"], "kwargs": {"capture_output" : true, "text" : true}, "capture": "stdout"}```

## Completion message

Here is the code snippet I loaded:
```
<previous_output>
```
