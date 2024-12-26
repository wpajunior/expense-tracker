import argparse
import csv
import hashlib

from datetime import datetime
from typing import Dict, List, TextIO


def _get_source_id() -> str:
    '''Extracts the source id from the file'''
    return 'commerzbank'

def _get_file_id(f: TextIO) -> str:
    '''Extracts the unique id from the file
    It is used to identify Commerzbank csv files files uniquely to avoid expenses duplication.'''
    hash_object = hashlib.sha256()

    for chunk in iter(lambda: f.read(4096), ''):
        hash_object.update(chunk.encode())
    f.seek(0)
    return hash_object.hexdigest()[:16]

def extract_data(input_file: str) -> List[Dict[str, str]]:
    source_id = _get_source_id()
    transactions = []
    with open(input_file, 'r', encoding='utf-8-sig') as csvfile:
        file_id = _get_file_id(csvfile)
        reader = csv.DictReader(csvfile, delimiter=';')

        i = 1
        for row in reader:
            parsed_date = datetime.strptime(row['Buchungstag'], '%d.%m.%Y').date()
            row_dict = {
                'id': file_id + str(i),
                'date': parsed_date.strftime('%Y-%m-%d'),
                'description': row['Buchungstext'],
                'amount_eur': float(row['Betrag'].replace(',', '.')),
                'original_currency': row['Währung'],
                'source_id': source_id
            }
            transactions.append(row_dict)
            i += 1
    return transactions
