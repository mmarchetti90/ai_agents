#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import requests

### CLASSES AND FUNCTIONS ------------------ ###

class pubmed_search:
    
    """
    Class for retrieving abstracts from PubMed using a set of keywords
    """
    
    # Variables for guiding LMM choice
    tool_type = "function"
    name = 'pubmed_literature_search'
    description = """
    This is a tool that downloads scientific research abtracts from PubMed and is best used to find up-to-date reseach data
    """
    inputs = {
        'query': {
            'type': 'str',
            'description': 'String of space-separated keywords'
        }
    }
    output_type = 'str'
    
    # Main class variables
    base_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils'
    esearch_extension = 'esearch.fcgi?'
    efetch_extension = 'efetch.fcgi?'
    db = 'pubmed'
    retmax = 10
    search_retmode = 'json'
    fetch_retmode = 'text'
    fetch_rettype = 'abstract'
    
    ### ------------------------------------ ###
    
    def __init__(self):
        
        self.is_initialized = False # For compatibility with smolagents
    
    ### ------------------------------------ ###
    
    def forward(self, query: str) -> str:

        # Remove spaces and commas, then convert to lowercase
        query = query.replace(',', ' ').replace(' ', '+').lower()

        # Remove repeated keywords
        query = '+'.join(list(set(query.split('+'))))
        
        # Retrieve PMIDs
        pmids = self.get_pmids(query)
        
        # Retrieve abstracts
        abstracts = [self.get_abstract(pmid) for pmid in pmids]
        abstracts = '\n\n'.join(abstracts)
        
        return abstracts

    ### ------------------------------------ ###
    
    def get_pmids(self, query: str) -> list:
        
        full_url = f'{self.base_url}/{self.esearch_extension}db={self.db}&retmode={self.search_retmode}&retmax={self.retmax}&term={query}'
        search_response = requests.get(full_url)
        if search_response.status_code == 200:
            try:
                search_data = search_response.json()
                pmids = search_data['esearchresult']['idlist']
                return pmids
            except:
                return []
        else:
            return []
        
    ### ------------------------------------ ###
    
    def get_abstract(self, pmid: str) -> str:
        
        full_url = f'{self.base_url}/{self.efetch_extension}db={self.db}&id={pmid}&retmode={self.fetch_retmode}&rettype={self.fetch_rettype}'
        fetch_response = requests.get(full_url)
        if fetch_response.status_code == 200:
            fetch_data = fetch_response.text.split('\n\n')
            journal_info, title, authors, authors_info, *abstract = fetch_data
            journal_info = journal_info.replace('1. ', '')
            pm_link = 'https://pubmed.ncbi.nlm.nih.gov/{pmid}/'
            citation = f'{journal_info} "{title}" {pm_link}'
            abstract = [a.replace(' \n', '').replace('\n', ' ') for a in abstract
                        if not a.startswith('DOI')
                        and not a.startswith('PMID')
                        and not a.startswith('Conflict of interest statement:')
                        and not a.startswith('Competing interests:')
                        and not a.startswith('Trial registration:')
                        and not a.startswith('©')]
            #abstract = citation + '\n' + '\n'.join(abstract)
            abstract = '\n'.join(abstract)
            return abstract
        else:
            return ''
        
### ---------------------------------------- ###

if __name__ == '__main__':
    
    query = 'role of EGFR in breast cancer'
    abstracts = pubmed_search().forward(query)
    with open('test_pubmed_abstracts.txt', 'w') as out:
        out.write(abstracts)
