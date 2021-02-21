from orderbook import OrderBook
from spectrum import Spectrum
from utils import instruments_info


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

        self.VWAP_bids = { band: 0 for band in self.BAND_VALUES }
        self.VWAP_asks = { band: 0 for band in self.BAND_VALUES }

    def normalize(self):
        """
        Normalize spectrums by `MAX_BAND`
        """

        self.bids_normalized = [ bid / self.MAX_BAND for bid in self.bids ]

        self.asks_normalized = [ ask / self.MAX_BAND for ask in self.asks ]

        self.normalize_VWAPs()

    def normalize_VWAPs(self):
        """
        Normalize VWAP relative to midpoint
        """

        mid_px = (self.best_bid + self.best_ask) / 2

        px_step = self.get_px_step()

        for band, VWAP_bid in self.VWAP_bids.items():
            self.VWAP_bids[band] = (mid_px - VWAP_bid) / px_step

        for band, VWAP_ask in self.VWAP_asks.items():
            self.VWAP_asks[band] = (VWAP_ask - mid_px) / px_step

    def get_px_step(self):
        return instruments_info[self.seccode]['PRICE_STEP']

    def change_VWAP_bids(self, order_book: OrderBook):
        # TODO: recalculate VWAP bids
        pass

    def change_VWAP_asks(self, order_book: OrderBook):
        # TODO: recalculate VWAP asks
        pass

    def update_post(self, order_book: OrderBook, new_price: float, volume: int, ask: bool):
        step = self.get_px_step()

        if not ask:
            if new_price > self.best_bid:

                self.best_bid = new_price
                self.bids = [0] * 10

                for bid in order_book.bids.values():
                    self.change_bids(price=bid['PRICE'], volume=bid['VOLUME'], step=step, add=True)

            elif new_price == self.best_bid:
                self.bids[9] += volume

            else:
                self.change_bids(price=new_price, volume=volume, step=step, add=True)

            self.change_VWAP_bids(order_book)

        else:
            if new_price < self.best_ask:

                self.best_ask = new_price
                self.asks = [0] * 10

                for ask in order_book.asks.values():
                    self.change_asks(price=ask['PRICE'], volume=ask['VOLUME'], step=step, add=True)

            elif new_price == self.best_ask:
                self.asks[0] += volume

            else:
                self.change_asks(price=new_price, volume=volume, step=step, add=True)

            self.change_VWAP_asks(order_book)

        self.normalize()

    def update_revoke(self, order_book: OrderBook, new_price: float, volume: int, ask: bool):
        step = self.get_px_step()

        if not ask:
            if new_price == self.best_bid:
                if volume >= self.bids[9]:

                    self.best_bid = -1

                    for bid in order_book.bids.values():
                        if bid['PRICE'] > self.best_bid:
                            self.best_bid = bid['PRICE']

                    self.bids = [0] * 10

                    for bid in order_book.bids.values():
                        self.change_bids(price=bid['PRICE'], volume=bid['VOLUME'], step=step, add=True)
                else:
                    self.bids[9] -= volume

            elif new_price < self.best_bid:
                self.change_bids(price=new_price, volume=volume, step=step, add=False)

            self.change_VWAP_bids(order_book)

        else:
            if new_price == self.best_ask:
                if volume >= self.asks[0]:

                    self.best_ask = 10000000000000000000

                    for ask in order_book.asks.values():
                        if ask['PRICE'] < self.best_ask:
                            self.best_ask = ask['PRICE']

                    self.asks = [0] * 10

                    for ask in order_book.asks.values():
                        self.change_asks(price=ask['PRICE'], volume=ask['VOLUME'], step=step, add=True)

                else:
                    self.asks[0] -= volume

            elif new_price > self.best_ask:
                self.change_asks(price=new_price, volume=volume, step=step, add=False)

            self.change_VWAP_asks(order_book)

        self.normalize()
