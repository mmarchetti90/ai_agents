#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

from collections.abc import Callable
from src.models.embedding_model import init_text_embedding_model
from torch import no_grad as torch_no_grad

### CLASSES AND FUNCTIONS ------------------ ###

class rag_filter:

    """
    Class for filtering text based on a query
    """
    
    # Variables for guiding LMM choice

    tool_type = "llm"
    
    name = 'rag_filter'
    
    description = """
    This is a tool that filters text based on a query
    """
    
    inputs = {
        'query': {
            'type': 'string',
            'description': 'Context to guide filtering'
        },
        'data': {
            'type': 'string',
            'description': 'Data to be filtered'
        },
        'max_hits': {
            'type': 'int',
            'description': 'Top relevant info to return'
        }
    }
    
    output_type = 'list of strings'
    
    ### ------------------------------------ ###
    
    def __init__(self, model_checkpoint: str, device_map: str='cpu', similarity_fn_name: str='cosine'):
        
        self.is_initialized = False # For compatibility with smolagents

        self.model = init_text_embedding_model(model_checkpoint, device_map, similarity_fn_name)
    
    ### ------------------------------------ ###
    
    @torch_no_grad()
    def forward(self, query: str, data: list[str], max_hits: int=5) -> str:

        # Split data into sentences if it was provided as a single string

        if type(data) == str:

            data = [d for d in data.replace('\n', '. ').split('. ') if len(d)]
            #data = [d for d in data.split('\n') if len(d)]

        # Embed query and data

        query_embedding = self.model.encode(query)

        data_embedding = self.model.encode(data)

        # Compute similarity of data to query

        similarity = [
            (sentence, score)
            for sentence,score in zip(data,
                                      self.model.similarity(query_embedding,
                                                            data_embedding).tolist()[0])
        ]

        similarity.sort(key=lambda s: s[1], reverse=True)

        # Extract top hits and structure as bullet-points

        relevant_info = '\n'.join([f'* {s[0]}' for s in similarity[:max_hits]])

        return relevant_info
        
### ---------------------------------------- ###

if __name__ == '__main__':
    
    query = "Tolkien's Middle Earth."

    data = [
        "Middle Earth is home to many races, including dwarves, humans, and elves.",
        "Luke Skywalker is a central character in Star Wars.",
        "Captain America is a known Marvel superhero.",
        "Sauron waged war in Middle Earth.",
        "Eru Ilúvatar is the core deity in Tolkien's works.",
        "Bilbo Baggins had a great adventure in Middle Earth.",
        "Tattoine is a remote planet in the Star Wars universe."
    ]
    
    text_filter = rag_filter(model_checkpoint='Qwen/Qwen3-Embedding-0.6B')

    output = text_filter.forward(query, data, 3)

    with open('test_rag_filter.txt', 'w') as out:
    
        out.write('\n'.join([
            '# query:',
            query,
            '# raw_data:',
            "\n".join(["* " + d for d in data]),
            '# filtered_data:',
            output
        ]))
