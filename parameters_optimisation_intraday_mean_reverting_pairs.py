#Optimisation of parameters that have a direct effect on profitability and risk metrics:
#Linear regression lookback period, the residuals z-score entry threshold and the residuals z-score exit threshold.
#Strategy of interest where we will apply this optimisation is the "Intraday Mean Reverting Equity Pairs Trade".

#We will consider a range of values for each parameter and then calculate a backtest for the strategy across each of these ranges, 
#outputting the total return, Sharpe ratio and drawdown characteristics of each simulation, to a CSV  le for each parameter set. 
#This will allow us to ascertain an optimised Sharpe or minimised max drawdown for our trading strategy.

# intraday_mr.py
from __future__ import print_function 

import datetime
import numpy as np 
import pandas as pd
import statsmodels.api as sm

from strategy import Strategy
from event import SignalEvent
from backtest import Backtest
from hft_data import HistoricCSVDataHandlerHFT
from hft_portfolio import PortfolioHFT
from execution import SimulatedExecutionHandler

from itertools import product

class IntradayOLSMRStrategy(Strategy): 
  """
  Uses ordinary least squares (OLS) to perform a rolling linear regression 
  to determine the hedge ratio between a pair of equities.
  The z-score of the residuals time series is then calculated 
  in a rolling fashion and if it exceeds an interval of thresholds 
  (defaulting to [0.5, 3.0]) then a long/short signal pair are generated (for the high threshold)
  or an exit signal pair are generated (for the low threshold).
  """
  
  def __init__(self, bars, events, ols_window=100, zscore_low=0.5, zscore_high=3.0):
    """
    Initialises the stat arb strategy.
    Parameters:
    bars - The DataHandler object that provides bar information
    events - The Event Queue object.
    """
    self.bars = bars
    self.symbol_list = self.bars.symbol_list
    self.events = events
    self.ols_window = ols_window
    self.zscore_low = zscore_low
    self.zscore_high = zscore_high
    
    self.pair = (’AAPL’, ’MSFT’)
    self.datetime = datetime.datetime.utcnow()
    
    self.long_market = False
    self.short_market = False
    
  def calculate_xy_signals(self, zscore_last): 
    """
    Calculates the actual x, y signal pairings
    to be sent to the signal generator.
    Parameters
    zscore_last - The current zscore to test against
    """
    y_signal = None
    x_signal = None
    
    p0 = self.pair[0]
    p1 = self.pair[1]
    dt = self.datetime
    hr = abs(self.hedge_ratio)
    

if __name__ == "__main__":
  csv_dir = ’/path/csv/file’ # Path of the cvs
  symbol_list = [’AAPL’, ’MSFT’]
  initial_capital = 100000.0
  heartbeat = 0.0
  start_date = datetime.datetime(2021, 1, 1, 10, 41, 0)
  
  # Create the strategy parameter grid
  # using the itertools cartesian product generator
  strat_lookback = [50, 100, 200] 
  strat_z_entry = [2.0, 3.0, 4.0] 
  strat_z_exit = [0.5, 1.0, 1.5] 
  strat_params_list = list(product(strat_lookback, strat_z_entry, 
                                   strat_z_exit))
  
  # Create a list of dictionaries with the correct 
  # keyword/value pairs for the strategy parameters 
  strat_params_dict_list = [dict(ols_window=sp[0], zscore_high=sp[1], zscore_low=sp[2])
                            for sp in strat_params_list
                           ]
  # Carry out the set of backtests for all parameter combinations
  backtest = Backtest(csv_dir, symbol_list, initial_capital, heartbeat,
                      start_date, HistoricCSVDataHandlerHFT, SimulatedExecutionHandler, 
                      PortfolioHFT, IntradayOLSMRStrategy, strat_params_list=strat_params_dict_list
                     )
  backtest.simulate_trading()
  
  # backtest.py
  

