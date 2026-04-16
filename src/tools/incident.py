"""Incident & disruption tools."""
import json, random
from datetime import datetime, timedelta

_INCIDENT_TYPES = ["signal_failure","track_maintenance","weather_disruption","mechanical_issue","staff_shortage","trespasser_on_track","power_outage","level_crossing_incident"]
_LINES = ["L1 Bruxelles-Anvers","L25 Bruxelles-Liege","L96 Bruxelles-Namur","L50A Bruxelles-Gand","L161 Namur-Luxembourg","L130 Namur-Charleroi","L36 Bruxelles-Liege (HSL)","L2 Bruxelles-Louvain","L124 Charleroi-Mons","L51 Bruxelles-Bruges-Ostende"]

def get_active_disruptions(region: str = "all") -> str:
    """Get all currently active disruptions and service alerts.

    :param region: Filter by region - wallonie, flandre, bruxelles, or all.
    :return: JSON list of active disruptions with severity, affected lines, and expected resolution.
    """
    incidents = []
    for _ in range(random.randint(1,4)):
        start = datetime.now() - timedelta(hours=random.randint(1,12))
        end = start + timedelta(hours=random.randint(2,24))
        incidents.append({"id": f"INC-{datetime.now().strftime('%Y%m%d')}-{random.randint(100,999)}", "type": random.choice(_INCIDENT_TYPES), "severity": random.choice(["low","medium","high","critical"]), "affected_line": random.choice(_LINES), "description_fr": "Perturbation du trafic ferroviaire suite a un incident technique.", "started_at": start.strftime("%Y-%m-%d %H:%M"), "expected_resolution": end.strftime("%Y-%m-%d %H:%M"), "alternative_transport": random.choice(["Bus de remplacement","Deviation via ligne alternative","Service reduit avec retards 15-30 min",None]), "affected_trains_count": random.randint(5,40)})
    return json.dumps({"region": region, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "active_disruptions": incidents, "total_count": len(incidents)}, ensure_ascii=False)

def get_planned_works(date_from: str = "today", date_to: str = "next_week") -> str:
    """Get planned engineering works and scheduled maintenance.

    :param date_from: Start date (YYYY-MM-DD or today).
    :param date_to: End date (YYYY-MM-DD or next_week).
    :return: JSON list of planned works with affected services and alternatives.
    """
    works = []
    for i in range(random.randint(2,5)):
        start = datetime.now() + timedelta(days=random.randint(1,14))
        end = start + timedelta(days=random.randint(1,5))
        works.append({"id": f"WRK-{start.strftime('%Y%m%d')}-{random.randint(10,99)}", "type": random.choice(["track_renewal","signal_upgrade","platform_renovation","bridge_maintenance"]), "affected_line": random.choice(_LINES), "start_date": start.strftime("%Y-%m-%d"), "end_date": end.strftime("%Y-%m-%d"), "impact": random.choice(["No trains - bus replacement","Reduced service - every 30 min","Single track - delays 10-15 min"]), "affected_stations": random.sample(["Namur","Charleroi-Sud","Mons","Liege-Guillemins","Louvain","Ottignies"], random.randint(2,4))})
    return json.dumps({"period": {"from": date_from, "to": date_to}, "planned_works": works}, ensure_ascii=False)

def report_incident(train_number: str, incident_type: str, description: str) -> str:
    """Report an incident or issue on a specific train.

    :param train_number: The train where the incident occurred.
    :param incident_type: Category - safety, comfort, cleanliness, accessibility, other.
    :param description: Free-text description of the incident.
    :return: JSON confirmation with incident reference and follow-up info.
    """
    return json.dumps({"incident_reference": f"RPT-{datetime.now().strftime('%Y%m%d%H%M')}-{random.randint(100,999)}", "train_number": train_number, "type": incident_type, "description": description, "reported_at": datetime.now().strftime("%Y-%m-%d %H:%M"), "status": "received", "follow_up": "Un agent analysera votre signalement dans les 24 heures.", "priority": "high" if incident_type == "safety" else "normal"}, ensure_ascii=False)
