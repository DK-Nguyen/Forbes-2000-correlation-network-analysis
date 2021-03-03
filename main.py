import hydra
from omegaconf import DictConfig
import logging
from pathlib import Path

from src import scraping_forbes_2000, get_company_tickers

# A logger for this file
log = logging.getLogger(__name__)


@hydra.main()
def main(cfg: DictConfig):
    PROJECT_DIR = Path(hydra.utils.get_original_cwd())
    forbes_2000_path = PROJECT_DIR/'data/forbes_2000.csv'
    tickers_path = PROJECT_DIR/'data/tickers.csv'

    scraping_forbes_2000(output_path=forbes_2000_path)
    get_company_tickers(forbes_2000_path, output_path=tickers_path)


if __name__ == '__main__':
    main()

