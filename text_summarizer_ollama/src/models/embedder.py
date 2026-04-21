#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import numpy as np

from collections.abc import Callable
from numpy.typing import NDArray
from ollama import embed as OllamaEmbed

### CLASSES AND FUNCTIONS ------------------ ###

class Embedder:

    """
    Class for embedding text and computing similarity
    
    Parameters
    ----------
    model_checkpoint: str
        Name of the model checkpoint to use
    device_map: str='auto'
        Device to be used for inference
    similarity_fn_name: str='cosine'
        Similarity function to be used

    Methods
    -------
    init_model(model_checkpoint: str) -> Callable
        Initializes the model to be used for inference
        Ran automatically at initialization
    forward(prompt: str, data: list[str], max_hits: int=5) -> str
        Runs inference and returns info relevant to the query
    """
    
    ### ------------------------------------ ###
    
    def __init__(
        self,
        model_checkpoint: str
    ) -> None:

        self.model_checkpoint = model_checkpoint
    
    ### ------------------------------------ ###
    
    def transform(self, text: list[str]) -> NDArray:

        """
        Embeds text

        Parameters
        ----------
        text: list[str]
            List of strings to embed

        Returns
        -------
        np.array
            Strings embeddings
        """

        embeddings = np.array(OllamaEmbed(model=self.model_checkpoint, input=text).embeddings)

        return embeddings
    
    ### ------------------------------------ ###

    def compare(
        self,
        query_embedding: NDArray,
        data_embedding: NDArray,
        max_hits: int=5,
        score_threshold: float=0.75
    ) -> dict[int, list[tuple[int, int]]]:

        """
        Compares data to a query and returns the index of the top most similar items

        Parameters
        ----------
        query_embedding: np.array
            Transformed query
        data_embedding: np.array
            Transformed data
        max_hits: int=5
            Maximum hits to be returned
        score_threshold: float=0.75
            Minimum similarity score

        Returns
        -------
        list[str]
            List of top hits indices
        """

        # Lambda function for cosine similarity
        cosine_similarity = lambda a,b: np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        # Compute similarity and return top hits indexes and scores
        similarity = [[cosine_similarity(q, d) for d in data_embedding] for q in query_embedding]
        top_hits = {}
        for q,sim in enumerate(similarity):
            sim = np.array(sim)
            q_top_hits = np.argsort(sim)[::-1][:max_hits]
            top_hits[q] = [(idx, score) for idx,score in zip(q_top_hits, sim[q_top_hits]) if score >= score_threshold]

        return top_hits
        
### ---------------------------------------- ###

if __name__ == '__main__':
    
    query = ["Tolkien's Middle Earth.", 'Star Wars']
    data = [
        "Middle Earth is home to many races, including dwarves, humans, and elves.",
        "Luke Skywalker is a central character in Star Wars.",
        "Captain America is a known Marvel superhero.",
        "Sauron waged war in Middle Earth.",
        "Eru Ilúvatar is the core deity in Tolkien's works.",
        "Bilbo Baggins had a great adventure in Middle Earth.",
        "Tattoine is a remote planet in the Star Wars universe."
    ]
    model_checkpoint ='qwen3-embedding:0.6b'
    text_embedder = Embedder(model_checkpoint)
    query_embedding = text_embedder.transform(query)
    data_embedding = text_embedder.transform(data)
    top_hits = text_embedder.compare(query_embedding, data_embedding, 4, 0.5)
    output_text = []
    for q,ts in top_hits.items():
        output_text.append('-' * 40)
        output_text.append(f'# {query[q]}')
        output_text.append('\n'.join([f'* {data[t]} (score={s:.3f})' for t,s in ts]) if len(ts) else 'None')
        output_text.append('-' * 40)
    output_text = '\n'.join(output_text)
    with open('test_tag_filter.txt', 'w') as out:
        out.write(output_text)
