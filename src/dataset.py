import pandas as pd
import requests
from pathlib import Path
import logging
from googlesearch import search
from tqdm import tqdm
import yfinance as yf
import matplotlib.pyplot as plt
import threading

thread_local = threading.local()

# A logger for this file
log = logging.getLogger(__name__)


def scraping_forbes_2000(output_path: str):
    """
    Get the data of 2000 companies from https://www.forbes.com/global2000/ and save to csv file
    :param output_path: the path to save the .csv file to
    """
    if Path(output_path).exists():
        log.info(f"{output_path} exists, do nothing")
    else:
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


def get_company_tickers(forbes_2000_path: str, output_path: Path):
    """
    Get the stock data in 10 years
    :param forbes_2000_path:
    :param output_path:
    :return:
    """
    df = pd.read_csv(forbes_2000_path)
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
        if counter % 10 == 0:
            # save the names and tickers
            new_output_path = add_counter_path(output_path, int(counter/10))
            df = pd.DataFrame.from_dict(data=names_tickers, orient='index')
            df.to_csv(new_output_path, header=False)


def add_counter_path(file_path: Path, counter: int) -> Path:
    """
    Add a counter to a name for a file, for example: from data.csv to data1.csv
    :param file_path:
    :param counter:
    :return:
    """
    file_name = file_path.name
    name, suffix = file_name.split(sep='.')
    new_file_name = name + str(counter) + '.' + suffix
    return file_path.parent/new_file_name


# def get_stock_data():
    # data = yf.download(tickers="nok", period="10y", interval="1d")
    # open_data = data['Open']
    # open_data.plot()
    # plt.show()
