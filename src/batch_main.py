from src.main import main
from src.settings import SETTINGS


def batch_main():
    """Executes main function in a batch"""
    for year in (2015, 2016, 2017, 2018, 2019):
        SETTINGS['cutoff_value'] = year
        SETTINGS['log_name'] = f'{year}_log.txt'
        SETTINGS['csv_name'] = f'{year}_firepoints.csv'
        main(**SETTINGS)


if __name__ == '__main__':
    batch_main()
