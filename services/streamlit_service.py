import io
import os

import streamlit
from PIL import Image

from config.configuration import configs
from constants import app_constants as ac
from services import file_service as fs


def get_image_bytes(image_path):
    with Image.open(image_path) as img:
        extension = fs.get_file_extension(img)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format=extension.upper())
        img_bytes = img_bytes.getvalue()
    return img_bytes


@streamlit.cache_data(show_spinner=configs['streamlit.spinner.messages.get_assistant_avatar'])
def get_assistant_avatar(tenant=ac.TENANT_LOGSENSE):
    image_path = get_assistant_icon_path(tenant)
    return get_image_bytes(image_path)


@streamlit.cache_data(show_spinner=configs['streamlit.spinner.messages.get_user_avatar'])
def get_user_avatar(tenant=ac.TENANT_LOGSENSE):
    image_path = os.path.join(ac.ROOT_PATH, 'resources', tenant, 'st_user.png')
    return get_image_bytes(image_path)


@streamlit.cache_data(show_spinner=configs['streamlit.spinner.messages.get_avatar_for_role'])
def get_avatar_for_role(role, tenant=ac.TENANT_LOGSENSE):
    return get_user_avatar(tenant) if role == 'user' else get_assistant_avatar(tenant)


def set_static_content(st, query_type, tenant=ac.TENANT_LOGSENSE):
    # st.image('resources/st_banner.png', use_column_width=True)
    # st.title('LogSense AI Assistant')
    left_co, cent_co, last_co = st.columns(3)
    html_string = ''
    if ac.QUERY_TYPE_CHAT == query_type:
        html_string = '''
            <h3>Welcome to LogSense AI. How can I assist you?</h3>
            '''
    with cent_co:
        st.image(get_assistant_icon_path(tenant), width=100)
    st.markdown(html_string, unsafe_allow_html=True)


def set_page_config(st, tenant=ac.TENANT_LOGSENSE):
    page_title = configs.get(f'{tenant}.pageTitle', tenant)
    st.set_page_config(page_title=page_title,
                       page_icon=get_assistant_avatar(tenant))


def get_assistant_icon_path(tenant):
    return os.path.join(ac.ROOT_PATH, 'resources', tenant, 'st_assistant.png')


def get_selection_from_sidebar(st: streamlit, message, values):
    return st.sidebar.selectbox(message, values)


@streamlit.cache_data(show_spinner=configs['streamlit.spinner.messages.write_response'])
def write_response(st, response, documents=None, prefix=None):
    if prefix:
        st.markdown(prefix)
    st.markdown(response)
    if documents:
        links = ', '.join([f"[{doc[0]}]({doc[1]})" for doc in documents])
        st.markdown(f'Check out these for more information: {links}')
