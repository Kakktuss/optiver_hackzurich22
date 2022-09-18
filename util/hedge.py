import time
from scipy.stats import norm
from collections import defaultdict
from optibook import ORDER_TYPE_IOC, ORDER_TYPE_LIMIT, SIDE_ASK, SIDE_BID
from .pricevolume import PriceVolume
from .print import print_order_response


MAX_HEDGE_VOLUME = 100
HEDGES_PAIRS = [
    ("SMALL_CHIPS", "SMALL_CHIPS_NEW_COUNTRY"),
    ("SMALL_CHIPS_NEW_COUNTRY", "SMALL_CHIPS"),
    ("TECH_INC", "TECH_INC_NEW_COUNTRY"),
    ("TECH_INC_NEW_COUNTRY", "TECH_INC")
]
HEDGES_PAIRS_STATS = {
    "SMALL_CHIPS|SMALL_CHIPS_NEW_COUNTRY": (-0.827610270874872, 0.5929684620454442),
    "SMALL_CHIPS_NEW_COUNTRY|SMALL_CHIPS": (0.17858620689655047, 0.38040822149654424),
    "TECH_INC|TECH_INC_NEW_COUNTRY": (-0.7082548768547146, 0.40281408861900425),
    "TECH_INC_NEW_COUNTRY|TECH_INC": (-0.3725184317508457, 0.35763365261850366)
}

def prevent_breach():
    pass

def calc_volume_factor(spread, hedge_mu, hedge_std):
    return (round(norm.cdf(spread, hedge_mu, hedge_std) * 10000) / 10000 - round(norm.cdf(0, hedge_mu, hedge_std) * 10000) / 10000) / (1 - round(norm.cdf(0, hedge_mu, hedge_std) * 10000) / 10000)

def collect_hedge_trades(e, tradable_instruments):
    """
    get all the favourable hednging opportunities from the order book
    """
    #return {
    #    k: {
    #       "ask": book.asks[0] if book.asks and book.asks[0] else None,
    #       "bid": book.bids[0] if book.bids else None
    #    } 
    #    for k in tradable_instruments if (book:= e.get_last_price_book(k))
    #}
    best_prices = {}
    for stock_a, stock_b in HEDGES_PAIRS:
        instrument_prices = []
        i = 0
        j = 0
        book_a = e.get_last_price_book(stock_a) 
        book_b = e.get_last_price_book(stock_b)
        while book_a and book_b and book_a.bids and book_b.bids and j < len(book_a.bids) and i < len(book_b.asks) and (spread := book_b.asks[i].price < book_a.bids[j].price):
            instrument_prices.append({
                "ask": book_b.asks[i].price,
                "bid": book_a.bids[j].price,
                "volume": min(book_a.bids[j].volume, book_b.asks[i].volume, MAX_HEDGE_VOLUME)
            })
            
            j+=1
            
            while book_a and book_b and book_a.bids and book_b.bids and j < len(book_a.bids) and i < len(book_b.asks) and (spread := book_b.asks[i].price < book_a.bids[j].price):
                instrument_prices.append({ 
                    "ask": book_b.asks[i].price,
                    "bid": book_a.bids[j].price,
                    "volume": min(book_a.bids[j].volume, book_b.asks[i].volume, MAX_HEDGE_VOLUME)
                })
                
                j+=1
                
            j = 0
            i += 1
            
        best_prices["|".join([stock_a, stock_b])] = instrument_prices
            
    return best_prices
    
    
def define_and_rank_hedge_trades(e, ranked_hedge_trades):
    """
    given the hedning opportunities, modify the trade such that the volume is adjusted based on how
    wide is the spread with respect to the statistics that were collected
    """
    hedges = [
        (hedge.split("|")[0], hedge.split("|")[1], trade["bid"], trade["ask"],
        (volume := round(calc_volume_factor(spread := (trade["bid"] - trade["ask"]), *HEDGES_PAIRS_STATS[hedge]) * trade["volume"])),
        spread, volume * spread)
        for hedge, trades in ranked_hedge_trades.items() for trade in trades
    ]
    
    # sort the trades based on the realizable profit
    hedges.sort(key=lambda trade: trade[6], reverse=True)
    
    return hedges
    
    
def place_hedges_bets(e, hedges):
    """
    go through the edge trades and place them
    """
    tradable_instruments = e.get_instruments()
    
    # get all the positions to keep track of the changes
    previous_positions = e.get_positions()
    
    trade_executed = False
    
    order_responses = defaultdict(list)
    
    # for all the edge positions
    for hedge in hedges:
        # do not place the bet if any of the two is paused
        if tradable_instruments[hedge[0]].paused or tradable_instruments[hedge[1]].paused and hedge[4] == 0:
            continue
        
        trade_executed = True
        
        # remove previous orders
        e.delete_orders(hedge[0])
        e.delete_orders(hedge[1])
        
        # place new orders
        order_responses[hedge[0]].append(e.insert_order(hedge[0], price= hedge[2], volume= hedge[4], side= SIDE_ASK, order_type= ORDER_TYPE_LIMIT))
        #print_order_response(order_response)
        order_responses[hedge[1]].append(e.insert_order(hedge[1], price= hedge[3], volume= hedge[4], side= SIDE_BID, order_type= ORDER_TYPE_LIMIT))
        #print_order_response(order_response)
        
    if trade_executed:
        # give some time to execute the orders
        time.sleep(2)
        
        # remove previous orders
        for stock in tradable_instruments:
            e.delete_orders(stock)
    
    # check how much the position has changed since the hedging trade
    hedge_position_delta = {}
    for k, v in e.get_positions().items():
        traded_pricevolume = PriceVolume(0, 0)
        trading_history = e.get_trade_history(k)
        for order in order_responses[k]:
            order_id = order.order_id
            for executed_trade in trading_history:
                if order_id == executed_trade.order_id:
                    traded_pricevolume = traded_pricevolume + PriceVolume(executed_trade.price, executed_trade.volume if executed_trade.side == SIDE_BID else -executed_trade.volume)
        
        hedge_position_delta[k] = traded_pricevolume
    
    return hedge_position_delta