import argparse
import csv
import os

from parser import amex, commerzbank, lufthansa, n26
from typing import Dict, List

parsers = {
    '.pdf': [amex.extract_data],
    '.csv': [commerzbank.extract_data, lufthansa.extract_data, n26.extract_data]
}

def get_files(folder: str) -> Dict[str, List[str]]:
    '''Returns a dictionary with the files in the folder, grouped by extension'''
    files = {}
    for file in os.listdir(folder):
        file = os.path.join(folder, file)
        if os.path.isfile(file):
            _, extension = os.path.splitext(file)
            if extension not in files:
                files[extension] = []
            files[extension].append(file)
    
    return files


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Parse financial files')
    p.add_argument('folder', type=str, help='Folder with financial files')
    args = p.parse_args()

    files = get_files(args.folder)

    transactions = []
    for extension, files_by_extension in files.items():
        for file in files_by_extension:
            parsed = False
            if extension in parsers:
                for parser in parsers[extension]:
                    try:
                        transactions.append(parser(file))
                        parsed = True
                    except:
                        pass
            if not parsed:
                print(f'Could not parse file {file}')


    with open('output.csv', 'w') as csvfile:
        field_names = ['id', 'date', 'description', 'amount_eur', 'amount_usd', 'amount_brl', 'original_currency', 'source_id']
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()

        for transaction in transactions:
            for t in transaction:
                writer.writerow(t)