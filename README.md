# TradingGym

# Trading Gym (>Python 3.7)
Trading Gym is an open-source project for the development of deep reinforcement learning algorithms in the context of forex trading.
## Highlight of the project 
1. customized gym.env for forex trading, with three actions (buy,sell, nothing). rewards is forex point based and realized by stop loss (SL) and profit taken (PT). The SL is fixed by passing parameter and PT is AI learning to maximize the rewards. 
2. multiply pairs with same time frame, time frame can setup from 1M, 5M, 30M, 1H, 4H. Both over night cash penalty, transaction fee, transaction overnight penalty (SWAP) can be configured.
3. data process will split the data into daily, weekly or monthly time serial based. and will training in parallel by using Isaac or Ray (coming soon)
4. file log, console print-out and live graph are available for render 
## The trading environment:

`Candle Trading` is a trading environment with input ohlc (open, high,low,close candlestick/bar) data, it is very useful to forex (currency) trading. We use profit-taking (machine learning) and fixed stop-loss.

## Create your own `data_process`

To create your own data, you can use `data_process` base class which can be found in the file 'data/data_process.py'. 

## Compatibility with OpenAI gym

The tgym (trading environment) is inherited from OpenAI Gym. We aim to entirely base it upon OpenAI Gym architecture and propose Trading Gym as an additional OpenAI environment.

## Examples
ppo_test.ipynb