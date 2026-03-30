import os
import anthropic
from dotenv import load_dotenv
import streamlit as st 

# pull in API key from .env into environment
load_dotenv()

# initialize Anthropic client using env key… keeps things clean + secure
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

system_prompt =   """ You are a flight information desk at San Antonio International Airport (SAT). You know about flights status in both terminals. See flight data below.
 You can help people locate the gate, understand if the flight is on time, late(delayed) or cancelled. You know the baggage claim locations for each flight.
 You can only answer questions related to the status of flights. If someone asks anything not related to flight arrivals or departures, politely let them know you can only assist with flight information and direct them to the information desk near the TSA area.
 The directory will be near the human ran  information desk.  You should be friendly to all users even if they are not nice. Many people will be dealing with the stress of travel and may not always respond kindly, that's ok. 
 Your job is to help them get information in a calm, polite and helpful way. Do not show your reasoning or internal thinking. Only provide the final, correct answer.
 If unsure, respond clearly without speculation. When answering, be concise and direct. Do not include unnecessary explanations.
 You must acknowledge if asked what languages you speak in the language asked. You will always  give flight information in the language the flight information is requested if you understand that language. 
 If asked where TSA  is you may say to the left just behind Ticketing area

FLIGHT DATA:
DEPARTURES
- AA 1423 | American | Dallas (DFW) | Departs 7:15 AM | Gate A3 | On Time
- WN 556 | Southwest | Houston (HOU) | Departs 8:45 AM | Gate B7 | On Time
- UA 2210 | United | Denver (DEN) | Departs 10:30 AM | Gate A9 | Delayed 25 min
- DL 884 | Delta | Atlanta (ATL) | Departs 12:15 PM | Gate B2 | On Time
- WN 1205 | Southwest | Las Vegas (LAS) | Departs 3:40 PM | Gate B5 | On Time
ARRIVALS
- AA 1890 | American | Dallas (DFW) | Arrives 9:05 AM | Gate A4 | Baggage Claim Carousel 2 | On Time
- WN 342 | Southwest | Chicago (MDW) | Arrives 11:20 AM | Gate B6 | Baggage Claim Carousel 1 | On Time
- UA 1877 | United | Houeston (IAH) | Arrives 1:45 PM | Gate A8 | Baggage Claim Carousel 3 | Delayed 40 min
- DL 2203 | Delta | Los Angeles (LAX) | Arrives 4:10 PM | Gate B1 | Baggage Claim Carousel 2 | On Time
- WN 987 | Southwest | Phoenix (PHX) | Arrives 6:30 PM | Gate B4 | Baggage Claim Carousel 1 | On Time
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
    later = now + timedelta(hours=6)
    from_time = now.strftime("%Y-%m-%dT%H:%M")
    to_time = later.strftime("%Y-%m-%dT%H:%M")
    return safe_api_call(
        f"https://aerodatabox.p.rapidapi.com/flights/airports/iata/{airport_code}/{from_time}/{to_time}"
        f"?direction=Arrival&withLeg=false&withCancelled=false&withCodeshared=false&withCargo=false&withPrivate=false"
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

st.set_page_config(page_title="ARIA", page_icon="✈️", layout="wide")

st.markdown("""<h1 style='color: #1B4F8A;'>A.R.I.A. 🛩️</h1>
<p style='color: #2E5FA3;'>Airport Realtime Information Assistant</p>""", unsafe_allow_html=True)

st.markdown("""
    <style>
    .stChatMessage { overflow-y: auto; }
    section.main { overflow-y: auto; }
    </style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "airport" not in st.session_state:
    st.session_state.airport = get_airport()

if st.session_state.airport and len(st.session_state.messages) == 0:
    st.session_state.messages.append({
        "role": "user",
        "content": f"The user is located near {st.session_state.airport}. Use this as their default airport context."
    })

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

airport_display = st.session_state.airport or "your airport"
user_question = st.chat_input(f"Are you looking for information about {airport_display}?")

if user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)
	
    flight_number = get_flight_number(user_question)
    dynamic_system = system_prompt

    if flight_number:
        raw_data = get_flight_data(flight_number)
        if raw_data:
            dynamic_system = system_prompt + f"\n\nFLIGHT DATA FROM AERODATABOX: {raw_data}"
    else:
        airport_code = get_airport_code(user_question)
        if airport_code:
            airport_data = get_airport_flights(airport_code)
            if airport_data:
                 arrivals = airport_data.get("arrivals", airport_data)
                 if isinstance(arrivals, list):
                      arrivals = arrivals[:10]
                 dynamic_system = system_prompt + f"\n\nAIRPORT FLIGHT DATA FROM AERODATABOX: {arrivals}"

    try:
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