### name
key_points_extractor

### description
This is a tool that extracts key points from text

### expected_inputs
```
{
  "query": {
    "type": "str",
    "description": "Input data to summarize"
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
You are an expert at extracting key points from a provided text.
[CONTEXT]
<im_end>
<|im_start|>user
Extract key information from following data: [QUERY]
Report the key information as bullet points wrapped within <output> </output> XML tags.
/no_think
<im_end>
<|im_start|>assistant

```
