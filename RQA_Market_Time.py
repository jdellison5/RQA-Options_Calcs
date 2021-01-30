# -*- coding: utf-8 -*-
"""
Created on Fri Jan 29 18:09:46 2021

@author: jdell
"""

from datetime import datetime
from datetime import timezone
from datetime import time
import pandas as pd


def pre_market_open():
    
    pre_market_start_time = datetime.datetime.now().replace(hour=12, minute=00, second=00, tzinfo=timezone.utc).timestamp()
