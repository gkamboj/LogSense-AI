import os
from io import BytesIO

import pdfplumber
from pdfplumber import PDF
from pypdf import PdfReader
from streamlit.runtime.uploaded_file_manager import UploadedFile

from config.configuration import configs
from constants import app_constants as ac


def get_file_extension(file):
    if isinstance(file, UploadedFile):
        filename = file.name
    else:
        filename = file.filename
    _, extension = os.path.splitext(filename)
    return extension.lower().lstrip('.')


def extract_text_from_pdf_path(pdf_path):
    if configs['file.pdf.lib'] == ac.LIB_PDFPLUMBER:
        with pdfplumber.open(pdf_path) as pdf:
            text = extract_text_from_pdf(pdf)
    else:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            text = extract_text_from_reader(pdf_reader)
    return text


def extract_text_from_bytes(file_bytes):
    if configs['file.pdf.lib'] == ac.LIB_PDFPLUMBER:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            text = extract_text_from_pdf(pdf)
    else:
        file = BytesIO(file_bytes)
        pdf_reader = PdfReader(file)
        text = extract_text_from_reader(pdf_reader)
    return text


def extract_text_from_pdf(pdf:PDF):
    text = ""
    for page in pdf.pages:
        text += page.extract_text()
    return text


def extract_text_from_reader(pdf_reader):
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


def shorten_file_name(file_name):
    # KBAs table document_id field is of max 20 chars, so shortening the name to 17 characters, with buffer of 3 characters
    name, ext = os.path.splitext(file_name)
    name = name[:17]
    return name