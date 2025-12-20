from __future__ import annotations
import plotly.graph_objects as go

from main import *
from utility import all_same

def save_simulation_plot(frames: list[MarketFrame], filename: str = "simulation.html") -> None:
    fig = go.Figure(layout={"paper_bgcolor": "#FFFFFF"})
    steps = list(range(len(frames)))

    for good in frames[0].prices.keys():
        prices = [market.prices[good] for market in frames]
        if any(prices):
            mode = "lines" if all_same(prices) else "lines"
            fig.add_trace(go.Scatter(x=steps, y=prices, mode=mode, name=f"Price of {good.name}"))
    
    for i, first_building in enumerate(frames[0].buildings):
        # TODO: remove exception?
        if first_building.type is pop_centers:
            continue
        
        activation_levels = [market.buildings[i].activation for market in frames]
        if any(activation_levels):
            mode = "lines" if all_same(activation_levels) else "lines+markers"
            fig.add_trace(go.Scatter(x=steps, y=activation_levels, mode=mode, name=f"Activation of {first_building.type.name}"))
        profits = [market.buildings[i].get_profit(market) for market in frames]
        if any(profits):
            mode = "lines" if all_same(profits) else "lines"
            fig.add_trace(go.Scatter(x=steps, y=profits, mode=mode, name=f"Profit of {first_building.type.name}"))

    fig.update_layout(
        title='Simulation Data Over Time',
        xaxis_title='Frame',
        yaxis_title='Value',
        legend_title='Metrics',
    )

    # Save to HTML
    fig.write_html(filename)
    print(f"Plot saved to {filename}")

save_simulation_plot(frames, "output.html")
