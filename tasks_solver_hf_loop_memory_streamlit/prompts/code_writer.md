### name
code_writer

### description
This is a tool that writes Python code

### expected_inputs
```
{
  "query": {
    "type": "str",
    "description": "Description of code to generate"
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
You are an expert Python programmer.
[CONTEXT]
<im_end>
<|im_start|>user
[QUERY]
Wrap the code within <output> </output> XML tags.
/no_think
<im_end>
<|im_start|>assistant

```
