import pandas as pd


def recommend_restaurant(
    restaurants,
    budget,
    itinerary_cost=0
):
    """
    Recommend a restaurant based on the
    user's remaining budget and restaurant rating.
    """

    if restaurants is None or restaurants.empty:
        return None

    data = restaurants.copy()

    # Convert numeric columns safely
    data["rating"] = pd.to_numeric(
        data["rating"],
        errors="coerce"
    ).fillna(0)

    data["average_cost"] = pd.to_numeric(
        data["average_cost"],
        errors="coerce"
    ).fillna(0)

    try:
        total_budget = float(budget)
    except (ValueError, TypeError):
        total_budget = 0

    try:
        trip_cost = float(itinerary_cost)
    except (ValueError, TypeError):
        trip_cost = 0

    remaining_budget = max(
        0,
        total_budget - trip_cost
    )

    # Restaurants affordable with remaining budget
    affordable = data[
        data["average_cost"] <= remaining_budget
    ].copy()

    # If none fit, choose cheapest restaurant
    if affordable.empty:

        cheapest = data.sort_values(
            by=[
                "average_cost",
                "rating"
            ],
            ascending=[
                True,
                False
            ]
        )

        if cheapest.empty:
            return None

        return cheapest.iloc[0]

    # Prefer highest rated affordable restaurant
    affordable = affordable.sort_values(
        by=[
            "rating",
            "average_cost"
        ],
        ascending=[
            False,
            True
        ]
    )

    return affordable.iloc[0]