from .bacen import ExchangeRateBacen
from .ecb import ExchangeRateECB

from datetime import date


class ConverterSelector:
    def __init__(self, bacen: ExchangeRateBacen, ecb: ExchangeRateECB):
        self.bacen = bacen
        self.ecb = ecb

    def convert(self, date: date, amount: float, from_currency: str, to_currency: str) -> float:
        if from_currency == 'BRL':
            converter = self.bacen
        elif from_currency == 'EUR':
            converter = self.ecb
        elif from_currency == 'USD':
            if to_currency == 'EUR':
                converter = self.ecb
            else:
                converter = self.bacen
        
        if converter is None:
            raise ValueError('Unsupported conversion')
        
        return round(converter.convert(date, amount, from_currency, to_currency), 2)
