"""
backend/utils/medication_regex.py

Universal Compiled Regex Library for Clinical Prescription Extraction.
Covers doses, frequencies, routes, durations, timings, PRN flags, and numeric schedules (1-0-1, etc.).
Pre-compiled for sub-millisecond execution.
"""

import re
from typing import Pattern, Dict, List

# ── DOSE PATTERNS ─────────────────────────────────────────────────────────────
# Matches: 500mg, 500 mg, 0.5 mg, 12.5mg, 1 g, 1000 mg, 250 mcg, 250μg, 250 ug,
# 5 IU, 5 Units, 10 units, 2 ml, 2mL, 5 drops, 2 puffs, 1 tablet, 2 tablets,
# half tablet, 1/2 tablet, quarter tablet, one tablet, two capsules, 1 cap, 2 caps,
# 3 sachets, 1 ampoule, 1 vial, etc.

DOSE_PATTERNS: List[Pattern] = [
    # Standard metric/unit dosage (e.g. 500mg, 0.5 mg, 250 mcg, 250μg, 5 IU, 2 mL, 10 units)
    re.compile(
        r'\b(?P<val>\d+(?:\.\d+)?|\d+/\d+)\s*'
        r'(?P<unit>mg|g|gm|mcg|μg|ug|ml|mL|IU|iu|units?|pills?|tablets?|tabs?|capsules?|caps?|puffs?|drops?|sachets?|ampoules?|vials?|puffs?)\b'
        r'(?!\s*/\s*(?:dL|L|mL))',
        re.IGNORECASE
    ),
    # Word-based dosage (e.g. half tablet, 1/2 tablet, quarter tablet, one tablet, two capsules)
    re.compile(
        r'\b(?P<val>half|quarter|one|two|three|four|five|1/2|1/4|3/4)\s*'
        r'(?P<unit>tablets?|tabs?|capsules?|caps?|puffs?|drops?|sachets?|ampoules?|vials?)\b',
        re.IGNORECASE
    ),
]

# ── FREQUENCY PATTERNS ────────────────────────────────────────────────────────
# Matches: OD, BD, BID, TDS, TID, QID, QDS, QD, QOD, HS, SOS, PRN,
# Once daily, Twice daily, Three times daily, Four times daily, Daily, Every day,
# Morning, Night, Morning and evening,
# Numeric: 1-0-0, 0-1-0, 0-0-1, 1-1-0, 1-0-1, 1-1-1, 2-2-2, 1/2-0-1/2,
# Hourly: Every 4 hours, Every 6 hours, Every 8 hours, Every 12 hours, q4h, q6h, q8h, q12h,
# Period: Weekly, Monthly, Alternate day, Every other day

NUMERIC_SCHEDULE_PATTERN = re.compile(
    r'\b(?P<m>[0-9/]+)-(?P<a>[0-9/]+)-(?P<e>[0-9/]+)(?:-(?P<n>[0-9/]+))?\b'
)

HOURLY_PATTERN = re.compile(
    r'(?i)\b(?:every\s+(?P<num>\d+)\s*hours?|q(?P<qnum>\d+)h)\b'
)

FREQUENCY_PATTERNS: List[Pattern] = [
    # Numeric schedules: 1-0-1, 1-1-1, 0-0-1, 1-0-0, 2-2-2, 1/2-0-1/2
    NUMERIC_SCHEDULE_PATTERN,
    # Hourly intervals: q4h, q6h, q8h, q12h, every 8 hours
    HOURLY_PATTERN,
    # Latin & standard doctor abbreviations
    re.compile(
        r'(?i)\b(?:once\s+daily|twice\s+daily|three\s+times\s+daily|four\s+times\s+daily|'
        r'thrice\s+daily|every\s+day|daily|alternate\s+day|every\s+other\s+day|weekly|monthly|'
        r'morning\s+and\s+evening|morning|evening|night|bedtime|'
        r'bid|bd|tid|tds|qid|qds|qd|qod|od|hs|stat|prn|sos|as\s+needed|as\s+required|when\s+required|if\s+needed)\b'
    ),
]

# ── ROUTE PATTERNS ────────────────────────────────────────────────────────────
# Matches: PO, Oral, By mouth, IV, Intravenous, IM, Intramuscular, SC, SQ, Subcutaneous,
# Topical, Cream, Gel, Ointment, Eye drops, Ear drops, Nasal spray, Inhalation, Nebulization,
# Puffs, Suppository, Rectal

ROUTE_PATTERN = re.compile(
    r'(?i)\b(?:by\s+mouth|oral(?:ly)?|po|intravenous(?:ly)?|iv|intramuscular(?:ly)?|im|'
    r'subcutaneous(?:ly)?|sc|sq|sublingual(?:ly)?|topical(?:ly)?|cream|gel|ointment|'
    r'eye\s+drops?|ear\s+drops?|nasal\s+spray|inhalation|inhaled|nebulization|nebulised|'
    r'puffs?|suppository|rectal(?:ly)?)\b'
)

# ── TIMING PATTERNS ───────────────────────────────────────────────────────────
# Matches: Before meals, After meals, Before breakfast, After breakfast, Before lunch, After lunch,
# Before dinner, After dinner, Morning, Evening, Night, HS, Bedtime, AC, PC

TIMING_PATTERN = re.compile(
    r'(?i)\b(?:before\s+meals?|after\s+meals?|before\s+breakfast|after\s+breakfast|'
    r'before\s+lunch|after\s+lunch|before\s+dinner|after\s+dinner|'
    r'with\s+meals?|with\s+food|empty\s+stomach|'
    r'morning|evening|night|bedtime|hs|ac|pc)\b'
)

# ── DURATION PATTERNS ─────────────────────────────────────────────────────────
# Matches: For 5 days, For 7 days, For 10 days, For 2 weeks, For one month, Continue, Lifelong,
# Until finished, x5 days, x7 days

DURATION_PATTERN = re.compile(
    r'(?i)\b(?:(?:for|x)\s*)?(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*'
    r'(?:days?|weeks?|months?|years?)\b|\b(?:continue|lifelong|until\s+finished|long-term)\b'
)

# ── PRN / SOS PATTERNS ────────────────────────────────────────────────────────
PRN_PATTERN = re.compile(
    r'(?i)\b(?:sos|prn|if\s+needed|when\s+required|as\s+required|as\s+needed)\b'
)
