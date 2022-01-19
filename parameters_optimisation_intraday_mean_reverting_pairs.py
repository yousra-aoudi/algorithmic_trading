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
from __future__ import print_function

import datetime 
import pprint 
try:
  import Queue as queue 
except ImportError:
  import queue 
import time

class Backtest(object): 
  """
  Enscapsulates the settings and components for carrying out
  an event-driven backtest.
  """
  
  def __init__(self, csv_dir, symbol_list, initial_capital,
             heartbeat, start_date, data_handler,
             execution_handler, portfolio, strategy
            ):
    """
    Initialises the backtest.
    Parameters:
    csv_dir - The hard root to the CSV data directory.
    symbol_list - The list of symbol strings.
    intial_capital - The starting capital for the portfolio. 
    heartbeat - Backtest "heartbeat" in seconds
    start_date - The start datetime of the strategy.
    data_handler - (Class) Handles the market data feed. 
    execution_handler - (Class) Handles the orders/fills for trades. 
    portfolio - (Class) Keeps track of portfolio current and prior positions.
    strategy - (Class) Generates signals based on market data.
    """
    self.csv_dir = csv_dir
    self.symbol_list = symbol_list
    self.initial_capital = initial_capital
    self.heartbeat = heartbeat
    self.start_date = start_date
    self.data_handler_cls = data_handler 
    self.execution_handler_cls = execution_handler 
    self.portfolio_cls = portfolio
    self.strategy_cls = strategy
    self.events = queue.Queue()
    self.signals = 0
    self.orders = 0
    self.fills = 0
    self.num_strats = 1
    self._generate_trading_instances()
   
  def _generate_trading_instances(self, strategy_params_dict):
    """
    Generates the trading instance objects from
    their class types.
    """
    print("Creating DataHandler, Strategy, Portfolio and ExecutionHandler for") 
    print("strategy parameter list: %s..." % strategy_params_dict) 
    
    self.data_handler = self.data_handler_cls(self.events, self.csv_dir, 
                                              self.symbol_list, self.header_strings
                                             )
    
    self.strategy = self.strategy_cls(self.data_handler, self.events, **strategy_params_dict)
    self.portfolio = self.portfolio_cls(self.data_handler, self.events, self.start_date,
                                        self.num_strats, self.periods, self.initial_capital
                                       )
    self.execution_handler = self.execution_handler_cls(self.events)
    
  def _run_backtest(self): 
    """ 
    Executes the backtest. 
    """
    i=0
    while True:
      i += 1 
      print (i)
      # Update the market bars
      if self.data_handler.continue_backtest == True: 
        self.data_handler.update_bars()
      else: 
        break
      # Handle the events
    while True: 
      try:
        event = self.events.get(False) 
      except queue.Empty:
        break
      else:
        if event is not None:
          if event.type == ’MARKET’: 
            self.strategy.calculate_signals(event) self.portfolio.update_timeindex(event)
          elif event.type == ’SIGNAL’: 
            self.signals += 1 self.portfolio.update_signal(event)
          elif event.type == ’ORDER’: 
            self.orders += 1
            self.execution_handler.execute_order(event)
          elif event.type == ’FILL’: 
            self.fills += 1
            self.portfolio.update_fill(event)
    
    time.sleep(self.heartbeat)
    
  def _output_performance(self): 
    """ 
    Outputs the strategy performance from the backtest.
    """ 
    self.portfolio.create_equity_curve_dataframe()
    print("Creating summary stats...")
    stats = self.portfolio.output_summary_stats()
    print("Creating equity curve...") 
    print(self.portfolio.equity_curve.tail(10)) 
    pprint.pprint(stats)
    print("Signals: %s" % self.signals) 
    print("Orders: %s" % self.orders) 
    print("Fills: %s" % self.fills)
    
 def simulate_trading(self):
  """
  Simulates the backtest and outputs portfolio performance. 
  """
  out = open("output/opt.csv", "w")
  spl = len(self.strat_params_list)
  for i, sp in enumerate(self.strat_params_list):
    print("Strategy %s out of %s..." % (i+1, spl)) 
    self._generate_trading_instances(sp)
    self._run_backtest()
    stats = self._output_performance()
    pprint.pprint(stats)
    
    tot_ret = float(stats[0][1].replace("%","")) 
    cagr = float(stats[1][1].replace("%",""))
    
    sharpe = float(stats[2][1])
    max_dd = float(stats[3][1].replace("%","")) 
    dd_dur = int(stats[4][1])
    
    out.write("%s,%s,%s,%s,%s,%s,%s,%s\n" % (sp["ols_window"], 
                                             sp["zscore_high"], 
                                             sp["zscore_low"],
                                             tot_ret, cagr, 
                                             sharpe, max_dd, 
                                             dd_dur
                                            )
             )
  out.close()
  
# plot_sharpe.py
import matplotlib.pyplot as plt 
import numpy as np

def create_data_matrix(csv_ref, col_index): 
  data = np.zeros((3, 3))
  for i in range(0, 3):
    for j in range(0, 3):
      data[i][j] = float(csv_ref[i*3+j][col_index]) 
  return data

if __name__ == "__main__":
  # Open the CSV file and obtain only the lines
  # with a lookback value of 100
  csv_file = open("/path/to/opt.csv", "r").readlines() csv_ref = [c.strip().split(",")
                                                                  for c in csv_file if c[:3] == "100"
                                                                 ]
  data = create_data_matrix(csv_ref, 5)
  
  fig, ax = plt.subplots()
  heatmap = ax.pcolor(data, cmap=plt.cm.Blues)
  row_labels = [0.5, 1.0, 1.5]
  column_labels = [2.0, 3.0, 4.0]
  
  for y in range(data.shape[0]):
    for x in range(data.shape[1]):
      plt.text(x + 0.5, y + 0.5, ’%.2f’ % data[y, x],
               horizontalalignment=’center’,
               verticalalignment=’center’,
              )
      
  plt.colorbar(heatmap)
  ax.set_xticks(np.arange(data.shape[0])+0.5, minor=False) 
  ax.set_yticks(np.arange(data.shape[1])+0.5, minor=False)
  ax.set_xticklabels(row_labels, minor=False) 
  ax.set_yticklabels(column_labels, minor=False)
  
  plt.suptitle(’Sharpe Ratio Heatmap’, fontsize=18) 
  plt.xlabel(’Z-Score Exit Threshold’, fontsize=14)
  
  
# plot_drawdown.py
import matplotlib.pyplot as plt 
import numpy as np

def create_data_matrix(csv_ref, col_index):
  data = np.zeros((3, 3)) for i in range(0, 3):
    for j in range(0, 3):
      data[i][j] = float(csv_ref[i*3+j][col_index])
  return data

if __name__ == "__main__":
  # Open the CSV file and obtain only the lines
  # with a lookback value of 100
  csv_file = open("/path/to/opt.csv", "r").readlines()
  csv_ref = [c.strip().split(",") for c in csv_file if c[:3] == "100"
            ]
  
  data = create_data_matrix(csv_ref, 6)
  fig, ax = plt.subplots()
  heatmap = ax.pcolor(data, cmap=plt.cm.Reds)
  row_labels = [0.5, 1.0, 1.5]
  column_labels = [2.0, 3.0, 4.0]

  for y in range(data.shape[0]):
    for x in range(data.shape[1]):
      plt.text(x + 0.5, y + 0.5, ’%.2f%%’ % data[y, x],
               horizontalalignment=’center’,
               verticalalignment=’center’,
              )
      
  plt.colorbar(heatmap)
  
  ax.set_xticks(np.arange(data.shape[0])+0.5, minor=False) 
  ax.set_yticks(np.arange(data.shape[1])+0.5, minor=False) 
  ax.set_xticklabels(row_labels, minor=False) 
  ax.set_yticklabels(column_labels, minor=False)
  
  plt.suptitle(’Maximum Drawdown Heatmap’, fontsize=18) 
  plt.xlabel(’Z-Score Exit Threshold’, fontsize=14) 
  plt.ylabel(’Z-Score Entry Threshold’, fontsize=14) 
  plt.show()

  

