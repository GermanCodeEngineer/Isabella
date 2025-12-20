from __future__ import annotations
from copy import deepcopy
from pmp_manip.utility import grepr_dataclass

good_types = []
@grepr_dataclass(grepr_fields=["name"], unsafe_hash=True, frozen=True)
class GoodType:
    name: str
    
    def __post_init__(self) -> None:
        good_types.append(self)

building_types = []
@grepr_dataclass(grepr_fields=["name", "inputs", "outputs"], unsafe_hash=True, frozen=True)
class BuildingType:
    name: str
    inputs: dict[GoodType, float]
    worker_demand: int # TODO: add professions
    worker_wage: float
    outputs: dict[GoodType, float]
    
    def __post_init__(self) -> None:
        building_types.append(self)

@grepr_dataclass(grepr_fields=["type", "level", "activation"])
class Building:
    type: BuildingType
    level: int
    activation: float = 0 # 0 - 1
    
    def get_revenue(self, market: MarketFrame, activation_offset: float = 0) -> float:
        base = sum((quantity * market.get_good_price(good)) for good, quantity in self.type.outputs.items())
        return base * self.level * (self.activation + activation_offset)
    
    def get_expenses(self, market: MarketFrame, activation_offset: float = 0) -> float:
        base = sum((quantity * market.get_good_price(good)) for good, quantity in self.type.inputs.items())
        return base * self.level * (self.activation + activation_offset)
        # TODO: add wages
    
    def get_profit(self, market: MarketFrame, activation_offset: float = 0) -> float:
        return self.get_revenue(market, activation_offset) - self.get_expenses(market, activation_offset)
    
    def next_frame(self, market: MarketFrame) -> None:
        profit = self.get_profit(market, activation_offset=0.01) # even activation=0 should not result in 0
        if profit <= 0:
            self.activation = round(max(self.activation - 0.1, 0), 3)
            print("Building", self.type.name, "lowered activation to", self.activation, "current profit aprx.", round(profit, 3))
        else:
            self.activation = round(min(self.activation + 0.1, 1), 3)
            print("Building", self.type.name, "increased activation to", self.activation, "current profit aprx.", round(profit, 3))
        print("Rev", round(self.get_revenue(market, 0.01), 3), "Exp", round(self.get_expenses(market, 0.01), 3))
    
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
        return {good: {"buy": buy_orders[good], "sell": sell_orders[good]} for good in good_types}
   
    def get_good_buy_sell_orders(self) -> tuple[dict[GoodType, float], dict[GoodType, float]]:
        buy_orders = dict.fromkeys(good_types, 0)
        sell_orders = dict.fromkeys(good_types, 0)
        for building in self.buildings:
            for good, orders in building.type.inputs.items():
                buy_orders[good] += round(orders * building.activation, 3)
            for good, orders in building.type.outputs.items():
                sell_orders[good] += round(orders * building.activation, 3)
        return (buy_orders, sell_orders)
    
    def next_frame(self) -> MarketFrame:
        buy_orders, sell_orders = self.get_good_buy_sell_orders()
        new_prices = {}
        for good in good_types:
            good_buy_orders = buy_orders[good]
            good_sell_orders = sell_orders[good]
            price = self.get_good_price(good)
            if good_buy_orders == good_sell_orders:
                new_price = price
                print("Price of", good.name, "stayed at", price)
            elif good_buy_orders < good_sell_orders:
                new_price = round(max(price - 0.1, 0), 3)
                print("Price of", good.name, "reduced from", price, "to", new_price)
            else:
                new_price = round(price + 0.1, 3)
                print("Price of", good.name, "increased from", price, "to", new_price)
            new_prices[good] = round(new_price, 3)
        
        new_buildings = deepcopy(self.buildings)
        for building in new_buildings:
            building.next_frame(self)
        return MarketFrame(buildings=new_buildings, prices=new_prices)

logs = GoodType(name="Logs")
planks = GoodType(name="Planks")

logging_camp = BuildingType(name="Logging Camp",
    inputs={}, worker_demand=..., worker_wage=..., outputs={logs: 3},
)
sawmill = BuildingType(name="Sawmill",
    inputs={logs: 4}, worker_demand=..., worker_wage=..., outputs={planks: 5},
)
pop_centers = BuildingType(name="Population Centers",
    inputs={logs: 3}, worker_demand=..., worker_wage=..., outputs={},
)

frames = []
market_frame = MarketFrame(
    buildings=[
        Building(logging_camp, level=1), 
        #Building(sawmill, level=1), 
        FixedBuilding(pop_centers, level=1)
    ],
    prices={logs: 0, planks: 0},
)
frames.append(market_frame)
print(market_frame)
for i in range(60):
    if i % 5 == 0:
        print(500*"=")
    else:
        print(100*"=")
    market_frame = market_frame.next_frame()
    frames.append(market_frame)
    #print(market_frame)
