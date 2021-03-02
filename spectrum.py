from orderbook import OrderBook
import math
from utils import instruments_info


class Spectrum:
    def __init__(self, seccode):
        self.seccode = seccode
        self.best_ask = int(1e19)
        self.best_bid = -1
        self.bids = [0] * 10
        self.asks = [0] * 10
        self.bids_normalized = [0] * 10
        self.asks_normalized = [0] * 10

    @staticmethod
    def distance_idx(dif, step):
        return math.floor(dif / (step * 5))

    def normalize(self):
        """
        calculates normalized version of spectrums
        """

        total_bids = sum(self.bids)
        total_asks = sum(self.asks)

        if total_bids > 0:
            self.bids_normalized = [bid / total_bids for bid in self.bids]

        if total_asks > 0:
            self.asks_normalized = [ask / total_asks for ask in self.asks]

    def change_bids(self, price: float, volume: int, step: float, add: bool):
        dif = self.best_bid - price

        if dif <= step * 49:
            if add:
                self.bids[9 - Spectrum.distance_idx(dif, step)] += volume
            else:
                self.bids[9 - Spectrum.distance_idx(dif, step)] = \
                    max(0, self.bids[9 - Spectrum.distance_idx(dif, step)] - volume)

    def change_asks(self, price: float, volume: int, step: float, add: bool):
        dif = price - self.best_ask

        if dif <= step * 49:
            if add:
                self.asks[Spectrum.distance_idx(dif, step)] += volume
            else:
                self.asks[Spectrum.distance_idx(dif, step)] = \
                    max(0, self.asks[Spectrum.distance_idx(dif, step)] - volume)

    def update_post(self, order_book: OrderBook, new_price: float, volume: int, ask: bool):
        step = instruments_info[self.seccode]['PRICE_STEP']

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

        self.normalize()

    def update_revoke(self, order_book: OrderBook, new_price: float, volume: int, ask: bool):
        step = instruments_info[self.seccode]['PRICE_STEP']

        if not ask:
            if new_price == self.best_bid:
                if volume >= self.bids[9]:

                    self.best_bid = -1

                    for bid in order_book.bids.values():
                        if bid['PRICE'] > self.best_bid:
                            self.best_bid = bid['PRICE']

                    self.bids = [0] * 10
                    if self.best_bid > 0:
                        for bid in order_book.bids.values():
                            self.change_bids(price=bid['PRICE'], volume=bid['VOLUME'], step=step, add=True)
                else:
                    self.bids[9] -= volume

            elif new_price < self.best_bid:
                self.change_bids(price=new_price, volume=volume, step=step, add=False)

        else:
            if new_price == self.best_ask:
                if volume >= self.asks[0]:

                    self.best_ask = int(1e19)

                    for ask in order_book.asks.values():
                        if ask['PRICE'] < self.best_ask:
                            self.best_ask = ask['PRICE']
                            
                    self.asks = [0] * 10
                    if 0 < self.best_ask < int(1e19):
                        for ask in order_book.asks.values():
                            self.change_asks(price=ask['PRICE'], volume=ask['VOLUME'], step=step, add=True)

                else:
                    self.asks[0] -= volume

            elif new_price > self.best_ask:
                self.change_asks(price=new_price, volume=volume, step=step, add=False)

        self.normalize()

    def update_match(self, order_book: OrderBook, new_price: float, volume: int, ask: bool):

        self.update_revoke(order_book, new_price, volume, ask)



