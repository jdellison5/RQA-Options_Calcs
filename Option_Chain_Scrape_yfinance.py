# -*- coding: utf-8 -*-
"""
Created on Thu Jan 28 16:03:44 2021

@author: jdell
"""

import warnings

warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
import datetime
import yfinance as yf
import os
import pyarrow as pa
import pyarrow.parquet as pq

# Save data to Parquet file
# cdir = os.getcwd()[:15]
# if "jdell" in cdir:
#     base_path = "C:\\Users\\jdell\\Richmond Quantitative Advisors\\Andrew Holpe - The Answer 3.10\\"
# else:
#     base_path = (
#         "C:\\Users\\AHolp\\OneDrive - Richmond Quantitative Advisors\\The Answer 3.10\\"
#     )

# path = base_path + "03. Portfolio Analysis Working Files\\00.  Master Data Files\\"

path = ""


# ticker = '^GSPC'
ticker = "SPY"
symbol = yf.Ticker(ticker)
options_dates = symbol.options

full_chain_df = pd.DataFrame()

for date in options_dates:
    options = symbol.option_chain(date=date)
    df_calls = options[0]
    df_puts = options[1]
    full_chain_df = pd.concat([full_chain_df, df_calls, df_puts], axis=0)

price_data = yf.download(tickers=ticker, period="30y", interval="1d")
adj_close = price_data["Adj Close"]

df = full_chain_df

if ticker == "^GSPC":
    ticker = "SPX"
else:
    pass

df["Underlying_Ticker"] = ticker

# Munge contract specs
contract_list = list(df["contractSymbol"])
tickers_list = [i[: len(ticker)] for i in contract_list]
expiry_list = [i[len(ticker) : len(ticker) + 6] for i in contract_list]
option_type_list = [i[len(ticker) + 6 : len(ticker) + 6 + 3] for i in contract_list]

year_df = pd.DataFrame([i[:2] for i in expiry_list])
month_df = pd.DataFrame([i[2:4] for i in expiry_list])
day_df = pd.DataFrame([i[4:] for i in expiry_list])
expiry_df = pd.concat([year_df, month_df, day_df], axis=1)
expiry_df.columns = ["Y", "M", "D"]
expiry_df["Expiry"] = pd.to_datetime(expiry_df.M + expiry_df.D + expiry_df.Y)

df = df.reset_index()
df["Expiry"] = expiry_df["Expiry"]
df["Contract_Type"] = pd.DataFrame(option_type_list)
todays_date = datetime.datetime.now().strftime("%Y-%m-%d")
df["Data_Date"] = todays_date
df["Data_Date"] = pd.to_datetime(df["Data_Date"])
df["Days_to_Expiry"] = df["Expiry"] - df["Data_Date"]


import RQA_Option_Greeks as greeks
from RQA_Stock_Fundamentals import CurrentFundamentalSnap

last_close = adj_close[-1]
# fd = CurrentFundamentalSnap(symbols=[ticker])
# annualized_dividend_yield = float(fd.getFundamentalSnapshot()['Dividend %'][0])/100
annualized_dividend_yield = symbol.dividends[-4:].sum() / last_close
annual_RF_rate = 0.02
delta_list = []
gamma_list = []

for i in df.index:
    option_type = df["Contract_Type"][i][0].lower()
    strike = df["strike"][i]
    time_to_expiry_years = df["Days_to_Expiry"][i] / datetime.timedelta(days=365)
    implied_vol = df["impliedVolatility"][i]

    delta = greeks.delta(
        flag=option_type,
        S=last_close,
        K=strike,
        t=time_to_expiry_years,
        r=annual_RF_rate,
        sigma=implied_vol,
        q=annualized_dividend_yield,
    )

    delta_list.append(delta)

    gamma = greeks.gamma(
        flag=option_type,
        S=last_close,
        K=strike,
        t=time_to_expiry_years,
        r=annual_RF_rate,
        sigma=implied_vol,
        q=annualized_dividend_yield,
    )

    gamma_list.append(gamma)


time_stamp = datetime.datetime.now()

df["Delta"] = pd.DataFrame(delta_list)
df["Gamma"] = pd.DataFrame(gamma_list)

df["Delta_Exposure"] = df["openInterest"] * df["Delta"]
df["Gamma_Exposure"] = df["openInterest"] * df["Gamma"]

delta_exposure = df["Delta_Exposure"].sum(axis=0)
gamma_exposure = df["Gamma_Exposure"].sum(axis=0)

print(f"Net Delta Exposure: {delta_exposure}")
print(f"Net Gamma Exposure: {gamma_exposure}")

opt_v_share_vol = (df["volume"].sum() * 100) / price_data["Volume"][
    -1
]  # When over 0.4, NOPE_MAD provides a fairly good windo into predicting earnings behavior.
nope = 10000 * (df["volume"] * df["Delta"]).sum() / price_data["Volume"][-1]
print(f"Option vs. Shares - Volume: {opt_v_share_vol}")
print(f"NOPE: {nope}")
"""
Find today's deviation as compared to the MAD calculated by: [(today's NOPE) - (median NOPE of last 30 days)] / (median absolute deviation of last 30 days)
"""

Master_Options_df = pq.read_table(path + ticker + "_Options_Effects.parquet")
Master_Options_df = Master_Options_df.to_pandas()

option_effects_list = [
    time_stamp,
    delta_exposure,
    gamma_exposure,
    opt_v_share_vol,
    nope,
]
option_effects_df = pd.DataFrame(option_effects_list).transpose()
option_effects_df.columns = [
    "Date/Time",
    "Delta_Exposure",
    "Gamma_Exposure",
    "Opt_v_Share_Volume",
    "NOPE",
]

Master_Options_df = pd.concat([Master_Options_df, option_effects_df], axis=0)

option_pq = pa.Table.from_pandas(Master_Options_df)
pq.write_table(option_pq, path + ticker + "_Options_Effects.parquet")

print(Master_Options_df)
