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

### chat
```json
[
  {"role" : "system", "content" : "You are an expert at creating accurate summaries from provided text."},
  {"role" : "user", "content" : "Here's the data to summarize:\n[QUERY]\nSummarize the provided data and wrap the summary within <output> </output> XML tags."}
]
```
