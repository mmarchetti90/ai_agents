# Skills structure

Skills are structured as markdown docs with the following components

## Header

A yaml-like section with skill name and description.\
The skill name must match the root directory.\
The description is used by the agent for selecting the skill.
This section **does not** have a markdown header.

**e.g.**
```yaml
---
name: examine-code
description: Checks a code snippet and returns insights
---
```

## Inputs

This section reports the inputs that are required to run the skill as a JSON snippet.
This section has the markdown header `## Inputs`.

**e.g.**
``````
```json
{
  "var_1" : "Value of variable 1",
  "var_2" : "Value of variable 2"
}
```
``````

## Default inputs

This section reports the default values of input variables as a JSON snippet.
This section has the markdown header `## Default inputs`.

**e.g.**
``````
```json
{
  "var_1" : 1,
  "var_1" : 2
}
```
``````

## Mock function

This section reports a mock function for Ollama tools selection.
This section has the markdown header `## Mock function`.
N.B. The function name is the same as the skill, but with undescores replacing hyphens.

**e.g.**
``````
```python
def do_something(var_1: int, var_2: int):
  """
  This function does something

  Args:
    var_1: The first integer number
    var_2: The second integer number
  Returns:
    str: The output
  """

  output = ""

  return output
```
``````

## Purpose

This section provides a description of the skill purpose and is used as a chat message.
This section has the markdown header `## Purpose`.

## Directions

List of directions the LLM should follow.
Used as a chat message.
This section has the markdown header `## Directions`.

**e.g.**
```
- Verify coding language
- List global variables
- List classes and functions
- Highlight syntax errors
- Discuss comments
- Do not execute the code snippet
```

## Workflow

Numbered list of tasks to be executed.
This section has the markdown header `## Workflow`.
Steps that start with the keyword `RUN` are to be executed using subprocess.run
These steps must report a one-line JSON with the following structure:

```json
{
    "message": "Message to be stored to chat upon task completion. Can be empty",
    "args": "List of args for subprocess.run",
    "kwargs": "Dict of kwargs for subprocess.run",
    "capture": "Output to capture, i.e. 'none', 'stdout', 'stdin', or use any other string to capture both stdin and stderr"
}
```

N.B. Input variables can be inserted in args or kwargs as `<var_name>`
N.B. A special variable, `<previous_output>` is substituted with the output of a previous task.

**e.g.**
```
1. RUN ```{"message": "Hello word!", "args": ["python", "scripts/mock.py", "--var_1", "<var_1>", "--var_2", "<var_2>"], "kwargs": {"capture_output" : true, "text" : true}, "capture": "stdout"}```
2. What do you think about <previous_output>? /think
3. Summarize your thoughts as a markdown document /no_think
4. RUN ```{"message": "Markdown report was created", "args": ["echo", "<previous_output>"], "kwargs": {"capture_output" : false, "stdout" : "code_report.md"}, "capture": "none"}```
```

## Completion message

Message to be added to chat upon skill fully successfull completion.
This section has the markdown header `## Completion message`.

