---
name: plan-coding-project
description: Plans the structure of a coding project, generating a useful guide on how to design the code
---

## Inputs

```json
{
  "project_description" : "Description of the project",
  "language" : "The primary coding language to use"
}
```

## Default inputs

```json
{
  "project_description" : "None",
  "language" : "Python"
}
```

## Mock function

```python
def plan_coding_project(project_description: str, language: str):
  """
  Checks a code snippet and returns insights

  Args:
    project_description: Description of the project.
    language: The primary coding language to use.
  Returns:
    str: The generated project structure
  """

  output = ""

  return output
```

## Purpose

Plan the structure of a coding project based on the user's description

## Directions

- Only use the stated coding language
- Assume the project files will all be created in the current directory
- Think about what the project aims to achieve
- Break down the code into discreet code snippets to achieve specific goals

Here's an example of a project structure:
./
├── README.md
│   Description of the project and how to run it.
├── main.py
│   Entrypoint.
├── code_snippet_1.py
│   Code snippet 1 to achieve a specific goal.
├── code_snippet_2.py
│   Code snippet 2 to achieve a specific goal.
├── makefile
│   Makefile instructions for building and running the project.
└── requirements.txt
    List of dependencies required for the project.

## Workflow

1. Analyze the project description
2. Create a project structure based on the analysis
3. Describe the necessary code snippets to implement the project

## Completion message

I generated a structure of the proposed project.
