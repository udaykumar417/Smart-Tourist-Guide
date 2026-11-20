import heapq
import math


def build_graph(routes):
    """
    Convert routes DataFrame into an adjacency graph.

    Expected columns:
        source
        destination
        distance
    """

    graph = {}

    if routes is None or routes.empty:
        return graph

    for _, row in routes.iterrows():

        source = str(row["source"]).strip()
        destination = str(row["destination"]).strip()

        try:
            distance = float(row["distance"])
        except (ValueError, TypeError):
            continue

        if source not in graph:
            graph[source] = []

        if destination not in graph:
            graph[destination] = []

        # Add both directions
        graph[source].append(
            (destination, distance)
        )

        graph[destination].append(
            (source, distance)
        )

    return graph


def heuristic(place_a, place_b, places):
    """
    Calculate straight-line distance between two places
    using latitude and longitude.

    This acts as the heuristic function h(n)
    in A*.
    """

    try:

        row_a = places[
            places["name"] == place_a
        ].iloc[0]

        row_b = places[
            places["name"] == place_b
        ].iloc[0]

        lat1 = math.radians(
            float(row_a["latitude"])
        )

        lon1 = math.radians(
            float(row_a["longitude"])
        )

        lat2 = math.radians(
            float(row_b["latitude"])
        )

        lon2 = math.radians(
            float(row_b["longitude"])
        )

    except (IndexError, ValueError, TypeError):

        return 0

    # Haversine distance
    earth_radius = 6371

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius * c


def a_star(
    graph,
    start,
    goal,
    places
):
    """
    A* Search Algorithm.

    f(n) = g(n) + h(n)

    g(n) = cost from start to current node
    h(n) = estimated cost to goal
    f(n) = total estimated cost
    """

    if start not in graph:
        return [], float("inf")

    if goal not in graph:
        return [], float("inf")

    # Priority queue
    open_set = []

    heapq.heappush(
        open_set,
        (
            heuristic(start, goal, places),
            0,
            start
        )
    )

    # Best known cost from start
    g_score = {
        start: 0
    }

    # Parent nodes
    came_from = {}

    visited = set()

    while open_set:

        _, current_cost, current = heapq.heappop(
            open_set
        )

        if current in visited:
            continue

        visited.add(current)

        # Goal reached
        if current == goal:

            path = reconstruct_path(
                came_from,
                current
            )

            return (
                path,
                current_cost
            )

        # Explore neighbors
        for neighbor, edge_cost in graph.get(
            current,
            []
        ):

            new_cost = (
                current_cost + edge_cost
            )

            if new_cost < g_score.get(
                neighbor,
                float("inf")
            ):

                g_score[neighbor] = new_cost

                came_from[neighbor] = current

                h_score = heuristic(
                    neighbor,
                    goal,
                    places
                )

                f_score = (
                    new_cost + h_score
                )

                heapq.heappush(
                    open_set,
                    (
                        f_score,
                        new_cost,
                        neighbor
                    )
                )

    return [], float("inf")


def reconstruct_path(
    came_from,
    current
):
    """
    Reconstruct the final path
    after A* reaches the goal.
    """

    path = [current]

    while current in came_from:

        current = came_from[current]

        path.append(current)

    path.reverse()

    return path


def find_route(
    routes,
    places,
    start,
    goal
):
    """
    Convenient wrapper around A*.
    """

    graph = build_graph(routes)

    return a_star(
        graph,
        start,
        goal,
        places
    )