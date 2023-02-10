import streamlit as st
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import mplfinance as mpf
import base64

# emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
st.set_page_config(page_title="S&P 500 App", page_icon=":bar_chart:")

# ---- MAINPAGE ----
st.title(":bar_chart: S&P 500 App")
st.markdown("""
This app retrieves stock price information for any company in the S&P 500 Index. A **Between The Pipes** app by Stephan Teodosescu.
""")

"---"

st.sidebar.header('Filters')

# Web scraping of S&P 500 data
#
@st.cache
def load_data():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    html = pd.read_html(url, header = 0)
    df = html[0]
    return df

df = load_data()
sector = df.groupby('GICS Sector')


# ---- Sidebar ----

# Stock selection
sorted_stock_unique = sorted( df['Symbol'].unique() )
selected_stock = st.sidebar.selectbox('Stock', sorted_stock_unique)

# Period selection
selected_period = st.sidebar.radio('Select Period', ('1mo','3mo', '6mo', '1y', '5y', '10y', 'YTD','Max'))

# Sector selection
sorted_sector_unique = sorted( df['GICS Sector'].unique() )
selected_sector = st.sidebar.multiselect('Sector', sorted_sector_unique, sorted_sector_unique)



# ---- Individual Stock Plots ----
st.header('Individual Stocks')

st.write(f"Selected ticker: **{selected_stock}**")

history = yf.Ticker(selected_stock).history(period=selected_period)

col1, col2, col3 = st.columns(3)
col1.metric("Close", history['Close'].tail(1).apply(lambda x: float("{:.2f}".format(x)), "+5%"))
col2.metric("Daily Change", history['Close'].tail(1) - history['Open'].tail(1), "-8%")
col3.metric("YTD", value = 123, delta = "+5%")

#df.max()

tab1, tab2 = st.tabs(["📈 Chart", "🗃 Data"])

ticker = selected_stock

# stock plot
tab1.subheader("Stock Chart")
st.text('Stock performance over given period selected on the left.')
mpf.plot(history, type='candle', mav=(7),figratio=(18,10))

# selected stock table
tab2.subheader("Data Table")
st.write(history) #last 10 days
st.caption('Pro Tip: you can copy and paste cells from the above table into your favorite spreadsheet software.')


"---"

# Filtering data for selected section
df_selected_sector = df[ (df['GICS Sector'].isin(selected_sector)) ]

st.header('Sector Analysis')
st.text('Choose a single sector or multiple from the options on the left. Choose Show Plot below to display stock charts.')
st.write('Data Dimension: ' + str(df_selected_sector.shape[0]) + ' rows and ' + str(df_selected_sector.shape[1]) + ' columns.')
st.dataframe(df_selected_sector)

# Download S&P500 data
# https://discuss.streamlit.io/t/how-to-download-file-in-streamlit/1806
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    href = f'<a href="data:file/csv;base64,{b64}" download="SP500.csv">Download CSV File</a>'
    return href

st.markdown(filedownload(df_selected_sector), unsafe_allow_html=True)


# https://pypi.org/project/yfinance/

# the following retrieves data from yfinance package and groups by ticker symbol

data = yf.download(
        tickers = list(df_selected_sector[:5].Symbol),
        period = selected_period,
        interval = "1d",
        group_by = 'ticker',
        auto_adjust = True,
        prepost = True,
        threads = True,
        proxy = None
    )

# Plot Closing Price of Query Symbol

plt.style.use('fivethirtyeight')

def price_plot(symbol):
  df = pd.DataFrame(data[symbol].Close)
  df['Date'] = df.index
  fig = plt.figure()
  plt.fill_between(df.Date, df.Close, color='#00F43C', alpha=0.3)
  plt.plot(df.Date, df.Close, color='#00F43C', alpha=0.8)
  plt.xticks(rotation=90)
  plt.title(symbol, fontweight='bold')
  plt.xlabel('Date', fontweight='bold')
  plt.ylabel('Closing Price', fontweight='bold')
  return st.pyplot(fig)

num_company = st.sidebar.slider('No. of companies to show', 1, 5)

if st.button('Show Plots'):
    st.header('Stock Closing Price')
    for i in list(df_selected_sector.Symbol)[:num_company]:
        price_plot(i)


