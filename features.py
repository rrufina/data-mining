from orderbook import OrderBook
from spectrum import Spectrum


class FeatureGenerator(Spectrum):

    BEST_BID = -1
    BEST_ASK = int(1E19)

    MAX_BAND = 10 * int(1E6)

    BAND_VALUES = list(map(int, [     1E5,
                                 2  * 1E5,
                                 5  * 1E5,
                                      1E6,
                                 5  * 1E6,
                                 10 * 1E6]
                           ))

    PERIODS = [1, 5, 15, 30, 60]

    def __init__(self, seccode, px_step):
        self.seccode = seccode
        self.px_step = px_step

        self.best_bid = self.BEST_BID
        self.best_ask = self.BEST_ASK

        self.bids = [0] * 10
        self.asks = [0] * 10
        self.bids_normalized = [0] * 10
        self.asks_normalized = [0] * 10

        self.VWAP_bids = { band: 0 for band in self.BAND_VALUES }
        self.VWAP_asks = { band: 0 for band in self.BAND_VALUES }
        self.VWAP_bids_normalized = { band: 0 for band in self.BAND_VALUES }
        self.VWAP_asks_normalized = { band: 0 for band in self.BAND_VALUES }

        self.aggressive_bids = { period: 0 for period in self.PERIODS }
        self.aggressive_asks = { period: 0 for period in self.PERIODS }
        self.aggressive_bids_normalized_band = { period: 0 for period in self.PERIODS }
        self.aggressive_asks_normalized_band = { period: 0 for period in self.PERIODS }
        self.aggressive_bids_normalized_time = { period: 0 for period in self.PERIODS }
        self.aggressive_asks_normalized_time = { period: 0 for period in self.PERIODS }

        self.bids_makers = {period: 0 for period in self.PERIODS}
        self.asks_makers = {period: 0 for period in self.PERIODS}
        self.bids_makers_normalized_band = {period: 0 for period in self.PERIODS}
        self.asks_makers_normalized_band = {period: 0 for period in self.PERIODS}
        self.bids_makers_normalized_time = {period: 0 for period in self.PERIODS}
        self.asks_makers_normalized_time = {period: 0 for period in self.PERIODS}

        self.bid_ask_spread = 0

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

    def normalize_aggressors(self):
        self.aggressive_bids_normalized_band = { period: volume / self.MAX_BAND
                                                 for period, volume in self.aggressive_bids.items() }

        self.aggressive_asks_normalized_band = { period: volume / self.MAX_BAND
                                                 for period, volume in self.aggressive_asks.items() }

        self.aggressive_bids_normalized_time = { period: volume / period
                                                 for period, volume in self.aggressive_bids.items() }

        self.aggressive_asks_normalized_time = { period: volume / period
                                                 for period, volume in self.aggressive_asks.items() }

    def normalize_makers(self):
        self.bids_makers_normalized_band = { period: volume / self.MAX_BAND
                                                 for period, volume in self.bids_makers.items() }

        self.asks_makers_normalized_band = { period: volume / self.MAX_BAND
                                                 for period, volume in self.asks_makers.items() }

        self.bids_makers_normalized_time = { period: volume / period
                                                 for period, volume in self.bids_makers.items() }

        self.asks_makers_normalized_time = { period: volume / period
                                                 for period, volume in self.asks_makers.items() }

    def update_bid_ask_spread(self):
        if self.best_bid == self.BEST_BID or self.best_ask == self.BEST_ASK:
            self.bid_ask_spread = 0
        else:
            self.bid_ask_spread = (self.best_ask - self.best_bid) / self.px_step

    def update_VWAP_bids(self, order_book: OrderBook):
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

    def update_aggressive(self, aggressive_bids=None, aggressive_asks=None):
        self.update_aggressive_bids(aggressive_bids)
        self.update_aggressive_asks(aggressive_asks)

    def update_aggressive_bids(self, aggressors):
        if aggressors is None:
            return

        volume = 0
        period_idx = 0
        period = self.PERIODS[period_idx]
        current_time = aggressors[-1][0]

        # pair[0] is time, pair[1] is volume
        for pair in reversed(aggressors[:-1]):

            while current_time - pair[0] >= period:
                self.aggressive_bids[period] = volume

                try:
                    period_idx += 1
                    period = self.PERIODS[period_idx]
                except IndexError:
                    break
            else:
                volume += pair[1]

        # Handle remaining pairs
        if period_idx < len(self.PERIODS):
            for p in self.PERIODS:
                if p >= period:
                    self.aggressive_bids[p] = volume

    def update_aggressive_asks(self, aggressors):
        if aggressors is None:
            return

        volume = 0
        period_idx = 0
        period = self.PERIODS[period_idx]
        current_time = aggressors[-1][0]

        # pair[0] is time, pair[1] is volume
        for pair in reversed(aggressors[:-1]):

            while current_time - pair[0] >= period:
                self.aggressive_asks[period] = volume

                try:
                    period_idx += 1
                    period = self.PERIODS[period_idx]
                except IndexError:
                    break
            else:
                volume += pair[1]

        # Handle remaining pairs
        if period_idx < len(self.PERIODS):
            for p in self.PERIODS:
                if p >= period:
                    self.aggressive_asks[p] = volume

    def update_makers(self, bids_makers=None, asks_makers=None):
        self.update_bids_makers(bids_makers)
        self.update_asks_makers(asks_makers)

    def update_bids_makers(self, bids_makers):
        if bids_makers is None:
            return

        volume = 0
        period_idx = 0
        period = self.PERIODS[period_idx]
        current_time = bids_makers[-1][0]

        # pair[0] is time, pair[1] is volume, pair[2] is price
        for pair in reversed(bids_makers[:-1]):
            if pair[2] < self.best_bid - 4 * self.px_step:
                continue

            while current_time - pair[0] >= period:
                self.bids_makers[period] = volume

                try:
                    period_idx += 1
                    period = self.PERIODS[period_idx]
                except IndexError:
                    break
            else:
                volume += pair[1]

        # Handle remaining triple
        if period_idx < len(self.PERIODS):
            for p in self.PERIODS:
                if p >= period:
                    self.bids_makers[p] = volume

    def update_asks_makers(self, asks_makers):
        if asks_makers is None:
            return

        volume = 0
        period_idx = 0
        period = self.PERIODS[period_idx]
        current_time = asks_makers[-1][0]

        # triple[0] is time, triple[1] is volume, triple[2] is price
        for triple in reversed(asks_makers[:-1]):
            if triple[2] > self.best_ask + 4 * self.px_step:
                continue

            while current_time - triple[0] >= period:
                self.asks_makers[period] = volume

                try:
                    period_idx += 1
                    period = self.PERIODS[period_idx]
                except IndexError:
                    break
            else:
                volume += triple[1]

        # Handle remaining pairs
        if period_idx < len(self.PERIODS):
            for p in self.PERIODS:
                if p >= period:
                    self.asks_makers[p] = volume

    def update_post(self, order_book: OrderBook, new_price: float, volume: int, ask: bool,
                    aggressive_bids=None, aggressive_asks=None,
                    bids_makers=None, asks_makers=None):
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

        self.update_aggressive(aggressive_bids, aggressive_asks)
        self.update_makers(bids_makers, asks_makers)
        self.update_bid_ask_spread()
        self.normalize()
        self.normalize_VWAPs()
        self.normalize_aggressors()
        self.normalize_makers()

    def update_revoke(self, order_book: OrderBook, new_price: float, volume: int, ask: bool, aggressive_bids=None, aggressive_asks=None):
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

        self.update_aggressive(aggressive_bids, aggressive_asks)
        self.update_bid_ask_spread()
        self.normalize()
        self.normalize_VWAPs()
        self.normalize_aggressors()

    def update_match(self, order_book: OrderBook, new_price: float, volume: int, ask: bool,  aggressive_bids=None, aggressive_asks=None):
        self.update_revoke(order_book, new_price, volume, ask, aggressive_bids, aggressive_asks)
