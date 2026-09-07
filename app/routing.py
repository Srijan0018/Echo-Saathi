from dataclasses import dataclass
from decimal import Decimal

from ortools.constraint_solver import pywrapcp, routing_enums_pb2


@dataclass(frozen=True)
class RouteStop:
    stop_id: str
    weight_kg: Decimal
    volume_m3: Decimal


@dataclass(frozen=True)
class RouteTrip:
    stop_ids: tuple[str, ...]
    weight_kg: Decimal
    volume_m3: Decimal
    returned_to_depot: bool


DISTANCE_MATRIX: tuple[tuple[int, ...], ...] = (
    (0, 12, 18, 24, 31, 27, 21, 16, 28, 34),
    (12, 0, 10, 20, 25, 22, 15, 11, 23, 29),
    (18, 10, 0, 14, 19, 17, 12, 9, 17, 23),
    (24, 20, 14, 0, 11, 15, 18, 19, 9, 15),
    (31, 25, 19, 11, 0, 12, 21, 24, 8, 10),
    (27, 22, 17, 15, 12, 0, 13, 18, 12, 18),
    (21, 15, 12, 18, 21, 13, 0, 8, 20, 26),
    (16, 11, 9, 19, 24, 18, 8, 0, 22, 28),
    (28, 23, 17, 9, 8, 12, 20, 22, 0, 6),
    (34, 29, 23, 15, 10, 18, 26, 28, 6, 0),
)


def optimize_routes(
    stops: list[RouteStop],
    max_payload_kg: Decimal,
    max_volume_m3: Decimal,
) -> list[RouteTrip]:
    if not stops:
        return []
    if any(stop.weight_kg > max_payload_kg or stop.volume_m3 > max_volume_m3 for stop in stops):
        raise ValueError("a pickup exceeds vehicle capacity")

    manager = pywrapcp.RoutingIndexManager(len(stops) + 1, len(stops), 0)
    routing = pywrapcp.RoutingModel(manager)
    node_demands = [0] + [int(stop.weight_kg * 100) for stop in stops]
    node_volumes = [0] + [int(stop.volume_m3 * 1000) for stop in stops]

    def distance_callback(from_index: int, to_index: int) -> int:
        return DISTANCE_MATRIX[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    distance_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(distance_index)

    def weight_callback(index: int) -> int:
        return node_demands[manager.IndexToNode(index)]

    def volume_callback(index: int) -> int:
        return node_volumes[manager.IndexToNode(index)]

    weight_index = routing.RegisterUnaryTransitCallback(weight_callback)
    volume_index = routing.RegisterUnaryTransitCallback(volume_callback)
    capacities_weight = [int(max_payload_kg * 100)] * len(stops)
    capacities_volume = [int(max_volume_m3 * 1000)] * len(stops)
    routing.AddDimensionWithVehicleCapacity(weight_index, 0, capacities_weight, True, "Weight")
    routing.AddDimensionWithVehicleCapacity(volume_index, 0, capacities_volume, True, "Volume")

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.seconds = 1
    solution = routing.SolveWithParameters(search_parameters)
    if solution is None:
        raise ValueError("no feasible route found")

    trips: list[RouteTrip] = []
    for vehicle_id in range(len(stops)):
        index = routing.Start(vehicle_id)
        stop_ids: list[str] = []
        weight = Decimal("0")
        volume = Decimal("0")
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != 0:
                stop = stops[node - 1]
                stop_ids.append(stop.stop_id)
                weight += stop.weight_kg
                volume += stop.volume_m3
            index = solution.Value(routing.NextVar(index))
        if stop_ids:
            trips.append(RouteTrip(tuple(stop_ids), weight, volume, True))
    return trips
