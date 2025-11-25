import streamlit as st
import requests
import datetime

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="AI Travel Route Recommender", page_icon="🗺️", layout="wide")

st.title("🗺️ AI Travel Route Recommender")
st.write("Enter a city and your preferences. I’ll generate a 1-day travel route using Google Places + Weather API.")


# ---------------------------------------------------------
# API KEYS
# ---------------------------------------------------------
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
WEATHER_API_KEY = st.secrets["WEATHER_API_KEY"]


# ---------------------------------------------------------
# API FUNCTIONS
# ---------------------------------------------------------

# 1) Get city coordinates from Google Geocoding
def get_city_coordinates(city):
    url = f"https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": city, "key": GOOGLE_API_KEY}
    data = requests.get(url, params=params).json()

    if not data["results"]:
        return None

    loc = data["results"][0]["geometry"]["location"]
    return loc["lat"], loc["lng"]


# 2) Weather forecast
def get_weather(lat, lng):
    url = f"https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lng, "appid": WEATHER_API_KEY, "units": "metric", "lang": "kr"}
    data = requests.get(url, params=params).json()
    return data


# 3) Google Places search by type
def search_places(lat, lng, place_type):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": 5000,
        "type": place_type,
        "key": GOOGLE_API_KEY
    }
    data = requests.get(url, params=params).json()
    return data.get("results", [])


# ---------------------------------------------------------
# USER INPUT
# ---------------------------------------------------------
st.sidebar.header("✈️ Trip Settings")

city = st.sidebar.text_input("Destination City (ex: Tokyo, Seoul, Paris)")
travel_day = st.sidebar.date_input("Travel Date", datetime.date.today())
preference = st.sidebar.selectbox(
    "What do you want to do today?",
    ["Nature", "Food", "Museum", "Shopping", "Café", "Landmark"]
)

btn = st.sidebar.button("Generate Route")


# ---------------------------------------------------------
# RECOMMENDATION LOGIC
# ---------------------------------------------------------
place_mapping = {
    "Nature": "park",
    "Food": "restaurant",
    "Museum": "museum",
    "Shopping": "shopping_mall",
    "Café": "cafe",
    "Landmark": "tourist_attraction"
}

if btn:
    if not city:
        st.warning("Please enter a city name.")
        st.stop()

    st.subheader(f"📍 Your Trip to **{city}**")

    coords = get_city_coordinates(city)
    if not coords:
        st.error("City not found. Try another search.")
        st.stop()

    lat, lng = coords

    with st.spinner("Fetching weather..."):
        weather = get_weather(lat, lng)

    # Weather-based recommendation
    weather_main = weather["weather"][0]["main"]
    temp = weather["main"]["temp"]

    st.write(f"### 🌤 Weather on {travel_day}")
    st.write(f"- Condition: **{weather_main}**")
    st.write(f"- Temperature: **{temp}°C**")

    indoor_needed = weather_main in ["Rain", "Snow", "Thunderstorm"]

    if indoor_needed:
        st.info("It might rain today. I will prefer **indoor activities**.")
        # Override preference for indoor-friendly options
        if preference in ["Nature", "Landmark"]:
            preference = "Museum"

    # Place search
    place_type = place_mapping[preference]

    with st.spinner("Searching for places..."):
        places = search_places(lat, lng, place_type)

    if not places:
        st.error("No places found. Try a different preference.")
        st.stop()

    # Select top 4–6 places for the route
    top_places = places[:5]

    st.subheader("🗺️ Your Recommended 1-Day Route")

    for idx, p in enumerate(top_places):
        st.markdown("---")
        name = p.get("name", "Unknown")
        rating = p.get("rating", "N/A")
        address = p.get("vicinity", "No address available")
        photo_ref = None

        if "photos" in p:
            photo_ref = p["photos"][0]["photo_reference"]

        # Photo URL
        if photo_ref:
            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=600&photo_reference={photo_ref}&key={GOOGLE_API_KEY}"
        else:
            photo_url = None

        cols = st.columns([1, 2])

        # Image + Info
        if photo_url:
            cols[0].image(photo_url, use_container_width=True)
        else:
            cols[0].write("No image available")

        cols[1].write(f"### {idx+1}. {name}")
        cols[1].write(f"⭐ Rating: {rating}")
        cols[1].write(f"📍 Address: {address}")
        cols[1].write(f"🏷 Category: {preference}")

    st.success("Your travel route is ready! Enjoy your trip ✈️")
