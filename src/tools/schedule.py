"""Train schedule tools."""
import json
from datetime import datetime, timedelta
import random

_STATIONS = ["Bruxelles-Midi","Bruxelles-Central","Bruxelles-Nord","Liege-Guillemins","Namur","Charleroi-Sud","Anvers-Central","Gand-Saint-Pierre","Bruges","Mons","Louvain","Ottignies","Luxembourg","Arlon","Ostende","Mechelen"]
_TRAIN_TYPES = ["IC","S","L","P","ICE","Thalys"]

def get_next_departures(station: str, count: int = 5) -> str:
    """Return the next scheduled departures from a given station.

    :param station: Name of the departure station (e.g. 'Bruxelles-Midi').
    :param count: Number of departures to return (default 5, max 10).
    :return: JSON list of upcoming departures with train number, destination, platform, and status.
    """
    count = min(int(count), 10)
    now = datetime.now()
    departures = []
    for i in range(count):
        dep_time = now + timedelta(minutes=random.randint(5+i*12, 15+i*15))
        dest = random.choice([s for s in _STATIONS if s.lower() != station.lower()])
        delay = random.choices([0,0,0,0,3,5,8,12,15], k=1)[0]
        departures.append({"train_number": f"{random.choice(_TRAIN_TYPES)}{random.randint(100,9999)}", "destination": dest, "scheduled_departure": dep_time.strftime("%H:%M"), "platform": random.randint(1,14), "status": "on_time" if delay==0 else f"+{delay}min", "delay_minutes": delay})
    return json.dumps({"station": station, "departures": departures}, ensure_ascii=False)

def search_connection(origin: str, destination: str, departure_time: str = "now") -> str:
    """Search for train connections between two stations.

    :param origin: Departure station name.
    :param destination: Arrival station name.
    :param departure_time: Desired departure time in HH:MM format, or 'now'.
    :return: JSON with 1-3 route options including transfers, duration, and pricing.
    """
    base = datetime.now() if departure_time == "now" else datetime.now().replace(hour=int(departure_time.split(":")[0]), minute=int(departure_time.split(":")[1]))
    routes = []
    for i in range(3):
        dep = base + timedelta(minutes=i*25+random.randint(0,10))
        duration = random.randint(35,150)
        arr = dep + timedelta(minutes=duration)
        transfers = random.choices([0,0,1,1,2], k=1)[0]
        via = random.sample([s for s in _STATIONS if s not in [origin, destination]], transfers) if transfers > 0 else []
        routes.append({"departure": dep.strftime("%H:%M"), "arrival": arr.strftime("%H:%M"), "duration_minutes": duration, "transfers": transfers, "via": via, "train_type": random.choice(_TRAIN_TYPES), "price_standard_eur": round(random.uniform(8,35),2), "price_comfort_eur": round(random.uniform(15,55),2), "occupancy": random.choice(["low","medium","high"])})
    return json.dumps({"origin": origin, "destination": destination, "routes": routes}, ensure_ascii=False)

def get_train_status(train_number: str) -> str:
    """Get real-time status and location of a specific train.

    :param train_number: The train identifier (e.g. 'IC1234').
    :return: JSON with current position, delay info, next stops, and composition.
    """
    delay = random.choices([0,0,0,3,5,10,20], k=1)[0]
    current = random.choice(_STATIONS)
    nexts = random.sample([s for s in _STATIONS if s != current], 3)
    return json.dumps({"train_number": train_number, "status": "on_time" if delay==0 else "delayed", "delay_minutes": delay, "current_location": current, "next_stops": [{"station": s, "arrival": (datetime.now()+timedelta(minutes=10+i*15)).strftime("%H:%M")} for i,s in enumerate(nexts)], "composition": {"cars": random.randint(4,12), "first_class_cars": random.randint(1,3), "restaurant_car": random.choice([True,False]), "wifi": True, "bike_spaces": random.randint(4,16)}}, ensure_ascii=False)
