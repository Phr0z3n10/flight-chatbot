import os
import base64
import anthropic
from dotenv import load_dotenv
import streamlit as st
from streamlit_js_eval import get_geolocation
from geopy.geocoders import Nominatim
import requests
from datetime import datetime, timedelta, timezone

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

with open('airport_bg.jpg', 'rb') as f:
    bg_image = base64.b64encode(f.read()).decode()

system_prompt = """You are ARIA the Airport Realtime Information assistant. You are a veteran flight attendant who has flown into every airport on the planet. 
You've seen it all and with that have developed a warm, professional and calm personality. You should open each session with a genuine greeting that fits the moment. 
No generic greetings. You are multilingual and should respond in any language that is presented to you by the user if you know that language. 
You can answer questions that are present in the data you have access to via connection to AeroDataBox API. 
If the user asks questions not related to that data, you should politely redirect them to the options you have access to. 
Do not make up or try to infer information not available to you from the data connection. If the flight data is unavailable or the query returns no results, verify the information the user gave you with them.
If the information given is verified correct with the user, clearly explain to the user that you cannot find the information that they are looking for and advise them to contact the airline directly.
You will be provided with the user's nearest airport via geolocation at the start of the session and should use that as the default location for them unless they specify otherwise.You have access to live flight data for ANY airport worldwide. 
Each question is independent do not assume your data is limited to a previous airport just because you answered a question about it. Always fetch fresh data for whatever airport the user asks about.
If the user explicitly names an airport or city, always use that over the geolocation default. The user's stated preference always overrides the detected location.
When presenting flight information, do not just list data. Present it the way a warm, experienced flight attendant would — acknowledge the passenger's situation, lead with the most important information first, and close with a genuine offer to help further. 
Never present flight data as a cold table dump.
You should anticipate the related follow up questions a user may ask and present them in the form of a question after the initial query. 
For example, if a user asks "What terminal does delta flight 1234 from Fresno arrive at?" follow up by asking "Would you like me to check if there is baggage claim information?"
You should also verify if the user has all their questions answered before terminating the conversation. Some users will be frustrated and stressed during travel. 
You will handle rude or aggressive users with calmness, kindness and professionalism, because as a veteran flight attendant you understand and empathize.
When presenting airport arrival or departure lists, be concise. List only the most relevant flights in a clean simple format. Do not over-explain or second-guess the data.
"""

HEADERS = {
    "X-RapidAPI-Key": os.getenv("AERODATABOX_API_KEY"),
    "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
}

def safe_api_call(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200 or not response.text.strip():
            return None
        return response.json()
    except Exception:
        return None

def get_flight_data(flight_number):
    flight_number = flight_number.replace(" ", "").upper()
    return safe_api_call(f"https://aerodatabox.p.rapidapi.com/flights/number/{flight_number}")

def get_airport_flights(airport_code):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    later = now + timedelta(hours=12)
    from_time = now.strftime("%Y-%m-%dT%H:%M")
    to_time = later.strftime("%Y-%m-%dT%H:%M")
    return safe_api_call(
        f"https://aerodatabox.p.rapidapi.com/flights/airports/iata/{airport_code}/{from_time}/{to_time}"
        f"?withCancelled=false&withCodeshared=false&withCargo=false&withPrivate=false"
    )

def get_airport():
    try:
        location = get_geolocation()
        if location:
            geolocator = Nominatim(user_agent="aria_app")
            coords = f"{location['coords']['latitude']}, {location['coords']['longitude']}"
            airport = geolocator.reverse(coords, language='en')
            return airport.raw['address'].get('city', 'Unknown')
    except Exception:
        pass
    return None

def get_flight_number(text):
    if not text:
        return None
    try:
        result = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=20,
            messages=[{
                "role": "user",
                "content": f"Extract the IATA airline flight number from this text. Return only the flight number in format like WN4671, AA100, DL404. If no flight number can be determined return NONE: '{text}'"
            }]
        )
        response = result.content[0].text.strip()
        return None if response == "NONE" else response
    except Exception:
        return None

def get_airport_code(text):
    if not text:
        return None
    try:
        result = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=20,
            messages=[{
                "role": "user",
                "content": f"Extract the IATA airport code from this text. Return only the 3-letter IATA code like MCO, ORD, SAT. If no airport can be determined return NONE: '{text}'"
            }]
        )
        response = result.content[0].text.strip()
        return None if response == "NONE" else response
    except Exception:
        return None

# ── UI ────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="ARIA", page_icon="✈️", layout="wide")

st.markdown("""
    <div style='background: linear-gradient(135deg, #1B4F8A, #2E5FA3);
    padding: 30px; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='color: white; margin:0;'>A.R.I.A. 🛩️</h1>
        <p style='color: #CADCFC; margin:0;'>Airport Realtime Information Assistant</p>
    </div>
""", unsafe_allow_html=True)

st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/jpeg;base64,{bg_image}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    [data-testid="stAppViewContainer"]::before {{
        content: "";
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.70);
        z-index: 0;
    }}
    .stChatMessage {{ overflow-y: auto; }}
    section.main {{ overflow-y: auto; }}
    </style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

if "airport" not in st.session_state:
    st.session_state.airport = get_airport()

if st.session_state.airport and len(st.session_state.messages) == 0:
    st.session_state.messages.append({
        "role": "user",
        "content": f"The user is located near {st.session_state.airport}. Use this as their default airport context."
    })

# ── Chat history ──────────────────────────────────────────────────────────────

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ── Input ─────────────────────────────────────────────────────────────────────

airport_display = st.session_state.airport or "your airport"
user_question = st.chat_input(f"Are you looking for information about {airport_display}?")

if user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    today = datetime.now().strftime("%A, %B %d, %Y")
    dynamic_system = system_prompt + f"\n\nToday's date is {today}."

    flight_number = get_flight_number(user_question)

    if flight_number:
        raw_data = get_flight_data(flight_number)
        if raw_data:
            dynamic_system += f"\n\nFLIGHT DATA FROM AERODATABOX: {raw_data}"
    else:
        airport_code = get_airport_code(user_question)
        if airport_code:
            airport_data = get_airport_flights(airport_code)
            if airport_data:
                arrivals = airport_data.get("arrivals", [])[:3]
                departures = airport_data.get("departures", [])
                departures = sorted(
                    departures,
                    key=lambda x: x.get("movement", {}).get("scheduledTime", {}).get("utc", ""),
                    reverse=True
                )[:3]
                combined = {"arrivals": arrivals, "departures": departures}
                dynamic_system += f"\n\nAIRPORT FLIGHT DATA FROM AERODATABOX: {combined}"
    try:
        with st.spinner("ARIA is checking flight data..."):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=dynamic_system,
                messages=st.session_state.messages
            )
        reply = response.content[0].text
    except Exception:
        reply = "I'm sorry, I'm having trouble reaching the flight service right now. Please try again in a moment."

    with st.chat_message("assistant"):
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})