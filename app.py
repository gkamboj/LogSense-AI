import json
import traceback
from collections import defaultdict

import streamlit as st
from langchain.prompts import PromptTemplate

from config.configuration import configs
from constants import app_constants as ac
from services import common_service as cs
from services import mongo_service as ms
from services import operations_service as ops
from services import streamlit_service as sts

VAL_NO_CONTEXT = '[NO_CONTEXT]'
# PREFIX_NO_CONTEXT = 'Unable to answer from shared context, response from GPT-4:\n'
PREFIX_NO_CONTEXT = ''

STATIC_PROMPTS = {
    'with_context_chat': f'''Use strictly the shared context to answer the shared query, don't use anything from outside of it. If you are cannot find the answer from the given context,\
start your response with '{VAL_NO_CONTEXT}'. Query: \n''',
    'validate_response': '''Check if below statement is apologetic, gives impression that responder is unable to answer the query asked to it or responder does not know what was asked to it.\
Respond in 'YES' or 'NO' only. Statement: \n''',
    'with_context_logfile': '''Use strictly the shared context to analyse the the shared logs, don't use anything from outside of context. If you are cannot find \
the answer from the given context, just respond with the message: 'Sorry, I am unable to answer it from the shared context'. Logs:\n''',
    'without_context': f'''Answer the shared query with respect to SAP Commerce Cloud: '''
}

UPLOAD_FOLDER = '/Documents/ArtificialIntelligence/LogSenseAI/dataset/UPLOADS'  # Ensure this exists
ALLOWED_EXTENSIONS = {'pdf', 'log', 'txt'}

def get_static_prompt(prompt_type):
    return STATIC_PROMPTS[prompt_type]


@st.cache_data(show_spinner=configs['streamlit.spinner.messages.is_success_response'])
def is_success_response(response):
    return False if response.startswith(VAL_NO_CONTEXT) else True
    # llm = cs.get_llm()
    # validate_response_prompt = get_static_prompt('validate_response') + response
    # print(f'Validate response promot: {validate_response_prompt}')
    # llm_response = llm.invoke(validate_response_prompt).content
    # print(f'Response of validate response call: {llm_response}')
    # if isinstance(llm_response, str) and llm_response.lower() == 'yes':
    #     return False
    # else:
    #     return True


@st.cache_data(show_spinner=configs['streamlit.spinner.messages.get_allowed_query_types'])
def get_allowed_query_types():
    types = defaultdict(list)
    for query_type_config in configs['logsense.queryTypes']:
        types[query_type_config['name']] = query_type_config
    return types


def initialise_state_variables(query_type):
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if query_type != st.session_state.get('last_selected_query_type', None):
        st.session_state.messages = []
        st.session_state.last_selected_query_type = query_type
        st.session_state.logs = []
        st.session_state.last_file_id = None


def handle_user_input(prompt, _llm, _qa, user_avatar, assistant_avatar, query_type: str):
    context = ops.get_relevant_context(prompt)
    combined_prompt = get_static_prompt(f"with_context_{query_type.replace(' ', '').lower()}") + prompt
    print(f'Combined prompt: {combined_prompt}')
    st.session_state.messages.append({'role': 'user', 'content': prompt})

    with st.chat_message('user', avatar=user_avatar):
        st.markdown(prompt)

    with st.chat_message('assistant', avatar=assistant_avatar):
        # response = ops.get_prompt_result_from_context(combined_prompt, _chain=_qa)
        documents, prefix = [], None
        try:
            response = _qa.invoke({
                "context": context,
                "question": combined_prompt
            }).content
            print(f'Result: {response}')
            if not is_success_response(response):
                prefix = PREFIX_NO_CONTEXT
                if configs['app.allowWithoutContextResults']:
                    prompt = get_static_prompt('without_context') + prompt
                    response = ops.get_prompt_result(_llm, prompt)
            else:
                documents = set((doc['document']['id'], doc['document']['url']) for doc in context)
        except Exception:
            prompt = get_static_prompt('without_context') + prompt
            response = ops.get_prompt_result(_llm, prompt)
            print("Error through LLM chain: ")
            traceback.print_exc()
        sts.write_response(st, response, documents=documents, prefix=prefix)
    print(f'Response: {json.dumps(response)}')
    st.session_state.messages.append(
        {'role': 'assistant', 'content': response, 'documents': documents, 'prefix': prefix})


def run_streamlit_app():
    sts.set_page_config(st)

    query_types = get_allowed_query_types()
    query_type = sts.get_selection_from_sidebar(st, 'Select interaction type', query_types.keys())
    initialise_state_variables(query_type)

    sts.set_static_content(st, query_type)
    assistant_avatar = sts.get_assistant_avatar()
    user_avatar = sts.get_user_avatar()

    llm = cs.get_llm()
    if not llm:
        print('NO ACTIVE LLM INSTANCE AVAILABLE')
        return

    # vectorstore = ops.get_processed_data_from_loader(MergedDataLoader(loaders=ops.get_loaders()))
    # qa = ConversationalRetrievalChain.from_llm(llm, vectorstore.as_retriever())
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="{context}\n\nQuestion: {question}\nAnswer:"
    )
    qa = prompt | llm

    if query_types[query_type]['fileUpload']:
        query_type_config = query_types[query_type]
        allowed_extensions = query_type_config['extensions']
        # Separate handling for LOG FILE and EMBEDDING FILE
        file = st.file_uploader(query_type_config['message'], type=allowed_extensions)
        if query_type == ac.QUERY_TYPE_LOG_FILE:
            if file:
                if file.file_id != st.session_state.get('last_file_id', None):
                    st.session_state.messages = []
                    st.session_state.logs = ms.find_logs_for_file(file.file_id)
                    st.session_state.last_file_id = file.file_id
                    st.rerun()

        elif query_type == ac.QUERY_TYPE_RCA_UPLOAD:
            if file:
                result = ops.handle_file_upload(file)
                if result['success']:
                    st.success(f"Embeddings stored successfully for file: {file.name}")
                else:
                    st.error(f"Failed to process the embeddings due to error: {result['message']}")

    for message in st.session_state.messages:
        role = message['role']
        documents = message['documents'] if 'documents' in message else []
        prefix = message['prefix'] if 'prefix' in message else None
        with st.chat_message(role, avatar=sts.get_avatar_for_role(role)):
            sts.write_response(st, message['content'], documents=documents, prefix=prefix)

    if ac.QUERY_TYPE_LOG_FILE == query_type:
        if st.session_state.get('last_file_id', None):
            selected_log = st.selectbox(
                "Which log do you want to analyse?",
                [log['message'] + ' : ' + log['stackTrace'] for log in st.session_state.get('logs', [])],
                index=None,
                placeholder="Select the error log",
                key=f"log_selector_{len(st.session_state.messages)}"
            )

            def click_button():
                st.session_state.button_clicked = True

            if selected_log and st.button("Analyze Log",
                                          key=f"analyze_button_{len(st.session_state.messages)}",
                                          on_click=click_button,
                                          disabled=st.session_state.get('button_clicked', False)):
                handle_user_input(selected_log, llm, qa, user_avatar, assistant_avatar, query_type)
                st.session_state.button_clicked = False
                st.rerun()

    elif ac.QUERY_TYPE_CHAT == query_type:
        if prompt := st.chat_input('Enter a prompt here for LogSense'):
            handle_user_input(prompt, llm, qa, user_avatar, assistant_avatar, query_type)


run_streamlit_app()
