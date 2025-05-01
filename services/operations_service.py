import importlib
import json
import os
import traceback
from collections import defaultdict

import pandas as pd
import streamlit as st
from langchain_community.document_loaders.directory import DirectoryLoader
from langchain_community.document_loaders.merge import MergedDataLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from streamlit.runtime.uploaded_file_manager import UploadedFile

import services.embeddings_service as es
from config.configuration import configs
from constants import app_constants as ac
from services import file_service as fs, hana_service as hs, sharepoint_service as ss
from services.decorators import timing


@st.cache_resource(show_spinner=configs['streamlit.spinner.messages.get_processed_data_from_text'])
def get_processed_data_from_text(text):
    text_splitter = get_text_splitter()
    chunks = text_splitter.split_text(text)
    return FAISS.from_texts(chunks, embedding=es.get_embeddings_model())


@st.cache_resource(show_spinner=configs['streamlit.spinner.messages.get_processed_data_from_loader'])
def get_processed_data_from_loader(_merged_data_loader: MergedDataLoader):
    documents = _merged_data_loader.load()
    text_splitter = get_text_splitter()
    split_docs = text_splitter.split_documents(documents)
    return FAISS.from_documents(split_docs, embedding=es.get_embeddings_model())


@st.cache_resource(show_spinner=configs['streamlit.spinner.messages.get_loaders'])
def get_loaders(tenant=ac.TENANT_LOGSENSE):
    loaders = []
    if tenant == ac.TENANT_LOGSENSE:
        for dataset_config in configs['logsense.datasets']:
            loader_cls_name = dataset_config['loaderClass']
            module_name, class_name = loader_cls_name.rsplit('.', 1)
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                print(f"Error: Module '{module_name}' not found.")
                continue
            loader_cls = getattr(module, class_name, None)
            if loader_cls is None:
                print(f"Error: Class '{class_name}' not found in module '{module_name}'.")
                continue
            glob_pattern = dataset_config['glob']
            # for file_to_ignore in dataset_config.get('filesToIgnore', []):
            #     glob_pattern += '!' + file_to_ignore
            loader = DirectoryLoader(
                os.path.join(ac.ROOT_PATH, dataset_config['path']),
                glob=glob_pattern,
                loader_cls=loader_cls
            )
            loaders.append(loader)
    return loaders


def get_text_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len
    )


def parse_response(response):
    parts = []
    json_start = response.find("{")
    json_end = response.rfind("}") + 1
    if json_start != -1 and json_end != 0:
        parts.append(response[:json_start])
        json_string = response[json_start:json_end]
        parts.append(json.loads(json_string))
        parts.append(response[json_end:])
    else:
        parts = [response]
    return parts


@st.cache_data(show_spinner=configs['streamlit.spinner.messages.get_prompt_result_from_context'])
@timing(print_args=False)
def get_prompt_result_from_context(combined_prompt, _chain=None, _agent=None):
    answer = None
    if _chain:
        result = _chain.invoke({'question': str(combined_prompt),
                                'chat_history': [(message['role'], message['content']) for message in
                                                 st.session_state.messages]})
        print(f'Result: {json.dumps(result)}')
        answer = result['answer']
    elif _agent:
        result = _agent.invoke(str(combined_prompt))
        print(f'Result: {json.dumps(result)}')
        answer = result['output']
    print(f'Prompt response from LLM: {str(answer)}')
    return answer


@st.cache_data(show_spinner=configs['streamlit.spinner.messages.get_prompt_result'])
def get_prompt_result(_llm, prompt):
    return _llm.invoke(prompt).content


def process_db_embeddings_results(results):
    pass


@st.cache_data(show_spinner=configs['streamlit.spinner.messages.get_relevant_context'])
def get_relevant_context(query):
    query_embedding = es.vectorize_text(query)
    chunks_rows = hs.retrieve_relevant_chunks(query_embedding)
    section_priorities = {section['section']: section['priority'] for section in
                          configs['hana.embedding.contextSections']}
    max_chars = int(configs['sapAI.openai.maxTokens'] * 2.5)
    sorted_chunks = sorted(
        [(document_id, url, section, text, section_priorities.get(section))
         for document_id, url, section, text in chunks_rows],
        key=lambda x: x[4]
    )
    selected_chunks = []
    current_length = 0
    for document_id, url, section, text, _ in sorted_chunks:
        if current_length + len(text) <= max_chars:
            selected_chunks.append((document_id, url, section, text))
            current_length += len(text)
        else:
            break
    merged_chunks = defaultdict(str)
    for document_id, url, section, text in selected_chunks:
        key = (document_id, url, section)
        merged_chunks[key] += text + ' '
    formatted_context = [
        {
            "document": {
              "url": url,
              "id": document_id
            },
            "section": section,
            "text": text.strip()
        }
        for (document_id, url, section), text in merged_chunks.items()
    ]
    # context = "\n\n".join([f"Document ID: {chunk[0]}, Section: {chunk[1]}\n{chunk[2]}" for chunk in chunks])
    return formatted_context

@st.cache_data(show_spinner=configs['streamlit.spinner.messages.handle_file_upload'])
def handle_file_upload(file: UploadedFile):
    success, message = True, None
    try:
        file_bytes = file.read()
        if configs['sharepoint.upload']:
            upload_response = ss.upload_file_to_sharepoint(file_bytes, configs['sharepoint.uploadFolder'],
                                                       file.name.replace(' ', ''))
            document_id = fs.shorten_file_name(upload_response['id'])
            url = upload_response['url']
        else:
            print('Sharepoint upload is not active, using dummy URL to upload')
            document_id = fs.shorten_file_name(file.name.replace(' ', ''))
            url = 'www.example.com'
        file_text = fs.extract_text_from_bytes(file_bytes)
        print(f'file text: {file_text}')
        if not hs.check_kba_exists(document_id):
            hs.insert_kba(
                document_id,
                url,
                pd.to_datetime(pd.Timestamp.now()),
                None,
                1,
                None,
                None,
                None
            )
            es.insert_embeddings_for_document(document_id, file_text)
        else:
            print(f'Document with id {document_id} already present, not uploading again')
    except Exception as e:
        success = False
        message = str(e)
        print(f'Error processing file upload: ')
        traceback.print_exc()
    return {
        'success': success,
        'message': message
    }