from spectrum import Spectrum


class FeatureGenerator(Spectrum):
    instruments = [
        'USD000000TOM',
        'USD000UTSTOM',
        'EUR_RUB__TOD',
        'EUR_RUB__TOM'
    ]

    MAX_BAND = 10 * 1E6

    BAND_VALUES = [
             1E5,
        2  * 1E5,
        5  * 1E5,
             1E6,
        5  * 1E6,
        10 * 1E6
    ]

    def __init__(self, seccode):
        super().__init__(seccode)

        self.VWAP_bid = { band: 0 for band in self.BAND_VALUES }
        self.VWAP_ask = { band: 0 for band in self.BAND_VALUES }

    def normalize(self):
        """
        Normalize spectrums by `MAX_BAND`
        """

        self.bids_normalized = [ bid / self.MAX_BAND for bid in self.bids ]

        self.asks_normalized = [ ask / self.MAX_BAND for ask in self.asks ]

    def VWAP(self, band: int):
        # TODO: calculate VWAP for a given band
        # return () / band
        pass

    def normalize_VWAP(self, vwap: float, is_bid: bool, is_ask: bool, px_step=0.0025):
        """
        Normalize VWAP relative to midpoint
        """

        mid_px = (self.best_bid + self.best_ask) / 2

        if is_bid:
            return (mid_px - vwap) / px_step

        elif is_ask:
            return (vwap - mid_px) / px_step

        else:
            raise ValueError('VWAP must be either a bid or an ask. Check `is_bid` and `is_ask` arguments.')
