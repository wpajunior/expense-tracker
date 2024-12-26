import argparse
import csv
import hashlib

from typing import Dict, List, TextIO


def _get_source_id() -> str:
    '''Extracts the source id from the file'''
    return 'n26'

def _get_file_id(f: TextIO) -> str:
    '''Extracts the unique id from the file
    It is used to identify N26 csv files files uniquely to avoid expenses duplication.'''
    hash_object = hashlib.sha256()

    for chunk in iter(lambda: f.read(4096), ''):
        hash_object.update(chunk.encode())
    f.seek(0)
    return hash_object.hexdigest()[:16]


def extract_data(input_file: str) -> List[Dict[str, str]]:
    source_id = _get_source_id()
    transactions = []
    with open(input_file, 'r') as csvfile:
        file_id = _get_file_id(csvfile)
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')

        i = 1
        for row in reader:
            row_dict = {
                'id': file_id + str(i),
                'date': row['Value Date'],
                'description': row['Partner Name'],
                'amount_eur': float(row['Amount (EUR)']),
                'original_currency': row['Original Currency'].upper(),
                'source_id': source_id
            }
            if row_dict['original_currency'] == '':
                row_dict['original_currency'] = 'EUR'
            
            if row['Original Currency'] == 'USD':
                row_dict['amount_usd'] = float('-' + row['Original Amount'])
            elif row['Original Currency'] == 'BRL':
                row_dict['amount_brl'] = float('-' + row['Original Amount'])
            transactions.append(row_dict)
            i += 1
    return transactions
