import os
from configparser import ConfigParser

import chainlit as cl
import pinecone
from dotenv import load_dotenv
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import CohereEmbeddings
from langchain.embeddings.base import Embeddings
from langchain.embeddings.huggingface import (
    HuggingFaceEmbeddings,
    HuggingFaceInstructEmbeddings,
)
from langchain.memory import ConversationBufferMemory
from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.vectorstores.pinecone import Pinecone

from prompts import system_template

load_dotenv()
pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINECONE_ENV"))
openai_api_key = os.environ["OPENAI_API_KEY"]

messages = [
    SystemMessagePromptTemplate.from_template(system_template),
    HumanMessagePromptTemplate.from_template("{question}"),
]
prompt = ChatPromptTemplate.from_messages(messages)
chain_type_kwargs = {"prompt": prompt}


def initialize_embeddings():
    cfg = ConfigParser()
    cfg.read("./frontend/config.conf")

    if cfg.get("embeddings", "type") == "instruct":
        embeddings = HuggingFaceInstructEmbeddings(model_name=cfg.get("instruct_embeddings", "model"))
    elif cfg.get("embeddings", "type") == "sentence_transformers":
        embeddings = HuggingFaceEmbeddings(model_name=cfg.get("sentence_transformers_embeddings", "model"))
    elif cfg.get("embeddings", "type") == "cohere":
        print("Using Cohere embeddings")
        embeddings = CohereEmbeddings(
            cohere_api_key=os.environ.get("COHERE_API_KEY"),
            model=cfg.get("cohere_embeddings", "model"),
            truncate=cfg.get("cohere_embeddings", "truncate"),
        )
    else:
        raise NotImplementedError()
    return embeddings


@cl.action_callback("action_button")
async def on_action(action):
    actions = cl.user_session.get("actions")
    cl.user_session.set("task", action.value)
    if action.value == "prior_art":
        await cl.Message(content="You chose prior art search. What are you looking for?", author="Librarian").send()
        cl.user_session.set("botname", "Librarian")
    elif action.value == "draft_patent":
        await cl.Message(content="You chose to draft a patent. What is your invention?", author="Drafter").send()
        cl.user_session.set("botname", "Drafter")
    elif action.value == "compare_patent":
        await cl.Message(content="You chose to compare your patent. What is your patent?", author="Curator").send()
        cl.user_session.set("botname", "Curator")

    for action in actions:
        await action.remove()
    # Optionally remove the action button from the chatbot user interface
    # await action.remove()


@cl.on_chat_start
async def start():
    # Sending an action button within a chatbot message
    actions = [
        cl.Action(name="action_button", value="prior_art", description="Click me!", label="Prior art search"),
        cl.Action(name="action_button", value="draft_patent", description="Click me!", label="Draft your patent"),
        cl.Action(name="action_button", value="compare_patent", description="Click me!", label="Compare your patent"),
    ]
    cl.user_session.set("actions", actions)

    await cl.Message(content="How can PatentBot help you today?", actions=actions).send()


@cl.on_message
async def main(message: str):
    # Your custom logic goes here...
    task = cl.user_session.get("task")

    embeddings = initialize_embeddings()
    chain = await get_model(task, embeddings)

    res = await cl.make_async(chain)(message, callbacks=[cl.ChainlitCallbackHandler()])

    msg = cl.Message(content="", author=cl.user_session.get("botname"))
    for token in res["answer"].split(" "):
        await cl.sleep(0.1)
        await msg.stream_token(token + " ")
    await msg.send()


async def get_model(task: str, embeddings: Embeddings):
    cfg = ConfigParser()
    cfg.read("./frontend/config.conf")

    if cl.user_session.get("chain"):
        return cl.user_session.get("chain")

    docsearch = await cl.make_async(Pinecone.from_existing_index)(
        index_name=cfg.get("pinecone", "index_name"),
        embedding=embeddings,
    )

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    chain = ConversationalRetrievalChain.from_llm(
        ChatOpenAI(temperature=0, streaming=True, openai_api_key=openai_api_key),
        chain_type="stuff",
        retriever=docsearch.as_retriever(),
        memory=memory,
    )
    cl.user_session.set("chain", chain)
    return chain
