class OrderBook:
    total_mistakes = 0

    def __init__(self, seccode: str):
        self.seccode = seccode
        self.asks = dict()
        self.bids = dict()
        self.sorted_asks_list = []
        self.sorted_bids_list = []

    def __repr__(self):
        return self.seccode
    
    def _do_sorting(self, dic, to_reverse=False):
        temp_list = sorted(dic.values(), key=lambda item: item['PRICE'], reverse=to_reverse)
        cur_price = temp_list[0]['PRICE'] if temp_list else -1
        cur_volume = temp_list[0]['VOLUME'] if temp_list else -1
        sorted_list = []
        for index, item in enumerate(temp_list[1:]):
            if item['PRICE'] != cur_price:
                sorted_list.append((cur_price, cur_volume))
                cur_price = item['PRICE']
                cur_volume = item['VOLUME']
            else:
                cur_volume += item['VOLUME']

        if cur_price > -1:
            sorted_list.append((cur_price, cur_volume))
            
        return sorted_list
    
    
    def sort_bids_and_asks(self):
        self.sorted_asks_list = self._do_sorting(self.asks)
        self.sorted_bids_list = self._do_sorting(self.bids, True)    
        

    @staticmethod
    def print_error(error: str, row_numb: int) -> None:
        """
        error: description of the error
        row_numb: number of the entry in OrderLog which resulted the error

        prints the error to screen
        """
        # uncomment to print errors
        #         print('-' * 40)
        #         print(f'in row: {row_numb}')
        #         print(f"ERROR: {error}")
        #         print('-' * 40)
        #         print()
        OrderBook.total_mistakes += 1

    def order_exists(self, orderno: int, ask: bool) -> bool:
        """
        checks if the order with given orderno exists
        """

        dic = self.asks if ask else self.bids

        return orderno in dic

    def add_entry(self, entry, ask: bool):
        """
        adds an entry to ask or bid side of the OB
        """
        # what will be kept in the order book
        columns = ['ORDERNO', 'SECCODE', 'PRICE', 'VOLUME']

        key = entry['ORDERNO']
        values = dict()
        for col in columns:
            values[col] = entry[col]

        dic = self.asks if ask else self.bids

        dic[key] = values

    def revoke(self, orderno: int, volume: int, ask: bool, row_numb: int):
        """
        revokes given volume from order with the give orderno
        """

        if self.order_exists(orderno=orderno, ask=ask):
            dic = self.asks if ask else self.bids
            # acquiring the corresponding order
            order = dic[orderno]

            # check if revoking volume is not greater than the current one
            if order['VOLUME'] >= volume:
                # removing the order
                if order['VOLUME'] == volume:
                    del dic[orderno]
                # reducing volume of the order
                else:
                    order['VOLUME'] -= volume
            else:
                OrderBook.print_error(error="Cannot revoke more than there is",
                                      row_numb=row_numb)
                # removing the order to avoid negative numbers
                del dic[orderno]

        else:
            OrderBook.print_error(error=f"Record with the given ORDERNO={orderno} doesn't exist",
                                  row_numb=row_numb)

    def match(self, orderno: int, volume: int, ask: bool, row_numb: int):
        """
        handling match
        """
        # discuss with leva and ruphina
        # for one order match is the same as revoke
        self.revoke(orderno=orderno, volume=volume, ask=ask, row_numb=row_numb)
