import hydra
from omegaconf import DictConfig
import logging
from pathlib import Path

from src import scraping_forbes_2000, get_company_tickers, process_tickers, \
    get_stock_data, plot_data_df, stock_network

# A logger for this file
log = logging.getLogger(__name__)


@hydra.main()
def main(cfg: DictConfig):
    PROJECT_DIR = Path(hydra.utils.get_original_cwd())
    forbes_2000_path = PROJECT_DIR/'data/forbes_2000.csv'
    tickers_path = PROJECT_DIR/'data/tickers_v0.csv'
    processed_tickers_path = PROJECT_DIR/'data/tickers_v0_processed.csv'

    scraping_forbes_2000(output_path=forbes_2000_path)
    get_company_tickers(company_path=forbes_2000_path, output_path=tickers_path)
    process_tickers(tickers_path=tickers_path,
                    output_path=processed_tickers_path)

    stock_data_path = PROJECT_DIR/'data/stock_data_v1.csv'
    get_stock_data(tickers_path=processed_tickers_path,
                   output_path=stock_data_path)
    # plot_data_df(stock_data_path, tickers=['AAPL', 'MSFT', 'FB', 'GOOG', 'AMZN'])

    correlation_path = PROJECT_DIR/'data/stock_correlations_v3.csv'
    network_path = PROJECT_DIR/'data/stock_network_v3.gexf'
    stock_network(stock_data_path, correlation_path, network_path)


if __name__ == '__main__':
    main()
    # get_stock_data()
