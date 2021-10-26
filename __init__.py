__version__="0.0.2"
from gym.envs.registration import register
import pandas as pd
f='./data/split/GBPUSD/weekly/GBPUSD_2017_0.csv'
register(
     id='forex-trading-v0',
     entry_point='tradinggym.environments:tgym',
     kwargs={'df':pd.read_csv(f) }
)