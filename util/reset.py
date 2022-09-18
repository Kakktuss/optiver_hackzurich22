import time

from optibook import ORDER_TYPE_IOC, ORDER_TYPE_LIMIT, SIDE_ASK, SIDE_BID
from .print import print_order_response

def reset_positons(e):
    # get the open positions    
    positions = e.get_positions()
    print(positions)
    
    for stock in positions:
        e.delete_orders(stock)
    
    # for every position
    while any(amount != 0 for amount in e.get_positions().values()):
        positions = e.get_positions()
        for stock, amount in positions.items():
            # if the amount is not zero
            if amount != 0:
                # until the order is not placed
                placed_order = False
                while not placed_order:
                    # try to place the order as soon as the exchange is not paused
                    if not e.get_instruments()[stock].paused and (book := e.get_last_price_book(stock)) is not None:
                        b = book.asks if amount > 0 else book.bids
                        if b:
                            price = b[0].price
                            order_response = e.insert_order(stock, price= price, volume= abs(amount), side= SIDE_ASK if amount > 0 else SIDE_BID, order_type= ORDER_TYPE_LIMIT)
                            print_order_response(order_response)
                            print(stock, price, amount)
                            placed_order = order_response.success
        
        # wait until all the positions have been closed
        time.sleep(1)
        print(e.get_positions())
        for stock in positions:
            e.delete_orders(stock)
                
    print("all the positions have beed brought back to 0 lots")