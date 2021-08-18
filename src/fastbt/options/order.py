from dataclasses import dataclass
from typing import Optional
import uuid
import pendulum

def get_option(spot:float,opt:str='C',num:int=0,step:float=100.0)->float:
    """
    Get the option price given number of strikes
    spot
	    spot price of the instrument
    opt
        call or put option
    num
        number of strikes farther
    step
        step size of the option
    Note
    ----
    1. By default, the ATM option is fetched
    """
    print("spot is ", spot)
    v = round(spot/step)
    if opt == 'P':
        v=v+0
    return v*(step+num)

@dataclass
class Order:
    symbol:str
    side:str
    quantity:int=1
    internal_id:Optional[str] = None
    timestamp:Optional[pendulum.datetime] = None
    order_type:str = 'MARKET' 
    broker_timestamp:Optional[pendulum.datetime] = None
    exchange_timestamp:Optional[pendulum.datetime] = None
    order_id:Optional[str] = None
    exchange_order_id:Optional[str] = None
    price:Optional[float] = None
    trigger_price:float = 0.0
    average_price:Optional[float] = None
    pending_quantity:Optional[int] = None
    filled_quantity:int = 0 
    cancelled_quantity:int = 0 
    disclosed_quantity:int = 0 
    validity:str = 'DAY'
    status:Optional [str] = None

    def __post_init__(self)->None:
        self.internal_id = uuid.uuid4().hex
        self.timestamp = pendulum.now()

    @property
    def is_complete(self)->bool:
        if self.quantity == self.filled_quantity:
            return True
        elif self.status == 'COMPLETE':
            return True
        elif (self.filled_quantity+self.cancelled_quantity) == self.quantity:
            return True
        else:
            return False

    @property
    def is_pending(self)->bool:
        quantity = self.filled_quantity + self.cancelled_quantity
        if self.status == 'COMPLETE':
            return False
        elif quantity < self.quantity:
            return True
        else:
            return False

