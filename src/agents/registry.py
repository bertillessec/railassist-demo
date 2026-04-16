"""Agent registry - declarative configuration for all RailAssist agents."""

from src.tools import (
    get_next_departures, search_connection, get_train_status,
    lookup_ticket, check_subscription, submit_delay_compensation, get_fare_estimate,
    get_active_disruptions, get_planned_works, report_incident,
)

AGENT_REGISTRY: dict = {
    "schedule": {
        "name": "TrainScheduleAgent",
        "prompt": "schedule.prompty",
        "model": None,
        "tools": {get_next_departures, search_connection, get_train_status},
        "description": "Handles train timetables, departures, connections, real-time tracking, and platform information.",
        "is_sub": True,
    },
    "passenger": {
        "name": "PassengerServiceAgent",
        "prompt": "passenger.prompty",
        "model": None,
        "tools": {lookup_ticket, check_subscription, submit_delay_compensation, get_fare_estimate},
        "description": "Handles tickets, subscriptions, fare estimates, refunds, and delay compensation claims.",
        "is_sub": True,
    },
    "incident": {
        "name": "IncidentAgent",
        "prompt": "incident.prompty",
        "model": None,
        "tools": {get_active_disruptions, get_planned_works, report_incident},
        "description": "Handles active disruptions, planned engineering works, incident reporting, and alternative transport.",
        "is_sub": True,
    },
    "railassist": {
        "name": "RailAssist",
        "prompt": "railassist.prompty",
        "model": None,
        "tools": set(),
        "description": "Central orchestrator that delegates to specialised railway sub-agents.",
        "is_sub": False,
    },
}
