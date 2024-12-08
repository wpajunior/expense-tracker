import argparse
import csv
import hashlib
import pdfplumber
import re

from datetime import datetime
from typing import Dict, List, Tuple


def _get_source_id(text_lines: List[str]) -> str:
    '''Extracts the source id from the file'''
    if len(text_lines) < 8:
        raise ValueError(('File does not contain enough lines to extract unique id'))

    if 'American Express' in text_lines[0]:
        res = re.search(r'^.+(xxxx-xxxxxx-\d+).+$', text_lines[7])
        if res is None:
            raise ValueError(('Could the source from file'))
        return "amex " + res.group(1)

    raise ValueError(('Could not extract source id from file'))


def _get_file_id(text_lines: List[str]) -> str:
    '''Extracts the unique id from the file
    It is used to identify Amex pdf files uniquely to avoid expenses duplication.'''
    if len(text_lines) < 8:
        raise ValueError(('File does not contain enough lines to extract unique id'))

    id_line = text_lines[7]
    res = re.search(r'^.+-\d{5}\s\d\d\.\d\d\.\d\d$', id_line)
    if res is None:
        raise ValueError(('Could not extract unique id from file'))
    
    hash_object = hashlib.sha256(id_line.encode())
    return hash_object.hexdigest()[:16]

def _extract_years(text_lines: List[str]) -> Tuple[str, str]:
    '''Extracts the year from the file'''
    if len(text_lines) < 18:
        raise ValueError(('File does not contain enough lines to extract years'))

    date_range_line = text_lines[18]
    res = re.search(r'vom\s(\d\d\.\d\d\.\d\d)bis\s(\d\d\.\d\d\.\d\d)', date_range_line)
    if res is None:
        raise ValueError(('Could not extract years from file'))
    
    return res.group(1)[-2:], res.group(2)[-2:]


def extract_data(input_file: str) -> List[Dict[str, str]]:
    '''Extracts the transactions data from the AMEX pdf file'''
    transactions = []
    with pdfplumber.open(input_file) as pdf:
        text = pdf.pages[0].extract_text()
        text_lines = text.splitlines()
        source_id = _get_source_id(text_lines)
        year_start, year_end = _extract_years(text_lines)

        file_id = _get_file_id(text_lines)

        i = 1
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    res = re.search(r'^(\d\d\.\d\d)\s(\d\d\.\d\d)\s(.+)\s(\d+,\d\d)$', row[0])
                    if res is not None:
                        if res.group(1)[-2:] == '01':
                            year = year_end
                        else:
                            year = year_start

                        transaction_date_str = res.group(1) + '.' + year
                        transaction_date = datetime.strptime(transaction_date_str, '%d.%m.%y')
                        row_dict = {
                            'id': file_id + str(i),
                            'date': transaction_date.strftime('%Y-%m-%d'),
                            'description': res.group(3),
                            'amount_eur': '-' + res.group(4).replace(',', '.'),
                            'original_currency': 'EUR',
                            'source_id': source_id
                        }
                        transactions.append(row_dict)
                        i += 1
    return transactions
