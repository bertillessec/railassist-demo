"""Passenger service tools."""
import json, random
from datetime import datetime, timedelta

def lookup_ticket(ticket_reference: str) -> str:
    """Look up a ticket by its booking reference.

    :param ticket_reference: The ticket booking reference code.
    :return: JSON with ticket details including route, class, validity, and passenger info.
    """
    return json.dumps({"reference": ticket_reference, "status": random.choice(["valid","used","expired","cancelled"]), "passenger": "Voyageur Anonyme", "route": {"origin": "Bruxelles-Midi", "destination": "Liege-Guillemins", "date": (datetime.now()+timedelta(days=random.randint(-5,30))).strftime("%Y-%m-%d"), "departure": f"{random.randint(6,22)}:{random.choice(['00','15','30','45'])}"}, "class": random.choice(["standard","comfort"]), "price_eur": round(random.uniform(8,45),2), "type": random.choice(["single","return","railpass"]), "seat_reservation": random.choice([None, f"Car {random.randint(1,12)} Seat {random.randint(1,80)}"])}, ensure_ascii=False)

def check_subscription(card_number: str) -> str:
    """Check the status and validity of a subscription or railpass.

    :param card_number: The subscription or railpass card number.
    :return: JSON with subscription type, validity period, zones, and remaining trips.
    """
    start = datetime.now() - timedelta(days=random.randint(30,300))
    end = start + timedelta(days=365)
    return json.dumps({"card_number": card_number, "type": random.choice(["NMBS/SNCB Go Pass","Key Card","Campus","Railflex","Standard Abonnement"]), "holder": "Voyageur Anonyme", "valid_from": start.strftime("%Y-%m-%d"), "valid_until": end.strftime("%Y-%m-%d"), "status": "active" if end > datetime.now() else "expired", "zones": random.sample(["Zone Bruxelles","Zone Wallonie","Zone Flandre","All zones"], random.randint(1,3)), "remaining_trips": random.choice([None, random.randint(0,10)]), "discount_percentage": random.choice([50,100])}, ensure_ascii=False)

def submit_delay_compensation(ticket_reference: str, delay_minutes: int) -> str:
    """Submit a compensation claim for a delayed train.

    :param ticket_reference: The booking reference of the affected ticket.
    :param delay_minutes: The actual delay experienced in minutes.
    :return: JSON with claim reference, eligible compensation, and processing status.
    """
    if delay_minutes < 15: eligible, compensation = False, 0
    elif delay_minutes < 30: eligible, compensation = True, 25
    elif delay_minutes < 60: eligible, compensation = True, 50
    else: eligible, compensation = True, 100
    return json.dumps({"claim_reference": f"CLM-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}", "ticket_reference": ticket_reference, "delay_reported_minutes": delay_minutes, "eligible_for_compensation": eligible, "compensation_percentage": compensation, "estimated_refund_eur": round(random.uniform(5,40)*compensation/100,2) if eligible else 0, "status": "submitted" if eligible else "rejected_insufficient_delay", "processing_time_days": random.randint(5,15) if eligible else 0, "eu_regulation": "EC 1371/2007"}, ensure_ascii=False)

def get_fare_estimate(origin: str, destination: str, passenger_type: str = "adult") -> str:
    """Get a fare estimate between two stations.

    :param origin: Departure station.
    :param destination: Arrival station.
    :param passenger_type: Type of passenger - adult, child, senior, student.
    :return: JSON with fare options and available discounts.
    """
    base = round(random.uniform(8,45),2)
    factor = {"adult":1.0,"child":0.0,"senior":0.5,"student":0.5}.get(passenger_type, 1.0)
    return json.dumps({"origin": origin, "destination": destination, "passenger_type": passenger_type, "fares": {"standard_single": round(base*factor,2), "standard_return": round(base*1.8*factor,2), "comfort_single": round(base*1.5*factor,2), "comfort_return": round(base*2.5*factor,2)}, "promotions": [{"name": "Weekend Ticket", "price": round(base*0.5,2), "conditions": "Valid Sat-Sun"}, {"name": "Go Pass 10", "price": round(base*0.6,2), "conditions": "10 trips"}], "free_under_12": passenger_type=="child"}, ensure_ascii=False)
