class PriceVolume:
    """
    Bundles a price and a volume

    Attributes
    ----------
    price: float

    volume: int
    """
    def __init__(self, price, volume):
        self.price = price
        self.volume = volume

    def __repr__(self):
        return f"PriceVolume(price={str(self.price)}, volume={str(self.volume)})"

    def __eq__(self, other):
        if not isinstance(other, PriceVolume):
            return NotImplemented
        return self.price == other.price and self.volume == other.volume
    
    def __add__(self, other):
        # used to calculate the mean
        if not isinstance(other, PriceVolume):
            return NotImplemented
            
        if self.volume == 0 and other.volume == 0:
            return PriceVolume(0, 0)
        
        if (self.volume < 0) == (other.volume < 0):
            # if they agree in sign
            new_price = (self.price * self.volume + other.price * other.volume) / (self.volume + other.volume)
            new_volume = self.volume + other.volume
        
            return PriceVolume(new_price, new_volume)
        
        remaining_volume = self.volume + other.volume
        
        if (remaining_volume >= 0) == (self.volume >= 0):
            new_price = self.price
            new_volume = remaining_volume
        else:
            new_price = other.price
            new_volume = remaining_volume
        
        return PriceVolume(new_price, new_volume)