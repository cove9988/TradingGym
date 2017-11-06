import numpy as np
from tgym.core import DataGenerator


class WavySignal(DataGenerator):
    """Modulated sine generator
    """
    @staticmethod
    def _generator(period_1, period_2, epsilon, ba_spread=0):
        i = 0
        while True:
            i += 1
            bid_price = (1 - epsilon) * np.sin(2 * i * np.pi / period_1) + \
                epsilon * np.sin(2 * i * np.pi / period_2)
            yield bid_price, bid_price + ba_spread

class RandomGenerator(DataGenerator):
    
    @staticmethod
    def _generator(spread = 0.001,range_low =1.0,range_high=2.0, round_len = 4):
        while True:
            #val = np.random.randn()
            val = np.random.uniform(low = range_low, high=range_high)
            ask_price,bid_price  = round(val,round_len),round(val + spread,round_len)
            yield ask_price,bid_price 