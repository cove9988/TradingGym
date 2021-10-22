from stable_baselines3.ppo import MlpPolicy
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3 import PPO

from env.forex_trading import tgym

import pandas as pd
LOOKBACK_WINDOW_SIZE = 40

model_name = "msft.model"
df = pd.read_csv('./data/raw/MSFT.csv')
df = df.sort_values('Date')

    
# The algorithms require a vectorized environment to run
env = DummyVecEnv([lambda: tgym(df,LOOKBACK_WINDOW_SIZE)])

model = PPO(MlpPolicy, env, verbose=1)
model.learn(total_timesteps=50)
model.save(model_name)
del model
model =PPO.load(model_name)
obs = env.reset()

for i in range(len(df['Date'])):
    action, _states = model.predict(obs)
    obs, rewards, done, info = env.step(action)
    env.render(mode='live')