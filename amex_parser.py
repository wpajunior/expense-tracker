import argparse
import csv
import hashlib
import pdfplumber
import re

from typing import List


def get_source_id(text_lines: List[str]) -> str:
    '''Extracts the source id from the file'''
    if len(text_lines) < 8:
        raise ValueError(('File does not contain enough lines to extract unique id'))

    if 'American Express' in text_lines[0]:
        res = re.search(r'^.+(xxxx-xxxxxx-\d+).+$', text_lines[7])
        if res is None:
            raise ValueError(('Could the source from file'))
        return "amex " + res.group(1)

    raise ValueError(('Could not extract source id from file'))


def get_file_id(text_lines: List[str]) -> str:
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


def extract_data(input_file: str, output_file: str) -> None:
    with pdfplumber.open(input_file) as pdf:
        text = pdf.pages[0].extract_text()
        text_lines = text.splitlines()

        source_id = get_source_id(text_lines)
        file_id = get_file_id(text_lines)
        field_names = ['id', 'date', 'description', 'amount_eur', 'original_currency', 'source_id']

        with open(output_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=field_names)
            writer.writeheader()

            i = 1
            for page in pdf.pages:
                for table in page.extract_tables():
                    for row in table:
                        res = re.search(r'^(\d\d\.\d\d)\s(\d\d\.\d\d)\s(.+)\s(\d+,\d\d)$', row[0])
                        if res is not None:
                            row_dict = {
                                'id': file_id + str(i),
                                'date': res.group(1),
                                'description': res.group(3),
                                'amount_eur': '-' + res.group(4).replace(',', '.'),
                                'original_currency': 'EUR',
                                'source_id': source_id
                            }
                            writer.writerow(row_dict)
                            i += 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse Amex pdf files')
    parser.add_argument('input_file', help='Input file to parse')
    parser.add_argument('output_file', help='Output file to write')
    args = parser.parse_args()
    extract_data(args.input_file, args.output_file)
