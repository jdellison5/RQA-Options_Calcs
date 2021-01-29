# -*- coding: utf-8 -*-
"""
Created on Thu Jan 28 16:03:44 2021

@author: jdell
"""

import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
import datetime
import yfinance as yf


path = "C:\\Temp\\"

ticker = 'SPY'
symbol = yf.Ticker(ticker)
options_dates = symbol.options

full_chain_df = pd.DataFrame()

for date in options_dates:
    options = symbol.option_chain(date=date)
    df_calls = options[0]
    df_puts = options[1]
    full_chain_df = pd.concat([full_chain_df,df_calls,df_puts], axis=0)
#full_chain_df.to_csv(path+'SPY_options.csv')

price_data = yf.download(tickers=ticker, period='30y', interval='1d')
adj_close = price_data['Adj Close']



df = full_chain_df

df['Underlying_Ticker'] = ticker

#Munge contract specs
contract_list = list(df['contractSymbol'])
tickers_list = [i[:len(ticker)] for i in contract_list]
expiry_list = [i[len(ticker):len(ticker)+6] for i in contract_list]
option_type_list = [i[len(ticker)+6:len(ticker)+6+3] for i in contract_list]

year_df = pd.DataFrame([i[:2] for i in expiry_list])
month_df = pd.DataFrame([i[2:4] for i in expiry_list])
day_df = pd.DataFrame([i[4:] for i in expiry_list])
expiry_df = pd.concat([year_df,month_df,day_df],axis=1)
expiry_df.columns = ['Y','M','D']
expiry_df['Expiry'] = pd.to_datetime(expiry_df.M+expiry_df.D+expiry_df.Y)
expiry_df

df = df.reset_index()
df['Expiry'] = expiry_df['Expiry']
df['Contract_Type'] = pd.DataFrame(option_type_list)
todays_date = datetime.datetime.now().strftime("%Y-%m-%d")
df['Data_Date'] = todays_date
df['Data_Date'] = pd.to_datetime(df['Data_Date'])
df['Days_to_Expiry'] = df['Expiry'] - df['Data_Date']
#df.to_csv(path+ticker+'_options_chain.csv')


import RQA_Option_Greeks as greeks
from RQA_Stock_Fundamentals import CurrentFundamentalSnap



fd = CurrentFundamentalSnap(symbols=[ticker])
annualized_dividend_yield = float(fd.getFundamentalSnapshot()['Dividend %'][0])/100
last_close = adj_close[-1]
annual_RF_rate = 0.02
delta_list = []
gamma_list = []

for i in df.index:
    #print(i)
    option_type = df['Contract_Type'][i][0].lower()    
    strike = df['strike'][i]
    time_to_expiry_years = df['Days_to_Expiry'][i]/datetime.timedelta(days=365)
    implied_vol = df['impliedVolatility'][i]      
    
    
    delta = greeks.delta(flag=option_type, 
                  S=last_close, 
                  K=strike, 
                  t=time_to_expiry_years, 
                  r=annual_RF_rate,
                  sigma=implied_vol, 
                  q=annualized_dividend_yield)
                  
    delta_list.append(delta)
    
    gamma = greeks.gamma(flag=option_type, 
                  S=last_close, 
                  K=strike, 
                  t=time_to_expiry_years, 
                  r=annual_RF_rate,
                  sigma=implied_vol, 
                  q=annualized_dividend_yield)
    
    gamma_list.append(gamma)


df['Delta'] = pd.DataFrame(delta_list)
df['Gamma'] = pd.DataFrame(gamma_list)

df['Delta_Exposure'] = df['openInterest'] * df['Delta']
df['Gamma_Exposure'] = df['openInterest'] * df['Gamma']

delta_exposure = df['Delta_Exposure'].sum(axis=0)
gamma_exposure = df['Gamma_Exposure'].sum(axis=0)

print(f"Net Delta Exposure: {delta_exposure}")
print(f"Net Gamma Exposure: {gamma_exposure}")
