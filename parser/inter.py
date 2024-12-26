import argparse
import csv
import hashlib
import logging

from datetime import datetime
from typing import Dict, List, TextIO


def _get_source_id() -> str:
    '''Extracts the source id from the file'''
    return 'Banco Inter'


def _get_file_id(f: TextIO) -> str:
    '''Extracts the unique id from the file'''
    hash_object = hashlib.sha256()

    for chunk in iter(lambda: f.read(4096), ''):
        hash_object.update(chunk.encode())
    f.seek(0)
    return hash_object.hexdigest()[:16]


def _convert_to_float(amount: str) -> float:
    return float(amount.replace('.', '').replace(',', '.'))


def extract_data(input_file: str) -> List[Dict[str, str]]:
    source_id = _get_source_id()
    transactions = []
    with open(input_file, 'r') as csvfile:
        file_id = _get_file_id(csvfile)
        for i in range(5):
            next(csvfile)
        header_line = csvfile.readline()
        header = header_line.split(';')
        reader = csv.DictReader(csvfile, delimiter=';', fieldnames=header)

        for i, row in enumerate(reader):
            parsed_date = datetime.strptime(row['Data Lançamento'], '%d/%m/%Y').date()
            row_dict = {
                'id': file_id + str(i + 1),
                'date': parsed_date.strftime('%Y-%m-%d'),
                'description': row['Descrição'],
                'amount_brl': _convert_to_float(row['Valor']),
                'original_currency': 'BRL',
                'source_id': source_id
            }

            transactions.append(row_dict)

    return transactions