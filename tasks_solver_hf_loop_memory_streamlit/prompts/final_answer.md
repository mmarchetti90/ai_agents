### name
final_answer

### description
This is a tool used to provide a final answer to a query

### expected_inputs
```
{
  "query": {
    "type": "str",
    "description": "User-defined query to answer"
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
You are an expert at answering user queries.
[CONTEXT]
<im_end>
<|im_start|>user
Answer the following query: [QUERY]
Wrap the summary within <output> </output> XML tags.
/no_think
<im_end>
<|im_start|>assistant

```
