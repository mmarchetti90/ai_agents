---
name: read-code
description: Reads a code snippet and returns it as a string
---

## Inputs

```json
{
  "code_path" : "Path to the code file to be examined (e.g. 'src/main.py')"
}
```

## Default inputs

```json
{
  "code_path" : "src/main.py"
}
```

## Purpose

Reads a code snippet and returns it as a string.

## Directions

- Do not execute the code snippet

## Workflow

1. RUN ```{"message": "Code snippet was loaded", "args": ["python", "scripts/read_code.py", "--path", "<code_path>"], "kwargs": {"capture_output" : true, "text" : true}, "capture": "stdout"}```

## Completion message

Code snippet loaded:
```
<previous_output>
```
