import argparse
import csv
import hashlib
import logging

from datetime import datetime
from typing import TextIO


def get_source_id() -> str:
    '''Extracts the source id from the file'''
    return 'Miles & More Gold'

def get_file_id(f: TextIO) -> str:
    '''Extracts the unique id from the file
    It is used to identify Lufthansa csv files uniquely to avoid expenses duplication.'''
    hash_object = hashlib.sha256()

    for chunk in iter(lambda: f.read(4096), ''):
        hash_object.update(chunk.encode())
    f.seek(0)
    return hash_object.hexdigest()[:16]

def extract_data(input_file: str, output_file: str) -> None:
    source_id = get_source_id()
    with open(input_file, 'r') as csvfile:
        file_id = get_file_id(csvfile)
        next(csvfile)
        next(csvfile)
        header_line = csvfile.readline()
        header = header_line.split(';')
        header[8] = 'Original currency'
        print(header)
        reader = csv.DictReader(csvfile, delimiter=';', fieldnames=header)
        field_names = ['id', 'date', 'description', 'amount_eur', 'amount_usd', 'amount_brl', 'original_currency', 'source_id']

        with open(output_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=field_names)
            writer.writeheader()

            i = 1
            for row in reader:
                print(row['Currency'], '----', row['Original currency'])
                if row['Status'] == 'Authorised':
                    logging.warning(f'Row {i} is not Processed. Skipping...')
                    continue
                parsed_date = datetime.strptime(row['Authorised on'], '%d.%m.%Y').date()
                row_dict = {
                    'id': file_id + str(i),
                    'date': parsed_date.strftime('%Y-%m-%d'),
                    'description': row['Description'],
                    'amount_eur': row['Amount'].replace(',', '.'),
                    'original_currency': row['Original currency'],
                    'source_id': source_id
                }
                if row_dict['original_currency'] == '':
                    row_dict['original_currency'] = 'EUR'
                if row['Original currency'] == 'USD':
                    row_dict['amount_usd'] = row['Amount in foreign currency'].replace(',', '.')
                elif row['Original currency'] == 'BRL':
                    row_dict['amount_brl'] = row['Amount in foreign currency'].replace(',', '.')
        
                writer.writerow(row_dict)
                i += 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse Lufthansa csv files')
    parser.add_argument('input_file', type=str, help='Input file')
    parser.add_argument('output_file', type=str, help='Output file')
    args = parser.parse_args()

    extract_data(args.input_file, args.output_file)