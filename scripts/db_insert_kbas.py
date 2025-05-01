import pandas as pd

from config.configuration import configs
from services import hana_service as hs

SCHEMA = configs['hana.schema']
BASE_PATH = '' # Enter path of base folder containing KBAs folder
KBA_DIRECTORY = BASE_PATH + '/KBAs'
KBA_CSV = BASE_PATH + '/pending.csv'


def insert_kbas_data_old(hana_conn):
    data = pd.read_csv(KBA_CSV, sep=',')
    insert_query = f'''
        INSERT INTO {SCHEMA}.KBAs (SAP_Component, Document_Id, Version, Title, Category, Priority, Released_On, Link)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    '''
    with hana_conn.cursor() as cursor:
        for index, row in data.iterrows():
            cursor.execute(insert_query, (
                row['SAP Component'],
                row['Number'],
                row['Version'],
                row['Title'],
                row['Category'],
                row['Priority'],
                pd.to_datetime(row['Released On'], format='%d.%m.%Y').date(),
                row['Link']
            ))
            if (index + 1) % 100 == 0:
                hana_conn.commit()
                print(f'Committed {index + 1} rows.')
    hana_conn.commit()
    print(f'Committed all remaining rows, total: {len(data)}.')
    hana_conn.close()


def insert_kbas_data():
    data = pd.read_csv(KBA_CSV, sep=',')
    for index, row in data.iterrows():
        hs.insert_kba(
            row['Number'],
            row['Link'],
            pd.to_datetime(row['Released On'], format='%d.%m.%Y').date(),
            row['Title'],
            row['Version'],
            row['Category'],
            row['SAP Component'],
            row['Priority']
        )


def test_db_connection(hana_conn):
    try:
        cursor = hana_conn.cursor()
        schema_name = "LS"
        query = f"""
            SELECT TABLE_NAME 
            FROM TABLES 
            WHERE SCHEMA_NAME = '{schema_name}'
        """
        cursor.execute(query)
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        print("Tables in schema:", table_names)
        return table_names
    except Exception as e:
        print("Error fetching table names:", e)
        return None
    finally:
        cursor.close()


# insert_kbas_data(hs.get_hana_connection())
# test_db_connection((hs.get_hana_connection()))
