from copy import deepcopy
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines3.common import logger
from forex_trading import tgym

class bs3_env():
    def __init__(self,df, **kwargs) -> None:
        self.env = tgym(df,**kwargs)
         
    def get_sb_env(self):
        def get_self():
            return deepcopy(self.env)

        e = DummyVecEnv([get_self])
        obs = e.reset()
        return e, obs

    def get_multiproc_env(self, n=10):
        def get_self():
            return deepcopy(self.env)

        e = SubprocVecEnv([get_self for _ in range(n)], start_method="fork")
        obs = e.reset()
        return e, obs
    
    