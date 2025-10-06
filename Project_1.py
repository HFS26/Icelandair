

import requests
from datetime import datetime, time
from datetime import datetime, UTC
import re

def parse_fail41(content: str, filename: str):
    # content: the text of the file
    # filename: e.g. "FAIL41_BIRK_231630.85" — maybe encode issue time inside
    result = {"filename": filename}

    # Extract valid period:
    m = re.search(r"OUTLOOK FROM (\d{4}) TO (\d{4}) UTC", content)
    if m:
        from_hhmm = m.group(1)
        to_hhmm = m.group(2)
        # Possibly derive date from filename or assume today
        # For now dummy date
        
        today = datetime.now(UTC).date()

        valid_from = datetime.combine(today, time(int(from_hhmm[:2]), int(from_hhmm[2:])))
        valid_to   = datetime.combine(today, time(int(to_hhmm[:2]), int(to_hhmm[2:])))
        result["valid_from"] = valid_from
        result["valid_to"]   = valid_to

    # Extract winds/temperature lines
    # e.g. lines starting with “WINDS/TEMPERATURE AT SIGNIFICANT LEVELS:” ...
    # Then parse entries like “FL050: 170/30-50KT, STRONGEST IN THE SE, …”
    wt = {}
    m2 = re.search(r"WINDS/TEMPERATURE AT SIGNIFICANT LEVELS:\s*(.*)", content)
    if m2:
        rest = m2.group(1)
        # maybe split by comma separating each FLxxx:
        # something like FL050: …, FL100: …, FL180: … 
        entries = re.findall(r"(FL\d{3}:\s*[^,]+)", rest)
        for ent in entries:
            # e.g. "FL050: 170/30-50KT, STRONGEST IN THE SE"
            mm = re.match(r"FL(\d{3}):\s*(\d{1,3})/(\d{1,3}-\d{1,3})KT(?:,\s*([A-Z ]+))?(?:,\s*([^,]+))?", ent)
            if mm:
                fl = "FL" + mm.group(1)
                direction = int(mm.group(2))
                speed_range = mm.group(3)
                # maybe split speed_range into low/high
                low, high = speed_range.split("-")
                wt[fl] = {
                    "direction": direction,
                    "speed_kt": (int(low), int(high)),
                    "notes": mm.group(4) or "",
                    # temp: maybe from another line or maybe in same or next
                }
        result["winds_temperature"] = wt

    # Similar regexes for freezing level, turbulence, icing, etc.
    # ...

    return result

# Usage
url = "https://www.vedur.is/gogn/flugkort/flugskilyrdi/FAIL41_BIRK_231630.85"
resp = requests.get(url)
resp.raise_for_status()
data = parse_fail41(resp.text, "FAIL41_BIRK_231630.85")
print(data)
