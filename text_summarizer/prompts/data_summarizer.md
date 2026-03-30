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
  }
}
```

### output_type
str

### prompt
```
<|im_start|>system
You are an expert at creating accurate summaries from provided text.
<im_end>
<|im_start|>user
Here's the data to summarize:
[QUERY]

Summarize the provided data and wrap the summary within <output> </output> XML tags.
/no_think
<im_end>
<|im_start|>assistant

```
