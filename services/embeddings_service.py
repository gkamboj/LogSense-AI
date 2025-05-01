from services import common_service as cs
from services import documents_service as ds
from services import hana_service as hs
from services.decorators import timing


def get_embeddings_model():
    service = cs.get_active_ai_service()
    return service.get_embeddings() if service else None


@timing(print_args=True)
def vectorize_text(text):
    return get_embeddings_model().embed_query(text)


def generate_embeddings_for_list(chunks_with_metadata):
    for chunk in chunks_with_metadata:
        embedding = vectorize_text(chunk['text'])
        chunk['embedding'] = embedding
    return chunks_with_metadata


def insert_embeddings_for_document(doc_id, text):
    chunks_with_metadata = ds.split_document_into_chunks_with_metadata(text)
    chunks_with_embeddings = generate_embeddings_for_list(chunks_with_metadata)
    hs.store_embeddings_in_hana(doc_id, chunks_with_embeddings)

