### name
data_miner

### description
This is a tool that extracts relevant information from text

### expected_inputs
```
{
  "query": {
    "type": "str",
    "description": "Keywords to guide data mining"
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
You are an expert at data-mining text to extracting useful information.
[CONTEXT]
<im_end>
<|im_start|>user
Use the following to guide your data mining: [QUERY]
Wrap the extracted key information within <output> </output> XML tags.
/no_think
<im_end>
<|im_start|>assistant

```
