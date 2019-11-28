# Settings used for passing arguments to main function on main.py
SETTINGS = {
    # I/O SETTINGS
    'input_dir': 'data',     # where the zip files are located
    'output_dir': 'output',  # where to save output (if any)
    # FILTER SETTINGS
    'value_filter': True,    # True for filtering rows by columns whose values are higher than cutoff value
    'filter_type': 'equal',  # How to apply filter ('equal', 'below' or 'above')
    'value_column': 'year',  # column for filtering
    'cutoff_value': 2015,    # filter selects values higher than this
    # PERCENTILE SETTINGS
    'percentile_filter': False,  # True for filtering rows by columns whose values are above percentile cutoff value
    'percentile_column': 'frp',  # column for filtering
    'cutoff_percentile': 90,     # filter selects values above this percentile
    # ANALYSIS SETTINGS
    'analyse_column': 'frp',    # column for sorting top values
    'top_row_number': 100,       # number of top FirePoints to analyse
    'distance_cutoff': 10,      # distance (in kilometers) for considering a FirePoint as being close to another
    'temporal_cutoff': 30,      # time window (in days) for considering a FirePoint as being close to another
    'analyse_to_stdout': True,  # whether to print analysis results to standard output
    'analyse_to_log': True,     # whether or not to write analysis results to a log file
    'log_name': None,           # log file name (leave None for default)
    'analyse_to_csv': True,     # whether or not to write analysis results to a csv file
    'csv_name': None,           # csv file name (leave None for default)
    # PLOTTING SETTINGS
    'plot_data': False,  # True for plotting data as a scatter plot (lon x lat)
    'save_data': False  # True for saving csv after adding month/year column, filtering, etc
}
