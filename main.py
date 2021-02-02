import yfinance as yf
import matplotlib.pyplot as plt
# %matplotlib inline

data = yf.download(tickers="NOK", period="20y", interval="1d")
data['Close'].plot()
plt.show()

print(yfinance.__version__)
