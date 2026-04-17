#!/usr/bin/env python3

### IMPORTS -------------------------------- ###

import requests

### CLASSES AND FUNCTIONS ------------------ ###

class wikipedia_search:
    
    """
    Class for retrieving extracts from Wikipedia using a set of keywords
    """
    
    # Variables for guiding LMM choice
    tool_type = "function"
    name = 'wikipedia_search'
    description = """
    This is a tool that downloads extracts from Wikipedia and is best used to retrieve general knowledge about a subject
    """
    inputs = {
        'query': {
            'type': 'str',
            'description': 'String of space-separated keywords'
        }
    }
    output_type = 'str'
    
    # Main class variables
    base_url = 'https://en.wikipedia.org/w/api.php'
    headers = {'User-Agent': 'wikipedia_search (marco.marchetti.90@gmail.com) [Python-requests]'}
    article_search_params = {
        'action': 'query',
        'prop': 'info',
        'format': 'json',
        'generator': 'search',
        'gsrlimit': 5
    }
    extraction_params = {
        'action': 'query',
        'prop': 'extracts',
        'format': 'json',
        'exsentences': 10,
        'explaintext': 'true'
    }
    
    ### ------------------------------------ ###
    
    def __init__(self):
        
        self.is_initialized = False # For compatibility with smolagents
    
    ### ------------------------------------ ###
    
    def forward(self, query: str) -> str:
        
        # Remove spaces and commas, then convert to lowercase
        query = query.replace(',', ' ').replace(' ', '+').lower()

        # Remove repeated keywords
        query = '+'.join(list(set(query.split('+'))))
        
        # Retrieve articles' IDs
        page_ids = self.get_articles(query)
        
        # Retrieve extracts
        extracts = [self.get_extract(pid) for pid in page_ids]
        extracts = '\n\n'.join(extracts)
        
        return extracts

    ### ------------------------------------ ###
    
    def get_articles(self, query: str) -> list:
        
        params = self.article_search_params.copy()
        params['gsrsearch'] = query
        articles_search_response = requests.get(url=self.base_url, params=params, headers=self.headers)
        if articles_search_response.status_code == 200:
            try:
                articles = articles_search_response.json()['query']['pages']
                page_ids = [a['pageid'] for a in articles.values()]
                return page_ids
            except:
                return []
        else:
            return []
        
    ### ------------------------------------ ###
    
    def get_extract(self, pid: str) -> str:
        
        params = self.extraction_params.copy()
        params['pageids'] = pid
        extraction_response = requests.get(self.base_url, params, headers=self.headers)
        if extraction_response.status_code == 200:
            extract = extraction_response.json()['query']['pages'][str(pid)]['extract']
            extract = extract.replace('\n\n', '').replace('\n', ' ')
            return extract
        else:
            return ''

### ---------------------------------------- ###

if __name__ == '__main__':
    
    query = 'cancer EGFR'
    extracts = wikipedia_search().forward(query)
    with open('test_wikipedia_extracts.txt', 'w') as out:
        out.write(extracts)
