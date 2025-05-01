import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.configuration import configs


def identify_kba_sections(text):
    sections = []
    current_section = 'Header'
    section_pattern = r'^(Attributes|Cause|Environment|Keywords|Other Terms|Products|Reason and Prerequisites|Reproducing the Issue|Resolution|See Also|References|This document refers to|Symptom)$'
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if re.match(section_pattern, line):
            current_section = line
            line += ' : '
        sections.append((line, current_section))
    return sections


def split_document_into_chunks_with_metadata(document_text):
    sections = identify_kba_sections(document_text)
    chunks_with_metadata = []
    current_chunk = sections[0][0]
    current_section = sections[0][1]
    splitter = RecursiveCharacterTextSplitter(
        separators=['\n\n', '\n', '. ', ' ', ''],
        chunk_size=configs['hana.embedding.chunkSize'],
        chunk_overlap=50,
        length_function=len
    )

    for line, section in sections[1:]:
        if '{[user]}' in line:
            raise Exception('Invalid document, template not filled')
        if section != current_section:
            chunks = splitter.split_text(current_chunk)
            for chunk in chunks:
                chunks_with_metadata.append({
                    'text': chunk,
                    'metadata': {
                        'section': current_section
                    }
                })
            current_chunk = line
            current_section = section
        else:
            current_chunk += line + '\n'
    chunks_with_metadata.append({
        'text': ''.join(current_chunk),
        'metadata': {
            'section': current_section
        }
    })
    return chunks_with_metadata
