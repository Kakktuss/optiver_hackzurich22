import logging
import time
from typing import List
from optibook import common_types as t
from optibook import ORDER_TYPE_IOC, ORDER_TYPE_LIMIT, SIDE_ASK, SIDE_BID
from optibook.exchange_responses import InsertOrderResponse
from optibook.synchronous_client import Exchange
import random
import json

from util.pricevolume import PriceVolume
from util.hedge import place_hedges_bets, collect_hedge_trades, define_and_rank_hedge_trades
from util.balance_position import balance_position, get_delta
from util.reset import reset_positons

# TODO:
# - set limit of positions holding

PORTFOLIO = {}
    
def trade_cycle(e: Exchange):
    tradable_instruments = e.get_instruments()
    
    # collect all the best prices
    hedge_trades = collect_hedge_trades(e, tradable_instruments)
    
    # if no price was collected, do not trade at this time
    if any(hedge_trade for hedge_trade in hedge_trades.values()):
        # find possible hedges sorted based on the realizable profit
        ranked_hedge_trades = define_and_rank_hedge_trades(e, hedge_trades)
        
        # place the hedge bets and record the changes in our portfolio
        hedge_position_delta = place_hedges_bets(e, ranked_hedge_trades)
        
        print("Current positions")
        current_position = e.get_positions()
        #print(current_position)
        
        # update our portfolio based on the hedge delta - the price of our position
        # is a weighted average of the previous trades
        PORTFOLIO.update(
            {
                kp: PORTFOLIO[kp] + pp for kp, pp in hedge_position_delta.items()
            }
        )
        
        # check that the portfolio has the same number of stocks as the exchange states
        # check that if the numer of stocks != 0, the price is also != 0
        #assert all(PORTFOLIO[kp] == current_position[kp] for kp in tradable_instruments), "Computed stock do not match"
        
        balance_position(e, PORTFOLIO)
        
def main():
    exchange = Exchange()
    exchange.connect()
    
    #print("Initial positions")
    #print(exchange.get_positions())
    
    PORTFOLIO.update(
        {
            k: PriceVolume(0, 0) for k in exchange.get_instruments()
        }
    ) 
    
    # at the beginning of any trading session reset the positions to check performance
    reset_positons(exchange)
    
    print("Reset positions")
    print(exchange.get_positions())
    
    while True:
        trade_cycle(exchange)
        time.sleep(1)

    print(PORTFOLIO)

if __name__ == '__main__':
    main()
