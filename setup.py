from setuptools import find_packages, setup

setup(
    name='NASA fire data',
    version='0.1.0',
    packages=find_packages(), install_requires=['pandas', 'geopy', 'geopandas', 'matplotlib', 'numpy', 'seaborn']
)
