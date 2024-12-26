import requests

from datetime import date, datetime, timedelta


_DATE_FORMAT = '%Y-%m-%d'

class ExchangeRateECB:
    def __init__(self, start_date: date, end_date: date) -> None:
        self.start_date = start_date - timedelta(days=5)
        self.end_date = end_date
        self.rate_usd = {}
        self.rate_brl = {}
        self._BASE_URL = 'https://data-api.ecb.europa.eu/service/'
        self._RESOURCE = 'data'
        self._FLOW_REF = 'EXR'

    def _fetch_rates(self) -> None:
        base_url = 'https://data-api.ecb.europa.eu/service/'
        resource = 'data'
        flow_ref = 'EXR'
        key_usd = 'D.USD.EUR.SP00.A'
        key_brl = 'D.BRL.EUR.SP00.A'

        url_usd = f'{base_url}{resource}/{flow_ref}/{key_usd}'
        url_brl = f'{base_url}{resource}/{flow_ref}/{key_brl}'

        parameters = {
            'startPeriod': self.start_date.strftime(_DATE_FORMAT),
            'endPeriod': self.end_date.strftime(_DATE_FORMAT),
            'format': 'csvdata'
        }

        try:
            response_usd = requests.get(url_usd, params=parameters)
            response_brl = requests.get(url_brl, params=parameters)
        except requests.exceptions.RequestException as e:
            raise e

        DATE_COLUMN_INDEX = 6
        RATE_COLUMN_INDEX = 7
        for line in response_usd.text.splitlines()[1:]:
            columns = line.split(',')
            date = columns[DATE_COLUMN_INDEX]
            rate = columns[RATE_COLUMN_INDEX]
            self.rate_usd[date] = float(rate)

        for line in response_brl.text.splitlines()[1:]:
            columns = line.split(',')
            date = columns[DATE_COLUMN_INDEX] 
            rate = columns[RATE_COLUMN_INDEX]
            self.rate_brl[date] = float(rate)


    def convert(self, date: date, amount: float, currency_from: str, currency_to: str) -> float:
        if currency_from != 'EUR' and currency_to != 'EUR':
            raise ValueError('One of the currencies must be EUR')

        if len(self.rate_usd) == 0 or len(self.rate_brl) == 0:
            self._fetch_rates()
        
        if currency_from == 'USD' or currency_to == 'USD':
            rate_map = self.rate_usd
        elif currency_from == 'BRL' or currency_to == 'BRL':
            rate_map = self.rate_brl
        else:
            raise ValueError('Currency not supported')
        
        # Find the closest date
        for d in rate_map.keys():
            if datetime.strptime(d, _DATE_FORMAT).date() > date:
                break
            else:
                conversion_date = d
        
        if conversion_date is None:
            raise ValueError('No rate found for the givena date')
        
        rate_on_date = rate_map[conversion_date]
        if currency_from == 'EUR':
            return amount * rate_on_date
        else:
            return amount / rate_on_date
        