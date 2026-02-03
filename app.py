"""
Proposal App - Test Build (Tabs 1-4)

Tab 1: Intake (Property Lookup) - reused from your existing app structure.
Tab 2: Project Understanding - description + assumptions checkboxes + additional assumptions.
Tab 3: Scope of Services - task checkbox library (placeholder blocks for now).
Tab 4: Tasks 107-110 - permit checkboxes + additional permits + 108-110 checkboxes.

Run:
  pip install -r requirements.txt
  streamlit run app.py
"""

import streamlit as st
import re
import json
import pathlib
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, quote
from typing import Dict, Any, Optional, List

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Proposal App (Test)", page_icon="📄", layout="wide")

# -----------------------------------------------------------------------------
# UI Styling
# -----------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
/* Design tokens */
:root {
    --navy: #0b1f3a;
    --navy-2: #122c54;
    --ink: #101820;
    --paper: #f7f8fb;
    --panel: #ffffff;
    --border: #c9d3e1;
    --field-border: #0b1f3a;
    --field-border-width: 1px;
    --field-radius: 8px;
    --btn-bg: #eef3fb;
    --btn-text: #0b1f3a;
    --tab-bg: #e9eef6;
    --tab-bg-active: #ffffff;
    --tab-border: #0b1f3a;
    --tab-text: #0b1f3a;
    --tab-text-active: #0b1f3a;
    --tab-shadow: 0 6px 14px rgba(11,31,58,0.12);
}

/* App background */
html, body, [data-testid="stAppViewContainer"], .stApp {
    background: var(--paper) !important;
}

/* Make labels and text readable */
label, .stMarkdown, .stText, p, span, div {
    color: var(--ink) !important;
}

/* Force readable input text (including disabled) */
input[type="text"], input[type="number"], textarea {
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
}
input::placeholder, textarea::placeholder {
    color: #8a96a8 !important;
    -webkit-text-fill-color: #8a96a8 !important;
}

/* Inputs: text, number, textarea */
input[type="text"], input[type="number"], textarea {
    border: 0 !important;
    border-radius: var(--field-radius) !important;
    background: var(--panel) !important;
    color: var(--ink) !important;
    box-shadow: none !important;
}
/* Number input steppers: hide right-side buttons */
div[data-baseweb="input"] button,
div[data-baseweb="input"] [data-baseweb="button"],
div[data-baseweb="input"] [role="button"] {
    display: none !important;
}
div[data-baseweb="input"] [aria-label="Increment"],
div[data-baseweb="input"] [aria-label="Decrement"] {
    display: none !important;
}
div[data-baseweb="input"] > div > div:last-child {
    display: none !important;
}
div[data-baseweb="input"] > div > div:last-child > div {
    display: none !important;
}
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
    -webkit-appearance: none !important;
    margin: 0 !important;
}
input[type="number"] {
    -moz-appearance: textfield !important;
}

/* Additional Services: wrap long labels tighter */
.additional-services label {
    max-width: 260px;
    display: inline-block;
    white-space: normal;
}
.st-key-tab3-scope .task-label {
    margin-top: 10px;
    line-height: 1.2;
}
.st-key-tab3-scope div[data-baseweb="checkbox"] {
    margin-top: 0;
}
/* ===== Tab 3 (scoped to st.container(key="tab3-scope")) ===== */

/* Only the CPS header + CPS rows are forced into flex. Do NOT target all stHorizontalBlock. */
.st-key-tab3-scope .st-key-cps-header [data-testid="stHorizontalBlock"],
.st-key-tab3-scope [class^="st-key-cps-row-"] [data-testid="stHorizontalBlock"]{
  display:flex !important;
  flex-wrap:nowrap !important;
  align-items:center !important;
  justify-content:flex-start !important;
  gap:16px !important;
  width:100% !important;
}

/* Default: don't let child wrappers grow unpredictably */
.st-key-tab3-scope .st-key-cps-header [data-testid="stHorizontalBlock"] > div,
.st-key-tab3-scope [class^="st-key-cps-row-"] [data-testid="stHorizontalBlock"] > div{
  flex:0 0 auto !important;
  min-width:0 !important;
}

/* Checkbox column (32px) ? wrapper div that contains the checkbox widget */
.st-key-tab3-scope [class^="st-key-cps-row-"] [data-testid="stHorizontalBlock"] > div:has([class^="st-key-svc310_"]),
.st-key-tab3-scope .st-key-cps-header [data-testid="stHorizontalBlock"] > div:has(.cps-col-check){
  flex:0 0 32px !important;
  width:32px !important;
  min-width:32px !important;
  max-width:32px !important;
}

/* Fixed input columns (150px) ? wrapper divs that contain hrs/rate/cost widgets */
.st-key-tab3-scope [class^="st-key-cps-row-"] [data-testid="stHorizontalBlock"] > div:has([class^="st-key-hrs310_"]),
.st-key-tab3-scope [class^="st-key-cps-row-"] [data-testid="stHorizontalBlock"] > div:has([class^="st-key-rate310_"]),
.st-key-tab3-scope [class^="st-key-cps-row-"] [data-testid="stHorizontalBlock"] > div:has([class^="st-key-cost310_"]),
.st-key-tab3-scope .st-key-cps-header [data-testid="stHorizontalBlock"] > div:has(.cps-col-fixed){
  flex:0 0 150px !important;
  width:150px !important;
  min-width:150px !important;
  max-width:150px !important;
}

/* Service label should be the only flexible column */
.st-key-tab3-scope [class^="st-key-cps-row-"] [data-testid="stHorizontalBlock"] > div:has(.stMarkdown){
  flex:1 1 auto !important;
  min-width:0 !important;
}

/* Kill markdown paragraph margins so text aligns vertically with inputs */
.st-key-tab3-scope [class^="st-key-cps-row-"] .stMarkdown p,
.st-key-tab3-scope .st-key-cps-header .stMarkdown p{
  margin:0 !important;
}

/* Force BaseWeb input wrapper + input to obey 150px */
.st-key-tab3-scope [class^="st-key-cps-row-"] [class^="st-key-hrs310_"] [data-baseweb="input"],
.st-key-tab3-scope [class^="st-key-cps-row-"] [class^="st-key-rate310_"] [data-baseweb="input"],
.st-key-tab3-scope [class^="st-key-cps-row-"] [class^="st-key-cost310_"] [data-baseweb="input"]{
  width:150px !important;
  min-width:150px !important;
  max-width:150px !important;
}

.st-key-tab3-scope [class^="st-key-cps-row-"] [class^="st-key-hrs310_"] input,
.st-key-tab3-scope [class^="st-key-cps-row-"] [class^="st-key-rate310_"] input,
.st-key-tab3-scope [class^="st-key-cps-row-"] [class^="st-key-cost310_"] input{
  width:150px !important;
  min-width:150px !important;
  max-width:150px !important;
  box-sizing:border-box !important;
}
.additional-services .svc-label {
    margin-top: 10px;
    line-height: 1.2;
}
.st-key-tab3-scope div[data-baseweb="input"] {
    margin-top: 0;
}
.additional-services div[data-baseweb="checkbox"] {
    max-width: 260px;
}
.additional-services div[data-baseweb="input"] {
    max-width: 260px;
    margin-left: 24px;
}
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
    opacity: 1 !important;
}
/* BaseWeb input wrapper consistency */
div[data-baseweb="input"] > div {
    border: var(--field-border-width) solid var(--field-border) !important;
    border-radius: var(--field-radius) !important;
    background: var(--panel) !important;
    box-shadow: 0 2px 6px rgba(11,31,58,0.06) !important;
}
div[data-baseweb="input"] input {
    border: none !important;
    box-shadow: none !important;
}
input[disabled], textarea[disabled] {
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
    opacity: 1 !important;
    background: #ffffff !important;
}

/* Selectbox (BaseWeb) */
div[data-baseweb="select"] > div {
    border: var(--field-border-width) solid var(--field-border) !important;
    border-radius: var(--field-radius) !important;
    background: var(--panel) !important;
    color: var(--ink) !important;
    box-shadow: 0 2px 6px rgba(11,31,58,0.06) !important;
}
div[data-baseweb="select"] [aria-disabled="true"] {
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
    opacity: 1 !important;
}
div[data-baseweb="select"] * {
    color: var(--ink) !important;
}
div[data-baseweb="select"] [data-baseweb="select"] {
    background: var(--panel) !important;
}

/* Multiselect / dropdown menu background */
div[data-baseweb="popover"] {
    color: var(--ink) !important;
}
ul[role="listbox"] {
    background: var(--panel) !important;
}
li[role="option"] {
    background: var(--panel) !important;
    color: var(--ink) !important;
}
li[role="option"][aria-selected="true"] {
    background: #eef3fb !important;
    color: var(--ink) !important;
}

/* Checkboxes: increase contrast */
div[data-baseweb="checkbox"] svg {
    color: var(--navy) !important;
    fill: none !important;
}
div[data-baseweb="checkbox"] > div,
div[data-baseweb="checkbox"] div[role="checkbox"] {
    border-color: #b9c6db !important;
    background: #edf2f9 !important;
    opacity: 0.8 !important;
    border-width: 0.2px !important;
    border-radius: 4px !important;
    box-shadow: inset 0 0 0 0.2px #b9c6db !important;
}
div[data-baseweb="checkbox"] div[role="checkbox"][aria-checked="true"] {
    background: #edf2f9 !important;
    border-color: #b9c6db !important;
    box-shadow: inset 0 0 0 1px #b9c6db !important;
}
div[data-baseweb="checkbox"] div[role="checkbox"] > div {
    background: #edf2f9 !important;
}
div[data-baseweb="checkbox"] div[role="checkbox"] svg {
    fill: none !important;
}
div[data-baseweb="checkbox"] div[role="checkbox"] svg rect {
    fill: #edf2f9 !important;
    stroke: #b9c6db !important;
    stroke-width: 0.2px !important;
}
div[data-baseweb="checkbox"] div[role="checkbox"] svg path {
    stroke: #6b7a99 !important;
    fill: none !important;
}
div[data-baseweb="checkbox"] div[role="checkbox"]::before,
div[data-baseweb="checkbox"] div[role="checkbox"]::after {
    background: #edf2f9 !important;
}

/* Total proposal cost badge */
.total-proposal-badge {
    background: #f1f5fb;
    border: 2px solid var(--navy);
    color: var(--navy);
    border-radius: 10px;
    padding: 10px 14px;
    font-weight: 700;
    text-align: right;
    box-shadow: 0 6px 14px rgba(11,31,58,0.12);
}

/* Buttons */
button[kind="primary"], button, .stButton>button {
    border: 2px solid var(--navy) !important;
    background: var(--btn-bg) !important;
    color: var(--btn-text) !important;
    border-radius: var(--field-radius) !important;
    box-shadow: 0 6px 14px rgba(11,31,58,0.12) !important;
    height: 46px !important;
}
button:hover, .stButton>button:hover {
    background: #e4ebf7 !important;
}
button:disabled, .stButton>button:disabled {
    border: 2px solid var(--navy) !important;
    background: var(--btn-bg) !important;
    color: var(--btn-text) !important;
    box-shadow: none !important;
    opacity: 1 !important;
}

/* Link buttons should match regular buttons */
div[data-testid="stLinkButton"] > a,
div[data-testid="stLinkButton"] > a > button {
    border: 2px solid var(--navy) !important;
    background: var(--btn-bg) !important;
    color: var(--btn-text) !important;
    border-radius: var(--field-radius) !important;
    box-shadow: 0 6px 14px rgba(11,31,58,0.12) !important;
    height: 46px !important;
}
div[data-testid="stLinkButton"] > a:hover,
div[data-testid="stLinkButton"] > a:hover > button {
    background: #e4ebf7 !important;
}

/* Help tooltip icon */
[data-testid="stTooltipIcon"] {
    width: 22px !important;
    height: 22px !important;
    min-width: 22px !important;
    min-height: 22px !important;
    border-radius: 50% !important;
    background: var(--paper) !important;
    border: 2px solid var(--navy) !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}
[data-testid="stTooltipIcon"] svg {
    width: 12px !important;
    height: 12px !important;
    color: var(--navy) !important;
    fill: var(--navy) !important;
}

/* Tabs */
div[data-testid="stTabs"] {
    margin-top: 6px;
}
div[data-testid="stTabs"] button[role="tab"] {
    background: var(--tab-bg) !important;
    color: var(--tab-text) !important;
    border: 1px solid var(--tab-border) !important;
    border-bottom: 0 !important;
    border-radius: 12px 12px 0 0 !important;
    padding: 10px 18px !important;
    margin-right: 8px !important;
    box-shadow: var(--tab-shadow) !important;
    font-weight: 600 !important;
    letter-spacing: 0.2px !important;
}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    background: var(--tab-bg-active) !important;
    color: var(--tab-text-active) !important;
    border-bottom-color: transparent !important;
    box-shadow: none !important;
}
div[data-testid="stTabs"] div[role="tablist"] {
    gap: 6px !important;
    border-bottom: 1px solid var(--border) !important;
    padding-bottom: 4px !important;
}

/* Expand sidebar/background if present */
section[data-testid="stSidebar"] {
    background: var(--paper) !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


BASE_DIR = pathlib.Path(__file__).parent
CITY_LOOKUP_PATH = BASE_DIR / "Data" / "pinellas_county_cities_lookup.json"

# -----------------------------------------------------------------------------
# City lookup + map button helpers (from your Tab 1 code)
# -----------------------------------------------------------------------------
PINELLAS_CITY_MAP = {
    'SP': 'St. Petersburg',
    'ST PETERSBURG': 'St. Petersburg',
    'ST. PETERSBURG': 'St. Petersburg',
    'CLEARWATER': 'Clearwater',
    'CW': 'Clearwater',
    'CWD': 'Clearwater',
    'LARGO': 'Largo',
    'LA': 'Largo',
    'PINELLAS PARK': 'Pinellas Park',
    'PP': 'Pinellas Park',
    'PPW': 'Pinellas Park',
    'DUNEDIN': 'Dunedin',
    'TARPON SPRINGS': 'Tarpon Springs',
    'TS': 'Tarpon Springs',
    'SEMINOLE': 'Seminole',
    'KENNETH CITY': 'Kenneth City',
    'GULFPORT': 'Gulfport',
    'MB': 'Madeira Beach',
    'MADEIRA BEACH': 'Madeira Beach',
    'REDINGTON BEACH': 'Redington Beach',
    'TREASURE ISLAND': 'Treasure Island',
    'ST PETE BEACH': 'St. Pete Beach',
    'SOUTH PASADENA': 'South Pasadena',
    'BELLEAIR': 'Belleair',
    'BELLEAIR BEACH': 'Belleair Beach',
    'BELLEAIR BLUFFS': 'Belleair Bluffs',
    'INDIAN ROCKS BEACH': 'Indian Rocks Beach',
    'INDIAN SHORES': 'Indian Shores',
    'NORTH REDINGTON BEACH': 'North Redington Beach',
    'OLDSMAR': 'Oldsmar',
    'SAFETY HARBOR': 'Safety Harbor',
    'LFPW': 'Unincorporated Pinellas (Lealman)',
    'LEALMAN': 'Unincorporated Pinellas (Lealman)',
    'UNINCORPORATED': 'Unincorporated Pinellas',
    'COUNTY': 'Unincorporated Pinellas'
}

def _load_city_lookup() -> Dict[str, Any]:
    try:
        with open(CITY_LOOKUP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

CITY_LOOKUP = _load_city_lookup()
CITY_LOOKUP_BY_NAME = {k.strip().lower(): v for k, v in CITY_LOOKUP.items() if isinstance(v, dict)}

CITY_NAMES_FROM_LOOKUP = {
    name.strip().upper()
    for name, meta in CITY_LOOKUP.items()
    if isinstance(meta, dict) and meta.get("type") == "city_app"
}
for city_name in CITY_NAMES_FROM_LOOKUP:
    PINELLAS_CITY_MAP.setdefault(city_name, city_name.title())

def _get_city_map_url(city_name: str) -> Optional[str]:
    if not city_name:
        return None
    key = city_name.strip().lower()
    meta = CITY_LOOKUP_BY_NAME.get(key)
    if not meta:
        return None
    for k in (
        "zoning_flu_app",
        "zoning_lookup_app",
        "zoning_app",
        "gis_viewer_app",
        "future_land_use_2045_app",
        "open_data_hub",
        "mapserver",
    ):
        if meta.get(k):
            return meta.get(k)
    return None

def _build_map_url_with_address(map_url: Optional[str], address: str, city: str, zip_code: str) -> Optional[str]:
    if not map_url or not address:
        return map_url
    if not any(token in map_url.lower() for token in ("arcgis.com/apps", "webappviewer", "informationlookup")):
        return map_url

    search = address.strip()
    if city:
        city_lower = city.strip().lower()
        if city_lower and city_lower not in search.lower():
            search = f"{search}, {city}, FL"
        else:
            search = f"{search}, FL"
    if zip_code:
        zip_clean = zip_code.strip()
        if zip_clean and zip_clean not in search:
            search = f"{search} {zip_clean}"

    parsed = urlparse(map_url)
    query = parse_qs(parsed.query)
    if "find" in query:
        return map_url
    query["find"] = [search]
    new_query = urlencode(query, doseq=True, quote_via=quote)
    return urlunparse(parsed._replace(query=new_query))

def expand_city_name(city_abbr: str) -> str:
    if not city_abbr:
        return "Unincorporated Pinellas"
    city_upper = city_abbr.strip().upper()
    return PINELLAS_CITY_MAP.get(city_upper, city_abbr)

def validate_parcel_id(parcel_id: str):
    if not parcel_id:
        return False, "Parcel ID cannot be empty"
    if len(parcel_id) > 30:
        return False, "Parcel ID must be 30 characters or less"
    if not re.match(r'^[A-Za-z0-9\-\s\.]+$', parcel_id):
        return False, "Invalid characters in parcel ID"
    return True, ""

def strip_dor_code(land_use_text: str) -> str:
    if not land_use_text:
        return ""
    t = land_use_text.strip()
    if t and t[0].isdigit():
        parts = t.split(" ", 1)
        if len(parts) > 1:
            return parts[1].strip()
    return t

def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def format_currency(value: Optional[float]) -> str:
    if value is None or value == "":
        return ""
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return ""

@st.cache_resource
def get_resilient_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def scrape_pinellas_property(parcel_id: str) -> Dict[str, Any]:
    """
    Pinellas County Property Appraiser quicksearch backend.
    """
    session = get_resilient_session()
    url = "https://www.pcpao.gov/dal/quicksearch/searchProperty"

    normalized_parcel = parcel_id.strip()
    if "-" not in normalized_parcel and len(normalized_parcel) == 18:
        normalized_parcel = f"{normalized_parcel[0:2]}-{normalized_parcel[2:4]}-{normalized_parcel[4:6]}-{normalized_parcel[6:11]}-{normalized_parcel[11:14]}-{normalized_parcel[14:18]}"

    payload = {
        "draw": "1",
        "start": "0",
        "length": "10",
        "search[value]": "",
        "search[regex]": "false",
        "input": normalized_parcel,
        "searchsort": "parcel_number",
        "url": "https://www.pcpao.gov",
    }
    for i in range(11):
        payload[f"columns[{i}][data]"] = str(i)
        payload[f"columns[{i}][name]"] = ""
        payload[f"columns[{i}][searchable]"] = "true"
        payload[f"columns[{i}][orderable]"] = "true" if i >= 2 else "false"
        payload[f"columns[{i}][search][value]"] = ""
        payload[f"columns[{i}][search][regex]"] = "false"

    try:
        response = session.post(url, data=payload, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("recordsTotal", 0) == 0:
            return {"success": False, "error": "Parcel not found in PCPAO database"}

        if not data.get("data"):
            return {"success": False, "error": "No property data returned"}

        row = data["data"][0]

        owner = BeautifulSoup(row[2] if len(row) > 2 else "", "lxml").get_text(strip=True)
        address = BeautifulSoup(row[5] if len(row) > 5 else "", "lxml").get_text(strip=True)
        tax_district = BeautifulSoup(row[6] if len(row) > 6 else "", "lxml").get_text(strip=True)
        city = expand_city_name(tax_district)
        property_use = BeautifulSoup(row[7] if len(row) > 7 else "", "lxml").get_text(strip=True)
        legal_desc = BeautifulSoup(row[8] if len(row) > 8 else "", "lxml").get_text(strip=True)

        sqft = None
        acres = None
        zip_code = None
        strap = None

        try:
            parts = normalized_parcel.split("-")
            if len(parts) == 6:
                parts[0], parts[2] = parts[2], parts[0]
                strap = "".join(parts)
            else:
                strap = normalized_parcel.replace("-", "")

            detail_url = (
                f"https://www.pcpao.gov/property-details"
                f"?s={strap}&input={normalized_parcel}&search_option=parcel_number"
            )
            html = session.get(detail_url, timeout=30).text
            soup = BeautifulSoup(html, "html.parser")
            txt = soup.get_text(" ", strip=True)

            m = re.search(
                r"Land Area:\s*[^\d]*([\d,]+)\s*sf\s*\|\s*[^\d]*([\d.]+)\s*acres",
                txt,
                flags=re.IGNORECASE,
            )
            if m:
                sqft = int(m.group(1).replace(",", ""))
                acres = float(m.group(2))

            z = re.search(r"FL\s*(\d{5})", txt)
            if z:
                zip_code = z.group(1)
        except Exception:
            pass

        return {
            "success": True,
            "address": address,
            "city": city,
            "zip": zip_code or "",
            "owner": owner,
            "land_use": strip_dor_code(property_use),
            "site_area_sqft": f"{sqft:,}" if sqft else "",
            "site_area_acres": f"{acres:.2f}" if acres else "",
            "legal_description": legal_desc,
            "strap": strap or "",
        }
    except Exception as e:
        return {"success": False, "error": f"Error querying PCPAO API: {str(e)}"}

# -----------------------------------------------------------------------------
# Proposal state
# -----------------------------------------------------------------------------
def init_proposal_state() -> None:
    if "proposal" not in st.session_state:
        st.session_state.proposal = {
            "intake": {
                "county": "Pinellas",
                "municipality": "",
                "jurisdiction_display": "",
                "parcel_id": "",
                "address": "",
                "city": "",
                "zip": "",
                "owner": "",
                "land_use": "",
                "site_area_acres": "",
                "site_area_sqft": "",
                "zoning": "",
                "future_land_use": "",
            },
            "client": {
                "client_name": "",
                "client_contact_name": "",
                "entity_name": "",
                "entity_address_name": "",
                "entity_address_line1": "",
                "entity_address_line2": "",
                "entity_address_city_state_zip": "",
            },
            "project": {
                "project_name": "",
                "property_name": "",
                "property_address_line1": "",
                "property_address_line2": "",
                "property_address_city_state_zip": "",
                "proposal_date": "",
                # Tab 2 additions:
                "project_description_short": "",
                "assumptions_checked": {},   # id -> bool
                "assumptions_other": "",
            },
            "scope": {
                # Tab 3 selections (tasks + fees)
                "selected_tasks": {},        # task_num -> dict
            },
            "permits": {
                # Tab 4 permit + additional services selections
                "permit_flags": {},          # key -> bool
                "included_additional_services": [],
                "included_additional_services_with_fees": {},
                "excluded_additional_services": [],
            },
            "invoice": {
                # Tab 5 invoice/billing info
                "invoice_email": "",
                "invoice_cc_email": "",
                "kh_signer_name": "",
                "kh_signer_title": "",
                "use_retainer": False,
                "retainer_amount": 0,
            },
        }

# -----------------------------------------------------------------------------
# Totals
# -----------------------------------------------------------------------------
def compute_total_proposal_cost() -> int:
    scope = st.session_state.proposal.get("scope", {})
    permits = st.session_state.proposal.get("permits", {})
    selected_tasks = scope.get("selected_tasks", {})

    total = 0
    for task_num, task in selected_tasks.items():
        total += int(task.get("fee", 0) or 0)
        if task_num == "310":
            svc_total = task.get("services_total_cost")
            if svc_total is None:
                services = task.get("services", {}) or {}
                svc_total = sum(int(s.get("cost", 0) or 0) for s in services.values())
            total += int(svc_total or 0)

    addl = permits.get("included_additional_services_with_fees", {}) or {}
    total += sum(int(v or 0) for v in addl.values())
    return total

# -----------------------------------------------------------------------------
# Tab 3/4/5 data (from New-Proposal-App)
# -----------------------------------------------------------------------------
DEFAULT_FEES = {
    "110": {"name": "Civil Engineering Design", "amount": 40000, "type": "Hourly, Not-to-Exceed"},
    "120": {"name": "Civil Schematic Design", "amount": 35000, "type": "Hourly, Not-to-Exceed"},
    "130": {"name": "Civil Design Development", "amount": 45000, "type": "Hourly, Not-to-Exceed"},
    "140": {"name": "Civil Construction Documents", "amount": 50000, "type": "Hourly, Not-to-Exceed"},
    "150": {"name": "Civil Permitting", "amount": 40000, "type": "Hourly, Not-to-Exceed"},
    "210": {"name": "Meetings and Coordination", "amount": 20000, "type": "Hourly, Not-to-Exceed"},
    "310": {"name": "Civil Construction Phase Services", "amount": 35000, "type": "Lump Sum"},
}

TASK_DESCRIPTIONS = {
    "110": [
        "Kimley-Horn will prepare an onsite drainage report with supporting calculations showing the proposed development plan is consistent with the Southwest Florida Water Management District Basis of Review. This design will account for the stormwater design to support the development of the project site. The drainage report will include limited stormwater modeling to demonstrate that the Lot A site development will maintain the existing discharge rate and provide the required stormwater attenuation.",
        "The onsite drainage report will include calculations for 25-year 24-hour and 100-year 24-hour design storm conditions in accordance with Southwest Florida Water Management District Guidelines. A base stormwater design will be provided for the project site showing reasonable locations for stormwater conveyance features and stormwater management pond sizing.",
    ],
    "120": [
        "Kimley-Horn will prepare Civil Schematic Design deliverables in accordance with the Client's Design Project Deliverables Checklist. For the Civil Schematic Design task, the deliverables that Kimley-Horn will provide consist of Civil Site Plan, Establish Finish Floor Elevations, Utility Will Serve Letters and Points of Service, Utility Routing and Easement Requirements.",
    ],
    "130": [
        "Upon Client approval of the Schematic Design task, Kimley-Horn will prepare Design Development Plans of the civil design in accordance with the Client's Design Project Deliverables Checklist for Civil Design Development Deliverables. These documents will be approximately 50% complete and will include detail for City code review and preliminary pricing but will not include enough detail for construction bidding.",
    ],
    "140": [
        "Based on the approved Development Plan, Kimley-Horn will provide engineering and design services for the preparation of site construction plans for on-site improvements.",
        "Cover Sheet",
        "The cover sheet includes plan contents, vicinity map, legal description and team identification.",
        "General Notes",
        "These sheets will provide general notes for the construction of the project.",
        "Existing Conditions / Demolition Plan",
        "Consisting of the boundary, topographic, and tree survey provided by others. This sheet will include and identify the required demolition of the existing items on the project site and facilities improvements prior to construction of the proposed site and facilities improvements.",
        "Stormwater Pollution Prevention Plan",
        "This sheet will include and identify stormwater best management practices for the construction of the proposed site including erosion control and stormwater management areas; applicable details, and specifications. This sheet may also be combined with the Existing Conditions/Demolition Plan sheets depending on the scope of the work.",
        "Site Plan (Horizontal Control & Signing and Marking Plan)",
        "Kimley-Horn shall prepare a Site Plan, as indicated above, with associated parking and infrastructure. Site Plan shall consist of the following: site geometry, building setbacks; roadway and parking dimensions including handicap spaces; landscape island locations and dimensions; storm water detention area locations and dimensions; boundary dimensions; dimensions and locations of pedestrian walks; signing and marking design. Signing and Marking within the structured parking as well as loading areas and compactors (if applicable) to be designed by the Architect.",
        "Paving, Grading, and Drainage Plan",
        "Kimley-Horn shall design and prepare a plan for the site paving, grading and drainage systems in accordance with the City, the FDOT, and the Water Management District (SWFWMD) to consist of: flood routing; pipe materials and sizing; grate and invert elevations; surface parking including pavement structural section (as provided by owner's geotechnical report); subgrade treatment; curbs; horizontal control; sidewalks; driveway connections; spot elevations and elevation contours; and construction details and specifications, and erosion and sedimentation control measures.",
        "**NOTE:**Any structural retaining walls are not included with this scope and shall be designed and permitted by others. Hardscape areas shall be designed by others, therefore paving, grading and drainage of these areas is not included. Stub-out connections for the hardscape drainage areas will be shown per direction from the Hardscape designer.",
        "Detailed grading and drainage design for any proposed pool deck or amenity area is to be designed and coordinated by the Architect and the MEP. Kimley-Horn can provide these services if requested by the client as additional services.",
        "Utility Plans",
        "Kimley-Horn shall prepare a plan for the site water distribution and sanitary sewer collection systems consisting of: sewer main locations; pipe sizing; manhole locations; rim and invert elevations; sewer lateral locations and size; existing sewer main connection; main location; materials and sizing; fire hydrant locations; water service locations; fire service locations and sizes; pipe materials; meter locations; sample points; existing water main connections; and construction details and specifications. Kimley-Horn will design the sanitary sewer to discharge to the adjacent development collection system. No upgrades to the off-site infrastructure. Should this be required during design and permitting, this will be submitted as an additional service.",
        "**NOTE:**Kimley-Horn's contract does not include the design of the fire lines from the designated point of service (P.O.S.) up to 1' above the building finished floor as those lines will need to be sized and designed by a licensed fire sprinkler engineer and permitted separately.",
        "Kimley-Horn has assumed utilities are available and have adequate capacity to accommodate the proposed development. Kimley-Horn assumes the utilities are located at the project boundary and will not require off-site utility extensions. If off-site extensions are needed, they will be provided as additional services. Lift station, force main, and pump design and permitting, if needed, is not included but can be provided as an Additional Service if needed.",
        "It is assumed a private lift station will not be required to serve this development, therefore lift station design is not included in this scope.",
        "Kimley-Horn shall show any existing utility locations on the utility plans as provided by the surveyor, and research applicable utility records for locations in accordance with best available information.",
        "Dedicated Fire Lines and Combination Domestic Water / Fire Lines, if needed, shall be designed and permitted by a licensed Fire Contractor Class I, II or V per NFPA 24 and is not included in this scope of services. Those lines will be shown on the Civil plans for permitting and reference only.",
        "Routing of proposed dry utilities such as gas, electric, telephone or cable service connections is not included in this scope of services and should be provided by others. Kimley-Horn will meet with the project team to incorporate dry utility routing as provided to us into our utility plans for coordination purposes.",
        "Street lighting design, photometrics and site electrical plans will be provided by the Client's Architect or Architect's MEP. Overhead electrical lines and transformers will be designed and located by the site electrical designer or local provider but will be placed on the Construction plans for coordination.",
        "Civil Details and Construction Specifications",
        "Kimley-Horn shall prepare construction details for site work improvements and erosion and sediment control measures. Typically, these details will correspond with City standard details. Standard FDOT details will not be provided but will be referenced throughout the plans.",
        "**NOTE:**A specifications package is not included in this scope of services as specifications are per authority having jurisdiction (AHJ). Preparation of detailed specifications to be supplied with the architect's specifications can be provided, per request, as additional services.",
    ],
    "150": [
        "Prepare and submit on the Client's behalf the following permitting packages for review/approval of construction documents, and attend meetings required to obtain the following Agency approvals:",
        "Southwest Florida Water Management District Environmental Resource Permit xxx Minor Modification",
        "City of Tampa Water Department Commitment / Construction Plan Approval",
        "Hillsborough County Environmental Protection Commission",
        "Kimley-Horn will coordinate with the City of Tampa Development Review and coordination with the Florida Department of Transportation and the Hillsborough County departments as needed to obtain the necessary regulatory and utility approval of the site plans and associated drainage facilities. We will assist the Client with meetings necessary to gain site plan approval.",
        "This scope does not anticipate a Geotechnical or Environmental Assessment Report, Survey, Topographic Survey, or Arborist Report be required for this permit application.",
        "It is assumed Client will provide the needed information regarding the development program and requirements. Kimley-Horn will work with the Owner and their team to integrate the necessary design requirements into the Civil design to support entitlement, platting, and development approvals.",
        "These permit applications will be submitted using the electronic permitting submittal system (web-based system) for the respective jurisdictions where applicable.",
    ],
    "210": [
        "Kimley-Horn will be available to provide miscellaneous project support at the direction of the Client. This task may include design meetings, additional permit support, permit research, or other miscellaneous tasks associated with the initial and future development of the project site. This task will also cover tasks such as design coordination meetings, scheduling, coordination with other client consultants, responses to additional rounds of agency comments.",
    ],
    "310": [
        "Engineering construction phase services will be performed in connection with site improvements designed by Kimley-Horn. The scope of this task assumes construction phase services will be performed concurrent and in coordination with one General Contractor for the entire project. This task does not include constructing the project in multiple phases. Kimley-Horn construction phase services will include the following:",
        "Provide for review of shop drawings and submittals required for the site improvements controlled by our design documents. Kimley-Horn has included up to {shop_drawing_hours} hours for review of shop drawings and samples.",
        "Review and reply to Contractor's request(s) for information during construction phase. Kimley-Horn has included up to {rfi_hours} hours for response to RFI's.",
        "Attendance at up to {oac_meetings} one-hour each Owner-Architect-Contractor (OAC) virtual meetings.",
        "Kimley-Horn will visit the construction site during the duration of construction for an estimated total of up to {site_visits} site visits at two-hours each to observe the progress of the civil components of work completed.",
        "Provide up to two (2) reviews of 'as-built' documents, submitted by General Contractor's registered land surveyor.",
        "Kimley-Horn will prepare Record Drawings for potable water and sanitary sewer only. Kimley-Horn has included up to {record_drawing_hours} hours for record drawing preparation.",
        "Kimley-Horn will submit FDEP water and sewer clearance submittals based on as-built information provided by the Contractor.",
        "Kimley-Horn shall submit a Letter of General Compliance for the civil related components of construction to the AHJ.",
        "Submit Certification of Completion to the Water Management District (WMD).",
        "The above hours allocated to the respective construction phase services may be interchangeable amongst the construction phase services outlined in this task, however the total number of hours included within the entirety of the task is up to {total_hours} hours.",
    ],
}

PERMIT_MAPPING = {
    "Pinellas": {
        "ahj_name": "Pinellas County",
        "wmd": "Southwest Florida Water Management District",
        "wmd_short": "SWFWMD",
        "default_permits": ["ahj", "wmd_erp", "sewer", "water"],
    },
    "Hillsborough": {
        "ahj_name": "Hillsborough County",
        "wmd": "Southwest Florida Water Management District",
        "wmd_short": "SWFWMD",
        "default_permits": ["ahj", "wmd_erp", "sewer", "water"],
    },
    "Pasco": {
        "ahj_name": "Pasco County",
        "wmd": "Southwest Florida Water Management District",
        "wmd_short": "SWFWMD",
        "default_permits": ["ahj", "wmd_erp", "sewer", "water"],
    },
}

ADDITIONAL_SERVICES_LIST = [
    ("offsite_roadway", "Off-site roadway, traffic signal design or utility improvements", False, 25000),
    ("offsite_utility", "Off-site utility capacity analysis and extensions", False, 15000),
    ("utility_relocation", "Utility relocation design and plans", False, 12000),
    ("cost_opinions", "Preparation of opinions of probable construction costs", False, 5000),
    ("dewatering", "Dewatering permitting (to be provided by Contractor)", False, 3000),
    ("site_lighting", "Site lighting, photometric, and site electrical plan", False, 8000),
    ("dry_utility", "Dry utility coordination and design", False, 10000),
    ("landscape", "Landscape, irrigation, hardscape design and tree mitigation", False, 20000),
    ("fire_line", "Fire line design", False, 6000),
    ("row_permitting", "Right-of-way permitting", False, 8000),
    ("concurrency", "Concurrency application assistance", False, 5000),
    ("3d_modeling", "3D modeling and graphic/presentations", False, 8000),
    ("leed", "LEED certification and review", False, 20000),
    ("schematic_dd", "Schematic and design development plans", False, 15000),
    ("extra_meetings", "Meetings other than those described in the tasks above", False, 5000),
    ("surveying", "Boundary, topographic and tree surveying, platting and subsurface utility exploration", False, 25000),
    ("platting", "Platting or easement assistance", False, 8000),
    ("traffic_studies", "Traffic studies, analysis, property share agreement", False, 30000),
    ("mot_plans", "Maintenance of traffic plans", False, 12000),
    ("structural", "Structural engineering (including retaining walls)", False, 35000),
    ("signage", "Signage design", False, 4000),
    ("extra_design", "Design elements beyond those outlined in the above project understanding", False, 10000),
    ("peer_review", "Responding to comments from third-party peer review", False, 8000),
]

TASK_310_SERVICES = [
    ("shop_drawings", "Shop Drawing Review", 30, 165, 4950),
    ("rfi", "RFI Response", 50, 165, 8250),
    ("oac", "OAC Meetings", 24, 0, 3000),
    ("site_visits", "Site Visits (2 hrs each)", 4, 0, 1000),
    ("asbuilt", "As-Built Reviews", 2, 0, 500),
    ("inspection_tv", "Inspection & TV Reports", 0, 165, 0),
    ("record_drawings", "Record Drawings (Water/Sewer)", 40, 165, 6600),
    ("fdep", "FDEP Clearance Submittals", 0, 0, 0),
    ("compliance", "Letter of General Compliance", 0, 0, 0),
    ("wmd", "WMD Certification", 0, 0, 0),
]
# -----------------------------------------------------------------------------
# UI renderers
# -----------------------------------------------------------------------------
def render_tab1():
    st.subheader("Project Info — Intake (Lookup)")
    left, right = st.columns([1, 1])

    intake = st.session_state.proposal["intake"]

    with left:
        st.markdown("**Property Lookup**")

        parcel_col, county_col = st.columns([2, 1])
        with parcel_col:
            parcel_id_input = st.text_input(
                "Parcel ID",
                value=intake.get("parcel_id", ""),
                placeholder="e.g. 19-31-17-73166-001-0010",
            )
        with county_col:
            county_options = ["Pinellas", "Hillsborough", "Pasco"]
            current_county = intake.get("county", "Pinellas") or "Pinellas"
            county_index = county_options.index(current_county) if current_county in county_options else 0
            county_input = st.selectbox("County", options=county_options, index=county_index)
            intake["county"] = county_input

        if st.button("Lookup Property Data", type="primary", use_container_width=True, key="lookup_property"):
            if not parcel_id_input:
                st.error("Please enter a parcel ID.")
            else:
                is_valid, error_msg = validate_parcel_id(parcel_id_input)
                if not is_valid:
                    st.error(error_msg)
                elif county_input != "Pinellas":
                    intake["county"] = county_input
                    intake["parcel_id"] = parcel_id_input
                    st.error("Property lookup is only implemented for Pinellas County right now.")
                else:
                    with st.spinner("Fetching property data from PCPAO API..."):
                        result = scrape_pinellas_property(parcel_id_input)

                    if result.get("success"):
                        intake["county"] = county_input
                        intake["parcel_id"] = parcel_id_input
                        intake["address"] = result.get("address", "") or ""
                        intake["city"] = expand_city_name(result.get("city", "") or "")
                        intake["zip"] = result.get("zip", "") or ""
                        intake["owner"] = result.get("owner", "") or ""
                        intake["land_use"] = result.get("land_use", "") or ""
                        intake["site_area_sqft"] = result.get("site_area_sqft", "") or ""
                        intake["site_area_acres"] = result.get("site_area_acres", "") or ""
                        intake["municipality"] = intake["city"]
                        intake["jurisdiction_display"] = intake["city"]
                        st.success("Property data retrieved.")
                        st.rerun()
                    else:
                        st.error(result.get("error", "Lookup failed"))

        intake["county"] = county_input
        city = expand_city_name(intake.get("city", "") or "")
        map_url = _get_city_map_url(city)
        map_url = _build_map_url_with_address(
            map_url,
            intake.get("address", "") or "",
            city,
            intake.get("zip", "") or "",
        )
        button_label = f"Open {city} Zoning and Land Use Map" if city else "Open Zoning and Land Use Map"
        if map_url:
            st.link_button(button_label, map_url, use_container_width=True)
            if city.strip().lower() == "pinellas park":
                st.caption("Pinellas Park map opens with a confirmation prompt—check the box to continue.")
            if city.strip().lower() == "largo":
                st.caption("Largo map opens with a prompt—select a screen to continue.")
        else:
            st.button(button_label, use_container_width=True, disabled=True)
            st.info("No city map link found for this municipality.")

        st.markdown("**Lookup Summary (Auto-fills tokens)**")
        intake["county"] = st.text_input("County", value=intake.get("county", ""))
        intake["city"] = st.text_input("City", value=intake.get("city", ""))
        intake["address"] = st.text_input("Address", value=intake.get("address", ""))
        intake["owner"] = st.text_input("Owner", value=intake.get("owner", ""))
        intake["land_use"] = st.text_input("Land Use", value=intake.get("land_use", ""))
        intake["zoning"] = st.text_input("Zoning (full)", value=intake.get("zoning", ""))
        intake["future_land_use"] = st.text_input("Future Land Use (full)", value=intake.get("future_land_use", ""))
        intake["site_area_acres"] = st.text_input("Site Area (acres)", value=intake.get("site_area_acres", ""))
        intake["site_area_sqft"] = st.text_input("Site Area (sf)", value=intake.get("site_area_sqft", ""))

    with right:
        project = st.session_state.proposal["project"]
        client = st.session_state.proposal["client"]

        current_addr = intake.get("address", "") or ""
        prev_addr = st.session_state.get("last_intake_address", "")
        prop_addr_key = "property_address_line1_input"
        prop_csz_key = "property_address_city_state_zip_input"
        if prop_addr_key not in st.session_state:
            st.session_state[prop_addr_key] = project.get("property_address_line1", "") or current_addr
        if current_addr and (not st.session_state[prop_addr_key] or st.session_state[prop_addr_key] == prev_addr):
            st.session_state[prop_addr_key] = current_addr
        if prop_csz_key not in st.session_state:
            st.session_state[prop_csz_key] = project.get("property_address_city_state_zip", "")
        if intake.get("city") or intake.get("zip"):
            city = expand_city_name(intake.get("city", "")) if intake.get("city") else ""
            zip_code = intake.get("zip", "")
            csz = f"{city}, FL {zip_code}".strip().replace("  ", " ").strip(", ")
            if csz and (not st.session_state[prop_csz_key] or st.session_state[prop_csz_key] == st.session_state.get("last_intake_csz", "")):
                st.session_state[prop_csz_key] = csz
            st.session_state["last_intake_csz"] = csz
        st.session_state["last_intake_address"] = current_addr

        st.markdown("**Project (Tokens)**")
        project["project_name"] = st.text_input("Project Name", value=project.get("project_name", ""))
        st.markdown("**Property Address**")
        project["property_name"] = st.text_input("Name", value=project.get("property_name", ""), key="property_name")
        project["property_address_line1"] = st.text_input("Address", key=prop_addr_key)
        project["property_address_line2"] = st.text_input("Apt / Unit / Suite", value=project.get("property_address_line2", ""), key="property_address_line2")
        project["property_address_city_state_zip"] = st.text_input("City, State, ZIP", key=prop_csz_key)
        project["proposal_date"] = st.text_input("Proposal Date (optional)", value=project.get("proposal_date", ""))

        st.markdown("**Client / Entity (Tokens)**")
        client["client_name"] = st.text_input("Client Name", value=client.get("client_name", ""))
        client["client_contact_name"] = st.text_input("Client Contact Name", value=client.get("client_contact_name", ""))
        client["entity_name"] = st.text_input("Client Legal Entity (Sunbiz)", value=client.get("entity_name", ""))
        st.markdown("**Entity Address**")
        client["entity_address_name"] = st.text_input("Name", value=client.get("entity_address_name", ""), key="entity_address_name")
        client["entity_address_line1"] = st.text_input("Address", value=client.get("entity_address_line1", ""), key="entity_address_line1")
        client["entity_address_line2"] = st.text_input("Apt / Unit / Suite", value=client.get("entity_address_line2", ""), key="entity_address_line2")
        client["entity_address_city_state_zip"] = st.text_input("City, State, ZIP", value=client.get("entity_address_city_state_zip", ""), key="entity_address_city_state_zip")

def render_tab2():
    st.subheader("Project Understanding")

    proj = st.session_state.proposal["project"]
    intake = st.session_state.proposal["intake"]

    # Short description field (user input)
    proj["project_description_short"] = st.text_area(
        "Short project description",
        value=proj.get("project_description_short", ""),
        height=120,
        placeholder="Example: Client plans to develop ...",
    )

    st.markdown("### Project Assumptions (check all that apply)")
    city_name = expand_city_name(intake.get("city", "") or "")
    county_name = intake.get("county", "") or ""
    if city_name and "unincorporated" in city_name.lower():
        jurisdiction = f"{county_name} County".strip()
    else:
        jurisdiction = city_name or f"{county_name} County".strip()
    if not jurisdiction:
        jurisdiction = "jurisdiction"
    assumptions = [
        ("assump_one_phase", "The project will be designed, permitted, and constructed in one phase."),
        ("assump_waivers_addsvc", "If waivers are required, that will be considered an additional service."),
        ("assump_water_sewer_cosp", f"Water and Sewer will be served by {jurisdiction}. It is assumed existing infrastructure is adequate. Lift station not required; can be added if required."),
        ("assump_no_offsite", "Offsite roadway improvements or utility extensions not within the site area will be considered a separate scope."),
        ("assump_no_platting", "It is assumed that platting is not required; platting assistance can be provided as a separate scope."),
        ("assump_no_traffic", "It is assumed that no traffic analysis is required; if needed it can be provided as an additional service."),
        ("assump_geotech_by_client", "A geotechnical report with pavement recommendations, borings, and groundwater information will be provided by Client."),
        ("assump_no_wetlands", "No wetlands are present on the subject site."),
        ("assump_no_flood_comp", "No floodplain compensation is anticipated to be required."),
        ("assump_no_protected_species", "No protected species are anticipated to be present on the subject site."),
    ]
    checked = proj.setdefault("assumptions_checked", {})
    for aid, label in assumptions:
        checked[aid] = st.checkbox(label, value=bool(checked.get(aid, False)), key=f"tab2_{aid}")

    st.markdown("### Additional Project Assumptions (optional)")
    proj["assumptions_other"] = st.text_area(
        "Additional assumptions / clarifications",
        value=proj.get("assumptions_other", ""),
        height=100,
        placeholder="Enter any additional assumptions, exclusions, phasing notes, etc.",
    )

    st.markdown("### Project Understanding (auto-generated)")
    parts = []
    desc = proj.get("project_description_short", "").strip()
    if desc:
        parts.append(desc.rstrip("."))
    parcel_id = intake.get("parcel_id", "")
    address = intake.get("address", "")
    city = intake.get("city", "")
    county = intake.get("county", "")
    land_use = intake.get("land_use", "")
    acres = intake.get("site_area_acres", "")
    zoning = (intake.get("zoning", "") or "").strip()
    flu = (intake.get("future_land_use", "") or "").strip()

    loc_bits = []
    if address:
        loc_bits.append(address)
    if city:
        loc_bits.append(city)
    if county:
        loc_bits.append(f"{county} County")
    if loc_bits:
        parts.append(f"The site is located at {', '.join(loc_bits)}")
    if parcel_id:
        parts.append(f"Parcel ID {parcel_id}")
    if land_use:
        parts.append(f"Current land use is {land_use}")
    if acres:
        parts.append(f"Site area is {acres} acres")
    if zoning:
        parts.append(f"Zoning: {zoning}")
    if flu:
        parts.append(f"Future Land Use: {flu}")

    if parts:
        paragraph = ". ".join(parts).strip() + "."
    else:
        paragraph = "Enter project details in Tab 1 and the short description above to generate this paragraph."

    current_text = proj.get("project_understanding", "")
    last_auto = proj.get("project_understanding_auto", "")
    if not current_text or current_text == last_auto:
        proj["project_understanding"] = paragraph
        proj["project_understanding_auto"] = paragraph

    proj["project_understanding"] = st.text_area(
        "Project Understanding (auto-generated)",
        value=proj.get("project_understanding", paragraph),
        height=110,
    )

    # Simple preview of what will be inserted
    st.divider()
    st.markdown("**Preview (Project Understanding paragraph stub)**")
    if intake.get("parcel_id"):
        st.write(
            f"{proj.get('project_description_short','').strip()} "
            f"(Parcel ID: {intake.get('parcel_id','')}; Address: {intake.get('address','')})"
        )
    else:
        st.write(proj.get("project_description_short","").strip())

def render_tab3():
    st.subheader("Scope of Services")
    st.markdown("Select the tasks to include and enter the fee for each task.")

    scope = st.session_state.proposal["scope"]
    selected_tasks = scope.setdefault("selected_tasks", {})

    with st.container(key="tab3-scope"):
        for task_num in sorted(DEFAULT_FEES.keys()):
            task = DEFAULT_FEES[task_num]
            existing = selected_tasks.get(task_num, {})

            col_check, col_name, col_fee = st.columns([0.5, 3, 2])

            with col_check:
                task_selected = st.checkbox(
                    f"{task_num}",
                    value=bool(existing) or task_num == "310",
                    key=f"check_{task_num}",
                    label_visibility="collapsed",
                )

            with col_name:
                if task_num == "310":
                    st.markdown(
                        f'<div class="task-label" style="display:inline-block; transform: translateY(8px);"><strong>Task {task_num}: {task["name"]}</strong> <em>(uncheck if not needed)</em></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="task-label" style="display:inline-block; transform: translateY(8px);"><strong>Task {task_num}: {task["name"]}</strong></div>',
                        unsafe_allow_html=True,
                    )

            with col_fee:
                existing_fee = existing.get("fee")
                fee_text = st.text_input(
                    "Fee ($)",
                    value=format_currency(existing_fee) if isinstance(existing_fee, (int, float)) and existing_fee is not None else "",
                    placeholder=format_currency(task["amount"]),
                    key=f"fee_{task_num}",
                    label_visibility="collapsed",
                )

        
            if task_selected:
                cleaned = re.sub(r"[^\d.]", "", str(fee_text or "")).strip()
                final_fee = int(float(cleaned)) if cleaned else task["amount"]
                selected_tasks[task_num] = {
                    "name": task["name"],
                    "fee": final_fee,
                }
            else:
                selected_tasks.pop(task_num, None)

            if task_selected and task_num == "310":
                st.markdown("**Construction Phase Services:**")
                st.caption("Select services, enter hours/count, rate, and cost")

                header = st.container(horizontal=True, key="cps-header")
                with header:
                    st.markdown('<div class="cps-col-check"></div>', unsafe_allow_html=True)
                    st.markdown('<div class="cps-col-service"><b>Service</b></div>', unsafe_allow_html=True)
                    st.markdown('<div class="cps-col-fixed"><b>Hrs/Count</b></div>', unsafe_allow_html=True)
                    st.markdown('<div class="cps-col-fixed"><b>$/hr</b></div>', unsafe_allow_html=True)
                    st.markdown('<div class="cps-col-fixed"><b>Cost</b></div>', unsafe_allow_html=True)

                service_data = {}
                existing_services = selected_tasks.get("310", {}).get("services", {})

                def render_service_row(
                    svc_key: str,
                    svc_name: str,
                    default_hrs: int,
                    default_rate: int,
                    default_cost: int,
                    existing: Dict[str, Any],
                ) -> Dict[str, Any]:
                    prev_hours = existing.get("hours")
                    prev_rate = existing.get("rate")

                    with st.container(horizontal=True, key=f"cps-row-{_slug(svc_key)}"):
                        is_selected = st.checkbox(
                            "",
                            value=svc_key in ["shop_drawings", "rfi", "oac", "site_visits", "asbuilt", "fdep", "compliance", "wmd"],
                            key=f"svc310_{svc_key}",
                            label_visibility="collapsed",
                        )

                        st.markdown(svc_name)

                        if default_hrs > 0 or svc_key in ["inspection_tv", "record_drawings"]:
                            hrs_text = st.text_input(
                                "Hrs",
                                value=str(prev_hours) if isinstance(prev_hours, (int, float)) and prev_hours else "",
                                placeholder=str(default_hrs),
                                key=f"hrs310_{svc_key}",
                                disabled=not is_selected,
                                label_visibility="collapsed",
                            )
                            cleaned = re.sub(r"[^\d.]", "", str(hrs_text or "")).strip()
                            if cleaned:
                                hrs_value = int(float(cleaned))
                                hrs_has_value = True
                            else:
                                hrs_value = 0
                                hrs_has_value = False
                        else:
                            hrs_value = 0
                            hrs_has_value = False
                            st.text_input(
                                "Hrs",
                                value="",
                                placeholder="-",
                                key=f"hrs310_{svc_key}_na",
                                disabled=True,
                                label_visibility="collapsed",
                            )

                        if default_rate > 0 or svc_key in ["inspection_tv", "record_drawings"]:
                            fallback_rate = default_rate if default_rate else 165
                            rate_text = st.text_input(
                                "Rate",
                                value=format_currency(prev_rate) if isinstance(prev_rate, (int, float)) and prev_rate else format_currency(fallback_rate),
                                placeholder=format_currency(fallback_rate),
                                key=f"rate310_{svc_key}",
                                disabled=not is_selected,
                                label_visibility="collapsed",
                            )
                            cleaned = re.sub(r"[^\d.]", "", str(rate_text or "")).strip()
                            if cleaned:
                                rate_value = int(float(cleaned))
                            else:
                                rate_value = int(fallback_rate) if fallback_rate else 0
                        else:
                            rate_value = 0
                            st.text_input(
                                "Rate",
                                value="",
                                placeholder="-",
                                key=f"rate310_{svc_key}_na",
                                disabled=True,
                                label_visibility="collapsed",
                            )

                        if is_selected:
                            computed_cost = hrs_value * rate_value if hrs_has_value and rate_value else 0
                            st.text_input(
                                "Cost",
                                value=format_currency(computed_cost),
                                placeholder=format_currency(default_cost),
                                key=f"cost310_{svc_key}",
                                disabled=True,
                                label_visibility="collapsed",
                            )
                            cost_value = int(computed_cost) if computed_cost else 0
                        else:
                            cost_value = 0
                            st.text_input(
                                "Cost",
                                value=format_currency(0),
                                placeholder=format_currency(0),
                                key=f"cost310_{svc_key}_na",
                                disabled=True,
                                label_visibility="collapsed",
                            )

                    return {
                        "included": is_selected,
                        "name": svc_name,
                        "hours": hrs_value if is_selected else 0,
                        "rate": rate_value if is_selected else 0,
                        "cost": cost_value if is_selected else 0,
                    }

                for svc_key, svc_name, default_hrs, default_rate, default_cost in TASK_310_SERVICES:
                    prev_service = existing_services.get(svc_key, {})
                    service_data[svc_key] = render_service_row(
                        svc_key,
                        svc_name,
                        default_hrs,
                        default_rate,
                        default_cost,
                        prev_service,
                    )

                st.markdown("---")
                total_hrs_text = st.text_input(
                    "**Total Task 310 Hours**",
                    value=str(selected_tasks.get("310", {}).get("total_hours", 180)),
                    key="total_construction_hours",
                )
                cleaned = re.sub(r"[^\d.]", "", str(total_hrs_text or "")).strip()
                total_hrs = int(float(cleaned)) if cleaned else 0

                selected_tasks["310"]["services"] = service_data
                selected_tasks["310"]["services_total_cost"] = sum(
                    svc.get("cost", 0) for svc in service_data.values()
                )
                selected_tasks["310"]["total_hours"] = total_hrs
                selected_tasks["310"]["hours"] = {
                    "shop_drawing": service_data["shop_drawings"]["hours"],
                    "rfi": service_data["rfi"]["hours"],
                    "oac_meetings": service_data["oac"]["hours"],
                    "site_visits": service_data["site_visits"]["hours"],
                    "record_drawing": service_data["record_drawings"]["hours"],
                    "total": total_hrs,
                }


def render_tab4():
    st.subheader("Permitting Requirements")
    st.markdown("Select the permits/approvals required for this project (applies to Task 150 - Civil Permitting):")

    intake = st.session_state.proposal["intake"]
    permits = st.session_state.proposal["permits"]
    scope = st.session_state.proposal["scope"]
    selected_tasks = scope.get("selected_tasks", {})

    permit_flags = permits.setdefault("permit_flags", {})
    permit_config = PERMIT_MAPPING.get(intake.get("county", ""), {})
    default_permits = permit_config.get("default_permits", [])
    ahj_name = permit_config.get("ahj_name", "Authority Having Jurisdiction")
    wmd_name = permit_config.get("wmd_short", "Water Management District")

    col_permit1, col_permit2, col_permit3 = st.columns(3)

    with col_permit1:
        st.markdown("**Local / Utilities**")
    with col_permit2:
        st.markdown("**State / Regional**")
    with col_permit3:
        st.markdown("**FDOT**")

    with col_permit1:
        permit_ahj = st.checkbox(f"{ahj_name}", value=permit_flags.get("permit_ahj", "ahj" in default_permits), key="permit_ahj")
        permit_sewer = st.checkbox("Sewer Provider", value=permit_flags.get("permit_sewer", "sewer" in default_permits), key="permit_sewer")
        permit_water = st.checkbox("Water Provider", value=permit_flags.get("permit_water", "water" in default_permits), key="permit_water")
        permit_site_plan_review = st.checkbox("Site Plan / Development Review", value=permit_flags.get("permit_site_plan_review", False), key="permit_site_plan_review")
        permit_site_eng_grading = st.checkbox("Site Engineering, Grading & Drainage", value=permit_flags.get("permit_site_eng_grading", False), key="permit_site_eng_grading")
        permit_row_utilization = st.checkbox("Right-of-Way Utilization Permit", value=permit_flags.get("permit_row_utilization", False), key="permit_row_utilization")
        permit_zoning_clearance = st.checkbox("Zoning Clearance", value=permit_flags.get("permit_zoning_clearance", False), key="permit_zoning_clearance")

    with col_permit2:
        permit_wmd_erp = st.checkbox(f"{wmd_name} ERP", value=permit_flags.get("permit_wmd_erp", "wmd_erp" in default_permits), key="permit_wmd_erp")
        permit_fdep = st.checkbox("FDEP Potable Water/Wastewater", value=permit_flags.get("permit_fdep", False), key="permit_fdep")
        permit_fdot_drainage = st.checkbox("FDOT Drainage Connection", value=permit_flags.get("permit_fdot_drainage", False), key="permit_fdot_drainage")
        permit_floodplain = st.checkbox("Floodplain / Construction in Flood Zone", value=permit_flags.get("permit_floodplain", False), key="permit_floodplain")
        permit_utilities_conn = st.checkbox("Utilities Connection Request", value=permit_flags.get("permit_utilities_conn", False), key="permit_utilities_conn")
        permit_reclaimed_water = st.checkbox("Reclaimed Water Connection + Inspection", value=permit_flags.get("permit_reclaimed_water", False), key="permit_reclaimed_water")

    with col_permit3:
        permit_fdot_driveway = st.checkbox("FDOT Driveway Connection", value=permit_flags.get("permit_fdot_driveway", False), key="permit_fdot_driveway")
        permit_fdot_utility = st.checkbox("FDOT Utility Connection", value=permit_flags.get("permit_fdot_utility", False), key="permit_fdot_utility")
        permit_fdot_general_use = st.checkbox("FDOT General Use Permit", value=permit_flags.get("permit_fdot_general_use", False), key="permit_fdot_general_use")
        permit_fdot_construction = st.checkbox("FDOT Construction Agreement", value=permit_flags.get("permit_fdot_construction", False), key="permit_fdot_construction")
        permit_fema = st.checkbox("FEMA", value=permit_flags.get("permit_fema", False), key="permit_fema")

    permit_flags.update({
        "permit_ahj": permit_ahj,
        "permit_sewer": permit_sewer,
        "permit_water": permit_water,
        "permit_wmd_erp": permit_wmd_erp,
        "permit_fdep": permit_fdep,
        "permit_fdot_drainage": permit_fdot_drainage,
        "permit_fdot_driveway": permit_fdot_driveway,
        "permit_fdot_utility": permit_fdot_utility,
        "permit_fdot_general_use": permit_fdot_general_use,
        "permit_fdot_construction": permit_fdot_construction,
        "permit_site_plan_review": permit_site_plan_review,
        "permit_site_eng_grading": permit_site_eng_grading,
        "permit_row_utilization": permit_row_utilization,
        "permit_zoning_clearance": permit_zoning_clearance,
        "permit_floodplain": permit_floodplain,
        "permit_utilities_conn": permit_utilities_conn,
        "permit_reclaimed_water": permit_reclaimed_water,
        "permit_fema": permit_fema,
    })

    st.markdown("---")
    st.subheader("Additional Services")
    st.markdown("**Check the services you ARE providing** in this proposal and enter the fee. Unchecked services will be listed as 'Additional Services' (not included).")
    st.caption("Tip: Check services you ARE including and enter fees. Unchecked items appear in 'Additional Services (Not Included)' section.")

    included_additional_services = []
    excluded_additional_services = []
    included_additional_services_with_fees = {}

    st.markdown('<div class="additional-services">', unsafe_allow_html=True)
    for i in range(0, len(ADDITIONAL_SERVICES_LIST), 2):
        cols = st.columns([0.08, 1, 0.08, 1])
        pair = ADDITIONAL_SERVICES_LIST[i:i + 2]

        # Left item
        key, service_name, default_checked, default_fee = pair[0]
        with cols[0]:
            is_checked_left = st.checkbox(
                "",
                value=bool(permits.get("included_additional_services_with_fees", {}).get(service_name)) if service_name in permits.get("included_additional_services_with_fees", {}) else default_checked,
                key=f"addl_svc_{key}",
                label_visibility="collapsed",
            )
        with cols[1]:
            st.markdown(f'<div class="svc-label">{service_name}</div>', unsafe_allow_html=True)
            prev_fee = permits.get("included_additional_services_with_fees", {}).get(service_name)
            fee_text = st.text_input(
                "Fee ($)",
                value=format_currency(prev_fee) if isinstance(prev_fee, (int, float)) and prev_fee is not None else "",
                placeholder=format_currency(default_fee),
                key=f"addl_fee_{key}",
                label_visibility="collapsed",
            )

        if is_checked_left:
            cleaned = re.sub(r"[^\d.]", "", str(fee_text or "")).strip()
            final_fee = int(float(cleaned)) if cleaned else default_fee
            included_additional_services.append(service_name)
            included_additional_services_with_fees[service_name] = final_fee
        else:
            excluded_additional_services.append(service_name)

        # Right item (if present)
        if len(pair) > 1:
            key, service_name, default_checked, default_fee = pair[1]
            with cols[2]:
                is_checked_right = st.checkbox(
                    "",
                    value=bool(permits.get("included_additional_services_with_fees", {}).get(service_name)) if service_name in permits.get("included_additional_services_with_fees", {}) else default_checked,
                    key=f"addl_svc_{key}",
                    label_visibility="collapsed",
                )
            with cols[3]:
                st.markdown(f'<div class="svc-label">{service_name}</div>', unsafe_allow_html=True)
                prev_fee = permits.get("included_additional_services_with_fees", {}).get(service_name)
                fee_text = st.text_input(
                    "Fee ($)",
                    value=format_currency(prev_fee) if isinstance(prev_fee, (int, float)) and prev_fee is not None else "",
                    placeholder=format_currency(default_fee),
                    key=f"addl_fee_{key}",
                    label_visibility="collapsed",
                )

            if is_checked_right:
                cleaned = re.sub(r"[^\d.]", "", str(fee_text or "")).strip()
                final_fee = int(float(cleaned)) if cleaned else default_fee
                included_additional_services.append(service_name)
                included_additional_services_with_fees[service_name] = final_fee
            else:
                excluded_additional_services.append(service_name)
    st.markdown("</div>", unsafe_allow_html=True)

    permits["included_additional_services"] = included_additional_services
    permits["included_additional_services_with_fees"] = included_additional_services_with_fees
    permits["excluded_additional_services"] = excluded_additional_services

    st.markdown("---")
    addl_total = sum(included_additional_services_with_fees.values()) if included_additional_services_with_fees else 0
    st.text_input(
        "Additional Services Total",
        value=format_currency(addl_total) if addl_total is not None else "",
        placeholder=format_currency(0),
        disabled=True,
    )
    st.markdown("---")
    st.subheader("Selected Tasks Summary")
    if selected_tasks or included_additional_services_with_fees:
        total_fee = 0

        for task_num in sorted(selected_tasks.keys()):
            task = selected_tasks[task_num]
            st.write(f"- Task {task_num}: {task['name']} - **{format_currency(task['fee'])}**")
            total_fee += task["fee"]
            if task_num == "310":
                svc_total = task.get("services_total_cost", 0)
                if svc_total:
                    st.write(f"  - Construction Phase Services (detail): **{format_currency(svc_total)}**")
                    total_fee += svc_total

        if included_additional_services_with_fees:
            st.markdown("**Additional Services Included:**")
            for service_name, service_fee in included_additional_services_with_fees.items():
                st.write(f"- {service_name} - **{format_currency(service_fee)}**")
                total_fee += service_fee

        st.markdown("---")
        st.markdown(f"### **Total Fee: {format_currency(total_fee)}**")
    else:
        st.info("Select at least one task in the Scope of Services tab")


def render_tab5():
    st.subheader("Invoice & Billing Information")

    invoice = st.session_state.proposal["invoice"]
    scope = st.session_state.proposal["scope"]
    permits = st.session_state.proposal["permits"]
    intake = st.session_state.proposal["intake"]

    col_inv1, col_inv2 = st.columns(2)

    with col_inv1:
        invoice["invoice_email"] = st.text_input(
            "Invoice Email Address",
            value=invoice.get("invoice_email", ""),
            placeholder="e.g., accounting@company.com",
        )
        invoice["kh_signer_name"] = st.text_input(
            "Kimley-Horn Signer Name",
            value=invoice.get("kh_signer_name", ""),
            placeholder="e.g., John Smith, PE",
        )
        invoice["use_retainer"] = st.checkbox(
            "Require Retainer",
            value=bool(invoice.get("use_retainer", False)),
        )

    with col_inv2:
        invoice["invoice_cc_email"] = st.text_input(
            "CC Email (optional)",
            value=invoice.get("invoice_cc_email", ""),
            placeholder="e.g., manager@company.com",
        )
        invoice["kh_signer_title"] = st.text_input(
            "Kimley-Horn Signer Title",
            value=invoice.get("kh_signer_title", ""),
            placeholder="e.g., Senior Project Manager",
        )
        retainer_text = st.text_input(
            "Retainer Amount ($)",
            value=format_currency(invoice.get("retainer_amount")) if invoice.get("retainer_amount") is not None else "",
            placeholder=format_currency(0),
        )
        cleaned = re.sub(r"[^\d.]", "", str(retainer_text or "")).strip()
        invoice["retainer_amount"] = int(float(cleaned)) if cleaned else 0

    st.markdown("---")
    st.subheader("Preview Output (test)")

    selected_tasks = scope.get("selected_tasks", {})
    if selected_tasks:
        st.markdown("## Scope of Services (selected)")
        for task_num in sorted(selected_tasks.keys()):
            task = selected_tasks[task_num]
            st.markdown(f"### Task {task_num}: {task['name']} - {format_currency(task['fee'])}")
            descs = TASK_DESCRIPTIONS.get(task_num, [])
            if task_num == "310":
                hours = task.get("hours", {})
                fmt = {
                    "shop_drawing_hours": hours.get("shop_drawing", 0),
                    "rfi_hours": hours.get("rfi", 0),
                    "oac_meetings": hours.get("oac_meetings", 0),
                    "site_visits": hours.get("site_visits", 0),
                    "record_drawing_hours": hours.get("record_drawing", 0),
                    "total_hours": task.get("total_hours", 0),
                }
                descs = [d.format(**fmt) for d in descs]
            for line in descs:
                st.write(f"- {line}")
    else:
        st.info("Select tasks in Tab 3 to see the generated scope output.")

    permit_config = PERMIT_MAPPING.get(intake.get("county", ""), {})
    ahj_name = permit_config.get("ahj_name", "Authority Having Jurisdiction")
    wmd_name = permit_config.get("wmd_short", "Water Management District")

    permit_flags = permits.get("permit_flags", {})
    permit_list = []
    if permit_flags.get("permit_ahj"):
        permit_list.append(ahj_name)
    if permit_flags.get("permit_sewer"):
        permit_list.append("Sewer Provider")
    if permit_flags.get("permit_water"):
        permit_list.append("Water Provider")
    if permit_flags.get("permit_site_plan_review"):
        permit_list.append("Site Plan / Development Review")
    if permit_flags.get("permit_site_eng_grading"):
        permit_list.append("Site Engineering, Grading & Drainage")
    if permit_flags.get("permit_row_utilization"):
        permit_list.append("Right-of-Way Utilization Permit")
    if permit_flags.get("permit_zoning_clearance"):
        permit_list.append("Zoning Clearance")
    if permit_flags.get("permit_wmd_erp"):
        permit_list.append(f"{wmd_name} ERP")
    if permit_flags.get("permit_fdep"):
        permit_list.append("FDEP Potable Water/Wastewater")
    if permit_flags.get("permit_fdot_drainage"):
        permit_list.append("FDOT Drainage Connection")
    if permit_flags.get("permit_floodplain"):
        permit_list.append("Floodplain / Construction in Flood Zone")
    if permit_flags.get("permit_utilities_conn"):
        permit_list.append("Utilities Connection Request")
    if permit_flags.get("permit_reclaimed_water"):
        permit_list.append("Reclaimed Water Connection + Inspection")
    if permit_flags.get("permit_fdot_driveway"):
        permit_list.append("FDOT Driveway Connection")
    if permit_flags.get("permit_fdot_utility"):
        permit_list.append("FDOT Utility Connection")
    if permit_flags.get("permit_fdot_general_use"):
        permit_list.append("FDOT General Use Permit")
    if permit_flags.get("permit_fdot_construction"):
        permit_list.append("FDOT Construction Agreement")
    if permit_flags.get("permit_fema"):
        permit_list.append("FEMA")

    if permit_list:
        st.markdown("## Permitting Requirements (selected)")
        for p in permit_list:
            st.write(f"- {p}")

    included = permits.get("included_additional_services_with_fees", {})
    excluded = permits.get("excluded_additional_services", [])

    if included:
        st.markdown("## Additional Services Included")
        for svc, fee in included.items():
            st.write(f"- {svc} - {format_currency(fee)}")

    if excluded:
        st.markdown("## Additional Services (Not Included)")
        for svc in excluded:
            st.write(f"- {svc}")

    st.markdown("## Invoice & Billing")
    st.write(f"Invoice Email: {invoice.get('invoice_email', '')}")
    if invoice.get("invoice_cc_email"):
        st.write(f"CC Email: {invoice.get('invoice_cc_email')}")
    st.write(f"Signer: {invoice.get('kh_signer_name', '')} - {invoice.get('kh_signer_title', '')}")
    if invoice.get("use_retainer"):
        st.write(f"Retainer: {format_currency(invoice.get('retainer_amount', 0))}")
    else:
        st.write("Retainer: Not required")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    init_proposal_state()

    total_cost = compute_total_proposal_cost()
    _, total_col = st.columns([5, 2])
    with total_col:
        st.markdown(
            f"<div class='total-proposal-badge'>Total Proposal Cost: {format_currency(total_cost)}</div>",
            unsafe_allow_html=True,
        )

    tabs = st.tabs(["Project Info", "Project Understanding", "Scope of Services", "Permitting & Summary", "Invoice & Billing"])

    with tabs[0]:
        render_tab1()
    with tabs[1]:
        render_tab2()
    with tabs[2]:
        render_tab3()
    with tabs[3]:
        render_tab4()
    with tabs[4]:
        render_tab5()

if __name__ == "__main__":
    main()
