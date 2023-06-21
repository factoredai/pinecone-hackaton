import re
import json
import pandas as pd
from langchain.embeddings.huggingface import HuggingFaceInstructEmbeddings
from langchain.vectorstores.pinecone import Pinecone


def create_embeddings_from_jsonlines(path:str, text_column: str, index_name: str):
    data=  []
    with open(path) as f:
        for line in f:
            data.append(json.loads(line))
    df = pd.DataFrame.from_dict(data)
    all_text = df[text_column].tolist()
    parsed = []
    for text in all_text:
        try:
            parsed.append(re.split('num="0000">', text)[1].split('</p>')[0])
        except:
            continue
    embeddings_model = HuggingFaceInstructEmbeddings()
    vectordb = Pinecone.from_texts(parsed, embeddings_model, index_name = index_name)
    return vectordb.as_retriever()

    

