from backend.schemas.simulation import SimulationRequest, SimulationResponse


def run_simulation(data: SimulationRequest) -> SimulationResponse:
    """
    Perform deterministic financial calculations based on SaaS unit economics.
    Does NOT use AI or randomized simulation.
    """
    # 1. Revenue Calculations
    mrr = round(float(data.customers * data.price), 2)
    arr = round(float(mrr * 12.0), 2)

    # 2. Expense & Gross Burn Calculations
    monthly_burn = round(
        float(data.marketing_spend + data.salaries + data.infrastructure_cost + data.other_expenses),
        2
    )

    # 3. Net Burn & Cash Runway
    net_burn = round(float(monthly_burn - mrr), 2)
    cash = data.cash_balance if data.cash_balance is not None else 50000.0

    if monthly_burn > 0:
        runway_months = round(float(cash / monthly_burn), 1)
    else:
        runway_months = 999.0

    # 4. Status Indicator
    if mrr >= monthly_burn and monthly_burn > 0:
        status = "PROFITABLE"
    elif runway_months < 6.0:
        status = "HIGH RISK"
    else:
        status = "BALANCED"

    return SimulationResponse(
        mrr=mrr,
        arr=arr,
        monthly_burn=monthly_burn,
        net_burn=net_burn,
        runway_months=runway_months,
        status=status
    )
