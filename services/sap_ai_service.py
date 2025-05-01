import os

import streamlit as st
from gen_ai_hub.proxy.langchain import ChatOpenAI
from gen_ai_hub.proxy.langchain import init_embedding_model

from config.configuration import configs


def set_proxy_config():
    os.environ['AICORE_AUTH_URL'] = configs['sapAI.configs.authUrl'] + "/oauth/token"
    os.environ['AICORE_CLIENT_ID'] = configs['sapAI.configs.clientId']
    os.environ['AICORE_CLIENT_SECRET'] = configs['sapAI.configs.clientSecret']
    os.environ['AICORE_BASE_URL'] = configs['sapAI.configs.baseUrl'] + "/v2"
    os.environ['AICORE_RESOURCE_GROUP'] = configs['sapAI.configs.resourceGroup']


@st.cache_resource(show_spinner=configs['streamlit.spinner.messages.get_llm'])
def get_llm():
    return get_openai_llm()


def get_openai_llm():
    set_proxy_config()
    return ChatOpenAI(
        temperature=configs['sapAI.configs.temperature'],
        proxy_model_name=configs['sapAI.openai.model']
    )


@st.cache_resource(show_spinner=configs['streamlit.spinner.messages.get_embeddings'])
def get_embeddings():
    set_proxy_config()
    embeddings = init_embedding_model(configs['sapAI.configs.embeddings.model'])
    return embeddings
