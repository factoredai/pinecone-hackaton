import os

import pinecone

class Connection:
    def __init__(self):
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_env = os.getenv("PINECONE_ENV")
        self.index_name = "second-test"
    
    def connect(self):
        pinecone.init(api_key=os.getenv("PINECONE_API_KEY"),environment=os.getenv("PINECONE_ENV"))
        self.pinecone_index = pinecone.Index(name=self.index_name)
    
