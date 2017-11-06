from __future__ import absolute_import 
from tgym.envs.trading_spread import SpreadTrading
from tgym.envs.trading_tick import TickTrading
from tgym.gens.csvstream import CSVStreamer

generator = CSVStreamer(filename='./examples/price_2.csv')

episode_length = 200

environment = SpreadTrading(spread_coefficients=[2, -1],
                            data_generator=generator,
                            episode_length=episode_length)

environment = TickTrading

#environment.render()
while True:
    action = input("Action: Buy (b) / Sell (s) / Hold (enter): ")
    if action == 'b':
        action = [0, 1, 0]
    elif action == 's':
        action = [0, 0, 1]
    else:
        action = [1, 0, 0]
    environment.step(action)
    environment.render()
