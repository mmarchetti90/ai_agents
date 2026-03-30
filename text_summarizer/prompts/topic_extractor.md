### name
topic_extractor

### description
This is a tool that extracts key points from text

### expected_inputs
```
{
  "query": {
    "type": "str",
    "description": "Input data to analyze"
  }
}
```

### output_type
str

### prompt
```
<|im_start|>system
You are an expert at extracting the main topic from a provided text.
<im_end>
<|im_start|>user
Extract the main topic from the following text:
[QUERY]

Report the main topic as a single keyword wrapped within <output> </output> XML tags.
/no_think
<im_end>
<|im_start|>assistant

```
