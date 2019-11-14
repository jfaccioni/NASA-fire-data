# Settings used for passing arguments to main function on main.py
SETTINGS = {
    'input_dir': 'data',     # where the zip files are located
    'output_dir': 'output',  # where to save output (if any)

    'value_filter': True,    # True for filtering rows by columns whose values are higher than cutoff value
    'value_column': 'year',  # column for filtering
    'cutoff_value': 2015,    # filter selects values higher than this

    'percentile_filter': False,  # True for filtering rows by columns whose values are above percentile cutoff value
    'percentile_column': 'frp',  # column for filtering
    'cutoff_percentile': 90,     # filter selects values above this percentile

    'analyse_top_frp': True,  # True for printing points close to top RFP points (takes a long time)

    'plot_data': False,  # True for plotting data as a scatter plot (lon x lat)
    'save_data': False  # True for saving csv after adding month/year column, filtering, etc
}
