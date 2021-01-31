FROM continuumio/miniconda3:latest

RUN apt-get -y update &&\
    apt-get install -y --no-install-recommends \
    build-essential &&\
    apt-get autoremove &&\
    apt-get clean

RUN mkdir /app
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Option_Chain_Scrape_yfinance.py .
COPY Black_Scholes_Greek_calcs.py .
COPY RQA_Market_Time.py .
COPY RQA_Option_Greeks.py .
COPY RQA_Stock_Fundamentals.py .
COPY SPY_Options_Effects.parquet .


ENTRYPOINT ["python3", "Option_Chain_Scrape_yfinance.py"]