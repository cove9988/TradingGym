import math
import random
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
import pandas as pd
# from render.StockTradingGraph import StockTradingGraph


# np.seterr(all='raise')
class StockTradingGraph():
    pass


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
        self.transaction_fee = kwargs.get(
            "transaction_cost_pct") if kwargs.get(
                "transaction_cost_pct") else 10
        self.over_night_penalty = kwargs.get(
            "over_night_penalty") if kwargs.get("over_night_penalty") else 10
        self.stop_loss_max = kwargs.get("stop_loss_max") if kwargs.get(
            "stop_loss_max") else 300
        self.profit_taken_max = kwargs.get("profit_taken_max") if kwargs.get(
            "profit_taken_max") else 2000
        self.balance = kwargs.get("balance") if kwargs.get(
            "balance") else 10000
        self.asset_col = kwargs.get("asset_col") if kwargs.get(
            "asset_col") else "symbol"
        self.time_col = kwargs.get("time_col") if kwargs.get(
            "time_col") else "time"
        self.point = kwargs.get("point") if kwargs.get("point") else 100000
        self.random_start = kwargs.get("random_start") if kwargs.get(
            "random_start") else True
        self.cache_indicator_data = kwargs.get("cache_indicator_data") if kwargs.get(
            "cache_indicator_data") else True
        self.balance_initial = self.balance
        self.df = df
        self.df["_time"] = df[self.time_col]
        self.df["_day"] = df["day"]
        self.assets = df[self.asset_col].unique()
        self.dt_datetime = df[self.time_col].sort_values().unique()
        self.df = self.df.set_index(self.time_col)
        self.equity_list = [0] * len(self.assets)
        self.total_equity = self.balance + sum(self.equity_list)
        self.visualization = None
        self.ticket_id = 0
        self.transction_live = []
        self.transction_history = []
        self.max_draw_downs = [0.0] * len(self.assets)
        self.max_draw_down_pct = sum(self.max_draw_downs) / self.balance * 100
        self.starting_point= 0
        self.current_step = 0
        self.starting_point = 0
        self.episode = -1
        self.tranaction_open_this_step = []
        self.tranaction_close_this_step = []
        self.cached_data = [self.get_observation_vector(_dt) for _dt in self.dt_datetime]
        self.cached_time_serial = ((self.df[["_time","_day"]].sort_values("_time")).drop_duplicates()).values.tolist()
        self.reward_range = (-np.inf, np.inf)

        self.action_space = spaces.Box(low=0,
                                       high=3,
                                       shape=(len(self.assets), ))
        # first two 2 = balance, max_draw_down_pct
        _space = 2 + len(self.assets) \
                 + len(self.assets) * len(self.observation_list)
        self.observation_space = spaces.Box(low=-np.inf,
                                            high=np.inf,
                                            shape=(_space, ))
        print(f'initial done:\n \
            observation_list:{self.observation_list}\n \
            assets:{self.assets}\n \
            time serial: {min(self.dt_datetime)} -> {max(self.dt_datetime)} length: {len(self.dt_datetime)}')

    # @property
    # def current_step(self):
    #     return self.current_step - self.starting_point

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def _take_action(self, actions):
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
            self._o = self.get_cached_observation(self.current_step,i, "open")
            self._h = self.get_cached_observation(self.current_step,i, "high")
            self._l = self.get_cached_observation(self.current_step,i, "low")
            self._c = self.get_cached_observation(self.current_step,i, "close")
            self._t = self.get_cached_observation(self.current_step,i, "_time")
            self._day = self.get_cached_observation(self.current_step,i, "_day")
            _action = math.floor(x)
            _profit_taken = math.ceil((x - math.floor(x)) *
                                      self.profit_taken_max -
                                      self.stop_loss_max)
            rewards[i] = self._calculate_reward(i)
            if _action in (0, 1):  # buy sell
                self.ticket_id += 1
                transaction = {
                    "Ticket": self.ticket_id,
                    "Symbol": i,
                    "ActionTime": self._t,
                    "Type": _action,
                    "Lot": 1,
                    "ActionPrice": self._c,
                    "SL": self.stop_loss_max,
                    "PT": _profit_taken,
                    "Swap": 0.0,
                    "CloseTime": "",
                    "ClosePrice": 0.0,
                    "pip": 0,
                    "Reward": -self.transaction_fee,
                    "DateDuration":self._day,
                    "Status": 0
                }
                self.tranaction_open_this_step.append(transaction)
                self.balance -= self.transaction_fee
                self.transction_live.append(transaction)

        return sum(rewards)

    def _calculate_reward(self, i):
        _total_reward = 0
        _max_draw_down = 0
        for tr in self.transction_live:
            if tr["Symbol"] == i:
                #cash discount overnight
                if self._day > tr["DateDuration"]:
                    tr["DateDuration"] = self._day
                    tr["Reward"] -= self.over_night_penalty

                if tr["Type"] == 0:
                    #stop loss trigger
                    _sl_price = tr["ActionPrice"] - tr["SL"] / self.point
                    _pt_price = tr["ActionPrice"] + tr["PT"] / self.point
                    if _sl_price <= self._l:
                        self._manage_tranaction(tr, -tr["SL"], _sl_price)
                        _total_reward += -tr["SL"]
                    elif _pt_price >= self._h:
                        self._manage_tranaction(tr, tr["PT"], _pt_price)
                        _total_reward += tr["PT"]
                    _dd = int((tr["ActionPrice"] - self._l) / self.point)
                    if _dd < 0:
                        _max_draw_down += _dd

                elif tr["Type"] == 1:
                    #stop loss trigger
                    _sl_price = tr["ActionPrice"] + tr["SL"] / self.point
                    _pt_price = tr["ActionPrice"] - tr["PT"] / self.point
                    if _sl_price <= self._h:
                        self._manage_tranaction(tr, -tr["SL"], _sl_price)
                        _total_reward += -tr["SL"]
                    elif _pt_price >= self._l:
                        self._manage_tranaction(tr, tr["PT"], _pt_price)
                        _total_reward += tr["PT"]

                    _dd = int((self._h - tr["ActionPrice"]) / self.point)
                    if _dd < 0:
                        _max_draw_down += _dd

            if abs(_max_draw_down) > self.max_draw_downs[i]:
                self.max_draw_downs[i] = abs(_max_draw_down)

        return _total_reward

    def _manage_tranaction(self, tr, pip, close_price):
        self.transction_live.remove(tr)
        tr["ClosePrice"] = close_price
        tr["pip"] = pip
        tr["Reward"] = tr["Reward"] + pip
        tr["Status"] = 1
        tr["CloseTime"] = self._t
        self.balance += tr["Reward"]
        self.total_equity -= abs(tr["Reward"])
        self.tranaction_close_this_step.append(tr)
        self.transction_history.append(tr)

    def step(self, actions):
        # Execute one time step within the environment
        reward = self._take_action(actions)
        if self.balance > 0:
            self.max_draw_down_pct = sum(self.max_draw_downs) / self.balance * 100

        self.current_step += 1
        done = (self.balance <= 0 or self.total_equity <= 0
                or self.current_step >= len(self.dt_datetime) - 1)
        obs = ([self.balance, self.max_draw_down_pct] + self.equity_list +
               self.get_cached_observation(self.current_step))
        return np.array(obs).astype(np.float32), reward, done, {} 

    def get_cached_observation(self, _step, _iter = 0, col = None):
        if (col is None) :
            return self.cached_data[_step]
        else:
            if col == '_time':
                return self.cached_time_serial[_step][0]
            elif col == '_day':
                return self.cached_time_serial[_step][1]

            col_pos = -1
            for i, _symbol in enumerate(self.observation_list) :
                if _symbol == col:
                    col_pos = i
                    break
            assert col_pos >= 0
            return self.cached_data[_step][ _iter * len(self.observation_list) + col_pos]
        
    def get_observation_vector(self, _dt, cols=None):
        cols = self.observation_list
        v = []
        for a in self.assets:
            subset = self.df.query(f'{self.asset_col} == "{a}" & {self.time_col} == "{_dt}"')
            assert not subset.empty
            v += subset.loc[_dt, cols].tolist()
        assert len(v) == len(self.assets) * len(cols)
        return v

    def reset(self):
        # Reset the state of the environment to an initial state
        self.seed()
        if self.random_start:
            self.starting_point = random.choice(range(int(len(self.dt_datetime) * 0.5)))
        else:
            self.starting_point = 0

        self.current_step = self.starting_point
        self.balance = self.balance_initial
        self.equity_list = [0] * len(self.assets)
        self.total_equity = self.balance + sum(self.equity_list)
        self.visualization = None
        self.ticket_id = 0
        self.transaction = {}
        self.transction_live = []
        self.transction_history = []
        self.max_draw_downs = [0.0] * len(self.assets)
        self.max_draw_down_pct = sum(self.max_draw_downs) / self.balance * 100
        self.cached_data = [self.get_observation_vector(_dt) for _dt in self.dt_datetime]
        self.cached_time_serial = ((self.df[["_time","_day"]].sort_values("_time")).drop_duplicates()).values.tolist()
        self.episode += 1
        _space = ([self.balance, self.max_draw_down_pct] +
                [0] * len(self.assets) + self.get_cached_observation(self.current_step))
        return np.array(_space).astype(np.float32)

    def _render_to_file(self, filename='render.txt'):
        profit = self.balance - self.balance_initial

        file = open(filename, 'a+')
        log = f"Step: {self.current_step}   Balance: {self.balance}, Profit: {profit} MDD: {self.max_draw_down_pct}\n Open:\n{self.tranaction_open_this_step}\nClose:\{self.tranaction_close_this_step}"
        file.write(log)
        file.close()

    def render(self, mode='live', title=None, **kwargs):
        # Render the environment to the screen
        if mode == 'human':
            pass
        if mode == 'file':
            self._render_to_file(kwargs.get('filename', 'render.txt'))
        elif mode == 'live':
            if self.visualization == None:
                self.visualization = StockTradingGraph(self.df, title)

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
