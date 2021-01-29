# -*- coding: utf-8 -*-
"""
Created on Fri Jan 29 11:01:05 2021

@author: jdell
"""


import pandas as pd
import numpy as np
from bs4 import BeautifulSoup as soup
from urllib.request import Request, urlopen
import os

pd.set_option('display.max_colwidth', 25)


class CurrentFundamentalSnap():
    
    def __init__(self, symbols:list):
        
        self.symbols = symbols
    
    
    # Input Symbols
    def getFundamentalSnapshot(self):    
        symbols_np = np.unique(self.symbols)
        symbols1 = list(symbols_np)
        symbols2 = []
        for i in symbols1: 
            if '.' in i:
                i = i.replace('.','-')
            else:
                pass
            symbols2.append(i)
        
        
        # Set up scraper loop
        
        Master_df = pd.DataFrame()
        
        for sym in symbols2:
            url= ("http://finviz.com/quote.ashx?t="+sym.lower())
            req=Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            webpage=urlopen(req).read()
            html=soup(webpage, "html.parser")
            
            def get_fundamentals():
                try:
                    # Find fundamentals table
                    fundamentals=pd.read_html(str(html), attrs= {'class': 'snapshot-table2'})[0]
                    # Clean up fundamentals dataframe
                    fundamentals.columns= ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']
                    colOne= []
                    colLength=len(fundamentals)
                    for k in np.arange(0, colLength, 2):
                        colOne.append(fundamentals[f'{k}'])
                    attrs = pd.concat(colOne, ignore_index=True)
                    
                    colTwo= []
                    colLength=len(fundamentals)
                    
                    for k in np.arange(1, colLength, 2):
                        colTwo.append(fundamentals[f'{k}'])    
                    vals=pd.concat(colTwo, ignore_index=True)
            
                    fundamentals = pd.DataFrame()
                    fundamentals['Attributes'] = attrs
                    fundamentals['Values'] = vals
                    fundamentals=fundamentals.set_index('Attributes')
                    
                    return fundamentals 
                
                except Exception as e:
                    return e
            
            
            #print ('Fundamentals Snapshot: ')
            #print(get_fundamentals())
            
            df = get_fundamentals()
             
            fundamental_df = pd.DataFrame(df).rename(columns= lambda x:sym)
            fundamental_df.index.name = 'Ticker Stats'
            Master_df = pd.concat([Master_df, fundamental_df],axis=1)
            
        Master_df_final = Master_df.transpose()

        Master_df_final = Master_df_final.applymap(lambda x: x.replace("%",""))
        #Master_df_final['Short Float'] = Master_df_final['Short Float'].str.replace('-', 0)
        #Master_df_final[['Short Float','Short Ratio']] = Master_df_final[['Short Float','Short Ratio']].astype(float)
        print(Master_df_final)
        return Master_df_final
        
        