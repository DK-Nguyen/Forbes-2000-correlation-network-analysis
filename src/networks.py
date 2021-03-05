import pandas as pd
from pathlib import Path
import networkx as nx
from scipy.stats import pearsonr
from itertools import combinations
import logging
from tqdm import tqdm

# A logger for this file
log = logging.getLogger(__name__)


def stock_network(stock_data_path: Path, correlation_path: Path, network_path: Path):
    """
    Calculating the pairwise correlation of the stock values in the data
    load from stock_data_path
    :param stock_data_path: the path to load the stock data from
    :param correlation_path: the path to save the correlation data to
    :param network_path: the path to save the network to
    :return:
    """
    if correlation_path.exists():
        log.info(f'{correlation_path}, do nothing')
        return
    if network_path.exists():
        log.info(f'{network_path}, do nothing')
        return

    log.info(f"constructing stock network based from data in {stock_data_path}")
    df = pd.read_csv(stock_data_path, index_col='Date')
    tickers = df.columns

    G = nx.Graph()
    G.add_nodes_from(tickers)
    correlations = {}

    alpha = 0.001
    log.info(f'make an edge when |correlation| > 0.5')
    num_combinations = len(list(combinations(tickers, 2)))
    for ticker1, ticker2 in tqdm(combinations(tickers, 2), total=num_combinations):
        r, p = pearsonr(df[ticker1], df[ticker2])
        correlations[ticker1+'__'+ticker2] = r, p
        # if p < alpha:
        if r > 0.5 or r < -0.5:
            G.add_edge(ticker1, ticker2)

    corr_result = pd.DataFrame.from_dict(correlations, orient='index')
    corr_result.columns = ['PCC', 'p-value']
    nx.draw(G, node_size=50)

    log.info(f'number of nodes: {G.number_of_nodes()}')
    log.info(f'number of links: {G.number_of_edges()}')
    log.info(f'network density: {nx.density(G)}')

    # save the correlation data to csv file
    log.info(f"Save correlation data to {correlation_path}")
    corr_result.to_csv(correlation_path, header=True, index=True)
    # save the network to disk
    log.info(f"Save network to {network_path}")
    nx.write_gexf(G, network_path)
