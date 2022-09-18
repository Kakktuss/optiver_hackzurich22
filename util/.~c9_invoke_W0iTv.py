from optibook import ORDER_TYPE_IOC, ORDER_TYPE_LIMIT, SIDE_ASK, SIDE_BID
from .print import print_order_response

MAX_DELTA = 1

EDGES_PAIRS = [
    ("SMALL_CHIPS", "SMALL_CHIPS_NEW_COUNTRY"),
    ("SMALL_CHIPS_NEW_COUNTRY", "SMALL_CHIPS"),
    ("TECH_INC", "TECH_INC_NEW_COUNTRY"),
    ("TECH_INC_NEW_COUNTRY", "TECH_INC")
]

def get_delta_pairs(e):
    open_pos = e.get_positions()
    return {
        "|".join([k, v]): open_pos[k]["volume"] + open_pos[v]["volume"] for k, v in EDGES_PAIRS
    }

def get_delta(e):
    return sum(e.get_positions().values())

def balance_position(e, portfolio):
    #balance_if_profitable(e, get_delta_pairs(e))
    print(get_delta_pairs(e))
    sell_if_profitable(e, portfolio)
    
    #delta = get_delta(e)
    
    #if not (-MAX_DELTA < delta < MAX_DELTA):
    #    force_balance(e)
        
def sell_if_profitable(e, portfolio):
    # for every entry in out portfolio
    for k, pv in portfolio.items():
        if pv.volume != 0:
            price = pv.price
            volume = pv.volume
            
            bet_type = SIDE_ASK if volume > 0 else SIDE_BID
            
            book = e.get_last_price_book(k)
            if book and (target := (book.bids if volume > 0 else book.asks)):
                is_profitable = (book.bids[0].price - price if volume > 0 else price - book.asks[0].price) > 0
                if is_profitable:
                    order_response = e.insert_order(k, price= target[0].price, volume= min(target[0].volume, volume), side= bet_type, order_type= ORDER_TYPE_LIMIT)
                    #print_order_response(order_response)
                
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
    
def force_balance(e):
    pass

