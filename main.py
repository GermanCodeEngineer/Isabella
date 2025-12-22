from __future__ import annotations
from copy import copy, deepcopy
from colorama import init as init_colorama, Fore
from pmp_manip.utility import grepr_dataclass
from typing import ClassVar

from utility import SaveInstances, three_way_max

@grepr_dataclass(grepr_fields=["name"], unsafe_hash=True, frozen=True)
class GoodType(SaveInstances):
    instances: ClassVar[list[GoodType]]

    name: str
    text_color: str

    @property
    def formatted_name(self):
        return f"{self.text_color}{self.name}{Fore.RESET}"

@grepr_dataclass(grepr_fields=["buy", "sell"])
class GoodOrderInfo:
    buy: float
    sell: float

@grepr_dataclass(grepr_fields=["name", "inputs", "outputs"], unsafe_hash=True, frozen=True)
class BuildingType(SaveInstances):
    instances: ClassVar[list[BuildingType]]

    name: str
    text_color: str
    inputs: dict[GoodType, float]
    worker_demand: int # TODO: add professions
    worker_wage: float
    outputs: dict[GoodType, float]

    @property
    def formatted_name(self):
        return f"{self.text_color}{self.name}{Fore.RESET}"

@grepr_dataclass(grepr_fields=["type", "level", "activation"])
class Building:
    type: BuildingType
    level: int # positive
    activation: float = 0 # 0 - 1
    
    def lrepr(self) -> str:
        return f"{self.type.name}(a={self.activation})"
    
    def get_revenue(self, market: MarketFrame, activation_offset: float = 0) -> float:
        base = sum((quantity * market.get_good_price(good)) for good, quantity in self.type.outputs.items())
        return base * self.level * (self.activation + activation_offset)
    
    def get_expenses(self, market: MarketFrame, activation_offset: float = 0) -> float:
        goods_cost_base = sum((quantity * market.get_good_price(good)) for good, quantity in self.type.inputs.items())
        wages_cost_base = 0#self.type.worker_demand * WORKER_WAGE
        maintenance_cost = 0.1
        # TODO: add proper wages
        return (maintenance_cost + (goods_cost_base + wages_cost_base) * self.level * (self.activation + activation_offset))
    
    def get_profit(self, market: MarketFrame, activation_offset: float = 0) -> float:
        return self.get_revenue(market, activation_offset) - self.get_expenses(market, activation_offset)
    
    def next_frame(self, market: MarketFrame) -> None:
        SMALL_OFFSET = 0#0.0001
        own_index = market.buildings.index(self)
        
        sa_frame = copy(market)
        sa_frame.prices = sa_frame.update_prices(verbose=False)
        sa_profit = self.get_profit(sa_frame, activation_offset=SMALL_OFFSET) # even activation=0 should not result in 0
        
        if self.activation == 1:
            ma_profit = sa_profit
        else:
            ma_frame = copy(market)
            ma_frame.buildings = copy(market.buildings)
            ma_building = copy(market.buildings[own_index])
            ma_building.activation += 0.1
            ma_frame.buildings[own_index] = ma_building
            print("more buildings [", ", ".join([b.lrepr() for b in ma_frame.buildings]), "]")
            ma_frame.prices = ma_frame.update_prices(indent="more   * ")
            ma_profit = ma_building.get_profit(ma_frame, activation_offset=SMALL_OFFSET)
        
        if self.activation == 0:
            la_profit = sa_profit
        else:
            la_frame = copy(market)
            la_frame.buildings = copy(market.buildings)
            la_building = copy(market.buildings[own_index])
            la_building.activation -= 0.1
            la_frame.buildings[own_index] = la_building
            print("less buildings [", ", ".join([b.lrepr() for b in la_frame.buildings]), "]")
            la_frame.prices = la_frame.update_prices(indent="less * ")
            la_profit = la_building.get_profit(la_frame, activation_offset=SMALL_OFFSET)
        
        # TODO: possibly re-add rule: profit < 0 must make building lower activation
        max_profit, index = three_way_max(la_profit, sa_profit, ma_profit)
        if   (index == 1) and ((self.activation == 0) or isinstance(self, FixedBuilding)):
            index = 2
        elif (index == 3) and ((self.activation == 1) or isinstance(self, FixedBuilding)):
            index = 2
        
        if   index == 1:
            self.activation = round(max(self.activation - 0.1, 0), 3)
            print("Building", self.type.formatted_name, f"{Fore.RED}lowered activation to", self.activation, Fore.RESET)
        elif index == 2:
            print("Building", self.type.formatted_name, "kept activation", self.activation)
        elif index == 3:
            self.activation = round(min(self.activation + 0.1, 1), 3)
            print("Building", self.type.formatted_name, f"{Fore.GREEN}increased activation to", self.activation, Fore.RESET)
        print("    Rev", round(self.get_revenue(market, SMALL_OFFSET), 3), "Exp", round(self.get_expenses(market, SMALL_OFFSET), 3),
            "| profit", round(sa_profit, 3), "->", round(self.get_profit(market, 0), 3))
        print(f"    Profit less {Fore.BLUE}{round(la_profit, 3)}{Fore.RESET} more {Fore.YELLOW}{round(ma_profit, 3)}{Fore.RESET}")
    
@grepr_dataclass(grepr_fields=[])
class FixedBuilding(Building):
    activation: float = 1
            
    #def get_profit(self, market: MarketFrame, activation_offset: float = 0) -> float:
    #    return 1 # Constant Profitability, should not change activation

@grepr_dataclass(grepr_fields=["orders", "prices", "buildings"])
class MarketFrame:
    buildings: list[Building]
    prices: dict[GoodType, float]
    
    def get_good_price(self, good: GoodType) -> float:
        return self.prices[good]
    
    @property
    def orders(self) -> dict[GoodType, GoodOrderInfo]:
        return self.get_good_buy_sell_orders()
   
    def get_good_buy_sell_orders(self) -> dict[GoodType, GoodOrderInfo]:
        buy_sell_orders = {good: GoodOrderInfo(buy=0, sell=0) for good in GoodType.instances}
        for building in self.buildings:
            for good, orders in building.type.inputs.items():
                buy_sell_orders[good].buy += round(orders * building.activation, 3)
            for good, orders in building.type.outputs.items():
                buy_sell_orders[good].sell += round(orders * building.activation, 3)
        return buy_sell_orders
    
    def update_prices(self, verbose: bool=True, indent: str="") -> dict[GoodType, float]:
        orders = self.get_good_buy_sell_orders()
        new_prices = {}
        for good in GoodType.instances:
            good_buy_orders = orders[good].buy
            good_sell_orders = orders[good].sell
            price = self.get_good_price(good)
            
            try:
                ratio = good_buy_orders / good_sell_orders
            except ZeroDivisionError:
                # TODO: improve
                if good_buy_orders == 0:
                    new_price = price
                    #if verbose: print(f"{indent}same from no buys or sells")
                else:
                    new_price = max(price, 0.1) * 1.2
                    #if verbose: print(f"{indent}hiked but no sells")
            else:
                if ratio > 1:
                    price = max(price, 0.1)
                new_price = price * ((ratio - 1) / 3 + 1)
                #if verbose: print(f"{indent}normal adapted", ratio, ratio - 1, (ratio-1)/3+1, "!", price, new_price)
            new_price = round(new_price, 3)
            new_prices[good] = new_price
            
            if verbose:
                print(f"{indent}Price of", good.formatted_name, end=" ")
                if new_price > price:
                    print(f"{Fore.GREEN}increased from", price, "to", new_price, Fore.RESET)
                elif new_price == price:
                    print("stayed at", price)
                else:
                    print(f"{Fore.RED}reduced from", price, "to", new_price, Fore.RESET)
                print(f"{indent}    Buy", good_buy_orders, "Sell", good_sell_orders)
        return new_prices
    
    def next_frame(self) -> MarketFrame:
        new_prices = self.update_prices(verbose=True)        
        print(20*"-")
        new_buildings = deepcopy(self.buildings)
        for building in new_buildings:
            building.next_frame(self)
        return MarketFrame(buildings=new_buildings, prices=new_prices)

logs = GoodType(name="Logs", text_color=Fore.GREEN)
planks = GoodType(name="Planks", text_color=Fore.YELLOW)

logging_camp = BuildingType(name="Logging Camp", text_color=Fore.GREEN,
    inputs={}, worker_demand=100, worker_wage=..., outputs={logs: 3},
)
sawmill = BuildingType(name="Sawmill", text_color=Fore.YELLOW,
    inputs={logs: 4}, worker_demand=100, worker_wage=..., outputs={planks: 5},
)
pop_centers = BuildingType(name="Population Centers", text_color=Fore.CYAN,
    inputs={planks: 3}, worker_demand=0, worker_wage=..., outputs={},
)
WORKER_WAGE = 0.002

frames = []
market_frame = MarketFrame(
    buildings=[
        Building(logging_camp, level=1), 
        Building(sawmill, level=1), 
        FixedBuilding(pop_centers, level=1)
    ],
    prices={logs: 0, planks: 0},
)
frames.append(market_frame)

init_colorama()
import sys
print(market_frame)
for i in range(int(sys.argv[1])):
    if i % 5 == 0:
        print(495*"=")
    else:
        print(100*"=")
    market_frame = market_frame.next_frame()
    frames.append(market_frame)
    if __name__ == "__main__": input()
    #print(market_frame)
