from stable_baselines3.ppo import MlpPolicy
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3 import PPO

from env.StockTradingEnv import StockTradingEnv

import pandas as pd

model_name = "msft.model"
df = pd.read_csv('./data/MSFT.csv')
df = df.sort_values('Date')

    
# The algorithms require a vectorized environment to run
env = DummyVecEnv([lambda: StockTradingEnv(df)])

model = PPO(MlpPolicy, env, verbose=1)
model.learn(total_timesteps=25000)
model.save(model_name)
del model
model =PPO.load(model_name)
obs = env.reset()

for i in range(len(df['Date'])):
    action, _states = model.predict(obs)
    obs, rewards, done, info = env.step(action)
    env.render(mode='live')