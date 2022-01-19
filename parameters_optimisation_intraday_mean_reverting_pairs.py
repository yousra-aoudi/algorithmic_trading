#Optimisation of parameters that have a direct effect on profitability and risk metrics:
#Linear regression lookback period, the residuals z-score entry threshold and the residuals z-score exit threshold.
#Strategy of interest where we will apply this optimisation is the "Intraday Mean Reverting Equity Pairs Trade".

#We will consider a range of values for each parameter and then calculate a backtest for the strategy across each of these ranges, 
#outputting the total return, Sharpe ratio and drawdown characteristics of each simulation, to a CSV  le for each parameter set. 
#This will allow us to ascertain an optimised Sharpe or minimised max drawdown for our trading strategy.

