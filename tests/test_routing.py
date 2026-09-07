from decimal import Decimal

from app.routing import RouteStop, optimize_routes


def test_routing_returns_to_depot_when_weight_capacity_is_reached() -> None:
    trips = optimize_routes(
        [
            RouteStop("pickup-a", Decimal("60.00"), Decimal("0.20")),
            RouteStop("pickup-b", Decimal("60.00"), Decimal("0.20")),
            RouteStop("pickup-c", Decimal("20.00"), Decimal("0.20")),
        ],
        Decimal("100.00"),
        Decimal("1.00"),
    )

    assert len(trips) == 2
    assert all(trip.returned_to_depot for trip in trips)
    assert all(trip.weight_kg <= Decimal("100.00") for trip in trips)
    assert {stop_id for trip in trips for stop_id in trip.stop_ids} == {
        "pickup-a",
        "pickup-b",
        "pickup-c",
    }


def test_routing_rejects_a_stop_larger_than_capacity() -> None:
    try:
        optimize_routes(
            [RouteStop("oversized", Decimal("101.00"), Decimal("0.20"))],
            Decimal("100.00"),
            Decimal("1.00"),
        )
    except ValueError as error:
        assert "exceeds vehicle capacity" in str(error)
    else:
        raise AssertionError("oversized stop should be rejected")