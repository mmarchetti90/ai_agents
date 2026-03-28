### name
query_decomposition

### description
This is a tool that decomposes a query into subtasks for solving the query

### expected_inputs
```
{
  "query": {
    "type": "str",
    "description": "User-submitted query"
  },
  "context": {
    "type": "str",
    "description": "Context to guide the text generation"
  }
}
```

### output_type
str

### prompt
```
<|im_start|>system
You are an expert at decomposing a complex task into subtasks.
[CONTEXT]
<im_end>
<|im_start|>user
Decompose the following query into at most 10 subtasks: [QUERY]
Return all subtasks within <output> </output> XML tags as follows:
<output>
[
  {
    "task_id": "Unique numerical identifier.",
    "description": "Description of the task.",
    "dependencies": ["List of tasks' task_id required before the current one."]
  }
]
</output>
/no_think
<im_end>
<|im_start|>assistant

```
