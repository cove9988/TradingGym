"""
The aim of this file is to give a standalone example of how an environment  runs.
"""
import os
import numpy as np
from tgym.core import DataGenerator
from tgym.envs.trading_tick import TickTrading
from tgym.gens.deterministic import WavySignal, RandomGenerator
from tgym.gens.csvstream import CSVStreamer

gen_type = 'C'
if gen_type == 'W':
    generator = WavySignal(period_1=25, period_2=50, epsilon=-0.5,ba_spread = 0.0001 )
elif gen_type == 'R':
    generator = RandomGenerator(spread = 0.0001,range_low =1.0,range_high=2.0)
elif gen_type == 'C':
    filename = r'./examples/price_usdeur.csv'
    generator = CSVStreamer(filename=filename)   

episode_length = 200000
trading_fee = 0.2
time_fee = 0
# history_length number of historical states in the observation vector.
history_length = 2
profit_taken = 10
stop_loss = -5
render_show = False
environment = TickTrading(  data_generator=generator,
                            trading_fee=trading_fee,
                            time_fee=time_fee,
                            history_length=history_length,
                            episode_length=episode_length,
                            profit_taken = profit_taken,
                            stop_loss = stop_loss)

if render_show :
    environment.render()
i = 0
while True:
    #action = input("Action: Buy (b) / Sell (s) / Hold (enter): ")
    
    # if action == 'b':
    #     action = [0, 1, 0]
    # elif action == 's':
    #     action = [0, 0, 1]
    # else:
    #     action = [1, 0, 0]
    '''
    kind of random action
    '''
    action = [0, 1, 0] if i%7 == 0 else ([0, 0, 1] if i%13 == 0 else [1, 0, 0])
    
    environment.step(action)
    if render_show :
        environment.render()
    i += 1