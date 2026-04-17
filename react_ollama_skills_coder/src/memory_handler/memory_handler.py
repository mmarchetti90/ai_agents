#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import numpy as np
import sqlite3

from datetime import datetime
from io import BytesIO
from numpy.typing import NDArray
from ollama import embed as OllamaEmbed

### CLASSES -------------------------------- ###

class MemoryHandler:

    """
    Class for managing SQLite memory file
    Memories are timestamped and vectorized

    Parameters
    ----------
    memory_path: str
        Path to SQLite database
    model_checkpoint: str
        Name of the model checkpoint to use
    """

    ### ------------------------------------ ###

    def __init__(self, memory_path: str, model_checkpoint: str) -> None:

        self.memory_path = memory_path
        self.model_checkpoint = model_checkpoint
        self.check_memory_db()
    
    ### ------------------------------------ ###
    ### EMBEDDING HANDLING                   ###
    ### ------------------------------------ ###

    def transform_memory(self, text: list[str]) -> NDArray:

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

    def compare_memories(
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

    ### ------------------------------------ ###
    ### MEMORY QC                            ###
    ### ------------------------------------ ###

    def check_memory_db(self) -> None:

        """
        Checks if memory database exists and creates it if otherwise
        """

        # Open connection and create cursor for ai_user_interactions table
        db_con = sqlite3.connect(self.memory_path)
        db_cur = db_con.cursor()

        # Check if ai_user_interactions table exists
        exist_query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        db_cur.execute(exist_query, ('ai_user_interactions',))
        table_exists = (db_cur.fetchone() is not None)

        # Close connection if it exists or create the table otherwise
        # Could have simply made a "CREATE TABLE IF NOT EXISTS" transaction, but liked this better
        if table_exists:
            # Close connection
            db_con.close()
            # Get number of rows
            self.get_memory_size()
        else:
            # Create table
            db_cur.execute('CREATE TABLE ai_user_interactions(timestamp TIMESTAMP, origin TEXT, encoding BLOB, content TEXT)')
            # Commit transactions
            db_con.commit()
            self.memory_count = 0
            # Close connection
            db_con.close()

    ### ------------------------------------ ###

    def get_memory_size(self):

        """
        Returns the number of rows in the ai_user_interactions table
        """

        # Open connection and create cursor for main table
        db_con = sqlite3.connect(self.memory_path)
        db_cur = db_con.cursor()

        # Get number of rows
        count_query = 'SELECT COUNT(*) FROM ai_user_interactions'
        db_cur.execute(count_query)
        row_count = db_cur.fetchone()
        self.memory_count = row_count[0] if row_count else 0

    ### ------------------------------------ ###
    ### MEMORY MODIFICATION                  ###
    ### ------------------------------------ ###

    def log_memory(self, origin: str, content:str) -> None:

        """
        Function to log new user-ai interactions to a local database
        """

        # Get timestamp
        timestamp = datetime.now()

        # Encode memory
        content_encoding = self.encode_text([content])[0]
        content_encoding = self.numpy_to_blob(content_encoding)

        # Open connection and create cursor for main table
        db_con = sqlite3.connect(self.memory_path)
        db_cur = db_con.cursor()

        # Add memory
        new_data = [timestamp, origin, content_encoding, content]
        insert_statement = 'INSERT INTO ai_user_interactions (timestamp, origin, encoding, content) VALUES (?, ?, ?, ?)'
        db_cur.execute(insert_statement, new_data)

        # Commit transactions
        db_con.commit()
        self.memory_count += 1
        
        # Close connection
        db_con.close()

    ### ------------------------------------ ###

    def trim_memory(self, max_memory_size: int=1000):

        """
        Removes entries if memory exceeds size limit
        """

        # Open connection and create cursor for main table
        db_con = sqlite3.connect(self.memory_path)
        db_cur = db_con.cursor()

        # Get number of rows
        memories_to_remove_count = self.memory_count - max_memory_size

        # Remove excess memories
        if memories_to_remove_count > 0:

            # Get timestamp of earliest memory to be removed
            select_statement = 'SELECT timestamp FROM ai_user_interactions'
            memory_timestamps = db_cur.execute(select_statement).fetchall()
            memory_timestamps = np.array([datetime.strptime(t[0], '%Y-%m-%d %H:%M:%S.%f') for t in memory_timestamps])
            threshold = np.sort(memory_timestamps)[memories_to_remove_count - 1]

            # Remove old memories
            delete_query = 'DELETE FROM ai_user_interactions WHERE timestamp <= ?'
            db_con.execute(delete_query, (threshold,))

            # Commit transactions
            db_con.commit()
        
        # Close connection
        db_con.close()

        # Update memory_count
        self.get_memory_size()

    ### ------------------------------------ ###

    def retrieve_memory(self, context: list[str], origin: list[str]=['assistant'], max_hits: int=5, score_threshold: float=0.75) -> list:

        """
        Function to retrieve past user-ai interactions from a local database
        """

        # Open connection and create cursor for main table
        db_con = sqlite3.connect(self.memory_path)
        db_cur = db_con.cursor()

        # Define WHERE statement based on number of permitted origins
        where_statement = 'WHERE origin ' + ('= ?' if len(origin) == 1 else 'IN (' + ', '.join(['?'] * len(origin)) + ')')

        # Retrieve encodings
        select_statement = f'SELECT encoding FROM ai_user_interactions {where_statement}'
        memory_encodings = [self.blob_to_numpy(e[0]) for e in db_cur.execute(select_statement, origin).fetchall()]
        if not len(memory_encodings):
            return []
        memory_encodings = np.stack(memory_encodings, axis=0)

        # Encode
        context_encoding = self.encode_text(context)

        # Compute similarity of context to memory
        top_hits = self.compare_memories(context_encoding, memory_encodings, max_hits, score_threshold)
        top_hits_idx = np.unique([t for ts in top_hits.values() for t,s in ts])

        # Retrieve content of memories
        if top_hits_idx.shape[0] > 0:
            select_statement = f'SELECT content FROM ai_user_interactions {where_statement}'
            memory_contents = db_cur.execute(select_statement, origin).fetchall()
            relevant_memories = np.array(memory_contents).ravel()[top_hits_idx].tolist()
        else:
            relevant_memories = []
        
        # Close connection
        db_con.close()

        return relevant_memories

    ### ------------------------------------ ###
    ### UTILS                                ###
    ### ------------------------------------ ###

    def encode_text(self, text: list[str]) -> NDArray:

        """
        Function to encode text using RAG
        """

        encoding = self.transform_memory(text)
        encoding = np.array(encoding)

        return encoding

    ### ------------------------------------ ###

    @staticmethod
    def numpy_to_blob(array: NDArray) -> bytes:

        """
        Converts a numpy array to a binary blob
        """
        
        blob = BytesIO()
        np.save(blob, array)
        blob.seek(0)
        
        return sqlite3.Binary(blob.read())

    ### ------------------------------------ ###

    @staticmethod
    def blob_to_numpy(blob: bytes) -> NDArray:
        
        """
        Converts a binary blob to a numpy array
        """
        
        array = BytesIO(blob)
        array.seek(0)
        
        return np.load(array)
