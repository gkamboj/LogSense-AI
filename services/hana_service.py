from contextlib import closing

from hdbcli import dbapi

from config.configuration import configs
from services.decorators import timing

SCHEMA = configs['hana.schema']


def get_hana_connection():
    return dbapi.connect(
        address=configs['hana.address'],
        port=configs['hana.port'],
        user=configs['hana.user'],
        password=configs['hana.password'],
        encrypt=True,
        sslValidateCertificate=True
    )


@timing(print_args=False)
def retrieve_relevant_chunks(query_embedding, top_k=3):
    connection = get_hana_connection()
    cursor = connection.cursor()
    allowed_sections = [contextSec['section'] for contextSec in configs['hana.embedding.contextSections']]
    sections_placeholder = ', '.join(['?'] * len(allowed_sections))
    combined_query = f'''
            WITH RankedDocuments AS (
                SELECT document_id,
                       ROW_NUMBER() OVER (ORDER BY COSINE_SIMILARITY(embedding, TO_REAL_VECTOR(?)) DESC) AS rank
                FROM {SCHEMA}.{configs["hana.embeddingsTable"]}
            )
            SELECT e.document_id, k.link, e.section, e.text 
            FROM {SCHEMA}.{configs["hana.embeddingsTable"]} e 
            JOIN {SCHEMA}.{configs["hana.kbaTable"]} k ON e.document_id = k.document_id
            WHERE e.document_id IN (
                SELECT document_id 
                FROM RankedDocuments 
                WHERE rank <= {top_k}
            )
            AND e.section IN ({sections_placeholder})
            ORDER BY e.chunk_id 
            '''
    cursor.execute(combined_query, (str(query_embedding).replace(" ", ""), *allowed_sections))
    return cursor.fetchall()


def store_embeddings_in_hana(doc_id, chunks_with_metadata):
    with closing(get_hana_connection()) as conn:
        with closing(conn.cursor()) as cursor:
            for i, chunk in enumerate(chunks_with_metadata, start=1):
                padded_number = f"{i:03d}"
                chunk_id = f"{doc_id}_{padded_number}"
                cursor.execute(
                    f'INSERT INTO {SCHEMA}.{configs["hana.embeddingsTable"]} (Chunk_Id, Document_Id, Text, Embedding, Section) '
                    f'VALUES (?, ?, ?, ?, ?)',
                    (
                        chunk_id,
                        doc_id,
                        chunk['text'],
                        chunk['embedding'],
                        chunk['metadata'].get('section').lower()
                    )
                )
            conn.commit()
            cursor.close()


def insert_kba(id, link, release_date, title, version, category, component, priority):
    print(f'id: {str(id)}, link: {str(link)}, release_date: {str(release_date)}, title: {str(title)}, version: {str(version)}, category: {str(category)}, component: {str(component)}, priority: {str(priority)}')
    with closing(get_hana_connection()) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f'INSERT INTO {SCHEMA}.{configs["hana.kbaTable"]} (Document_Id, Link, Released_On, Title, Version, Category, SAP_Component, Priority) '
                f'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    id,
                    link,
                    release_date,
                    title,
                    version,
                    category,
                    component,
                    priority
                )
            )
        conn.commit()
        conn.close()
    print(f'Inserted KBA with id {id}')


def check_kba_exists(document_id):
    with closing(get_hana_connection()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                f'SELECT 1 FROM {SCHEMA}.{configs["hana.kbaTable"]} WHERE Document_Id = ?',
                document_id
            )
            return cursor.fetchone() is not None
