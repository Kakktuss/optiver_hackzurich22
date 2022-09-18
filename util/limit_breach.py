def respect_the_limit(e, stock, volume):
    positions = e.get_positions()
    
    future_volume = positions[stock] + volume
    
    return future_volume > 100 or future_volume < -100:
    # we breached the limit