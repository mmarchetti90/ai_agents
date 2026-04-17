---
name: task-completed
description: Use this tool if you fully completed your task
---

## Inputs

```json
{
  "completion_message" : "Comment on how you completed the task",
  "task_output" : "Report the actual outputs from the task (e.g. loaded code snippets, project structures you generated, code analyses, etc.)"
}
```

## Default inputs

```json
{
  "completion_message" : "Task completed",
  "task_output" : "None"
}
```

## Mock function

```python
def task_completed(completion_message: str, task_output: str):
  """
  Marks the user task as completed

  Args:
    completion_message: Comment on how you completed the task.
    task_output: Report the actual outputs from the task (e.g. loaded code snippets, project structures you generated, code analyses, etc.)
  Returns:
    bool: Completion signal
  """

  return True
```

## Purpose

Use this tool if you completed your task.

## Directions

- None

## Workflow

1. Do nothing

## Completion message

I successfully completed the user task.

