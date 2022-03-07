import math
import datetime
import random
import json
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
import pandas as pd
from stable_baselines3.common.vec_env import DummyVecEnv,SubprocVecEnv
from env.util.plot_chart import TradingChart
from env.util.log_render import render_to_file
from env.util.read_config import EnvConfig
from env.util.action_enum import ActionEnum, form_action

class tgym(gym.Env):
    """
    Rewards 
        value[step...forward_window]   BUY     SELL    HOLD
        SL                             SL      SL      +
        PT                             PT      PT      -
        NN                             -       -       +
    """
    metadata = {'render.modes': ['graph', 'human', 'file']}
    env_id = "TradingGym-v9"
    def __init__(self, df, env_config_file='./env/config/gdbusd-test-9.json') -> None:
        super(tgym, self).__init__()
        self.cf = EnvConfig(env_config_file)
        self.observation_list = self.cf.env_parameters("observation_list")
        self.balance_initial = self.cf.env_parameters("balance")
        self.over_night_cash_penalty = self.cf.env_parameters("over_night_cash_penalty")
        self.asset_col = self.cf.env_parameters("asset_col")
        self.time_col = self.cf.env_parameters("time_col")
        self.random_start = self.cf.env_parameters("random_start")
        self.do_nothing = self.cf.env_parameters("do_nothing")
        self.log_filename = self.cf.env_parameters("log_filename") + \
            datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
        self.description = self.cf.env_parameters("description")
        self.shaping_reward = self.cf.env_parameters("shaping_reward")
        self.forward_window = self.cf.env_parameters("forward_window")
        self.backward_window = self.cf.env_parameters("backward_window")
        self.training = True
        self.df = df
        self.df_len = len(self.df)
        self.df["_time"] = df[self.time_col]
        self.df["_day"] = df["weekday"]
        self.asset = df[self.asset_col][0]
        self._profit_taken = self.cf.symbol(self.asset,"profit_taken_max")
        self._stop_loss = self.cf.symbol(self.asset,"stop_loss_max")
        self.dt_datetime = df[self.time_col].sort_values().unique()
        # self.dt_datetime = self.dt_datetime.insert(0,'step',range(0,len(self.dt_datetime)))
        self.df = self.df.set_index(self.time_col)
        self.episode = 0
        self.visualization = False
        self.reward_box = []
        if self.training:
            self._calculate_reward()
            
        # --- reset value ---
        self.reset()

        # --- for space configure ---
        self.reward_range = (self._stop_loss,self._profit_taken)
        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(high=60.0,low=0.0,shape=(self.backward_window,len(self.observation_list)))
        print(
            f'initial done:\n'
            f'observation_list:{self.observation_list}\n '
            f'asset:{self.asset}\n '
            f'time serial: {min(self.dt_datetime)} -> {max(self.dt_datetime)} length: {len(self.dt_datetime)}'
        )

    def _get_reward(self, _action):
        _s = self.current_step - self.backward_window
        return self.reward_box[_s][_action]

    def _take_action(self, action, done):
        if not self.training:
            self.tranaction_open_this_step = []
            self.tranaction_close_this_step = []

            self._o, self._c, self._h, self._l,self._t,self._day = self.df.iloc[self.current_step][["Open","Close","High","Low","_time","_day"]]


            if self.cf.symbol(self.asset,"limit_order") :
                self._limit_order_process(action, done)
            self._close_order(done)

            if action in (ActionEnum.BUY, ActionEnum.SELL) and not done \
                and self.current_holding < self.cf.symbol(self.asset,"max_current_holding"):
                self.ticket_id += 1
                if self.cf.symbol(self.asset,"limit_order"):
                    self.transaction_limit_order.append({
                        "Ticket": self.ticket_id,
                        "Symbol": self.asset,
                        "ActionTime": self._t,
                        "Type": action,
                        "Lot": 1,
                        "ActionPrice": self._l if action == ActionEnum.BUY else self._h,
                        "SL": self._stop_loss,
                        "PT": self._profit_taken,
                        "MaxDD": 0,
                        "Swap": 0.0,
                        "CloseTime": "",
                        "ClosePrice": 0.0,
                        "Point": 0,
                        "Reward": +self.cf.symbol(self.asset,"transaction_fee"),
                        "DateDuration": self._day,
                        "Status": 0,
                        "LimitStep":self.current_step,
                        "ActionStep":-1,
                        "CloseStep":-1,
                    })
                else:
                    transaction = {
                        "Ticket": self.ticket_id,
                        "Symbol": self.asset,
                        "ActionTime": self._t,
                        "Type": action,
                        "Lot": 1,
                        "ActionPrice": self._c,
                        "SL": self._stop_loss,
                        "PT": self._profit_taken,
                        "MaxDD": 0,
                        "Swap": 0.0,
                        "CloseTime": "",
                        "ClosePrice": 0.0,
                        "Point": 0,
                        "Reward": +self.cf.symbol(self.asset,"transaction_fee"),
                        "DateDuration": self._day,
                        "Status": 0,
                        "LimitStep":self.current_step,
                        "ActionStep":self.current_step,
                        "CloseStep":-1,
                    }
                    self.current_holding += 1
                    self.tranaction_open_this_step.append(transaction)
                    self.balance += self.cf.symbol(self.asset,"transaction_fee")
                    self.transaction_live.append(transaction)
        return self._get_reward(action) if self.training else 0

    def _close_order(self, done):
        closed = True
        for tr in self.transaction_live:
            _point = self.cf.symbol(self.asset,"point")
            #cash discount overnight
            if self._day > tr["DateDuration"]:
                tr["DateDuration"] = self._day
                tr["Reward"] += self.cf.symbol(self.asset,"over_night_penalty")

            if tr["Type"] == ActionEnum.BUY:  #buy
                #stop loss trigger
                _sl_price = tr["ActionPrice"] + tr["SL"] / _point
                _pt_price = tr["ActionPrice"] + tr["PT"] / _point
                if done:
                    p = (self._c - tr["ActionPrice"]) * _point
                    self._manage_tranaction(tr, p, self._c, status=2)
                elif self._l <= _sl_price:
                    self._manage_tranaction(tr, tr["SL"], _sl_price)
                elif self._h >= _pt_price:
                    self._manage_tranaction(tr, tr["PT"], _pt_price)
                else:
                    closed = False

            elif tr["Type"] == ActionEnum.SELL:  # sell
                #stop loss trigger
                _sl_price = tr["ActionPrice"] - tr["SL"] / _point
                _pt_price = tr["ActionPrice"] - tr["PT"] / _point
                if done:
                    p = (tr["ActionPrice"] - self._c) * _point
                    self._manage_tranaction(tr, p, self._c, status=2)
                elif self._h >= _sl_price:
                    self._manage_tranaction(tr, tr["SL"], _sl_price)
                elif self._l <= _pt_price:
                    self._manage_tranaction(tr, tr["PT"], _pt_price)
                else:
                    closed = False
        return closed

    def _calculate_reward(self):
        _point = self.cf.symbol(self.asset,"point")
        for _step in range(self.backward_window, self.df_len):
            buy_sl, buy_pt, sell_sl, sell_pt = False, False, False, False
            _c = self.df.iloc[_step]["Close"]
            i = _step + 1
            while i < self.df_len:
                _rr = {ActionEnum.BUY:0.0,ActionEnum.SELL:0.0,ActionEnum.HOLD:0.0,"Step":0}
                _h, _l = self.df.iloc[i][["High","Low"]]
                _sl_price = self._stop_loss/_point
                _pt_price = self._profit_taken/_point
                if not buy_sl and not buy_pt:
                    if _l <= _c + _sl_price :
                        buy_sl = True
                    elif _h > _c + _pt_price:
                        buy_pt = True
                        # print(self.current_step, 'Buy PT', i)
                    else:
                        pass
                elif buy_sl and buy_pt:
                    buy_pt = False
                else:
                    pass

                if not sell_sl and not sell_pt:    
                    if _h >=  _c - _sl_price: 
                        sell_sl = True
                    elif _l < _c - _pt_price :
                        # print(self.current_step, 'Sell PT', i)
                        sell_pt = True
                    else:
                        pass
                elif sell_sl and sell_pt:
                    sell_pt = False
                else:
                    # print((_c - row.High ) * _point , self._stop_loss,i, 'SELL --',self.current_step, action)
                    pass
                if (buy_pt or buy_sl) and (sell_pt or sell_sl):
                    break

                i += 1
        
            # print(f'current_step:{self.current_step} i {i} buy_sl: {buy_sl}, buy_pt: {buy_pt}, sell_sl: {sell_sl}, sell_pt: {sell_pt}')

            # if self.current_holding < self.cf.symbol(self.asset,"max_current_holding"):
            _sl = - self.shaping_reward * 2
            _pt = self.shaping_reward * 4
            if buy_sl :
                _rr[ActionEnum.BUY] = _sl
            elif buy_pt:
                _rr[ActionEnum.BUY] = _pt
            else:
                _rr[ActionEnum.BUY] = 0.0

            if sell_sl:
                _rr[ActionEnum.SELL] = _sl
            elif sell_pt:
                _rr[ActionEnum.SELL] = _pt
            else:
                _rr[ActionEnum.SELL] = 0.0

            if buy_sl or sell_sl:
                _rr[ActionEnum.HOLD] =  -_sl
            elif buy_pt or sell_pt:
                _rr[ActionEnum.HOLD] =  -_pt
            else:
                _rr[ActionEnum.HOLD] = self.shaping_reward * 0
            
            _rr["Step"] = _step
            self.reward_box.append(_rr)

    def _limit_order_process(self, _action, done):
        for tr in self.transaction_limit_order:
            if tr["Type"] != _action or done:
                self.transaction_limit_order.remove(tr)
                tr["Status"] = 3
                tr["CloseStep"]=self.current_step
                self.transaction_history.append(tr)
            else:
                if (tr["ActionPrice"] >= self._l and _action == 0) \
                    or (tr["ActionPrice"] <= self._h and _action == 1):
                    tr["ActionStep"]=self.current_step
                    self.current_holding += 1
                    self.balance += self.cf.symbol(self.asset,"transaction_fee")
                    self.transaction_limit_order.remove(tr)
                    self.transaction_live.append(tr)
                    self.tranaction_open_this_step.append(tr)
                elif tr["LimitStep"] + self.cf.symbol(self.asset,"limit_order_expiration") > self.current_step:
                    tr["CloseStep"]=self.current_step
                    tr["Status"] = 4
                    self.transaction_limit_order.remove(tr)
                    self.transaction_history.append(tr)

    def _manage_tranaction(self, tr, _p, close_price, status=1):
        self.transaction_live.remove(tr)
        tr["ClosePrice"] = close_price
        tr["Point"] = int(_p)
        tr["Reward"] = int(tr["Reward"] + _p)
        tr["Status"] = status
        tr["CloseTime"] = self._t
        self.balance += int(tr["Reward"])
        self.total_equity -= int(abs(tr["Reward"]))
        self.tranaction_close_this_step.append(tr)
        self.transaction_history.append(tr)
        self.current_holding -= 1

    def step(self, action):
        # Execute one time step within the environment
        self.current_step += 1
        done = (self.balance <= 0
                or self.current_step == len(self.df) - 1)
        if done:
            self.done_information += f'Episode: {self.episode} Balance: {self.balance} Step: {self.current_step}\n'
            self.visualization = True
        reward = self._take_action(action, done)
        if not self.training:
            if self._day > self.current_day:
                self.current_day = self._day
                self.balance -= self.over_night_cash_penalty
            if self.balance != 0:
                self.max_draw_down_pct = abs(
                    self.max_draw_downs / self.balance * 100)

        # no action anymore
        # print(f"step:{self.current_step}, action:{action}, reward :{reward}, balance: {self.balance} {self.max_draw_down_pct}")
        return self.get_observation(), reward, done, {
            "Close": self.tranaction_close_this_step
        }

    def reset(self):
        # Reset the state of the environment to an initial state
        self.current_step = self.backward_window
        self.equity_list = 0
        self.balance = self.balance_initial
        self.total_equity = self.balance + self.equity_list
        self.ticket_id = 0
        self.transaction_live = []
        self.transaction_history = []
        self.transaction_limit_order = []
        self.current_draw_downs = 0.0
        self.max_draw_downs = 0.0
        self.max_draw_down_pct = self.max_draw_downs / self.balance * 100
        self.current_holding = 0
        self.tranaction_open_this_step = []
        self.tranaction_close_this_step = []
        self.current_day = 0
        self.done_information = ''
        self.log_header = True
        self.visualization = False
        return self.get_observation()

    def get_observation(self):
            if self.current_step-self.backward_window <0 : 
                print(f'no enough data {self.current_step} -{self.backward_window}')
                return []
            else:
                _d = self.df.iloc[self.current_step-self.backward_window:self.current_step]
                return _d[self.observation_list].to_numpy()

    def render(self, mode='human', title=None, **kwargs):
        # Render the environment to the screen
        if mode in ('human', 'file'):
            printout = False
            if mode == 'human':
                printout = True
            pm = {
                "log_header": self.log_header,
                "log_filename": self.log_filename,
                "printout": printout,
                "balance": self.balance,
                "balance_initial": self.balance_initial,
                "tranaction_close_this_step": self.tranaction_close_this_step,
                "done_information": self.done_information
            }
            render_to_file(**pm)
            if self.log_header: self.log_header = False
        elif mode == 'graph' and self.visualization:
            print('plotting...')
            p = TradingChart(self.df, self.transaction_history)
            p.plot()

    def close(self):
        pass

    def get_sb_env(self):
        e = DummyVecEnv([lambda: self])
        obs = e.reset()
        return e, obs