"""Constants for the Canal & River Trust Stoppages integration."""

from datetime import timedelta

DOMAIN = "canal_river_trust"

DEFAULT_SCAN_INTERVAL = timedelta(seconds=1800)
LOOKAHEAD_DAYS = 60

API_BASE_URL = (
    "https://canalrivertrust.org.uk/api/stoppage/notices"
    "?consult=false&start={start}&end={end}"
    "&fields=title,region,waterways,path,typeId,reasonId,"
    "programmeId,start,end,state,image&geometry=point"
)

PLATFORMS: list[str] = ["sensor", "geo_location"]

CONF_WATERWAYS = "waterways"
CONF_SCAN_INTERVAL = "scan_interval"

# Mapping of waterway codes to human-readable names
WATERWAY_MAP: dict[str, str] = {
    "GU": "Grand Union Canal",
    "KA": "Kennet & Avon Canal",
    "OX": "Oxford Canal",
    "TM": "Trent & Mersey Canal",
    "SU": "Shropshire Union Canal",
    "LL": "Leeds & Liverpool Canal",
    "LA": "Llangollen Canal",
    "MB": "Monmouthshire & Brecon Canal",
    "WB": "Worcester & Birmingham Canal",
    "SW": "Staffs & Worcestershire Canal",
    "AN": "Ashton Canal",
    "MA": "Macclesfield Canal",
    "PF": "Peak Forest Canal",
    "RE": "Regent's Canal",
    "LN": "Lee Navigation",
    "HU": "Huddersfield Narrow",
    "CA": "Caldon Canal",
    "CH": "Chesterfield Canal",
    "ER": "Erewash Canal",
    "BC": "Birmingham Canal Navigations",
    "BW": "Bridgewater Canal",
    "AI": "Aire & Calder Navigation",
    "SH": "Sheffield & South Yorkshire Navigation",
    "GL": "Gloucester & Sharpness Canal",
    "RI": "River Severn",
    "RS": "River Soar",
    "RT": "River Trent",
    "RW": "River Weaver",
    "RL": "River Lee",
    "RA": "River Avon",
}

# Mapping of stoppage type IDs to human-readable names
TYPE_MAP: dict[int, str] = {
    1: "Navigation Closure",
    2: "Navigation Restriction",
    3: "Towpath Closure",
    4: "Advice",
    8: "Towpath Restriction",
    9: "Navigation and Towpath Closure",
    10: "Customer Service Facility",
    11: "Navigation Restriction and Towpath Closure",
}

# Mapping of stoppage reason IDs to human-readable names
REASON_MAP: dict[int, str] = {
    2: "3rd Party Works",
    5: "Inspections",
    6: "Maintenance",
    8: "Repair",
    9: "Suspected Vandalism",
    10: "Vegetation",
    12: "Information",
    13: "Event",
    14: "Boating Incident",
    15: "Emergency Services Incident",
    16: "Underwater Obstruction",
    17: "Vehicle Incident",
    18: "Low Water Levels",
    19: "High Water Levels",
    20: "Pollution Incident",
}

CRT_BASE_URL = "https://canalrivertrust.org.uk"

