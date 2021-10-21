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

## Create your own `DataGenerator`

To create your own data generator, it must inherit from the `DataGenerator` base class which can be found in the file 'tgym/core.py'. It consists of four methods. Only the private `_generator` method which defines the times series needs to be overridden. Example can be found at `examples/generator_random.py`. For only one product, the `_generator` method **must** yield a `(bid, ask)` tuple, one element at a time. For two or more products, you must return a tuple consisting of bid and ask prices for each product, concatenated. For instance for two products, the method should yield `(bid_1, ask_1, bid_2, ask_2)`. The logic for the time series is encoded there.

## Compatibility with OpenAI gym

The tgym (trading environment) is inherited from OpenAI Gym. We aim to entirely base it upon OpenAI Gym architecture and propose Trading Gym as an additional OpenAI environment.

## Examples
ppo_test.ipynb