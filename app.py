import os
import anthropic
from dotenv import load_dotenv
import streamlit as st 

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

system_prompt =  """ You are a flight information desk at San Antonio International Airport (SAT). You know about flights status in both terminals. See flight data below.
You can help people locate the gate, understand if the flight is on time, late(delayed) or cancelled. You know the baggage claim locations for each flight. you can only answer questions relat$
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

st.title("A.I.R.")
st.caption("Airport Information Relay — San Antonio International Airport (SAT)")

st.markdown("""     <h1 style='color: #1B4F8A;'>  A.I.R.  🛩️</h1>     <p style='color: #2E5FA3;'>Airport Information Relay — San Antonio International Airport (SAT) </p> """, unsafe_allow_html=True)


if "messages"  not in st.session_state:
	st.session_state.messages = [ ]

for q in st.session_state.messages:
	with st.chat_message(q["role"]):
		st.markdown(q["content"])

user_question = st.chat_input("Ask me about Arrivals and Departures")
if user_question: 
	st.session_state.messages.append({"role": "user", "content": user_question})
	with st.chat_message("user"):
		st.markdown(user_question)

	response = client.messages.create(
  	    	model="claude-opus-4-5",
            	max_tokens=1024,
            	system=system_prompt,
            	messages = st.session_state.messages
        )

	with st.chat_message("assistant"):
		st.markdown(response.content[0].text)

	st.session_state.messages.append({"role": "assistant", "content": response.content[0].text})
