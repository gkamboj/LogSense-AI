import concurrent
import os

from services import embeddings_service as es
from services import file_service as fs
from services.decorators import timing

BASE_PATH = ''
KBA_DIRECTORY = BASE_PATH + '/KBAs'


@timing(print_args=True)
def insert_document_embeddings(pdf_path, doc_id):
    success = False
    try:
        document_text = fs.extract_text_from_pdf_path(pdf_path)
        es.insert_embeddings_for_document(doc_id, document_text)
    except Exception as e:
        success = True
        print('Error while inserting embeddings for document {}: {}'.format(doc_id, e))
    return success


def insert_kbas_embeddings(max_workers=5):
    processed_files_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'embeddings_processed_files.txt')
    with open(processed_files_file, 'r') as file:
        processed_files = file.read().splitlines()

    def process_file(filename):
        try:
            if filename not in processed_files:
                result = insert_document_embeddings(os.path.join(KBA_DIRECTORY, filename), filename.split('.')[0])
                if result:
                    print(f'Saved embeddings for {filename}')
                    with open(processed_files_file, 'a') as file:
                        file.write(filename + '\n')
        except Exception as e:
            print(f'Error processing {filename}: {e}')

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_file, filename) for filename in os.listdir(KBA_DIRECTORY)]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f'An error occurred: {e}')


insert_kbas_embeddings()
