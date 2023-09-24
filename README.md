# Support_Resistance_Trader

This script is a very promising script for currencies and cyclical assets. This script utilizes the free-to-use binance API.

###How the script works in general:

1) The script initially gathers a 1-minute resolution data for the last 30 days, which takes a minute or two for the script to initialize
2) Then it calculates the significant support and resistance levels that are untouched for a given number of candles and records them as the significant prices
3) The script connects to multiple two different WebSockets, one to get the live market feed and the other to get the live account feed and get all the fills etc.
4) The Script has two separate infinite loops; one checks for naked positions which can occur due to servers slacking over heavy volume and failing to send/record fills and thus doesn't trigger TP/SL orders, and the final one is to keep the WebSockets alive inline with the Binance Docs
5) Finally, the script infinitely runs and places bids/asks whenever the current price goes above the significant high(Short) or goes below the significant low(Long)

This is a very promising script if combined with some other models/indicators and has the correct parameters for the right market conditions. Cyclical markets and currencies have the tendency to go through vast low-volatility (Crab) markets


![image](https://github.com/IBatuu/Support_Resistance_Trader/assets/78052559/98b3a4d4-b22a-42b4-b9aa-ced4891d16e1)
