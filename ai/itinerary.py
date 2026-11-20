def generate_itinerary(
    recommendations,
    start_location,
    available_time,
    budget
):
    """
    Generate a simple personalized day itinerary.

    The highest AI-scored places are selected while
    respecting the user's available time and budget.
    """

    itinerary = []

    if recommendations is None or recommendations.empty:
        return itinerary

    try:
        available_minutes = int(float(available_time) * 60)
    except (ValueError, TypeError):
        available_minutes = 0

    try:
        total_budget = float(budget)
    except (ValueError, TypeError):
        total_budget = 0

    used_time = 0
    used_budget = 0

    # Approximate travel time between attractions
    travel_time = 20

    # Start from the user's selected location
    current_location = start_location

    for _, place in recommendations.iterrows():

        try:
            visit_duration = int(
                float(place["visit_duration"])
            )
        except (ValueError, TypeError):
            continue

        try:
            entry_fee = float(
                place["entry_fee"]
            )
        except (ValueError, TypeError):
            entry_fee = 0

        # Skip if the place exceeds budget
        if used_budget + entry_fee > total_budget:
            continue

        # Add travel time except for first destination
        extra_travel_time = (
            0 if len(itinerary) == 0
            else travel_time
        )

        required_time = (
            visit_duration + extra_travel_time
        )

        # Skip if it doesn't fit
        if used_time + required_time > available_minutes:
            continue

        itinerary.append(
            {
                "name": place["name"],
                "category": place["category"],
                "rating": place["rating"],
                "ai_score": place["ai_score"],
                "entry_fee": entry_fee,
                "visit_duration": visit_duration,
                "best_time": place["best_time"],
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "travel_time": extra_travel_time
            }
        )

        used_time += required_time
        used_budget += entry_fee

        current_location = place["name"]

    return itinerary


def calculate_itinerary_summary(itinerary):
    """
    Calculate total time and budget for the itinerary.
    """

    total_visit_time = sum(
        item["visit_duration"]
        for item in itinerary
    )

    total_travel_time = sum(
        item["travel_time"]
        for item in itinerary
    )

    total_budget = sum(
        item["entry_fee"]
        for item in itinerary
    )

    total_time = (
        total_visit_time +
        total_travel_time
    )

    return {
        "places": len(itinerary),
        "visit_time": total_visit_time,
        "travel_time": total_travel_time,
        "total_time": total_time,
        "budget": total_budget
    }