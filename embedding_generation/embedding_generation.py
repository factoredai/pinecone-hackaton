import os 

import hydra
from omegaconf import DictConfig
from utils import func
import torch
from dotenv import load_dotenv
import pinecone
from tqdm.auto import tqdm
import sentence_transformers

load_dotenv()

@hydra.main(version_base=None, config_path="configs/", config_name="config")
def main(config: DictConfig):
    dataset = hydra.utils.instantiate(config.dataset.source, _recursive_=False)
    
    if config.dataset.dropna:
        dataset.dropna(axis=0, inplace=True)
      
    dataset.abstract = dataset.abstract.apply(func.remove_html_tags)
    
    dataset.abstract = dataset.abstract.apply(func.process_text)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    model = sentence_transformers.SentenceTransformer('all-MiniLM-L6-v2', device=device) #hydra.utils.get_class(config.embed_model.model)(config.embed_model.source, device=device)
    
    # get api key from app.pinecone.io
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
    # find your environment next to the api key in pinecone console
    PINECONE_ENV = os.getenv('PINECONE_ENVIRONMENT')
    
    print('INITIALIZING INDEX')
    
    pinecone.init(
        api_key=PINECONE_API_KEY,
        environment=PINECONE_ENV
    )
        
    if config.index.index_name not in pinecone.list_indexes():
        print('CREATING NEW INDEX')
        pinecone.create_index(
            name=config.index.index_name,
            dimension=model.get_sentence_embedding_dimension(),
            metric='cosine'
        )
        print('INDEX CREATED')
    
    index = pinecone.Index(config.index.index_name)
    
    # CREATES LIST OF TEXTS TO EMBED
        
    abstracts = []

    for record in dataset.abstract:
        abstracts.append(record)

    abstracts = list(set(abstracts))
    
    # EMBEDDING GENERATION
    batch_size = config.embed_model.batch_size
    
    print('UPSERTTING STARTED')
    for i in tqdm(range(0, len(abstracts), batch_size)):
        
        i_end = min(i+batch_size, len(abstracts))
        
        ids = [str(x) for x in range(i, i_end)]
        
        metadatas = [{'text': text} for text in abstracts[i:i_end]]
        
        xc = model.encode(abstracts[i:i_end]).tolist()
        
        records = zip(ids, xc, metadatas)
       
        index.upsert(vectors=records)

    print(index.describe_index_stats())
    
    
if __name__ == "__main__":
    main()