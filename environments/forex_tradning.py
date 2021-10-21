import math
import datetime
import random
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
import pandas as pd
from stable_baselines3.common.vec_env import DummyVecEnv
from environments.render.plot_chart import TradingChart
from environments.render.log_render import render_to_file 

# from render.StockTradingGraph import StockTradingGraph


class tgym(gym.Env):
    """forex/future trading gym environment
    dt can be any unit from minutes to day. dt is the index of pd
    must have pd columns [(time_col),(asset_col), open,close,high,low,day]
    data_process will add additional time information: time(index), minute, hour, weekday, week, month,year, day(since 1970)
    use StopLoss and ProfitTaken to simplify the action,
    feed a fixed StopLoss (SL = 200) and PT = SL * ratio
    action space: [action[0,2],ratio[0,10]]
    rewards is point
        
    Reward, we want to incentivize profit that is sustained over long periods of time. 
    At each step, we will set the reward to the account balance multiplied by 
    some fraction of the number of time steps so far.
    The purpose of this is to delay rewarding the agent too fast in the early stages 
    and allow it to explore sufficiently before optimizing a single strategy too deeply. 
    It will also reward agents that maintain a higher balance for longer, 
    rather than those who rapidly gain money using unsustainable strategies.
    
    consider multiply assets
    use SL and PT for the action
    Action space that has a discrete number of action types (buy, sell, nothing), 
    floor(action) == 0 buy, 1 sell, 2 nothing
    PT = math.ceil(SL * (1 + (action - math.floor(action))
    
    Observation_space contains all of the input variables we want our agent to consider before making, 
    or not making a trade. We want our agent to “see” the forex data points 
    (open price, high, low, close, and daily volume) for the last five days, 
    as well a couple other data points like its account balance, current positions, and current profit.
    The intuition here is that for each time step, we want our agent to consider the price action 
    leading up to the current price, as well as their own portfolio’s status in order to make 
    an informed decision for the next action.
    1. df observation_list [open, high, low, close, hour, dayofweek, tech_indictors] * len(assets)      
    2. balance, total_equity, assets
        parameters
        **kwargs={
               "observation_list":[time,hour,dayofweek,open,high,low,close,rsi,ma...],
               "stop_loss_max: 300,
               "profit_taken_max: 1000,
               "balance":100000,
               "asset_col":"symbol",
               "time_col":"time",
               }
    """
    metadata = {'render.modes': ['live', 'human', 'file', 'none']}

    def __init__(self, df, **kwargs) -> None:
        assert df.ndim == 2
        super(tgym, self).__init__()
        self.observation_list = kwargs.get("observation_list")
        self.transaction_fee = kwargs.get("transaction_cost_pct", 10)
        self.over_night_penalty = kwargs.get("over_night_penalty", 10)
        self.over_night_cash_penalty = kwargs.get("over_night_penalty", 100)
        self.stop_loss_max = kwargs.get("stop_loss_max", 300)
        self.profit_taken_max = kwargs.get("profit_taken_max", 2500)
        self.balance_initial = kwargs.get("balance", 10000)
        self.asset_col = kwargs.get("asset_col", "symbol")
        self.time_col = kwargs.get("time_col", "time")
        self.point = kwargs.get("point", 100000)
        self.max_current_holding = kwargs.get("max_current_holding", 10)
        self.random_start = kwargs.get("random_start", True)
        self.log_filename = kwargs.get(
            'log_filename', './data/log/log_') + datetime.datetime.now(
            ).strftime('%Y%m%d%H%M%S') + '.csv'
        self.df = df
        self.df["_time"] = df[self.time_col]
        self.df["_day"] = df["day"]
        self.assets = df[self.asset_col].unique()
        self.dt_datetime = df[self.time_col].sort_values().unique()
        self.df = self.df.set_index(self.time_col)
        self.visualization = None
        # --- reset value ---
        self.equity_list = [0] * len(self.assets)
        self.balance = self.balance_initial
        self.total_equity = self.balance + sum(self.equity_list)
        self.ticket_id = 0
        self.transaction_live = []
        self.transaction_history = []
        self.current_draw_downs = [0.0] * len(self.assets)
        self.max_draw_downs = [0.0] * len(self.assets)
        self.max_draw_down_pct = sum(self.max_draw_downs) / self.balance * 100
        self.current_step = 0
        self.episode = -1
        self.current_holding=0
        self.tranaction_open_this_step = []
        self.tranaction_close_this_step = []
        self.current_day = 0
        self.done_information = ''
        self.log_header = True
        # --- end reset ---
        self.cached_data = [
            self.get_observation_vector(_dt) for _dt in self.dt_datetime
        ]
        self.cached_time_serial = ((self.df[[
            "_time", "_day"
        ]].sort_values("_time")).drop_duplicates()).values.tolist()
        self.reward_range = (-np.inf, np.inf)
        self.action_space = spaces.Box(low=0,
                                       high=3,
                                       shape=(len(self.assets), ))
        # first two 3 = balance,current_holding, max_draw_down_pct
        _space = 3 + len(self.assets) \
                 + len(self.assets) * len(self.observation_list)
        self.observation_space = spaces.Box(low=-np.inf,
                                            high=np.inf,
                                            shape=(_space, ))
        print(
            f'initial done:\n'
            f'observation_list:{self.observation_list}\n '
            f'assets:{self.assets}\n '
            f'stop_loss_max:{self.stop_loss_max}\n'
            f'profit_taken_max: {self.profit_taken_max}\n'
            f'time serial: {min(self.dt_datetime)} -> {max(self.dt_datetime)} length: {len(self.dt_datetime)}'
        )
        self._seed()

    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def _take_action(self, actions, done):
        # action = math.floor(x),
        # profit_taken = math.ceil((x- math.floor(x)) * profit_taken_max - stop_loss_max )
        # _actions = np.floor(actions).astype(int)
        # _profit_takens = np.ceil((actions - np.floor(actions)) *self.profit_taken_max).astype(int)
        _action = 2
        _profit_taken = 0
        rewards = [0] * len(self.assets)
        self.tranaction_open_this_step = []
        self.tranaction_close_this_step = []
        # need use multiply assets
        for i, x in enumerate(actions):
            self._o = self.get_cached_observation(self.current_step, i, "open")
            self._h = self.get_cached_observation(self.current_step, i, "high")
            self._l = self.get_cached_observation(self.current_step, i, "low")
            self._c = self.get_cached_observation(self.current_step, i,
                                                  "close")
            self._t = self.get_cached_observation(self.current_step, i,
                                                  "_time")
            self._day = self.get_cached_observation(self.current_step, i,
                                                    "_day")
            _action = math.floor(x)
            rewards[i] = self._calculate_reward(i, done)
            if _action in (0, 1) and not done and self.current_holding < self.max_current_holding:
                # generating PT based on action fraction
                _profit_taken = math.ceil(
                    (x - _action) * self.profit_taken_max) + self.stop_loss_max
                self.ticket_id += 1
                transaction = {
                    "Ticket": self.ticket_id,
                    "Symbol": self.assets[i],
                    "ActionTime": self._t,
                    "Type": _action,
                    "Lot": 1,
                    "ActionPrice": self._c,
                    "SL": self.stop_loss_max,
                    "PT": _profit_taken,
                    "MaxDD": 0,
                    "Swap": 0.0,
                    "CloseTime": "",
                    "ClosePrice": 0.0,
                    "Point": 0,
                    "Reward": -self.transaction_fee,
                    "DateDuration": self._day,
                    "Status": 0
                }
                self.current_holding += 1
                self.tranaction_open_this_step.append(transaction)
                self.balance -= self.transaction_fee
                self.transaction_live.append(transaction)

        return sum(rewards)

    def _calculate_reward(self, i, done):
        _total_reward = 0
        _max_draw_down = 0
        for tr in self.transaction_live:
            if tr["Symbol"] == self.assets[i]:
                #cash discount overnight
                if self._day > tr["DateDuration"]:
                    tr["DateDuration"] = self._day
                    tr["Reward"] -= self.over_night_penalty

                if tr["Type"] == 0:  #buy
                    #stop loss trigger
                    _sl_price = tr["ActionPrice"] - tr["SL"] / self.point
                    _pt_price = tr["ActionPrice"] + tr["PT"] / self.point
                    if done:
                        p = (self._c - tr["ActionPrice"]) * self.point
                        self._manage_tranaction(tr, p, self._c, status=2)
                        _total_reward += p
                    elif self._l <= _sl_price:
                        self._manage_tranaction(tr, -tr["SL"], _sl_price)
                        _total_reward += -tr["SL"]
                        self.current_holding -= 1
                    elif self._h >= _pt_price:
                        self._manage_tranaction(tr, tr["PT"], _pt_price)
                        _total_reward += tr["PT"]
                        self.current_holding -= 1
                    else: # still open
                        self.current_draw_downs[i] = int(
                            (self._l - tr["ActionPrice"]) * self.point)
                        _max_draw_down += self.current_draw_downs[i]
                        if self.current_draw_downs[i] < 0:
                            if tr["MaxDD"] > self.current_draw_downs[i]:
                                tr["MaxDD"] = self.current_draw_downs[i]

                elif tr["Type"] == 1:  # sell
                    #stop loss trigger
                    _sl_price = tr["ActionPrice"] + tr["SL"] / self.point
                    _pt_price = tr["ActionPrice"] - tr["PT"] / self.point
                    if done:
                        p = (tr["ActionPrice"] - self._c) * self.point
                        self._manage_tranaction(tr, p, self._c, status=2)
                        _total_reward += p
                    elif self._h >= _sl_price:
                        self._manage_tranaction(tr, -tr["SL"], _sl_price)
                        _total_reward += -tr["SL"]
                        self.current_holding -= 1
                    elif self._l <= _pt_price:
                        self._manage_tranaction(tr, tr["PT"], _pt_price)
                        _total_reward += tr["PT"]
                        self.current_holding -= 1
                    else:
                        self.current_draw_downs[i] = int(
                            (tr["ActionPrice"] - self._h) * self.point)
                        _max_draw_down += self.current_draw_downs[i]
                        if self.current_draw_downs[i] < 0:
                            if tr["MaxDD"] > self.current_draw_downs[i]:
                                tr["MaxDD"] = self.current_draw_downs[i]
                       
                if _max_draw_down > self.max_draw_downs[i]:
                    self.max_draw_downs[i] = _max_draw_down

        return _total_reward

    def _manage_tranaction(self, tr, _point, close_price, status=1):
        self.transaction_live.remove(tr)
        tr["ClosePrice"] = close_price
        tr["Point"] = int(_point)
        tr["Reward"] = int(tr["Reward"] + _point)
        tr["Status"] = status
        tr["CloseTime"] = self._t
        self.balance += int(tr["Reward"])
        self.total_equity -= int(abs(tr["Reward"]))
        self.tranaction_close_this_step.append(tr)
        self.transaction_history.append(tr)

    def step(self, actions):
        # Execute one time step within the environment
        self.current_step += 1
        done = (self.balance <= 0
                or self.current_step == len(self.dt_datetime) - 1)
        if done:
            self.done_information += f'Episode: {self.episode} Balance: {self.balance} Step: {self.current_step}\n'
        reward = self._take_action(actions, done)
        if self._day > self.current_day:
            self.current_day = self._day
            self.balance -= self.over_night_cash_penalty
        if self.balance != 0:
            self.max_draw_down_pct = abs(
                sum(self.max_draw_downs) / self.balance * 100)

            # no action anymore
        obs = ([self.balance, self.current_holding, self.max_draw_down_pct] +
               self.current_draw_downs +
               self.get_cached_observation(self.current_step))
        return np.array(obs).astype(np.float32), reward, done, {
            "close": self.tranaction_close_this_step
        }

    def get_cached_observation(self, _step, _iter=0, col=None):
        if (col is None):
            return self.cached_data[_step]
        else:
            if col == '_time':
                return self.cached_time_serial[_step][0]
            elif col == '_day':
                return self.cached_time_serial[_step][1]

            col_pos = -1
            for i, _symbol in enumerate(self.observation_list):
                if _symbol == col:
                    col_pos = i
                    break
            assert col_pos >= 0
            return self.cached_data[_step][_iter * len(self.observation_list) +
                                           col_pos]

    def get_observation_vector(self, _dt, cols=None):
        cols = self.observation_list
        v = []
        for a in self.assets:
            subset = self.df.query(
                f'{self.asset_col} == "{a}" & {self.time_col} == "{_dt}"')
            assert not subset.empty
            v += subset.loc[_dt, cols].tolist()
        assert len(v) == len(self.assets) * len(cols)
        return v

    def reset(self):
        # Reset the state of the environment to an initial state
        self.seed()

        if self.random_start:
            self.current_step = random.choice(
                range(int(len(self.dt_datetime) * 0.5)))
        else:
            self.current_step = 0

        self.equity_list = [0] * len(self.assets)
        self.balance = self.balance_initial
        self.total_equity = self.balance + sum(self.equity_list)
        self.ticket_id = 0
        self.transaction_live = []
        self.transaction_history = []
        self.current_draw_downs = [0.0] * len(self.assets)
        self.max_draw_downs = [0.0] * len(self.assets)
        self.max_draw_down_pct = sum(self.max_draw_downs) / self.balance * 100
        self.episode = -1
        self.current_holding=0
        self.tranaction_open_this_step = []
        self.tranaction_close_this_step = []
        self.current_day = 0
        self.done_information = ''
        self.log_header = True

        _space = ([self.balance, self.current_holding, self.max_draw_down_pct] +
                  [0] * len(self.assets) +
                  self.get_cached_observation(self.current_step))
        return np.array(_space).astype(np.float32)

    def render(self, mode='live', title=None, **kwargs):
        # Render the environment to the screen
        if mode in ('human', 'file'):
            printout = False
            if mode == 'human':
                printout=True
            pm = {
                "log_header":self.log_header,
                "log_filename":self.log_filename,
                "printout":printout,
                "balance":self.balance,
                "balance_initial":self.balance_initial,
                "tranaction_close_this_step":self.tranaction_close_this_step,
                "done_information":self.done_information
            }
            render_to_file(**pm)
            if self.log_header : self.log_header = False
        elif mode == 'live':
            if self.visualization == None:
                self.visualization = TradingChart(self.df, title)

            if self.current_step > self.lookback_window_size:
                self.visualization.render(
                    self.current_step,
                    self.net_worth,
                    self.trades,
                    window_size=self.lookback_window_size)

    def close(self):
        if self.visualization != None:
            self.visualization.close()
            self.visualization = None

    def get_sb_env(self):
        e = DummyVecEnv([lambda: self])
        obs = e.reset()
        return e, obs