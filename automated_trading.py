#Event driven trading engine implementation

#Event - The Event is the fundamental class unit of the event-driven system. 
#It contains a type (such as "MARKET", "SIGNAL", "ORDER" or "FILL") that determines how it will be handled within the event-loop.

# event.py
from __future__ import print_function
class Event(object): 
  """
  Event is base class providing an interface for all subsequent (inherited) events, that will trigger further events in the
  trading infrastructure. """
  pass

#MarketEvent
#MarketEvents are triggered when the outer while loop of the backtesting system begins a new "heartbeat".

# event.py
class MarketEvent(Event): 
  """
  Handles the event of receiving a new market update with
  corresponding bars.
  """
  def __init__(self):
     """
     Initialises the MarketEvent. 
     """
     self.type = ’MARKET’
    
#SignalEvent
#The Strategy object utilises market data to create new SignalEvents. 
#The SignalEvent contains a strategy ID, a ticker symbol, a timestamp for when it was generated, a direction (long or short) 
#and a "strength" indicator (this is useful for mean reversion strategies).

# event.py
class SignalEvent(Event): 
  """
  Handles the event of sending a Signal from a Strategy object. This is received by a Portfolio object and acted upon.
  """
  def __init__(self, strategy_id, symbol, datetime, signal_type, strength): 
    """
    Initialises the SignalEvent.
    Parameters:
    strategy_id - The unique identifier for the strategy that
    generated the signal.
    symbol - The ticker symbol, e.g. ’GOOG’.
    datetime - The timestamp at which the signal was generated.
    signal_type - ’LONG’ or ’SHORT’.
    strength - An adjustment factor "suggestion" used to scale
    quantity at the portfolio level. Useful for pairs strategies.
    """
    self.type = ’SIGNAL’ 
    self.strategy_id = strategy_id 
    self.symbol = symbol
    self.datetime = datetime
    self.signal_type = signal_type
    self.strength = strength

 
#OrderEvent
#When a Portfolio object receives SignalEvents it assesses them in the wider context of the portfolio, in terms of risk and position sizing. 
#This ultimately leads to OrderEvents that will be sent to an ExecutionHandler.

# event.py
class OrderEvent(Event): 
  """
  Handles the event of sending an Order to an execution system.
  The order contains a symbol (e.g. GOOG), a type (market or limit),
  quantity and a direction.
  """
  def __init__(self, symbol, order_type, quantity, direction):
    """
    Initialises the order type, setting whether it is
    a Market order (’MKT’) or Limit order (’LMT’), has
    a quantity (integral) and its direction (’BUY’ or
    ’SELL’).
    Parameters:
    symbol - The instrument to trade.
    order_type - ’MKT’ or ’LMT’ for Market or Limit.
    quantity - Non-negative integer for quantity.
    direction - ’BUY’ or ’SELL’ for long or short.
    """
    self.type = ’ORDER’ 
    self.symbol = symbol 
    self.order_type = order_type 
    self.quantity = quantity 
    self.direction = direction
    
  def print_order(self): 
    """
    Outputs the values within the Order. 
    """
    print("Order: Symbol=%s, Type=%s, Quantity=%s, Direction=%s" %
          (self.symbol, self.order_type, self.quantity, self.direction) 
         )
    
#FillEvent
#When an ExecutionHandler receives an OrderEvent it must transact the order. 
#Once an order has been transacted it generates a FillEvent, 
#which describes the cost of purchase or sale as well as the transaction costs, such as fees or slippage.

# event.py
class FillEvent(Event): 
  """
  Encapsulates the notion of a Filled Order, as returned
  from a brokerage. Stores the quantity of an instrument
  actually filled and at what price. In addition, stores
  the commission of the trade from the brokerage.
  """
  def __init__(self, timeindex, symbol, exchange, quantity, 
               direction, fill_cost, commission=None):
    """
    Initialises the FillEvent object. Sets the symbol, exchange, quantity, direction, cost of fill and an optional commission.
    If commission is not provided, the Fill object will
    calculate it based on the trade size and Interactive
    Brokers fees.
    Parameters:
    timeindex - The bar-resolution when the order was filled.
    symbol - The instrument which was filled.
    exchange - The exchange where the order was filled.
    quantity - The filled quantity.
    direction - The direction of fill (’BUY’ or ’SELL’)
    fill_cost - The holdings value in dollars.
    commission - An optional commission sent from IB.
    """
    self.type = ’FILL’ 
    self.timeindex = timeindex 
    self.symbol = symbol
    self.exchange = exchange
    self.quantity = quantity
    self.direction = direction
    self.fill_cost = fill_cost
    # Calculate commission
    if commission is None:
      self.commission = self.calculate_ib_commission()
    else:
      self.commission = commission
 
def calculate_ib_commission(self):
  """
  Calculates the fees of trading based on an Interactive
  Brokers fee structure for API, in USD.
  This does not include exchange or ECN fees.
  Based on "US API Directed Orders": https://www.interactivebrokers.com/en/index.php? f=commission&p=stocks2
  """
  full_cost = 1.3
  if self.quantity <= 500:
    full_cost = max(1.3, 0.013 * self.quantity) 
  else: 
    # Greater than 500
    full_cost = max(1.3, 0.008 * self.quantity) 
  return full_cost

#Data Handler
#One of the goals of an event-driven trading system is to minimise duplication of code between the backtesting element and the live execution element.

# data.py
from __future__ import print_function

from abc import ABCMeta, abstractmethod 
import datetime
import os, os.path

import numpy as np 
import pandas as pd

from event import MarketEvent

# data.py

class DataHandler(object): 
  """
  DataHandler is an abstract base class providing an interface for all subsequent (inherited) data handlers (both live and historic).
  The goal of a (derived) DataHandler object is to output a generated set of bars (OHLCVI) for each symbol requested.
  This will replicate how a live strategy would function as current
  market data would be sent "down the pipe". Thus a historic and live system will be treated identically by the rest of the backtesting suite. 
  """
  __metaclass__ = ABCMeta
  
  @abstractmethod
  def get_latest_bar(self, symbol):
    """
    Returns the last bar updated.
    """
    raise NotImplementedError("Should implement get_latest_bar()")
  
  @abstractmethod
  def get_latest_bars(self, symbol, N=1):
    """
    Returns the last N bars updated.
    """
    raise NotImplementedError("Should implement get_latest_bars()")
    
  @abstractmethod
  def get_latest_bar_datetime(self, symbol):
    """
    Returns a Python datetime object for the last bar. 
    """
    raise NotImplementedError("Should implement get_latest_bar_datetime()")
  
  @abstractmethod 
  def get_latest_bar_value(self, symbol, val_type): 
    """
    Returns one of the Open, High, Low, Close, Volume or OI from the last bar.
    """
    raise NotImplementedError("Should implement get_latest_bar_value()")
  
  @abstractmethod
  def get_latest_bars_values(self, symbol, val_type, N=1):
    """
    Returns the last N bar values from the
    latest_symbol list, or N-k if less available. 
    """
    raise NotImplementedError("Should implement get_latest_bars_values()")
    
  @abstractmethod
  def update_bars(self):
    """
    Pushes the latest bars to the bars_queue for each symbol
    in a tuple OHLCVI format: (datetime, open, high, low,
    close, volume, open interest).
    """
    raise NotImplementedError("Should implement update_bars()")

# data.py
class HistoricCSVDataHandler(DataHandler):
  """
  HistoricCSVDataHandler is designed to read CSV files for each requested symbol from disk and provide an interface to obtain the "latest" bar in a manner identical to a live trading interface.
  """
  def __init__(self, events, csv_dir, symbol_list): 
    """
    Initialises the historic data handler by requesting the location of the CSV files and a list of symbols.
    It will be assumed that all files are of the form ’symbol.csv’, where symbol is a string in the list.
    Parameters:
    events - The Event Queue.
    csv_dir - Absolute directory path to the CSV files.
    symbol_list - A list of symbol strings.
    """
    self.events = events
    self.csv_dir = csv_dir
    self.symbol_list = symbol_list
    self.symbol_data = {}
    self.latest_symbol_data = {}
    self.continue_backtest = True
    self._open_convert_csv_files()
    
  # data.py
  def _open_convert_csv_files(self): 
    """
    Opens the CSV files from the data directory, converting
    them into pandas DataFrames within a symbol dictionary.
    For this handler it will be assumed that the data is taken from Yahoo. Thus its format will be respected. 
    """
    comb_index = None
    for s in self.symbol_list:
      # Load the CSV file with no header information, indexed on date 
      self.symbol_data[s] = pd.io.parsers.read_csv(os.path.join(self.csv_dir, ’%s.csv’ % s), header=0, index_col=0, parse_dates=True,
                                                 names=[’datetime’, ’open’, ’high’,’low’, ’close’, ’volume’, ’adj_close’]).sort()
      # Combine the index to pad forward values
      if comb_index is None:
        comb_index = self.symbol_data[s].index
      else: 
        comb_index.union(self.symbol_data[s].index)
      # Set the latest symbol_data to None
      self.latest_symbol_data[s] = []
      # Reindex the dataframes
      for s in self.symbol_list:
        self.symbol_data[s] = self.symbol_data[s].\
        reindex(index=comb_index, method=’pad’).iterrows()
        
    # data.py
    def _get_new_bar(self, symbol): 
      """
      Returns the latest bar from the data feed. 
      """
      for b in self.symbol_data[symbol]:
        yield b
    
    # data.py
    def get_latest_bar(self, symbol): 
      """
      Returns the last bar from the latest_symbol list.
      """ 
      try:
        bars_list = self.latest_symbol_data[symbol] 
        except KeyError:
          print("That symbol is not available in the historical data set.") 
          raise
        else:
          return bars_list[-1]
     def get_latest_bars(self, symbol, N=1): 
      """
      Returns the last N bars from the latest_symbol list,
      or N-k if less available. 
      """
      try:
        bars_list = self.latest_symbol_data[symbol] 
      except KeyError:
        print("That symbol is not available in the historical data set.")
        raise 
      else:
        return bars_list[-N:]
      
     #get_latest_bar_datetime, queries the latest bar for a datetime object representing the "last market price"
    def get_latest_bar_datetime(self, symbol): 
      """
      Returns a Python datetime object for the last bar. 
      """
      try:
        bars_list = self.latest_symbol_data[symbol]
        except KeyError:
          print("That symbol is not available in the historical data set.") 
          raise
        else:
          return bars_list[-1][0]
     
    #get_latest_bar_value and get_latest_bar_value
    def get_latest_bar_datetime(self, symbol): 
      """
      Returns a Python datetime object for the last bar. 
      """
      try:
        bars_list = self.latest_symbol_data[symbol]
      except KeyError:
        print("That symbol is not available in the historical data set.") 
        raise
      else:
        return bars_list[-1][0]
     
    def get_latest_bar_value(self, symbol, val_type): 
      """
      Returns one of the Open, High, Low, Close, Volume or OI
      values from the pandas Bar series object.
      """
      try:
        bars_list = self.latest_symbol_data[symbol]
      except KeyError:
        print("That symbol is not available in the historical data set.")
        raise 
      else:
        return getattr(bars_list[-1][1], val_type)
    
    def get_latest_bars_values(self, symbol, val_type, N=1): 
      """
      Returns the last N bar values from the latest_symbol list, or N-k if less available. 
      """
      try:
        bars_list = self.get_latest_bars(symbol, N) 
      except KeyError:
        print("That symbol is not available in the historical data set.")
        raise 
      else:
        return np.array([getattr(b[1], val_type) for b in bars_list])
  
    # data.py
    def update_bars(self): 
      """
      Pushes the latest bar to the latest_symbol_data structure for all symbols in the symbol list.
      """
      for s in self.symbol_list: 
        try:
          bar = next(self._get_new_bar(s)) 
        except StopIteration:
            self.continue_backtest = False 
        else:
          if bar is not None: 
            self.latest_symbol_data[s].append(bar)
            self.events.put(MarketEvent())
