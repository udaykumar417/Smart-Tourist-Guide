import pandas as pd


def calculate_recommendation_score(
    place,
    interests,
    budget,
    available_time
):
    """
    Calculate a personalized AI recommendation score.

    Score components:
    - Interest match: 40%
    - Rating: 25%
    - Budget compatibility: 20%
    - Time compatibility: 15%

    Final score: 0 - 100
    """

    score = 0.0

    # ==========================================================
    # 1. INTEREST MATCH - 40%
    # ==========================================================

    category = str(place.get("category", "")).strip()

    normalized_interests = [
        str(item).strip().lower()
        for item in interests
    ]

    if category.lower() in normalized_interests:
        interest_score = 40
    else:
        # Give a small score to places outside selected interests
        interest_score = 5

    score += interest_score

    # ==========================================================
    # 2. RATING - 25%
    # ==========================================================

    try:
        rating = float(place["rating"])
    except (ValueError, TypeError):
        rating = 0

    rating = max(0, min(rating, 5))

    rating_score = (rating / 5) * 25

    score += rating_score

    # ==========================================================
    # 3. BUDGET COMPATIBILITY - 20%
    # ==========================================================

    try:
        entry_fee = float(place["entry_fee"])
    except (ValueError, TypeError):
        entry_fee = 0

    try:
        user_budget = float(budget)
    except (ValueError, TypeError):
        user_budget = 0

    if user_budget <= 0:

        if entry_fee <= 0:
            budget_score = 20
        else:
            budget_score = 0

    elif entry_fee <= user_budget:

        # Cheaper places receive a higher score
        ratio = entry_fee / user_budget

        budget_score = 20 * (1 - ratio)

        # Minimum score for places within budget
        budget_score = max(5, budget_score)

    else:
        budget_score = 0

    score += budget_score

    # ==========================================================
    # 4. TIME COMPATIBILITY - 15%
    # ==========================================================

    try:
        visit_duration = float(place["visit_duration"])
    except (ValueError, TypeError):
        visit_duration = 0

    try:
        available_hours = float(available_time)
    except (ValueError, TypeError):
        available_hours = 0

    available_minutes = available_hours * 60

    if available_minutes <= 0:

        time_score = 0

    elif visit_duration <= available_minutes:

        ratio = visit_duration / available_minutes

        time_score = 15 * (1 - ratio)

        # Give at least a small score if it fits
        time_score = max(3, time_score)

    else:
        # Doesn't fit in available time
        time_score = 0

    score += time_score

    # Keep score between 0 and 100
    score = max(0, min(score, 100))

    return round(score, 2)


def recommend_places(
    places,
    interests,
    budget,
    available_time,
    minimum_rating=0
):
    """
    Generate personalized tourist recommendations.

    Returns a DataFrame sorted by AI score.
    """

    if places is None or places.empty:
        return pd.DataFrame()

    recommendations = places.copy()

    # ==========================================================
    # CLEAN NUMERIC COLUMNS
    # ==========================================================

    recommendations["rating"] = pd.to_numeric(
        recommendations["rating"],
        errors="coerce"
    ).fillna(0)

    recommendations["entry_fee"] = pd.to_numeric(
        recommendations["entry_fee"],
        errors="coerce"
    ).fillna(0)

    recommendations["visit_duration"] = pd.to_numeric(
        recommendations["visit_duration"],
        errors="coerce"
    ).fillna(0)

    # ==========================================================
    # MINIMUM RATING FILTER
    # ==========================================================

    recommendations = recommendations[
        recommendations["rating"] >= minimum_rating
    ].copy()

    # ==========================================================
    # CALCULATE AI SCORE
    # ==========================================================

    recommendations["ai_score"] = recommendations.apply(
        lambda place: calculate_recommendation_score(
            place=place,
            interests=interests,
            budget=budget,
            available_time=available_time
        ),
        axis=1
    )

    # ==========================================================
    # SORT BY AI SCORE
    # ==========================================================

    recommendations = recommendations.sort_values(
        by=["ai_score", "rating"],
        ascending=[False, False]
    )

    # Reset index
    recommendations = recommendations.reset_index(drop=True)

    return recommendations


def get_recommendation_reason(
    place,
    interests,
    budget,
    available_time
):
    """
    Generate a simple explanation for why a place
    was recommended.
    """

    reasons = []

    category = str(place.get("category", "")).strip()

    # Interest
    if category.lower() in [
        str(i).strip().lower()
        for i in interests
    ]:
        reasons.append("matches your interest")

    # Rating
    try:
        rating = float(place["rating"])
        if rating >= 4.5:
            reasons.append("highly rated")
    except (ValueError, TypeError):
        pass

    # Budget
    try:
        fee = float(place["entry_fee"])

        if fee <= float(budget):
            reasons.append("fits your budget")
    except (ValueError, TypeError):
        pass

    # Time
    try:
        duration = float(place["visit_duration"])

        if duration <= float(available_time) * 60:
            reasons.append("fits your available time")
    except (ValueError, TypeError):
        pass

    if not reasons:
        return "Suggested based on overall preferences"

    return " • ".join(reasons).capitalize()