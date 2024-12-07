import argparse
import csv
import hashlib

from typing import TextIO


def get_source_id() -> str:
    '''Extracts the source id from the file'''
    return 'n26'

def get_file_id(f: TextIO) -> str:
    '''Extracts the unique id from the file
    It is used to identify N26 csv files files uniquely to avoid expenses duplication.'''
    hash_object = hashlib.sha256()

    for chunk in iter(lambda: f.read(4096), ''):
        hash_object.update(chunk.encode())
    f.seek(0)
    return hash_object.hexdigest()[:16]


def extract_data(input_file: str, output_file: str) -> None:
    source_id = get_source_id()
    with open(input_file, 'r') as csvfile:
        file_id = get_file_id(csvfile)
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        field_names = ['id', 'date', 'description', 'amount_eur', 'amount_usd', 'original_currency', 'source_id']

        with open(output_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=field_names)
            writer.writeheader()

            i = 1
            for row in reader:
                row_dict = {
                    'id': file_id + str(i),
                    'date': row['Value Date'],
                    'description': row['Partner Name'],
                    'amount_eur': row['Amount (EUR)'],
                    'original_currency': row['Original Currency'].upper(),
                    'source_id': source_id
                }
                if row_dict['original_currency'] == '':
                    row_dict['original_currency'] = 'EUR'
                
                if row['Original Currency'] == 'USD':
                    row_dict['amount_usd'] = '-' + row['Original Amount']
                elif row['Original Currency'] == 'BRL':
                    row_dict['amount_brl'] = '-' + row['Original Amount']
                writer.writerow(row_dict)
                i += 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse N26 csv files')
    parser.add_argument('input_file', type=str, help='Input file')
    parser.add_argument('output_file', type=str, help='Output file')
    args = parser.parse_args()

    extract_data(args.input_file, args.output_file)