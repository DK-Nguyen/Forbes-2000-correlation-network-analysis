from typing import List, Union
import pandas as pd
import requests
from pathlib import Path
import logging
from googlesearch import search
from tqdm import tqdm
import yfinance as yf
import matplotlib.pyplot as plt
from copy import deepcopy
import pdb
import traceback
import sys
from functools import reduce

# A logger for this file
log = logging.getLogger(__name__)


def scraping_forbes_2000(output_path: Union[str, Path]):
    """
    Get the data of 2000 companies from https://www.forbes.com/global2000/ and save to csv file
    :param output_path: the path to save the .csv file to
    """
    if Path(output_path).exists():
        log.info(f"{output_path} exists, do nothing")
        return

    headers = {
        "accept": "application/json, text/plain, */*",
        "referer": "https://www.forbes.com/global2000/",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.67 Safari/537.36",
    }

    cookies = {
        "notice_behavior": "expressed,eu",
        "notice_gdpr_prefs": "0,1,2:1a8b5228dd7ff0717196863a5d28ce6c",
    }

    api_url = "https://www.forbes.com/forbesapi/org/global2000/2020/position/true.json?limit=2000"
    response = requests.get(api_url, headers=headers, cookies=cookies).json()

    sample_table = [
        [
            item["organizationName"],
            item["country"],
            item["revenue"],
            item["profits"],
            item["assets"],
            item["marketValue"]
        ] for item in
        sorted(response["organizationList"]["organizationsLists"], key=lambda k: k["position"])
    ]

    df = pd.DataFrame(sample_table, columns=["Company", "Country", "Sales", "Profits", "Assets", "Market Value"])
    df.to_csv(output_path, index=False)
    log.info(f"save forbes 2000 companies data to {output_path}")


def name_convert(company_name: str):
    """
    Search for the ticker symbol given a company name
    code based on https://github.com/MakonnenMak/company-name-to-ticker-yahoo-finance
    """
    search_val = 'yahoo finance ' + company_name
    link = []
    # limits to the first link

    for url in search(search_val, tld='es', lang='es', stop=1):
        link.append(url)

    link = str(link[0])
    link = link.split("/")
    if link[-1] == '':
        ticker = link[-2]
    else:
        x = link[-1].split('=')
        ticker = x[-1]

    # print(f"company name: {company_name}, ticker: {ticker}")

    return ticker


def add_string_to_path(file_path: Path, string: str) -> Path:
    """
    Add a string to a name for a file, for example: from data.csv to data1.csv
    :param file_path:
    :param string:
    :return:
    """
    file_name = file_path.name
    name, suffix = file_name.split(sep='.')
    new_file_name = name + string + '.' + suffix
    return file_path.parent/new_file_name


def get_company_tickers(company_path: Path, output_path: Path):
    """
    Get the stock data in 10 years
    :param company_path: path to the csv file that contains the names of the companies
    :param output_path: the path to save the ticker data to
    :return:
    """
    if output_path.exists():
        log.info(f"{output_path} exists, do nothing")
        return

    log.info("Getting company tickers from names...")
    df = pd.read_csv(company_path)
    company_names = df['Company'].to_list()
    names_tickers = {}

    counter = 0
    for company in tqdm(company_names):
        try:
            ticker = name_convert(company)
            names_tickers[company] = ticker
        except Exception as ex:
            log.exception(ex)
            names_tickers[f'err{counter}'] = ' '
        counter += 1
        if counter % 100 == 0:
            # save the names and tickers every 100 iterations
            new_output_path = add_string_to_path(output_path, str(int(counter/100)))
            df = pd.DataFrame.from_dict(data=names_tickers, orient='index')
            df.to_csv(new_output_path, header=False)

    # save the final file to the path
    df = pd.DataFrame.from_dict(data=names_tickers, orient='index')
    df.to_csv(output_path, header=False)


def process_tickers(tickers_path: Path, output_path: Path):
    """
    Process the companies' ticker data
    :param tickers_path: the path of the ticker data .csv file
    :param output_path: the path to save the processed tickers data
    :return:
    """
    if output_path.exists():
        log.info(f"{output_path} exists, do nothing")
        return

    df = pd.read_csv(tickers_path, header=None)
    tickers = df[1]
    output = deepcopy(df)

    invalid_tickers = [(i, t) for (i, t) in enumerate(tickers)
                       if '.html' in t or t == 'history' or t == 'profile' or t == 'news' or t == '1']
    invalid_indexes = [x[0] for x in invalid_tickers]
    invalid_companies = [(i, df[0][i]) for i in invalid_indexes]
    if len(invalid_companies) > 0:
        log.warning(f"These companies have invalid tickers: {invalid_companies}")
        output.drop(invalid_indexes, axis=0, inplace=True)

    # drop duplicated values
    output.drop_duplicates(1, keep='first', inplace=True)
    log.info(f"Remove {len(df)-len(output)} companies that have invalid tickers, "
             f"there are {len(output)} companies left")

    # save the processed data to csv file
    log.info(f"Save processed tickers to {output_path}")
    output.to_csv(output_path, header=False, index=False)


def get_stock_data(tickers_path: Path, output_path: Path, fill_na=False):
    """
    Get the stock data for the companies with tickers in in the tickers_path
    :param tickers_path:
    :param output_path:
    :param fill_na:
    :return:
    """
    if output_path.exists():
        log.info(f"{output_path} exists, do nothing")
        return

    df = pd.read_csv(tickers_path, header=None)
    tickers = df[1].to_list()

    stocks = []
    for t in tqdm(tickers):
        df_t = pd.DataFrame(download_stock_data(t))
        df_t.rename(columns={'Open': t}, inplace=True)
        if len(df_t) > 0:
            stocks.append(df_t)
        else:
            log.info(f"No stock data found for {t}. Skip it")

    try:
        output_df = reduce(lambda left, right: left.merge(right, how='left', on='Date'), stocks)
        if fill_na:
            output_df.fillna(0, inplace=True)
        output_df.to_csv(output_path, header=True, index=True)
        log.info(f"Save stock data of tickers to {output_path}")
    except Exception as e:
        ex_type, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)
        log.exception(e)


def download_stock_data(ticker: str):
    data = yf.download(tickers=ticker, period="10y", interval="1d")
    return data['Open']


def plot_data_df(df_path: Path, tickers: List):
    df = pd.read_csv(df_path, index_col='Date')
    plt.xlabel('Date')
    plt.ylabel('')
    for t in tickers:
        # if in debug mode, then use plt.ion()
        df[t].plot(legend=True)
    plt.show()
