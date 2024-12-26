import argparse
import csv
import os
import sys

from currency.bacen import ExchangeRateBacen
from currency.converter import ConverterSelector
from currency.ecb import ExchangeRateECB
from datetime import date, datetime
from dotenv import load_dotenv
from openai import OpenAI
from parser import amex, commerzbank, inter, lufthansa, n26
from typing import Dict, List, Tuple

parsers = {
    '.pdf': [amex.extract_data],
    '.csv': [commerzbank.extract_data, inter.extract_data, lufthansa.extract_data, n26.extract_data]
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


def find_max_min_dates(transactions: List[Dict]) -> Tuple[date, date]:
    '''Returns the minimum and maximum date from a list of transactions'''
    min_date = date.max
    max_date = date.min

    for transaction in transactions:
        transaction_date = datetime.strptime(transaction['date'], '%Y-%m-%d').date()
        if transaction_date < min_date:
            min_date = transaction_date
        if transaction_date > max_date:
            max_date = transaction_date
    
    return min_date, max_date


def get_transaction_categories(transactions: List[Dict]) -> List[str]:
    '''Returns the unique categories from a list of transactions'''

    transaction_descriptions = "\n".join([str(i) + "," + t['description'] for i, t in enumerate(transactions)])

    load_dotenv()
    client = OpenAI()

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are responsible for classifying transactions based on their description. Consider that I live in Potsdam/Germany but I might also have expenses in Brazil. The input will contain the transaction id and the transaction description separated by comma. For each input line, give as output the transaction id and the category separated by comma without anything else so I can parse it on my system. These are the possible categories:Salary,Contract Work,Investment Income,Rental Income,Other Income,Rent,Utilities,Insurance,Subscriptions,Groceries,Eating Out,Transportation,Healthcare,Subscriptions,Entertainment,Shopping,Education,Travel,Investment,Donations,Gifts,Fees and Charges,Transfers Between Accounts,Other Expenses",
            },
            {
                "role": "user",
                "content": transaction_descriptions,
            }
        ],
        # model="gpt-4o-mini",
        model="gpt-4o"
    )

    result = [None] * len(transactions)
    for message in chat_completion.choices[0].message.content.split("\n"):
        transaction_id, category = message.split(",")
        result[int(transaction_id)] = category.strip()

    return result


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
                        transactions += parser(file)
                        parsed = True
                    except Exception:
                        pass
            if not parsed:
                print(f'Could not parse file {file}')
                sys.exit(1)

    min_date, max_date = find_max_min_dates(transactions)
    ecb = ExchangeRateECB(min_date, max_date)
    bacen = ExchangeRateBacen(min_date, max_date)
    converter = ConverterSelector(bacen, ecb)

    categories = get_transaction_categories(transactions)

    with open('output.csv', 'w') as csvfile:
        field_names = ['id', 'date', 'category', 'description', 'amount_eur', 'amount_usd', 'amount_brl', 'original_currency', 'source_id']
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()

        for i, t in enumerate(transactions):
            t['category'] = categories[i]

            if t['original_currency'] == 'EUR':
                original_amount = t['amount_eur']
            elif t['original_currency'] == 'USD':
                original_amount = t['amount_usd']
            elif t['original_currency'] == 'BRL':
                original_amount = t['amount_brl']
            else:
                print(f'Unknown currency {t["original_currency"]}')
                sys.exit(1)

            try:
                transaction_date = datetime.strptime(t['date'], '%Y-%m-%d').date()
                if 'amount_eur' not in t or t['amount_eur'] == "":
                    t['amount_eur'] = converter.convert(transaction_date, original_amount, t['original_currency'], 'EUR')
                if 'amount_usd' not in t or t['amount_usd'] == "":
                    t['amount_usd'] = converter.convert(transaction_date, original_amount, t['original_currency'], 'USD')
                if 'amount_brl' not in t or t['amount_brl'] == "":
                    t['amount_brl'] = converter.convert(transaction_date, original_amount, t['original_currency'], 'BRL')
            except Exception as e:
                print(f'Could not convert transaction {t["id"]}: {e}')
                continue

            writer.writerow(t)