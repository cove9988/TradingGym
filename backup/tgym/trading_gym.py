from gym import Env
from gym.spaces import Discrete, Box
from gym.utils import seeding
import numpy as np
import random
from enum import Enum

class Actions(Enum):
    Sell = 0
    Hold = 1
    Buy = 2
    
class TradingGym(Env):
    metadata = {'render.modes':['human']}

    def __init__(self) -> None:
        super(TradingGym,self).__init__()
        
        self.n_actions = Discrete(len(Actions))  


    def reset(self) -> Any:
        self.balance = INITIAL_ACCOUNT_BALANCE
        self.net_worth =INITIAL_ACCOUNT_BALANCE
        self.max_net_worth=INITIAL_ACCOUNT_BALANCE
        self.cost=0
        self.total_holding = 0
        self.total_holding_value = 0
        self.current_step = random.randint(0,)
        
