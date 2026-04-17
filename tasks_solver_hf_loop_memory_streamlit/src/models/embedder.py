#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import numpy as np

from collections.abc import Callable
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer
#from torch import float16 as torch_float16
from torch import no_grad as torch_no_grad
#from torch.cuda import is_available as cuda_is_available
#from transformers import BitsAndBytesConfig

### CLASSES AND FUNCTIONS ------------------ ###

class embedder:

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
    init_model(model_checkpoint: str, device_map: str='auto', similarity_fn_name: str='cosine') -> Callable
        Initializes the model to be used for inference
        Ran automatically at initialization
    forward(prompt: str, data: list[str], max_hits: int=5) -> str
        Runs inference and returns info relevant to the query
    """
    
    ### ------------------------------------ ###
    
    def __init__(
        self,
        model_checkpoint: str,
        device_map: str='auto',
        similarity_fn_name: str='cosine'
    ) -> None:

        self.model = self.init_model(model_checkpoint, device_map, similarity_fn_name)

    ### ------------------------------------ ###

    def init_model(
        self,
        model_checkpoint: str,
        device_map: str='auto',
        similarity_fn_name: str='cosine'
    ) -> Callable:

        """
        Initializes the model to be used for inference
        
        Parameters
        ----------
        model_checkpoint: str
            Name of the model checkpoint to use
        device_map: str='auto'
            Device to be used for inference
        similarity_fn_name: str='cosine'
            Similarity function to be used
        """

        # Init model

        """
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch_float16
        ) if cuda_is_available else None

        embedder = SentenceTransformer(
            model_checkpoint,
            similarity_fn_name=similarity_fn_name,
            device=device_map,
            model_kwargs={
                "low_cpu_mem_usage" : True,
                "quantization_config" : quantization_config
            }
        )
        """

        # SentenceTransformer object

        embedder_model = SentenceTransformer(
            model_checkpoint,
            similarity_fn_name=similarity_fn_name,
            device=device_map,
            model_kwargs={
                "low_cpu_mem_usage" : True
            }
        )

        return embedder_model
    
    ### ------------------------------------ ###
    
    @torch_no_grad()
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

        embeddings = self.model.encode(text)

        return embeddings
    
    ### ------------------------------------ ###

    @torch_no_grad()
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
        data_embedding: list[str]
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

        # Compute similarity of data to query

        similarity = self.model.similarity(query_embedding, data_embedding)

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

    model_checkpoint, device_map ='Qwen/Qwen3-Embedding-0.6B', 'cpu'
    
    text_embedder = embedder(model_checkpoint, device_map)

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
