from orderbook import OrderBook
from spectrum import Spectrum


class FeatureGenerator(Spectrum):

    BEST_BID = -1
    BEST_ASK = int(1E19)

    MAX_BAND = 10 * 1E6

    BAND_VALUES = list(map(int, [     1E5,
                                 2  * 1E5,
                                 5  * 1E5,
                                      1E6,
                                 5  * 1E6,
                                 10 * 1E6]
                           ))

    def __init__(self, seccode, px_step):
        self.seccode = seccode
        self.px_step = px_step
        self.best_bid = self.BEST_BID
        self.best_ask = self.BEST_ASK
        self.bids = [0] * 10
        self.asks = [0] * 10
        self.bids_normalized = [0] * 10
        self.asks_normalized = [0] * 10
        self.bid_ask_spread = 0
        self.VWAP_bids = { band: 0 for band in self.BAND_VALUES }
        self.VWAP_asks = { band: 0 for band in self.BAND_VALUES }
        self.VWAP_bids_normalized = { band: 0 for band in self.BAND_VALUES }
        self.VWAP_asks_normalized = { band: 0 for band in self.BAND_VALUES }

    def reset_VWAP_bids(self):
        self.VWAP_bids = { band: 0 for band in self.BAND_VALUES }
        self.VWAP_bids_normalized = { band: 0 for band in self.BAND_VALUES }

    def reset_VWAP_asks(self):
        self.VWAP_asks = { band: 0 for band in self.BAND_VALUES }
        self.VWAP_asks_normalized = { band: 0 for band in self.BAND_VALUES }

    def normalize(self):
        """
        Normalize spectrums by `MAX_BAND`
        """

        self.bids_normalized = [ bid / self.MAX_BAND for bid in self.bids ]
        self.asks_normalized = [ ask / self.MAX_BAND for ask in self.asks ]

    def normalize_VWAPs(self):
        """
        Normalize VWAP relative to midpoint
        """

        if self.best_bid == self.BEST_BID:
            mid_px = self.best_ask
        elif self.best_ask == self.BEST_ASK:
            mid_px = self.best_bid
        else:
            mid_px = (self.best_bid + self.best_ask) / 2

        self.VWAP_bids_normalized = { band: (mid_px - VWAP_bid) / self.px_step
                           for band, VWAP_bid in self.VWAP_bids.items() }

        self.VWAP_asks_normalized = { band: (VWAP_ask - mid_px) / self.px_step
                           for band, VWAP_ask in self.VWAP_asks.items() }

    def update_bid_ask_spread(self):
        if self.best_bid == self.BEST_BID or self.best_ask == self.BEST_ASK:
            self.bid_ask_spread = 0
        else:
            self.bid_ask_spread = (self.best_ask - self.best_bid) / self.px_step

    def update_VWAP_bids(self, order_book: OrderBook):
        # Reset VWAP bids before updating them
        self.reset_VWAP_bids()

        # Handle empty bids
        if not order_book.bids:
            return

        # Sum of (price * volume), Covered volume
        total, volume = 0, 0
        # Index and value of current band
        band_idx = 0
        band = self.BAND_VALUES[band_idx]

        # Iterate through bids
        for bid in order_book.bids.values():
            current_volume = bid['VOLUME']

            # Update band if new volume is greater than current band
            while volume + current_volume >= band:
                # Update current volume
                current_volume = volume + current_volume - band

                # Update VWAP
                total += bid['PRICE'] * (band - volume)
                volume = band
                self.VWAP_bids[band] = total / band

                # Update band
                try:
                    band_idx += 1
                    band = self.BAND_VALUES[band_idx]
                except IndexError:
                    break
            else:
                # Update total price and covered volume
                total += bid['PRICE'] * current_volume
                volume += current_volume

        # Handle remaining bands
        if band_idx < len(self.BAND_VALUES):
            for b in self.BAND_VALUES:
                if b >= band:
                    self.VWAP_bids[b] = total / volume

    def update_VWAP_asks(self, order_book: OrderBook):
        # Reset VWAP asks before updating them
        self.reset_VWAP_asks()

        # Handle empty asks
        if not order_book.asks:
            return

        # Sum of (price * volume), Covered volume
        total, volume = 0, 0
        # Index and value of current band
        band_idx = 0
        band = self.BAND_VALUES[band_idx]

        # Iterate through asks
        for bid in order_book.asks.values():
            current_volume = bid['VOLUME']

            # Update band if new volume is greater than current band
            while volume + current_volume >= band:
                # Update current volume
                current_volume = volume + current_volume - band

                # Update VWAP
                total += bid['PRICE'] * (band - volume)
                volume = band
                self.VWAP_asks[band] = total / band

                # Update band
                try:
                    band_idx += 1
                    band = self.BAND_VALUES[band_idx]
                except IndexError:
                    break
            else:
                # Update total price and covered volume
                total += bid['PRICE'] * current_volume
                volume += current_volume

        # Handle remaining bands
        if band_idx < len(self.BAND_VALUES):
            for b in self.BAND_VALUES:
                if b >= band:
                    self.VWAP_asks[b] = total / volume

    def update_post(self, order_book: OrderBook, new_price: float, volume: int, ask: bool):
        step = self.px_step

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

            self.update_VWAP_bids(order_book)

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

            self.update_VWAP_asks(order_book)

        self.update_bid_ask_spread()
        self.normalize()
        self.normalize_VWAPs()

    def update_revoke(self, order_book: OrderBook, new_price: float, volume: int, ask: bool):
        step = self.px_step

        if not ask:
            if new_price == self.best_bid:
                if volume >= self.bids[9]:

                    self.best_bid = self.BEST_BID

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

            self.update_VWAP_bids(order_book)

        else:
            if new_price == self.best_ask:
                if volume >= self.asks[0]:

                    self.best_ask = self.BEST_ASK

                    for ask in order_book.asks.values():
                        if ask['PRICE'] < self.best_ask:
                            self.best_ask = ask['PRICE']

                    self.asks = [0] * 10
                    if 0 < self.best_ask < self.BEST_ASK:
                        for ask in order_book.asks.values():
                            self.change_asks(price=ask['PRICE'], volume=ask['VOLUME'], step=step, add=True)

                else:
                    self.asks[0] -= volume

            elif new_price > self.best_ask:
                self.change_asks(price=new_price, volume=volume, step=step, add=False)

            self.update_VWAP_asks(order_book)

        self.update_bid_ask_spread()
        self.normalize()
        self.normalize_VWAPs()
