### name
creative_writer

### description
This is a tool that writes text without any reference

### expected_inputs
```
{
  "query": {
    "type": "str",
    "description": "Description of text to generate"
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
You are a creative writer of fictional stories.
[CONTEXT]
<im_end>
<|im_start|>user
[QUERY]
Wrap the story within <output> </output> XML tags.
/no_think
<im_end>
<|im_start|>assistant

```
