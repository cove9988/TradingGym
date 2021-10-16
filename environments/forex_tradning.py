import math
import random
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
import enum
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
    as well a couple other data points like its account balance, current stock positions, and current profit.
    The intuition here is that for each time step, we want our agent to consider the price action 
    leading up to the current price, as well as their own portfolio’s status in order to make 
    an informed decision for the next action.
    1. df observation_list [open, high, low, close, hour, dayofweek, tech_indictors] * len(assets)      
    2. balance, equity, assets
        parameters
        **kwargs={"assets":["gbpusd",""],
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
        self.df = df
        self.assets = kwargs.get("assets")
        self.observation_list = kwargs.get("observation_list")
        self.transaction_fee = kwargs.get("transaction_cost_pct") if kwargs.get("transaction_cost_pct") else 10
        self.over_night_penalty = kwargs.get(
            "over_night_penalty") if kwargs.get("over_night_penalty") else 10
        self.stop_loss_max = kwargs.get("stop_loss_max") if kwargs.get(
            "stop_loss_max") else 300
        self.profit_taken_max = kwargs.get("profit_taken_max") if kwargs.get(
            "profit_taken_max") else 2000
        self.balance = kwargs.get("balance") if kwargs.get(
            "balance") else 100000
        self.asset_col = kwargs.get("asset_col") if kwargs.get(
            "asset_col") else "symbol"
        self.time_col = kwargs.get("time_col") if kwargs.get(
            "time_col") else "time"
        self.point = kwargs.get("point") if kwargs.get("point") else 100000
        self.assets = df[self.asset_col].unique()
        self.dt = df[self.time_col].sort_values().unique()
        self.df = self.df.set_index(self.time_col)
        self.profit = 0.0
        self.equity = self.balance + self.profit
        self.visualization = None
        self.ticket_id = 0
        self.transaction = {
            "Symbol": "",
            "Ticket": 0,
            "ActionTime": "",
            "Type": "B",
            "Lot": 0.0,
            "ActionPrice": 0.0,
            "SL": 0.0,
            "TP": 0.0,
            "Swap": 0.0,
            "CloseTime": "",
            "ClosePrice": 0.0,
            "pip": 0,
            "reward": 0,
            "status": 0
        }
        self.transction_live = []
        self.transction_history = []
        self.max_draw_down = 0.0
        self.max_draw_down_pct = self.max_draw_down / self.balance * 100
        self.current_step = 0
        self.over_night_penalty_date = self.df.loc[self.current_step, "day"]
        self.reward_range = (-np.inf, np.inf)

        self.action_space = spaces.Box(low=0,
                                       high=3,
                                       shape=(len(self.assets), ))
        # 3 = balance, equity, max_draw_down_pct
        _space = 3 + len(
            self.assets) + len(self.assets) * len(self.observation_list)
        self.observation_space = spaces.Box(low=-np.inf,
                                            high=np.inf,
                                            shape=(_space, ))
        self.episode = -1
        self.starting_point = 0
        self.cached_data = None
        if self.cache_indicator_data:
            print("caching data")
            self.cached_data = [
                self.get_date_vector(i) for i, _ in enumerate(self.dt)
            ]
            print("data cached!")
    
    @property
    def current_step(self):
        return self.time_index - self.starting_point
    
    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def _next_observation(self):
        obs = (
            [self.balance,self.equity,self.max_draw_down_pct] + self.get_date_vector(self.time_index)
        )

        return obs

    def _take_action(self, actions):
        # action = math.floor(x),
        # profit_taken = math.ceil((x- math.floor(x)) * profit_taken_max - stop_loss_max )
        # _actions = np.floor(actions).astype(int)
        # _profit_takens = np.ceil((actions - np.floor(actions)) *self.profit_taken_max).astype(int)

        _action = 2
        _profit_taken = 0
        # need use multiply assets
        for i, x in enumerate(actions):
            _action = math.floor(x)
            _profit_taken = math.ceil((x - math.floor(x)) *
                                      self.profit_taken_max -
                                      self.stop_loss_max)
        if _action in (0, 1):  # buy sell
            self.ticket_id += 1
            self.transaction = {
                "Ticket": self.ticket_id,
                "Symbol": self.assets[i],
                "ActionTime": self._t,
                "Type": "B" if _action == 0 else "S",
                "Lot": 1,
                "ActionPrice": self._c,
                "SL": self.stop_loss_max,
                "TP": _profit_taken,
                "Swap": 0.0,
                "CloseTime": "",
                "ClosePrice": 0.0,
                "pip": 0,
                "reward": -self.transaction_fee,
                "status": 0
            }
            self.balance -= self.transaction_fee
            self.transction_live.append(self.transaction)
            self.balance = self.balance - self.transaction_fee

    def _calculate_reward(self):
        _total_reward = 0
        _max_draw_down = 0
        for tr in self.transction_live:
            #cash discount overnight
            if self._day > self.over_night_penalty_date:
                self.over_night_penalty_date = self._day
                self.balance -= self.over_night_penalty

            if tr["Type"] == "B":
                #stop loss trigger
                _sl_price = tr["ActionPrice"] - tr["SL"] / self.point
                _pt_price = tr["ActionPrice"] + tr["PT"] / self.point
                if _sl_price <= self._l:
                    self._manage_tranaction(self, tr, -tr["SL"], _sl_price)
                    _total_reward += -tr["SL"]
                elif _pt_price >= self._h:
                    self._manage_tranaction(self, tr, tr["TP"], _pt_price)
                    _total_reward += tr["TP"]
                _dd = np.int16((tr["ActionPrice"] - self._l) / self.point)
                if _dd < 0:
                    _max_draw_down += _dd

            elif tr["Type"] == "S":
                #stop loss trigger
                _sl_price = tr["ActionPrice"] + tr["SL"] / self.point
                _pt_price = tr["ActionPrice"] - tr["PT"] / self.point
                if _sl_price <= self._h:
                    self._manage_tranaction(self, tr, -tr["SL"], _sl_price)
                    _total_reward += -tr["SL"]
                elif _pt_price >= self._l:
                    self._manage_tranaction(self, tr, tr["TP"], _pt_price)
                    _total_reward += tr["TP"]

                _dd = int((self._h - tr["ActionPrice"]) / self.point)
                if _dd < 0:
                    _max_draw_down += _dd

        if abs(_max_draw_down) > self.max_draw_down:
            self.max_draw_down = abs(_max_draw_down)
            self.max_draw_down_pct = self.max_draw_down / self.balance * 100

        return _total_reward

    def _manage_tranaction(self, tr, pip, close_price):
        tr["ClosePrice"] = close_price
        tr["pip"] = pip
        tr["reward"] = tr["reward"] + pip
        tr["status"] = 1
        tr["CloseTime"] = self._t
        self.balance += tr["reward"]
        self.equity -= abs(tr["reward"])
        self.transction_live.remove[tr]
        self.transction_history.append(tr)

    def step(self, actions):
        self._o, = self.get_date_vector(self.current_step, "open")
        self._h = self.get_date_vector(self.current_step, "high")
        self._l = self.get_date_vector(self.current_step, "low")
        self._c = self.get_date_vector(self.current_step, "close")
        self._t = self.get_date_vector(self.current_step, "time")
        self._day = self.get_date_vector(self.current_step, "day")
        # Execute one time step within the environment
        
        self._calculate_reward()
         
        reward = self._take_action(actions)

        self.current_step += 1
        done = (self.balance <= 0 or self.equity <= 0)
        obs = self._next_observation()
        return obs, reward, done, {}

    def get_date_vector(self, dt, cols=None):
        if (cols is None) and (self.cached_data is not None):
            return self.cached_data[dt]
        else:
            dt = self.dates[dt]
            if cols is None:
                cols = self.daily_information_cols
            trunc_df = self.df.loc[dt]
            v = []
            for a in self.assets:
                subset = trunc_df[trunc_df[self.stock_col] == a]
                v += subset.loc[dt, cols].tolist()
            assert len(v) == len(self.assets) * len(cols)
            return v

    def reset(self):
        # Reset the state of the environment to an initial state
        self.balance = INITIAL_ACCOUNT_BALANCE
        self.net_worth = INITIAL_ACCOUNT_BALANCE
        self.max_net_worth = INITIAL_ACCOUNT_BALANCE
        self.shares_held = 0
        self.cost_basis = 0
        self.total_shares_sold = 0
        self.total_sales_value = 0
        self.current_step = 0
        self.trades = []
        self.visualization = None
        return self._next_observation()

    def _render_to_file(self, filename='render.txt'):
        profit = self.net_worth - INITIAL_ACCOUNT_BALANCE

        file = open(filename, 'a+')

        file.write(f'Step: {self.current_step}\n')
        file.write(f'Balance: {self.balance}\n')
        file.write(
            f'Shares held: {self.shares_held} (Total sold: {self.total_shares_sold})\n'
        )
        file.write(
            f'Avg cost for held shares: {self.cost_basis} (Total sales value: {self.total_sales_value})\n'
        )
        file.write(
            f'Net worth: {self.net_worth} (Max net worth: {self.max_net_worth})\n'
        )
        file.write(f'Profit: {profit}\n\n')

        file.close()

    def render(self, mode='live', title=None, **kwargs):
        # Render the environment to the screen
        if mode == 'human':
            profit = self.net_worth - INITIAL_ACCOUNT_BALANCE

            print(f'Step: {self.current_step}')
            print(f'Balance: {self.balance}')
            print(
                f'Shares held: {self.shares_held} (Total sold: {self.total_shares_sold})'
            )
            print(
                f'Avg cost for held shares: {self.cost_basis} (Total sales value: {self.total_sales_value})'
            )
            print(
                f'Net worth: {self.net_worth} (Max net worth: {self.max_net_worth})'
            )
            print(f'Profit: {profit}')
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