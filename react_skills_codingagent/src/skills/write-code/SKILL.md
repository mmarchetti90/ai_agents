---
name: write-code
description: Creates code snippets based on user-provided specifications
---

## Inputs

```json
{
  "description" : "Structured overview of the code to be generated.",
  "language" : "The programming language to be used (e.g. Python, JavaScript, Bash).",
  "output_file" : "The text file the code will be written to."
}
```

## Default inputs

```json
{
  "description" : "",
  "language" : "Python",
  "output_file" : "snippet.py"
}
```

## Purpose

Generate a code snippet based on user-provided specifications.

## Directions

- Carefully analyze the code requirements
- Use the specified coding language
- Be thorough in your code annotation
- Do not execute the code snippet

## Workflow

1. Analyse the following code description: <description> /no_think
2. Write code that satisfies the user requirement using the following language: <language> /no_think
3. RUN ```{"message": "I wrote the code snippet to file", "args": ["echo", "<previous_output>"], "kwargs": {"capture_output" : false, "stdout" : "<output_file>"}, "capture": "none"}```
4. Provide a markdown description of the code, explaining in detail what it does and how to run it /no_think
5. RUN ```{"message": "Markdown report was created", "args": ["echo", "<previous_output>"], "kwargs": {"capture_output" : false, "stdout" : "code_annotation.md"}, "capture": "none"}```

## Completion message

Code snippet was successfully created.
