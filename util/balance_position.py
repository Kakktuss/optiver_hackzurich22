from optibook import ORDER_TYPE_IOC, ORDER_TYPE_LIMIT, SIDE_ASK, SIDE_BID
from .print import print_order_response
from collections import defaultdict

MAX_DELTA = 1

HEDGES_PAIRS = [
    ("SMALL_CHIPS", "SMALL_CHIPS_NEW_COUNTRY"),
    ("SMALL_CHIPS_NEW_COUNTRY", "SMALL_CHIPS"),
    ("TECH_INC", "TECH_INC_NEW_COUNTRY"),
    ("TECH_INC_NEW_COUNTRY", "TECH_INC")
]

def get_delta_pairs(e):
    #open_pos = e.get_positions()
    #return {
    #    "|".join([k, v]): open_pos[k]["volume"] + open_pos[v]["volume"] for k, v in EDGES_PAIRS
    #}
    dict_pairs = {}
    open_pos = e.get_positions_and_cash()
    delta_pairs = {}
    for k, v in HEDGES_PAIRS:
        delta = open_pos[k]["volume"] + open_pos[v]["volume"]
        name = "|".join([k, v])
        delta_pairs[name] = delta
    return delta_pairs


def get_delta(e):
    return sum(e.get_positions().values())

def balance_position(e, portfolio):
    #balance_if_profitable(e, get_delta_pairs(e))
    
    sell_if_profitable(e, portfolio)
    
    delta_pairs = get_delta_pairs(e)
    
    if not all(-MAX_DELTA < delta_pair < MAX_DELTA for delta_pair in delta_pairs.values()):
        force_balance(e, portfolio)
        
def sell_if_profitable(e, portfolio):
    # for every entry in out portfolio
    tradable_instruments = e.get_instruments()
    order_responses = defaultdict(list)
    for k, pv in portfolio.items():
        if pv.volume != 0:
            price = pv.price
            volume = pv.volume
            
            bet_type = SIDE_ASK if volume > 0 else SIDE_BID
            
            book = e.get_last_price_book(k)
            if book and (target := (book.bids if volume > 0 else book.asks)):
                is_profitable = (book.bids[0].price - price if volume > 0 else price - book.asks[0].price) > 0
                if is_profitable:
                    order_response[k].append(e.insert_order(k, price= target[0].price, volume= min(target[0].volume, abs(volume)), side= bet_type, order_type= ORDER_TYPE_LIMIT))
                    #print_order_response(order_response)
                    
    # give some time to execute the orders
    time.sleep(2)
    
    # remove previous orders
    for stock in tradable_instruments:
        e.delete_orders(stock)
                    
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
                    
    portfolio.update(
        {
            kp: portfolio[kp] + pp for kp, pp in hedge_position_delta.items()
        }
    )
                
def balance_if_profitable(e, portfolio):
    # for every entry in out portfolio
    for k, pv in portfolio:
        price = pv.price
        volume = pv.volume
        
        bet_type = SIDE_ASK if volume > 0 else SIDE_BID
        
        book = e.get_last_price_book(k)
        if book and (target := (book.bids if volume > 0 else book.asks)):
            is_profitable = book.bids[0].price - price if volume > 0 else price - book.asks[0].price
            if is_profitable:
                order_response = e.insert_order(k, price= target.price, volume= min(target.volume, volume), side= bet_type, order_type= ORDER_TYPE_LIMIT)
                #print_order_response(order_response)
    
def force_balance(e, portfolio):
    pass

