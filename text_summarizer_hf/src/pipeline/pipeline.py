#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import json
import numpy as np
import pandas as pd
import seaborn as sns
import sqlite3

from collections.abc import Callable
from datetime import datetime
from docx import Document as DocxReader
from io import BytesIO
from matplotlib import pyplot as plt
from numpy.typing import NDArray
from os.path import exists
from pypdf import PdfReader
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from typing import Any

### CLASSES -------------------------------- ###

class pipeline:

    """
    Class for text summarizer pipeline

    Parameters
    ----------
    config: dict
        Dictionary of configuration parameters
    llm: Callable
        llm class instance for running prompts
    text_embedder: Callable
        embedder class instance
    """

    ### ------------------------------------ ###

    def __init__(
        self,
        config: dict,
        llm: Any,
        text_embedder: Any
    ) -> None:

        """
        Initializes the AI Agent

        Parameters
        ----------
        config: dict
            Dictionary of configuration parameters
        llm: Callable
            llm class instance for running prompts
        text_embedder: Callable
            embedder class instance
        """

        # Init
        self.llm = llm
        self.text_embedder = text_embedder
        self.max_new_tokens = config['MAX_NEW_TOKENS']
        self.similarity_threshold = config['RAG_SIMILARITY_THRESHOLD']
        self.max_tool_retries = config['MAX_TOOL_RETRIES']
        self.max_clusters = config['MAX_CLUSTERS']

        # Init storage for last produced outputs
        self.output = {
            'summary_report' : '',
            'clustering_stats_plot' : None,
            'clusters_plot' : None
        }

        # Init trace
        self.agent_trace = []
        self.log_trace(trace_message='Agent initialized')

        # Adding LLM-based tools
        self.tools = {}
        for prompt_path in config['PROMPTS']:
            new_tool = self.llm_tool(prompt_path)
            self.add_tool(
                tool_call=new_tool,
                log=True
            )

    ### ------------------------------------ ###
    ### AGENT HISTORY                        ###
    ### ------------------------------------ ###

    def log_trace(self, trace_message: str) -> None:

        trace_timestamp = datetime.now().strftime("%H:%M:%S")
        timestamped_trace_message = f"[{trace_timestamp}] {trace_message}"
        print(timestamped_trace_message)
        self.agent_trace.append(timestamped_trace_message)

    ### ------------------------------------ ###
    ### TOOLS MANAGEMENT                     ###
    ### ------------------------------------ ###

    class empty_tool:

        """
        Mock tool that returns the query when run
        """

        ### -------------------------------- ###

        def __init__(self):

            pass

        ### -------------------------------- ###

        def forward(self, query: str, *args, **kwargs) -> str:

            return query

    ### ------------------------------------ ###

    class llm_tool:

        """
        Class for initializing LLM-based tools

        Parameters
        ----------
        prompt_path : str
            Path to markdown file describing the tool
        """

        ### -------------------------------- ###

        def __init__(self, prompt_path: str) -> None:

            raw = {
                entry.split('\n')[0].strip() : entry[entry.index('\n'):].replace('```', '').strip()
                for entry in open(prompt_path, 'r').read().strip().split('###')
                if len(entry)
            }
            self.tool_type = 'llm'
            self.name = raw['name']
            self.description = raw['description']
            self.inputs = json.loads(raw['expected_inputs'])
            self.prompt = raw['prompt']
            self.output_type = raw['output_type']

        ### -------------------------------- ###

        def forward(self, llm_engine: Callable[..., Any], query: str, max_new_tokens: int=512) -> str:

            # Update prompt
            updated_prompt = self.prompt.replace('[QUERY]', query)

            # Run LLM
            parsed_llm_output = llm_engine.forward(prompt=updated_prompt, max_new_tokens=max_new_tokens)

            return parsed_llm_output

    ### ------------------------------------ ###

    def add_tool(
        self,
        tool_call: Any,
        log: bool=True
    ) -> None:

        """
        Registers a tool to the agent

        Parameters
        ----------
        tool_call : Callable
            A class with the following attributes: name, description, inputs, output_type
            Must also have the following method: forward (runs the tool) 
        log : bool
            Set to True to log the entry
        """

        self.tools[tool_call.name] = tool_call
        if log:
            self.log_trace(trace_message=f'Added tool: {tool_call.name}')
    
    ### ------------------------------------ ###
    ### INPUT/OUTPUT                         ###
    ### ------------------------------------ ###

    def parse_input(self, input: str) -> list[str]:

        """
        Load text from different souces
        """

        # Load text
        supported_files = ['.txt', '.pdf', 'docx']
        if not exists(input) and all([not input.endswith(suffix) for suffix in supported_files]):
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
    ### QUERY PROCESSING                     ###
    ### ------------------------------------ ###

    def process_query(self, query: str='') -> str:

        """
        Query-processing workflow:
            1. Text is imported and split into sentences
            2. Each sentece is enbedded and similarity scores
            3. Sentences are clustered
            4. Each cluster is summarized and keywords are extracted

        Parameters
        ----------
        query : str
            The text to be summarized or a path to a file
        """

        # Return an empty string if the input is an empty string
        if not len(query):
            return ''
        
        # Load data
        self.log_trace(trace_message='Loading text')
        sentences = self.parse_input(query)
        if not len(sentences):
            return ''

        # Init SQLite db
        self.log_trace(trace_message='Initializing sentences db')
        self.init_db()

        # Subset sentences, embed them, and store in database
        self.log_trace(trace_message='Parsing sentences')
        for i in range(0, len(sentences), 100):
            text_sub = sentences[i:i+100]
            new_embeddings = self.embed_text(text_sub)
            all_embeddings = new_embeddings if i == 0 else np.concatenate([all_embeddings, new_embeddings], axis=0)
            self.log_data(table='sentences', column='content', data=text_sub, previous_count=i)
            new_embeddings = [self.numpy_to_blob(ne) for ne in new_embeddings] # For sqlite logging
            self.log_data(table='embeddings', column='embedding', data=new_embeddings, previous_count=i)
        
        # KMeans clustering
        self.log_trace(trace_message='Clustering')
        clusters = self.cluster_sentences(all_embeddings)
        clusters = [int(cl) for cl in clusters] # For sqlite logging
        self.log_data(table='clusters', column='cluster', data=clusters, previous_count=0)

        # Plot clusters distribution
        self.log_trace(trace_message='Plotting clusters distribution')
        self.plot_clusters_distribution()

        # Summarize clusters and extract topic
        self.log_trace(trace_message='Generating summary')
        self.summarize_text()
        self.log_trace(trace_message='Summary completed')

        return self.output['summary_report']
    
    ### ------------------------------------ ###
    ### SENTENCES DB                         ###
    ### ------------------------------------ ###

    def init_db(self) -> None:

        """
        Inits the sentences database
        """
        
        # Define db name
        db_timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        self.db_name = f'sentences_{db_timestamp}.db'

        # Open connection and create cursor
        db_con = sqlite3.connect(self.db_name)
        db_cur = db_con.cursor()
        
        # Create tables
        db_cur.execute('CREATE TABLE sentences(sentence_id INTEGER, content TEXT)')
        db_cur.execute('CREATE TABLE embeddings(sentence_id INTEGER, embedding BLOB)')
        db_cur.execute('CREATE TABLE clusters(sentence_id INTEGER, cluster INTEGER)')
        
        # Commit transactions
        db_con.commit()
        self.memory_count = 0
        
        # Close connection
        db_con.close()

    ### ------------------------------------ ###

    def log_data(self, table: str, column: str, data: Any, previous_count: int=0) -> None:

        """
        Function to log data to a local database
        Assumes the table also has a sentence_id field
        """

        # Open connection and create cursor for main table
        db_con = sqlite3.connect(self.db_name)
        db_cur = db_con.cursor()

        # Add sentences
        insert_statement = f'INSERT INTO {table} (sentence_id, {column}) VALUES (?, ?)'
        new_data = [(dn+previous_count, d) for dn,d in enumerate(data)]
        db_cur.executemany(insert_statement, new_data)

        # Commit transactions
        db_con.commit()
        
        # Close connection
        db_con.close()

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

    ### ------------------------------------ ###
    ### TEXT EMBEDDING                       ###
    ### ------------------------------------ ###

    def embed_text(self, text: list[str]) -> NDArray:

        """
        Function to embed text
        """

        embeddings = self.text_embedder.transform(text)
        embeddings = np.array(embeddings)

        return embeddings
    
    ### ------------------------------------ ###
    ### TEXT CLUSTERING                      ###
    ### ------------------------------------ ###

    def cluster_sentences(self, embeddings: NDArray) -> NDArray:

        """
        KMeans clustering of sentences
        """

        # Finding optimal clustering
        clustering_tests = []
        min_clusters, max_clusters = 2, min(embeddings.shape[0] // 4, self.max_clusters)
        max_clusters = max(max_clusters, min_clusters + 2)
        for k in range(min_clusters, max_clusters + 1):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(embeddings)
            cluster_labels = kmeans.labels_
            inertia = kmeans.inertia_
            silhouette_avg = silhouette_score(embeddings, cluster_labels)
            clustering_tests.append([k, inertia, silhouette_avg])
        clustering_tests = pd.DataFrame(clustering_tests, columns=['k', 'inertia', 'silhouette'])

        # Define optimal k
        optimal_k_inertia =  clustering_tests['k'].values[self.kneedle(clustering_tests['inertia'], False)[0]]
        optimal_k_silhouette = clustering_tests['k'].values[np.argmax(clustering_tests['silhouette'])]
        optimal_k = max([optimal_k_inertia, optimal_k_silhouette])

        # Plotting clustering stats
        fig, axes = plt.subplots(2, 1, sharex=True, figsize=(10, 8))
        for ax,param in zip(axes, ['inertia', 'silhouette']):
            sns.lineplot(clustering_tests, x='k', y=param, ax=ax, marker='o')
            ax.axvline(optimal_k)
        plt.tight_layout()
        plt.close()
        self.output['clustering_stats_plot'] = fig

        # Finalize clusters
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        kmeans.fit(embeddings)
        cluster_labels = kmeans.labels_

        self.log_trace(trace_message=f'  \u2714 Clustering completed. Found {optimal_k} clusters')
        for cl in np.unique(np.sort(cluster_labels)):
            self.log_trace(trace_message=f'    * CL{cl} : {(cluster_labels == cl).sum()} sentences')

        return cluster_labels

    ### ------------------------------------ ###

    @staticmethod
    def kneedle(vector, sort_vector=True):
        
        """
        Kneedle to find threshold cutoff.
        """
        
        # Sort vector
        if sort_vector:
            vector = np.sort(vector)[::-1]
        
        # Find gradient and intercept
        x0, x1 = 0, len(vector)
        y0, y1 = max(vector), min(vector)
        gradient = (y1 - y0) / (x1 - x0)
        intercept = y0
        
        # Compute difference vector
        difference_vector = [(gradient * x + intercept) - y for x,y in enumerate(vector)]
        
        # Find max of difference_vector and define cutoff
        cutoff_index = difference_vector.index(max(difference_vector))
        cutoff_value = vector[cutoff_index]
        
        return cutoff_index, cutoff_value

    ### ------------------------------------ ###

    def plot_clusters_distribution(self) -> None:

        """
        Plots a graphical representatio of where clusters are located within the text
        (if the text were squeezed to one page)
        """

        # Open connection and create cursor
        db_con = sqlite3.connect(self.db_name)
        db_cur = db_con.cursor()

        # Init plot matrix
        x, y = 256, 768
        plot_matrix = np.zeros(x * y) - 1
        tot_spaces = x * y

        # Get total word count
        select_statement = """
        SELECT
            content
        FROM
            sentences
        """
        word_count = np.array(db_cur.execute(select_statement).fetchall()).ravel()
        word_count = ' '.join(word_count)
        word_count = len(word_count.split(' '))

        # Populate plot matrix
        select_statement = """
        SELECT 
            sen.content,
            cl.cluster
        FROM
            sentences AS sen
        JOIN
            clusters AS cl ON sen.sentence_id = cl.sentence_id
        """
        cumulative_fraction = 0
        for sc in db_cur.execute(select_statement).fetchall():
            s, c = sc
            words_n = len(s.split(' '))
            words_fraction = words_n / word_count
            start_idx, end_idx = round(tot_spaces * cumulative_fraction) + 1, round(tot_spaces * (cumulative_fraction + words_fraction) + 1)
            plot_matrix[start_idx : end_idx] = c
            cumulative_fraction += words_fraction
        plot_matrix = plot_matrix.reshape((x, y))

        # Close connection
        db_con.close()

        # Plot a graphical distribution of clusters within the text
        palette = sns.color_palette('hls', plot_matrix.max() + 2, as_cmap=True)
        fig, ax = plt.subplots(1, 1, figsize=(3, 9))
        sns.heatmap(plot_matrix, vmin=0, vmax=plot_matrix.max() + 1, cmap=palette, cbar=False, ax=ax)
        ax.set_xticks([])
        ax.set_yticks([])
        self.output['clusters_plot'] = fig
    
    ### ------------------------------------ ###
    ### SUMMARIZATION                        ###
    ### ------------------------------------ ###

    def summarize_text(self) -> None:
        
        """
        Summarizes text clusters and reports their main topic
        """

        # Open connection and create cursor
        db_con = sqlite3.connect(self.db_name)
        db_cur = db_con.cursor()

        # Get unique clusters
        select_statement = """
        SELECT
            cluster
        FROM
            clusters
        """
        unique_clusters = np.sort(np.unique(np.array(db_cur.execute(select_statement).fetchall()).ravel()))

        # Summarize clusters
        summary_report = ['## TEXT SUMMARY']
        cl_summary_base = '\n---\n### CLUSTER [CLUSTER]\n#### TOPIC:\n[TOPIC]\n#### SUMMARY:\n[SUMMARY]'

        for cl in unique_clusters:

            self.log_trace(trace_message=f'  * Processing cluster {cl}')

            # Extract cluster sentences
            select_statement = f"""
            SELECT 
                sen.content,
                emb.embedding
            FROM
                sentences AS sen
            JOIN
                clusters AS cl ON sen.sentence_id = cl.sentence_id
            JOIN
                embeddings AS emb ON sen.sentence_id = emb.sentence_id
            WHERE
                cl.cluster = {cl}
            """
            cl_data = db_cur.execute(select_statement).fetchall()
            if not len(cl_data):
                continue
            cl_sentences = np.array([cd[0] for cd in cl_data])
            cl_embeddings = np.stack([self.blob_to_numpy(cd[1]) for cd in cl_data], axis=0)
            
            # Filter based on similarity to embeddings centroid
            cl_embeddings_centroid = cl_embeddings.mean(axis=0)
            cl_embeddings_centroid = cl_embeddings_centroid.reshape((1, cl_embeddings_centroid.shape[0]))
            similarity = self.text_embedder.compare(
                query_embedding=cl_embeddings_centroid,
                data_embedding=cl_embeddings,
                max_hits=cl_embeddings.shape[0],
                score_threshold=self.similarity_threshold
            )[0]
            good_sentences_idx = [s[0] for s in similarity]
            cl_sentences = cl_sentences[good_sentences_idx]
            self.log_trace(trace_message=f'    \u2714 Found {len(cl_sentences)} sentences')
            cl_sentences = '\n'.join(cl_sentences)
            
            # Summarize
            tool_tries = 0
            while True:
                try:
                    cl_summary = self.tools['data_summarizer'].forward(llm_engine=self.llm, query=cl_sentences, max_new_tokens=self.max_new_tokens)
                    cl_summary = cl_summary.replace('<summary>', '').replace('</summary>', '')
                    topics_input = cl_summary
                    self.log_trace(trace_message='    \u2714 Summary completed')
                    break
                except:
                    cl_summary, topics_input = '', cl_sentences
                    tool_tries += 1
                    if tool_tries < self.max_tool_retries:
                        self.log_trace(trace_message='    \u2717 Summary failed, execution is retried.')
                        continue
                    else:
                        self.log_trace(trace_message='    \u2717 Summary failed.')
                        break
            
            # Extract topic
            while True:
                try:
                    cl_topic = self.tools['topic_extractor'].forward(llm_engine=self.llm, query=topics_input, max_new_tokens=self.max_new_tokens)
                    self.log_trace(trace_message='    \u2714 Topic extraction completed')
                    break
                except:
                    cl_topic = ''
                    tool_tries += 1
                    if tool_tries < self.max_tool_retries:
                        self.log_trace(trace_message='    \u2717 Topic extraction failed, execution is retried.')
                        continue
                    else:
                        self.log_trace(trace_message='    \u2717 Topic extraction failed.')
                        break
            
            # Assemble
            cl_final = cl_summary_base.replace('[CLUSTER]', str(cl)).replace('[TOPIC]', cl_topic).replace('[SUMMARY]', cl_summary)
            summary_report.append(cl_final)
        summary_report = '\n'.join(summary_report)

        # Close connection
        db_con.close()

        # Log/export summary
        self.output['summary_report'] = summary_report
        with open(self.db_name.replace('db', 'md'), 'w') as summary_out:
            summary_out.write(summary_report)
