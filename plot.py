from __future__ import annotations
from typing import TYPE_CHECKING
from main import *

def save_simulation_plot(frames: list[MarketFrame], filename: str = "simulation.html") -> None:
    import plotly.graph_objects as go
    steps = list(range(len(frames)))
    logs_prices = [mf.prices[logs] for mf in frames]
    planks_prices = [mf.prices[planks] for mf in frames]
    # Activation levels for the specific buildings
    logging_activation = [mf.buildings[0].activation for mf in frames]
    sawmill_activation = [mf.buildings[1].activation for mf in frames]
    # Sum revenues for each building type
    logging_revenues = [
        sum(b.get_revenue(mf) for b in mf.buildings if b.type.name == "Logging Camp")
        for mf in frames
    ]
    sawmill_revenues = [
        sum(b.get_revenue(mf) for b in mf.buildings if b.type.name == "Sawmill")
        for mf in frames
    ]

    import plotly.graph_objects as go

    fig = go.Figure()

    # Prices over time
    fig.add_trace(go.Scatter(x=steps, y=logs_prices, mode='lines+markers', name='Logs Price'))
    #fig.add_trace(go.Scatter(x=steps, y=planks_prices, mode='lines+markers', name='Planks Price'))

    # Activation levels
    fig.add_trace(go.Scatter(x=steps, y=logging_activation, mode='lines+markers', name='Logging Camp Activation'))
    #fig.add_trace(go.Scatter(x=steps, y=sawmill_activation, mode='lines+markers', name='Sawmill Activation'))

    # Revenues
    fig.add_trace(go.Scatter(x=steps, y=logging_revenues, mode='lines+markers', name='Logging Revenue'))
    #fig.add_trace(go.Scatter(x=steps, y=sawmill_revenues, mode='lines+markers', name='Sawmill Revenue'))

    fig.update_layout(
        title='Simulation Data Over Time',
        xaxis_title='Step',
        yaxis_title='Value',
        legend_title='Metrics',
    )

    # Save to HTML
    fig.write_html(filename)
    print(f"Plot saved to {filename}")

save_simulation_plot(frames, "output.html")
