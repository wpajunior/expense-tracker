
import requests
import urllib

from datetime import datetime, timedelta

_DATE_FORMAT = '%Y-%m-%d'

class ExchangeRateBacen:
    def __init__(self, start_date, end_date):
        self.start_date = start_date - timedelta(days=5)
        self.end_date = end_date
        self.rate_usd = {}
        self.rate_eur = {}

    def _fetch_rates(self):
        base_url = 'https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata'
        resource = 'CotacaoMoedaPeriodo'
        stream = 'moeda=@moeda,dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao'
        key_usd = 'USD'
        key_eu = 'EUR'

        url = f'{base_url}/{resource}({stream})'

        parameters = {
            '@moeda': f"'{key_usd}'",
            '@dataInicial': f"'{self.start_date.strftime('%m-%d-%Y')}'",
            '@dataFinalCotacao': f"'{self.end_date.strftime('%m-%d-%Y')}'",
            '$filter': "tipoBoletim eq 'Fechamento'",
            '$select': 'cotacaoCompra,dataHoraCotacao'
        }

        encoded_params = urllib.parse.urlencode(parameters, quote_via=urllib.parse.quote)

        try:
            response_usd = requests.get(url, params=encoded_params)
            parameters['@moeda'] = f"'{key_eu}'"
            encoded_params = urllib.parse.urlencode(parameters, quote_via=urllib.parse.quote)
            response_eur = requests.get(url, params=encoded_params)
        except requests.exceptions.RequestException as e:
            raise e

        for data in response_usd.json()['value']:
            date = data['dataHoraCotacao'].split(' ')[0]
            rate = data['cotacaoCompra']
            self.rate_usd[date] = float(rate)

        for data in response_eur.json()['value']:
            date = data['dataHoraCotacao'].split(' ')[0]
            rate = data['cotacaoCompra']
            self.rate_eur[date] = float(rate)

    def convert(self, date, amount, currency_from, currency_to):
        if currency_from != 'BRL' and currency_to != 'BRL':
            raise ValueError('One of the currencies must be BRL')

        if len(self.rate_usd) == 0 or len(self.rate_eur) == 0:
            self._fetch_rates()

        if currency_from == 'USD' or currency_to == 'USD':
            rate_map = self.rate_usd
        elif currency_from == 'EUR' or currency_to == 'EUR':
            rate_map = self.rate_eur
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
        if currency_from == 'BRL':
            return amount / rate_on_date
        else:
            return amount * rate_on_date
 