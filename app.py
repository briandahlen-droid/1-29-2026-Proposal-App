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
input[type="text"], input[type="number"], textarea, input::placeholder, textarea::placeholder {
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
}

/* Inputs: text, number, textarea */
input[type="text"], input[type="number"], textarea {
    border: 0 !important;
    border-radius: var(--field-radius) !important;
    background: var(--panel) !important;
    color: var(--ink) !important;
    box-shadow: none !important;
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

/* Multiselect / dropdown menu background */
div[data-baseweb="popover"] {
    color: var(--ink) !important;
}

/* Checkboxes: increase contrast */
div[data-baseweb="checkbox"] svg {
    color: var(--navy) !important;
    fill: none !important;
}
div[data-baseweb="checkbox"] > div,
div[data-baseweb="checkbox"] div[role="checkbox"] {
    border-color: var(--navy) !important;
    background: #ffffff !important;
    border-width: 2px !important;
    border-radius: 4px !important;
    box-shadow: inset 0 0 0 2px var(--navy) !important;
}
div[data-baseweb="checkbox"] div[role="checkbox"][aria-checked="true"] {
    background: #ffffff !important;
}
div[data-baseweb="checkbox"] div[role="checkbox"] > div {
    background: #ffffff !important;
}
div[data-baseweb="checkbox"] div[role="checkbox"] svg {
    fill: none !important;
}
div[data-baseweb="checkbox"] div[role="checkbox"] svg rect {
    fill: #ffffff !important;
    stroke: var(--navy) !important;
    stroke-width: 2px !important;
}
div[data-baseweb="checkbox"] div[role="checkbox"] svg path {
    stroke: var(--navy) !important;
    fill: none !important;
}
div[data-baseweb="checkbox"] div[role="checkbox"]::before,
div[data-baseweb="checkbox"] div[role="checkbox"]::after {
    background: #ffffff !important;
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
                f"https://www.pcpao.gov/property-details?"
                f"s={strap}&input={normalized_parcel}&search_option=parcel_number"
            )
            html = session.get(detail_url, timeout=30).text
            soup = BeautifulSoup(html, "html.parser")
            txt = soup.get_text(" ", strip=True)

            m = re.search(r"Land Area:\s*≅\s*([\d,]+)\s*sf\s*\|\s*≅\s*([\d.]+)\s*acres", txt)
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
                "entity_address": "",
            },
            "project": {
                "project_name": "",
                "project_location": "",
                "proposal_date": "",
                # Tab 2 additions:
                "project_description_short": "",
                "assumptions_checked": {},   # id -> bool
                "assumptions_other": "",
            },
            "scope": {
                # Tab 3 selections (ids)
                "task_ids": {},              # id -> bool
                "scope_other": "",
            },
            "permits": {
                # Tab 4 permit selections
                "permit_ids": {},            # id -> bool
                "permit_other": "",
            },
            "tab4_tasks": {
                # Tab 4 tasks 108-110 selections
                "task_ids": {},              # id -> bool
            }
        }

# -----------------------------------------------------------------------------
# Tab 3/4 libraries (placeholders for now - wire your final text blocks later)
# -----------------------------------------------------------------------------
TAB3_TASKS = [
    # Keep only tasks that belong on Tab 3 (NOT 107-110, which live on Tab 4)
    {"id": "task_due_diligence_site_review", "section": "B — Due Diligence", "label": "Due-Diligence and Site Review", "output": "TODO: full block"},
    {"id": "task_city_site_plan_approval", "section": "C — City approvals", "label": "City of St. Petersburg Site Plan Approval Process", "output": "TODO: full block"},
    {"id": "task_landscape_drc_concept", "section": "D — Landscape concepts", "label": "Landscape DRC Concept Plan", "output": "TODO: full block"},
    {"id": "task_civil_construction_documents", "section": "F — Civil design", "label": "Civil Construction Documents", "output": "TODO: full block"},
    {"id": "task_fdot_driveway_access", "section": "Permitting/FDOT", "label": "FDOT Driveway Access Plans", "output": "TODO: full block"},
    {"id": "task_stormwater_design", "section": "G — Stormwater", "label": "Stormwater Design", "output": "TODO: full block"},
    {"id": "task_code_min_landscape", "section": "H — Landscape", "label": "Code Minimum Landscape Architecture", "output": "TODO: full block"},
    # Task 106 (include full block in your final build)
    {"id": "task_106_landscape_architecture", "section": "H — Landscape", "label": "Landscape Architecture (Task 106) — Streetscape + Elevated Amenity Deck", "output": "TODO: paste full Task 106 block"},
    # Optional extras
    {"id": "task_platting_assistance", "section": "N — Platting", "label": "Platting Assistance", "output": "TODO: full block"},
    {"id": "task_faa_permitting", "section": "O — FAA", "label": "FAA Permitting", "output": "TODO: full block"},
]

PERMITS = [
    {"id": "permit_cosp_civil", "label": "City of St. Petersburg Commercial Plan Site Civil Permit"},
    {"id": "permit_cosp_row", "label": "City of St. Petersburg Right-of-Way Permit – Site Work (no offsite extensions)"},
    {"id": "permit_swfwmd_erp_exemption", "label": "SWFWMD ERP Exemption"},
    {"id": "permit_fdep_water_sewer_exemption", "label": "FDEP Water and Sewer Exemption"},
    {"id": "permit_fdep_npdes", "label": "FDEP NPDES Permit"},
    # Add any other permit checkbox bullets here
]

TAB4_TASKS_108_110 = [
    {"id": "task_108_franchised_utility_coordination", "label": "Task 108 — Franchised Utility Coordination", "output": "TODO: full block"},
    {"id": "task_109_meetings", "label": "Task 109 — Meetings", "output": "TODO: full block"},
    {"id": "task_110_construction_phase_services", "label": "Task 110 — Construction Phase Services", "output": "TODO: full block"},
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
        button_label = f"Open {city} Zoning and Land Use Map" if city else "Open Zoning and Land Use Map"
        if map_url:
            st.link_button(button_label, map_url, use_container_width=True)
        else:
            st.button(button_label, use_container_width=True, disabled=True)
            st.info("No city map link found for this municipality.")

        st.markdown("**Lookup Summary (Auto-fills tokens)**")
        st.text_input("County", value=intake.get("county", ""), disabled=True)
        st.text_input("City", value=intake.get("city", ""), disabled=True)
        st.text_input("Address", value=intake.get("address", ""), disabled=True)
        st.text_input("Owner", value=intake.get("owner", ""), disabled=True)
        st.text_input("Land Use", value=intake.get("land_use", ""), disabled=True)
        intake["zoning"] = st.text_input("Zoning (full)", value=intake.get("zoning", ""))
        intake["future_land_use"] = st.text_input("Future Land Use (full)", value=intake.get("future_land_use", ""))
        st.text_input("Site Area (acres)", value=intake.get("site_area_acres", ""), disabled=True)
        st.text_input("Site Area (sf)", value=intake.get("site_area_sqft", ""), disabled=True)

    with right:
        project = st.session_state.proposal["project"]
        client = st.session_state.proposal["client"]

        current_addr = intake.get("address", "") or ""
        prev_addr = st.session_state.get("last_intake_address", "")
        proj_loc_key = "project_location_input"
        if proj_loc_key not in st.session_state:
            st.session_state[proj_loc_key] = project.get("project_location", "") or current_addr
        if current_addr and (not st.session_state[proj_loc_key] or st.session_state[proj_loc_key] == prev_addr):
            st.session_state[proj_loc_key] = current_addr
        st.session_state["last_intake_address"] = current_addr

        st.markdown("**Project (Tokens)**")
        project["project_name"] = st.text_input("Project Name", value=project.get("project_name", ""))
        project["project_location"] = st.text_input("Project Location / Address", key=proj_loc_key)
        project["proposal_date"] = st.text_input("Proposal Date (optional)", value=project.get("proposal_date", ""))

        st.markdown("**Client / Entity (Tokens)**")
        client["client_name"] = st.text_input("Client Name", value=client.get("client_name", ""))
        client["client_contact_name"] = st.text_input("Client Contact Name", value=client.get("client_contact_name", ""))
        client["entity_name"] = st.text_input("Client Legal Entity (Sunbiz)", value=client.get("entity_name", ""))
        client["entity_address"] = st.text_area("Entity Address", value=client.get("entity_address", ""), height=90)

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
    assumptions = [
        ("assump_one_phase", "The project will be designed, permitted, and constructed in one phase."),
        ("assump_waivers_addsvc", "If waivers are required, that will be considered an additional service."),
        ("assump_water_sewer_cosp", "Water and Sewer will be served by City of St. Petersburg. It is assumed existing infrastructure is adequate. Lift station not required; can be added if required."),
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
    zoning = intake.get("zoning", "")
    flu = intake.get("future_land_use", "")

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
        st.text_area(
            "Project Understanding (auto-generated)",
            value=paragraph,
            height=110,
            disabled=True,
        )
    else:
        st.text_area(
            "Project Understanding (auto-generated)",
            value="Enter project details in Tab 1 and the short description above to generate this paragraph.",
            height=110,
            disabled=True,
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

    scope = st.session_state.proposal["scope"]
    selected = scope.setdefault("task_ids", {})

    cols = st.columns(2)
    for idx, item in enumerate(TAB3_TASKS):
        key = f"tab3_{item['id']}"
        section_label = re.sub(r"^[A-Z]\s*[-—]\s*", "", item["section"]).strip()
        with cols[idx % 2]:
            selected[item["id"]] = st.checkbox(
                f"{section_label}",
                value=bool(selected.get(item["id"], False)),
                key=key,
            )

    scope["scope_other"] = st.text_area(
        "Additional scope items (optional)",
        value=scope.get("scope_other", ""),
        height=120,
        placeholder="Add any scope items not covered by the checkboxes.",
    )

def render_tab4():
    st.subheader("Permitting & Construction Administration")

    # Task 107: Permitting is not a checkbox; permit list is checkbox set
    st.markdown("### Task 107 — Permitting")
    permits = st.session_state.proposal["permits"]
    psel = permits.setdefault("permit_ids", {})

    for p in PERMITS:
        psel[p["id"]] = st.checkbox(
            p["label"],
            value=bool(psel.get(p["id"], False)),
            key=f"tab4_{p['id']}",
        )

    permits["permit_other"] = st.text_area(
        "Additional permits (optional)",
        value=permits.get("permit_other", ""),
        height=100,
        placeholder="List any additional permits/approvals required (one per line if possible).",
    )

    st.divider()

    st.markdown("### Tasks 108–110")
    tsel = st.session_state.proposal["tab4_tasks"].setdefault("task_ids", {})
    for t in TAB4_TASKS_108_110:
        tsel[t["id"]] = st.checkbox(t["label"], value=bool(tsel.get(t["id"], False)), key=f"tab4_{t['id']}")

def render_preview():
    st.subheader("Preview Output (test)")

    proj = st.session_state.proposal["project"]
    intake = st.session_state.proposal["intake"]
    scope = st.session_state.proposal["scope"]
    permits = st.session_state.proposal["permits"]
    tab4 = st.session_state.proposal["tab4_tasks"]

    st.markdown("## PROJECT UNDERSTANDING")
    st.write(proj.get("project_description_short", "").strip())

    st.markdown("## PROJECT ASSUMPTIONS")
    checked = proj.get("assumptions_checked", {})
    for aid, val in checked.items():
        if val:
            st.write(f"- {aid}")
    if proj.get("assumptions_other", "").strip():
        st.write(proj["assumptions_other"].strip())

    st.markdown("## SCOPE OF SERVICES (selected)")
    for item in TAB3_TASKS:
        if scope.get("task_ids", {}).get(item["id"], False):
            st.markdown(f"### {item['label']}")
            st.write(item["output"])

    if scope.get("scope_other", "").strip():
        st.markdown("### Additional scope items")
        st.write(scope["scope_other"].strip())

    st.markdown("## TASK 107 — PERMITTING (selected)")
    for p in PERMITS:
        if permits.get("permit_ids", {}).get(p["id"], False):
            st.write(f"- {p['label']}")
    extra = permits.get("permit_other", "").strip()
    if extra:
        for line in [ln.strip() for ln in extra.splitlines() if ln.strip()]:
            st.write(f"- {line}")

    st.markdown("## TASKS 108–110 (selected)")
    for t in TAB4_TASKS_108_110:
        if tab4.get("task_ids", {}).get(t["id"], False):
            st.markdown(f"### {t['label']}")
            st.write(t["output"])

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    init_proposal_state()

    tabs = st.tabs(["Project Info", "Project Understanding", "Scope of Services", "Permitting & CA", "Preview"])

    with tabs[0]:
        render_tab1()
    with tabs[1]:
        render_tab2()
    with tabs[2]:
        render_tab3()
    with tabs[3]:
        render_tab4()
    with tabs[4]:
        render_preview()

if __name__ == "__main__":
    main()
