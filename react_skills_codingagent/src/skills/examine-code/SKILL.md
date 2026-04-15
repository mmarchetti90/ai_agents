---
name: examine-code
description: Checks a code snippet and returns insights
---

## Inputs

```json
{
  "code_path" : "Path to the code file to be examined (e.g. 'src/main.py')",
  "element" : "The element to be examined (e.g. function, class). If 'all', examine all elements in the file.",
  "element_type" : "'class', 'function', or 'other'"
}
```

## Default inputs

```json
{
  "code_path" : "src/main.py",
  "element" : "all",
  "element_type" : "other"
}
```

## Purpose

Provide insights on a user-provided code snippet, including syntax errors, and code structure.

## Directions

- Verify coding language
- List global variables
- List classes and functions
- Highlight syntax errors
- Discuss comments
- Do not execute the code snippet

## Workflow

1. RUN ```{"message": "Code snippet was loaded", "args": ["python", "scripts/read_code.py", "--path", "<code_path>", "--element", "<element>", "--element_type", "<element_type>"], "kwargs": {"capture_output" : true, "text" : true}, "capture": "stdout"}```
2. Analyze the following code snippet:\n```\n<previous_output>\n``` /think
3. Summarize your findings as a markdown document /no_think
4. RUN ```{"message": "Markdown report was created", "args": ["echo", "<previous_output>"], "kwargs": {"capture_output" : false, "stdout" : "code_report.md"}, "capture": "none"}```

## Completion message

Code was examined and a report generated.

