from __future__ import absolute_import 
import logging
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from tgym.core import Env
from tgym.utils import calc_spread

plt.style.use('dark_background')
mpl.rcParams.update(
    {
        "font.size": 15,
        "axes.labelsize": 15,
        "lines.linewidth": 1,
        "lines.markersize": 8
    }
)
logging.basicConfig(filename='dqn.log',level=logging.INFO)
# create logger
logger = logging.getLogger('tx')
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)
logger.propagate = False

class TickTrading(Env):
    """Class for a discrete (buy/hold/sell) spread trading environment.
    """

    _actions = {
        'hold': np.array([1, 0, 0]),
        'buy': np.array([0, 1, 0]),
        'sell': np.array([0, 0, 1])
    }

    _positions = {
        'flat': np.array([1, 0, 0]),
        'long': np.array([0, 1, 0]),
        'short': np.array([0, 0, 1])
    }

    def __init__(self, data_generator, episode_length=1000, 
                trading_fee=0, time_fee=0, profit_taken = 20, stop_loss =-10, 
                reward_factor = 10000, history_length=2):
        """Initialisation function

        Args:
            data_generator (tgym.core.DataGenerator): A data
                generator object yielding a 1D array of bid-ask prices.
            episode_length (int): number of steps to play the game for
            trading_fee (float): penalty for trading
            time_fee (float): time fee
            history_length (int): number of historical states to stack in the
                observation vector.
        """

        assert history_length > 0
        self._data_generator = data_generator
        self._first_render = True
        self._trading_fee = trading_fee
        self._time_fee = time_fee
        self._episode_length = episode_length
        self.n_actions = 3
        self._prices_history = []
        self._history_length = history_length
        self._tick_buy =0
        self._tick_sell =0
        self._price = 0
        self._round_digits = 4
        self._holding_position =[] #[('buy',price, profit_taken, stop_loss),...]
        self._max_lost = -1000
        self._profit_taken = profit_taken
        self._stop_loss = stop_loss
        self._reward_factor = reward_factor
        self.reset()

    def reset(self):
        """Reset the trading environment. Reset rewards, data generator...

        Returns:
            observation (numpy.array): observation of the state
        """
        self._iteration = 0
        self._data_generator.rewind()
        self._total_reward = 0
        self._total_pnl = 0
        self._current_pnl = 0
        self._position = self._positions['flat']
        # self._entry_price = 0
        # self._exit_price = 0
        self._closed_plot = False
        self._holding_position =[]
        self._max_lost = -1000
        for i in range(self._history_length):
            self._prices_history.append(next(self._data_generator))

        self._tick_buy,self._tick_sell = self._prices_history[0]

        observation = self._get_observation()
        self.state_shape = observation.shape
        self._action = self._actions['hold']
        return observation

    def step(self, action):
        """Take an action (buy/sell/hold) and computes the immediate reward.

        Args:
            action (numpy.array): Action to be taken, one-hot encoded.

        Returns:
            tuple:
                - observation (numpy.array): Agent's observation of the current environment.
                - reward (float) : Amount of reward returned after previous action.
                - done (bool): Whether the episode has ended, in which case further step() calls will return undefined results.
                - info (dict): Contains auxiliary diagnostic information (helpful for debugging, and sometimes learning).

        """
        try:
            self._tick_buy,self._tick_sell  = next(self._data_generator)
            self._prices_history.append([self._tick_buy,self._tick_sell ])
        except StopIteration:
            done = True
            info['status'] = 'No more data.'

        self._action = action
        self._iteration += 1
        done = False
        instant_pnl = 0
        info = {}
        reward = -self._time_fee

        reward += self._add_position(action,self._profit_taken,self._stop_loss)
        reward += self._calculate_position()

        self._total_reward += reward

        # Game over logic
        if self._iteration >= self._episode_length:
            done = True
            info['status'] = 'Time out.'
        if reward <= self._max_lost:
            done = True
            info['status'] = 'Bankrupted.'
        if self._closed_plot:
            info['status'] = 'Closed plot'

        observation = self._get_observation()
        return observation, reward, done, info
    
    def _handle_close(self, evt):
        self._closed_plot = True

    def render(self, savefig=False, filename='myfig'):
        """Matlplotlib rendering of each step.

        Args:
            savefig (bool): Whether to save the figure as an image or not.
            filename (str): Name of the image file.
        """
        if self._first_render:
            self._f, self._ax = plt.subplots(
                1,
                sharex=True
            )

            self._ax = [self._ax]
            self._f.set_size_inches(12, 6)
            self._first_render = False
            self._f.canvas.mpl_connect('close_event', self._handle_close)

        #  price
        bid, ask = self._tick_buy,self._tick_sell
        self._ax[-1].plot([self._iteration, self._iteration + 1],
                          [bid, bid], color='white')
        self._ax[-1].plot([self._iteration, self._iteration + 1],
                          [ask, ask], color='white')
        ymin, ymax = self._ax[-1].get_ylim()
        yrange = ymax - ymin
        if (self._action == self._actions['sell']).all():
            self._ax[-1].scatter(self._iteration + 0.5, bid + 0.03 *
                                 yrange, color='orangered', marker='v')
        elif (self._action == self._actions['buy']).all():
            self._ax[-1].scatter(self._iteration + 0.5, ask - 0.03 *
                                 yrange, color='lawngreen', marker='^')
        plt.suptitle('TTL Reward: ' + "%.2f" % self._total_reward + 
                     '  No. Ttl/Curr Pstn: ' + "%.2f" % self._current_pnl + '/' + "%.2f" %  self._total_pnl + 
                     '  Pstn: ' + ['flat', 'long', 'short'][list(self._position).index(1)] +
                     '  Price: ' + "%.2f" % self._price + 
                     '  Tick:' + "%.2f" % self._iteration )
        self._f.tight_layout()
        plt.xticks(range(self._iteration)[::5])
        plt.xlim([max(0, self._iteration - 80.5), self._iteration + 0.5])
        plt.subplots_adjust(top=0.85)
        plt.pause(0.01)
        if savefig:
            plt.savefig(filename)

    def _get_observation(self):
        """Concatenate all necessary elements to create the observation.

        Returns:
            numpy.array: observation array.
        """
        return np.concatenate(
            [prices for prices in self._prices_history[-self._history_length:]] +
            [
                np.array([self._price]),
                np.array(self._position)
            ]
        )

    def _add_position(self,action,pr,ls):
        if all(action == self._actions['hold']): 
            self._position = self._positions['flat']
            return 0
        else:
            self._total_pnl += 1
            self._current_pnl += 1
            self._price = (self._tick_buy if all(action == self._actions['buy']) else self._tick_sell)
            bt = ('buy' if all(action == self._actions['buy']) else 'sell',self._price, pr, ls,self._total_pnl,self._iteration )
            self._holding_position.append(bt)
            self._position = (self._positions['long'] if all(action == self._actions['buy']) else self._positions['short']) 
            logger.info(('buy,' if all(action == self._actions['buy']) else 'sell,' ) + str(self._iteration) +',' + str(self._price))
            return -self._trading_fee
    
    def _close_position(self, position):
        middle_price = (self._tick_buy +self._tick_sell)/2.0
        pips = abs(round((middle_price - position[1]) * self._reward_factor, self._round_digits))
        pr = self._profit_taken
        st = self._stop_loss
        if position[0] == 'buy': 
            if middle_price < position[1]:
                pips = -pips
        if position[0] == 'sell': 
            if middle_price > position[1]:
                pips = -pips
        
        if pips >= pr:
            logger.info('profit_taken, ' + str(position) + ', ' + str(pips) )
            self._current_pnl -= 1
            return pr, True
        elif pips <= st:
            logger.info('stop_lost, ' + str(position) + ', ' + str(pips) )
            self._current_pnl -= 1
            return st, True
        else :
            #logger.info('nothing,' ) # + str(position) + ', ' + str(pips) )
            return pips, False

    def _calculate_position(self):
        rewards = 0
        result = []
        for position in self._holding_position:
            reward, remove = self._close_position(position)
            rewards += reward
            if not remove:
                result.append(position)
                
        self._holding_position = result
        return rewards

    @staticmethod
    def random_action_fun():
        """The default random action for exploration.
        We hold 80% of the time and buy or sell 10% of the time each.

        Returns:
            numpy.array: array with a 1 on the action index, 0 elsewhere.
        """
        return np.random.multinomial(1, [0.8, 0.1, 0.1])
