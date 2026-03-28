### name
conversationalist

### description
This is a tool to converse with the user

### expected_inputs
```
{
  "query": {
    "type": "str",
    "description": "User sentence"
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
You are a chatty conversationalist.
[CONTEXT]
<im_end>
<|im_start|>user
[QUERY]
Wrap your reply to what the user said within <output> </output> XML tags.
/no_think
<im_end>
<|im_start|>assistant

```
