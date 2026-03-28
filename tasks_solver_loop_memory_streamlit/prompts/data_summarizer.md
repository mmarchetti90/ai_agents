### name
data_summarizer

### description
This is a tool that summarizes text

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
You are an expert at creating accurate summaries from provided text.
[CONTEXT]
[QUERY]
<im_end>
<|im_start|>user
Summarize the provided data.
Wrap the summary within <output> </output> XML tags.
/no_think
<im_end>
<|im_start|>assistant

```
