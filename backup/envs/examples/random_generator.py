"""
In this example we show how a random generator is coded.
All generators inherit from the DataGenerator class
The class yields tuple (bid_price,ask_price)
spread = ask_price - bid_price
limit range between range_low, range_high
better format for return value
"""
from __future__ import absolute_import 
import numpy as np
from tgym.core import DataGenerator
from tgym.gens.deterministic import RandomGenerator

if __name__ == "__main__":
    time_series_length = 100
    mygen = RandomGenerator(spread = 0.01,range_low =1.0,range_high=2.0)
    prices_time_series = [next(mygen) for _ in range(time_series_length)]
    print (prices_time_series)
