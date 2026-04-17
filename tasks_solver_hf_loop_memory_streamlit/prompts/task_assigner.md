### name
task_assigner

### description
This is a tool that assigns a tool to a query

### expected_inputs
```
{
  "query": {
    "type": "str",
    "description": "User-submitted query"
  },
  "tools_description": {
    "type": "str",
    "description": "JSON-formatted string describing available tools"
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
You are an expert at assigning tools to specific tasks.
[CONTEXT]
The tool calls available to you are described within <tools> </tools> XML tags:
<tools>
[TOOLS]
</tools>
<im_end>
<|im_start|>user
Assign a tool to the following query: [QUERY]

Call the tool using the following JSON format within <output> </output> XML tags as follows:
<output>
{
  "tool": "Name of the tool you choose to use ([TOOL_NAMES]).",
  "reason": "Short explanation of why you chose this tool.",
  "input": "Specific input for the tool."
}
</output>
/no_think
<im_end>
<|im_start|>assistant

```
