from __future__ import annotations
from copy import deepcopy
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
    level: int
    activation: float = 0 # 0 - 1
    
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
        SMALL_OFFSET = 0.0001
        profit = self.get_profit(market, activation_offset=SMALL_OFFSET) # even activation=0 should not result in 0
        more_active_profit = self.get_profit(market, activation_offset=0.1)
        less_active_profit = self.get_profit(market, activation_offset=-0.1)
        max_profit, index = three_way_max(profit, more_active_profit, less_active_profit)
        if (self.activation == 0) and (index == 3):
            index = 1
        elif (self.activation > 0) and (max_profit <= 0):
            index = 3
        elif (self.activation == 1) and (index == 2):
            index = 1
        if index == 1:
            print("Building", self.type.formatted_name, "kept activation", self.activation)
        elif index == 2:
            self.activation = round(min(self.activation + 0.1, 1), 3)
            print("Building", self.type.formatted_name, f"{Fore.GREEN}increased activation to", self.activation, Fore.RESET)
        elif index == 3:
            self.activation = round(max(self.activation - 0.1, 0), 3)
            print("Building", self.type.formatted_name, f"{Fore.RED}lowered activation to", self.activation, Fore.RESET)
        print("    Rev", round(self.get_revenue(market, SMALL_OFFSET), 3), "Exp", round(self.get_expenses(market, SMALL_OFFSET), 3), 
            "| profit", round(profit, 3), "->", round(self.get_profit(market, 0), 3))
    
@grepr_dataclass(grepr_fields=[])
class FixedBuilding(Building):
    activation: float = 1
            
    def get_profit(self, market: MarketFrame, activation_offset: float = 0) -> float:
        return 1 # Constant Profitability, should not change activation

@grepr_dataclass(grepr_fields=["orders", "prices", "buildings"])
class MarketFrame:
    buildings: list[Building]
    prices: dict[GoodType, float]
    
    def get_good_price(self, good: GoodType) -> float:
        return self.prices[good]
    
    @property
    def orders(self):
        buy_orders, sell_orders = self.get_good_buy_sell_orders()
        return {good: {"buy": buy_orders[good], "sell": sell_orders[good]} for good in GoodType.instances}
   
    def get_good_buy_sell_orders(self) -> tuple[dict[GoodType, float], dict[GoodType, float]]:
        buy_orders = dict.fromkeys(GoodType.instances, 0)
        sell_orders = dict.fromkeys(GoodType.instances, 0)
        for building in self.buildings:
            for good, orders in building.type.inputs.items():
                buy_orders[good] += round(orders * building.activation, 3)
            for good, orders in building.type.outputs.items():
                sell_orders[good] += round(orders * building.activation, 3)
        return (buy_orders, sell_orders)
    
    def next_frame(self) -> MarketFrame:
        buy_orders, sell_orders = self.get_good_buy_sell_orders()
        new_prices = {}
        for good in GoodType.instances:
            good_buy_orders = buy_orders[good]
            good_sell_orders = sell_orders[good]

            price = self.get_good_price(good)
            if good_buy_orders == good_sell_orders:
                new_price = price
            elif good_buy_orders < good_sell_orders:
                ratio = good_buy_orders / good_sell_orders
                new_price = price * ((ratio - 1) / 3 + 1)
            else:
                if good_sell_orders == 0:
                    new_price = price + 0.1
                else:
                    ratio = good_buy_orders / good_sell_orders
                    new_price = price * ((ratio - 1) / 3 + 1)
            
            new_price = round(new_price, 3)
            print("Price of", good.formatted_name, end=" ")
            if new_price > price:
                print(f"{Fore.GREEN}increased from", price, "to", new_price, Fore.RESET)
            elif new_price == price:
                print("stayed at", price)
            else:
                print(f"{Fore.RED}reduced from", price, "to", new_price, Fore.RESET)
            print("    Buy", good_buy_orders, "Sell", good_sell_orders)
            new_prices[good] = new_price
        
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
