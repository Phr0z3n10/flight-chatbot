import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

print("API connected successfully!")

system_prompt =  """ You are a flight information desk at San Antonio International Airport (SAT). You know about flights status in both terminals. See flight data below.
You can help people locate the gate, understand if the flight is on time, late(delayed) or cancelled. You know the baggage claim locations for each flight. you can only answer questions related to the status of flights. If someone asks anything not related to flight arrivals or departures, politely let them know you can only assist with flight information and direct them to the information desk near the TSA area. The directory will be near the human ran  information desk.  You should be friendly to all users even if they are not nice. many people will be dealing with the stress of travel and may not always respond kindly, that's ok, your job is to help them get information in a calm, polite and helpful way. Remind the users to type done if they no longer need help or their questions where answered.
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
- UA 1877 | United | Houston (IAH) | Arrives 1:45 PM | Gate A8 | Baggage Claim Carousel 3 | Delayed 40 min
- DL 2203 | Delta | Los Angeles (LAX) | Arrives 4:10 PM | Gate B1 | Baggage Claim Carousel 2 | On Time
- WN 987 | Southwest | Phoenix (PHX) | Arrives 6:30 PM | Gate B4 | Baggage Claim Carousel 1 | On Time
"""

print("Hi! I am the Airport Information Relay or A.I.R. I can help you find flight information for Today's schedule. How can I assist you?")

running = True
while running:
    user_input = input("You: ")
    if user_input.lower() == "done":
        print("Goodbye and safe travels!")
        running = False
    else:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_input}]
        )
        print(response.content[0].text)
