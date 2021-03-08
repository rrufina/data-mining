import numpy as np
import csv


class Action:
    REVOKE = 0
    POST = 1
    MATCH = 2


SECCODES = ['USD000000TOD', 'USD000UTSTOM', 'EUR_RUB__TOD', 'EUR_RUB__TOM', 'EURUSD000TOD', 'EURUSD000TOM']

feature_seccodes = [
    'USD000000TOD',
    'USD000UTSTOM',
    'EUR_RUB__TOD',
    'EUR_RUB__TOM'
]

instruments_info = {'USD000000TOD': {'SCHEDULE': 174500000000, 'PRICE_STEP': 0.0025, 'INDEX': 0},
                    'USD000UTSTOM': {'SCHEDULE': 235000000000, 'PRICE_STEP': 0.0025, 'INDEX': 1},
                    'EUR_RUB__TOD': {'SCHEDULE': 150000000000, 'PRICE_STEP': 0.0025, 'INDEX': 2},
                    'EUR_RUB__TOM': {'SCHEDULE': 235000000000, 'PRICE_STEP': 0.0025, 'INDEX': 3},
                    'EURUSD000TOM': {'SCHEDULE': 235000000000, 'PRICE_STEP': 0.00001, 'INDEX': 4},
                    'EURUSD000TOD': {'SCHEDULE': 150000000000, 'PRICE_STEP': 0.00001, 'INDEX': 5}}

def read_orderlog(orderlog_path: str) -> list:
    """
    function for reading orderlog and storing in in a list

    orderlog_path: a path to orderlog file
    """

    order_log = []

    reader = csv.DictReader(open(orderlog_path))
    for row in reader:
        order_log.append(row)

    return order_log


def reformat_orderlog(log):
    """
    Change the column types (in place)
    """
    types_dict = {
        'NO': int,
        'SECCODE': lambda x: x,
        'BUYSELL': lambda x: x,
        'TIME': int,
        'ORDERNO': int,
        'ACTION': int,
        'PRICE': float,
        'VOLUME': int,
        'TRADENO': lambda x: float(x) if x != '' else np.nan,
        'TRADEPRICE': lambda x: float(x) if x != '' else np.nan
    }

    for row in log:
        for col in row:
            row[col] = types_dict[col](row[col])


def reformat_tradelog(log):
    """
    Change the column types (in place)
    """
    types_dict = {
        'TRADENO': int,
        'SECCODE': lambda x: x,
        'TIME': int,
        'BUYORDERNO': int,
        'SELLORDERNO': int,
        'PRICE': float,
        'VOLUME': int
    }

    for row in log:
        for col in row:
            row[col] = types_dict[col](row[col])


def filter(df, predicate):
    """
    Filter out rows that satisfy a predicate
    """
    if not df:
        return []

    return [row for row in df if predicate(row)]


prep_dic = {Action.POST: 0, Action.MATCH: 1, Action.REVOKE: 2}
unprep_dic = {v: k for k, v in prep_dic.items()}  # Inverse `prep_dic`


def apply(df, f):
    """
    Apply function to df
    """
    return [f(row) for row in df]


def sort(df, cols):
    """
    Sort df by columns
    """
    if not df:
        return []

    return sorted(df, key=lambda row: [row[col] for col in cols])


def harvard(row):
    """
    this function was written by 2 harvard professors
    """
    for col in row:
        if col == 'ACTION':
            row[col] = prep_dic[row[col]]

    return row


def harvard_inverse(row):
    """
    the same as harvard()
    """
    for col in row:
        if col == 'ACTION':
            row[col] = unprep_dic[row[col]]

    return row


def preprocess_orderlog(order_log: list) -> list:
    """
    function for preprocessing the orderlog

    returns preprocessed orderlog
    """
    # changing column types
    reformat_orderlog(order_log)
    # filtering out some rows
    order_log = filter(order_log, lambda row:
    row['SECCODE'] in SECCODES and
    row['TIME'] < 2350 * 1E8)

    # harvard hack
    order_log = apply(order_log, harvard)
    order_log = sort(order_log, ['TIME', 'ACTION'])
    order_log = apply(order_log, harvard_inverse)

    return order_log
