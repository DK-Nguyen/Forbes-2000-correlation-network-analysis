import yfinance as yf
import matplotlib.pyplot as plt
# %matplotlib inline

data = yf.download(tickers="NOK", period="10y", interval="1d")
data['Open'].plot()
plt.show()

