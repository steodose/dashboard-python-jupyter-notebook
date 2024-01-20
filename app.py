import streamlit as st
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import mplfinance as mpf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
from streamlit_extras.metric_cards import style_metric_cards

# emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
st.set_page_config(page_title="S&P 500 App", page_icon=":bar_chart:")

# ---- MAINPAGE ----
st.title(":bar_chart: S&P 500 App")
st.markdown("""
This app retrieves stock price information for any company in the S&P 500 Index. A **Between The Pipes** app by Stephan Teodosescu.
""")

"---"

st.sidebar.header('Filters')

# ---- Web scraping of S&P 500 data ---- #
#
@st.cache_data
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
selected_period = st.sidebar.selectbox('Select Period', ('1mo','3mo', '6mo', '1y', '5y', '10y', 'YTD','Max'))

# Sector selection (LEGACY CODE)
# sorted_sector_unique = sorted( df['GICS Sector'].unique() )
# selected_sector = st.sidebar.multiselect('Sector', sorted_sector_unique, sorted_sector_unique)



# ---- Individual Stock Plots ----
st.header('Individual Stocks')

st.write(f"Selected ticker: **{selected_stock}**")

# define historical stock df
history = yf.Ticker(selected_stock).history(period=selected_period)
history_reversed = history.iloc[::-1] # Reverse the DataFrame


# ---- Calculate Price Changes ----- #

# Calculate Close Price Change
if len(history) >= 2:
    close_change = ((history['Close'].iloc[-1] - history['Close'].iloc[-2]) / history['Close'].iloc[-2]) * 100
else:
    close_change = 0  # Default to 0 if not enough data

# Calculate Daily Change
if len(history) >= 1:
    daily_change = (history['Close'].iloc[-1] - history['Open'].iloc[-1])
else:
    daily_change = 0  # Default to 0 if not enough data

# Calculate Period-to-Date Change
if len(history) >= 1:
    start_price = history['Close'].iloc[0]  # First day closing price in the selected period
    end_price = history['Close'].iloc[-1]   # Most recent day closing price
    ptd = (end_price - start_price)
else:
    ptd = 0  # Default to 0 if not enough data

# Calculate Period-to-Date Percent Change
if len(history) >= 1:
    start_price = history['Close'].iloc[0]  # First day closing price in the selected period
    end_price = history['Close'].iloc[-1]   # Most recent day closing price
    ptd_change = ((end_price - start_price) / start_price) * 100
else:
    ptd_change = 0  # Default to 0 if not enough data

# ---- KPI Cards ---- # 

col1, col2, col3 = st.columns(3)
col1.metric("Latest Close", f"${history['Close'].iloc[-1]:.2f}")
col2.metric("Daily Change", f"{daily_change:.2f}", f"{close_change:.2f}%")
col3.metric(f"Period Change ({selected_period})", f"{ptd:.2f}", f"{ptd_change:.2f}%")

style_metric_cards(border_color = '#CCC',
                   border_left_color = '#AA0000')


# ---- Tabs ---- #
tab1, tab2, tab3 = st.tabs(["📈 Charts", "🗃 Table", "📰 S&P 500 Lookup"])

ticker = selected_stock


# ---- Stock Chart ----

with tab1:
    tab1.subheader("Stock Chart")
    st.text('Stock performance over given period selected on the left.')

    # Chart selection radio button
    chart_type = st.radio("Choose Chart Type", ('Candlestick', 'Line Chart'))
    
    if chart_type == 'Candlestick':
        # Creating the candlestick chart
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                vertical_spacing=0.03, subplot_titles=('', ''), 
                row_width=[0.2, 0.7])

        # Candlestick chart
        fig.add_trace(go.Candlestick(x=history.index,
                        open=history['Open'],
                        high=history['High'],
                        low=history['Low'],
                        close=history['Close'],
                                    showlegend = False), 
                                    row=1, col=1)

            # Determine the color for each bar
        colors = ['#00B39D' if close >= open else '#D50000' for open, close in zip(history['Open'], history['Close'])]

        # Volume bar chart with conditional coloring
        fig.add_trace(go.Bar(x=history.index, y=history['Volume'], marker_color=colors, showlegend=False), row=2, col=1)

        # Update layout
        fig.update_layout(
            title=f'Stock Data for {selected_stock}',
            xaxis_title='',
            yaxis_title='Price ($)',
            xaxis_rangeslider_visible=False
        )

        # Update y-axis labels
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)

        st.plotly_chart(fig, use_container_width=True)


    elif chart_type == 'Line Chart':
        # Determine the stock's performance
        is_positive = history['Close'].iloc[-1] >= history['Close'].iloc[0]

        # Set the gradient color based on performance
        gradient_color = 'rgba(0, 179, 157, {})'
        if not is_positive:
            gradient_color = 'rgba(213, 0, 0, {})'

        # Creating the line chart
        line_fig = go.Figure()

        # Adding the line plot
        line_fig.add_trace(go.Scatter(x=history.index, y=history['Close'], mode='lines', name='Close', line=dict(color=gradient_color.format(1))))

        # Adding gradient area under the line
        line_fig.add_trace(go.Scatter(x=history.index, y=history['Close'], mode='none', 
                                    fill='tozeroy', 
                                    fillcolor=gradient_color.format(0.2),  # Adjust transparency for gradient effect
                                    name='Area'))

        # Update layout
        line_fig.update_layout(title=f'Historical Stock Prices for {selected_stock}',
                            xaxis_title='Date',
                            yaxis_title='Price ($)',
                            showlegend=False)

        st.plotly_chart(line_fig, use_container_width=True)


# ---- Stock Table ----
    
with tab2:
    tab2.subheader("Data Table")
    st.write(history_reversed) 
    st.caption('Pro Tip: you can copy and paste cells from the above table into your favorite spreadsheet software.')


# ---- Lookup Table ---- #

with tab3:
    tab3.subheader("Look up stocks in the S&P 500 Index")
    st.write(df)

"---"

