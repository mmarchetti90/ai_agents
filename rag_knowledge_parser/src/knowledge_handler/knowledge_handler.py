#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import numpy as np
import sqlite3

from docx import Document as DocxReader
from io import BytesIO
from numpy.typing import NDArray
from ollama import embed as OllamaEmbed
from os import listdir
from pypdf import PdfReader

### CLASSES -------------------------------- ###

class KnowledgeHandler:

    """
    Class for reading docs, embedding them, and storing data into a SQLite db
    
    Parameters
    ----------
    knowledge_dir: str
        Path to knowledge-base directory
    model_checkpoint: str
        Name of the model checkpoint to use
    """

    ### ------------------------------------ ###

    def __init__(self, knowledge_dir: str, model_checkpoint: str) -> None:

        self.accepted_docs = ['.txt', '.pdf', 'docx']
        self.knowledge_dir = knowledge_dir
        self.db_path = f'{self.knowledge_dir}/knowledge.db'
        self.model_checkpoint = model_checkpoint
        self.update_knowledge_db()
    
    ### ------------------------------------ ###
    ### KNOWLEDGE BASE MAINTENANCE           ###
    ### ------------------------------------ ###

    def update_knowledge_db(self):

        """
        Checks if memory database exists and creates it if otherwise
        Also checks if there are new docs or if older ones have been removed
        """

        # Check if database exists
        self.check_db()

        # Scan knowledge_dir and compared to database documents list
        docs = self.check_docs()

        # Update db with new docs or remove old ones
        counts = {kind : 0 for kind in ['remove', 'add', 'keep']}
        for d,action in docs.items():
            counts[action] += 1
            if action == 'remove':
                self.remove_doc(d)
            elif action == 'add':
                self.add_doc(d)
            else:
                continue
        
        # Create log of updates
        self.updates = [
            f'Kept {counts["keep"]} old data objects.',
            f'Added {counts["add"]} new data objects.',
            f'Removed {counts["remove"]} old data objects.'
        ]
    
    ### ------------------------------------ ###

    def check_db(self) -> None:

        # Open connection and create cursor
        db_con = sqlite3.connect(self.db_path)
        db_cur = db_con.cursor()

        # Check if docs table exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_name TEXT UNIQUE
        )
        """
        db_cur.execute(create_table_query)

        # Check if data table exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_origin TEXT,
            embedding BLOB,
            content TEXT
        )
        """
        db_cur.execute(create_table_query)

        # Commit transactions
        db_con.commit()

        # Close connection
        db_con.close()

    ### ------------------------------------ ###

    def check_docs(self) -> dict:

        """
        Check documents in knowledge_dir and compared to those stored in knowledge.db
        """

        # Scan knwoledge_dir
        files = [f for f in listdir(self.knowledge_dir) if any([f.endswith(suffix) for suffix in self.accepted_docs])]

        # Open connection and create cursor
        db_con = sqlite3.connect(self.db_path)
        db_cur = db_con.cursor()

        # Check if docs need to be added or removed
        select_statement = 'SELECT doc_name FROM docs'
        db_docs = [d[0] for d in db_cur.execute(select_statement).fetchall()]

        # Compare list of docs in db_docs to files
        complete_docs_list = {
            d : ('add' if d not in db_docs else
                 'remove' if d not in files else
                 'keep')
            for d in set(files + db_docs)
        }

        # Close connection
        db_con.close()

        return complete_docs_list
    
    ### ------------------------------------ ###

    def remove_doc(self, d: str) -> None:

        """
        Removes entries based on doc name
        """

        # Open connection and create cursor
        db_con = sqlite3.connect(self.db_path)
        db_cur = db_con.cursor()

        # Remove d from docs table
        delete_query = 'DELETE FROM docs WHERE doc_name = ?'
        db_con.execute(delete_query, (d,))

        # Remove d from data table
        delete_query = 'DELETE FROM data WHERE doc_origin = ?'
        db_cur.execute(delete_query, (d,))

        # Commit transactions
        db_con.commit()
        
        # Close connection
        db_con.close()
    
    ### ------------------------------------ ###

    def add_doc(self, d: str) -> None:

        """
        Adds data from a new document
        """

        # Open connection and create cursor
        db_con = sqlite3.connect(self.db_path)
        db_cur = db_con.cursor()

        # Open document and parse its contents
        d_path = f'{self.knowledge_dir}/{d}'
        d_content = self.parse_doc(d_path)

        # Add doc to docs table
        insert_statement = 'INSERT INTO docs (doc_name) VALUES (?)'
        db_cur.execute(insert_statement, (d,))

        # Vectorize the document contents and add to database
        insert_statement = 'INSERT INTO data (doc_origin, embedding, content) VALUES (?, ?, ?)'
        new_data = [(d, self.numpy_to_blob(self.transform_data([dc])[0]), dc) for dc in d_content]
        db_cur.executemany(insert_statement, new_data)

        # Commit transactions
        db_con.commit()
        
        # Close connection
        db_con.close()

    ### ------------------------------------ ###
    ### DATA RETRIEVAL                       ###
    ### ------------------------------------ ###

    def retrieve_data(self, context: list[str], max_hits: int=5, score_threshold: float=0.75) -> list:

        """
        Function to retrieve data from a local database given a context
        """

        # Open connection and create cursor for main table
        db_con = sqlite3.connect(self.db_path)
        db_cur = db_con.cursor()

        # Retrieve embeddings
        select_statement = 'SELECT embedding FROM data'
        data_embeddings = [self.blob_to_numpy(e[0]) for e in db_cur.execute(select_statement).fetchall()]
        if not len(data_embeddings):
            return []
        data_embeddings = np.stack(data_embeddings, axis=0)

        # Embed context
        context_embeddings = self.transform_data(context)

        # Compute similarity of context to memory
        top_hits = self.compare_data(context_embeddings, data_embeddings, max_hits, score_threshold)
        top_hits_idx = np.unique([t for ts in top_hits.values() for t,s in ts])

        # Retrieve content of data
        if top_hits_idx.shape[0] > 0:
            select_statement = 'SELECT content FROM data'
            data_contents = db_cur.execute(select_statement).fetchall()
            relevant_data = np.array(data_contents).ravel()[top_hits_idx].tolist()
        else:
            relevant_data = []
        
        # Close connection
        db_con.close()

        return relevant_data
    
    ### ------------------------------------ ###
    ### EMBEDDING HANDLING                   ###
    ### ------------------------------------ ###

    def transform_data(self, text: list[str]) -> NDArray:

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

    def compare_data(
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
    ### UTILS                                ###
    ### ------------------------------------ ###

    def parse_doc(self, input: str) -> list[str]:

        """
        Load text from different souces
        """

        # Load text
        if all([not input.endswith(suffix) for suffix in self.accepted_docs]):
            # Assuming input is the text to summarize
            parsed_input = input.strip()
        elif input.lower().endswith('.txt'):
            # txt file
            parsed_input = open(input, 'r').read().strip()
        elif input.lower().endswith('.pdf'):
            # pdf file
            parsed_input = []
            reader = PdfReader(input)
            for page in reader.pages:
                parsed_input.append(page.extract_text())
            parsed_input = '\n'.join(parsed_input)
        elif input.lower().endswith('.docx'):
            # Windows docx file
            parsed_input = []
            reader = DocxReader(input)
            for paragraph in reader.paragraphs:
                parsed_input.append(paragraph.text)
            parsed_input = '\n'.join(parsed_input)
        else:
            parsed_input = ''
        
        # Clean text and split into sentences of at least 3 words
        parsed_input = ''.join([l for l in parsed_input.split('\n') if len(l)])
        sentences = [s for s in parsed_input.split('. ') if len(s.split(' ')) >= 3]

        return sentences
    
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
