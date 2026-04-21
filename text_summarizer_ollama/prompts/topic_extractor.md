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

### chat
```json
[
  {"role" : "system", "content" : "You are an expert at extracting the main topic from a provided text."},
  {"role" : "user", "content" : "Extract the main topic from the following text:\n[QUERY]\nReport the main topic as a single keyword wrapped within <output> </output> XML tags."}
]
```
