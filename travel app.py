import streamlit as st
import requests
import datetime

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="AI Travel Route Recommender", page_icon="🗺️", layout="wide")

st.title("🗺️ AI Travel Route Recommender")
st.write("AI-generated 1-day travel route using **OpenTripMap + OpenWeather API**.")
st.write("Enter your API keys on the left to begin!")

# ---------------------------------------------------------
# SIDEBAR: API KEY INPUTS
# ---------------------------------------------------------
st.sidebar.header("🔑 API Keys (Required)")

opentripmap_key = st.sidebar.text_input("OpenTripMap API Key", type="password")
weather_key = st.sidebar.text_input("OpenWeather API Key", type="password")

if not opentripmap_key or not weather_key:
    st.sidebar.warning("Please enter both API keys before generating a route.")
    st.stop()

# ---------------------------------------------------------
# USER INPUT
# ---------------------------------------------------------
st.sidebar.header("✈️ Trip Settings")

city = st.sidebar.text_input("Destination City (ex: Tokyo, Seoul, Paris)")
travel_day = st.sidebar.date_input("Travel Date", datetime.date.today())

preference = st.sidebar.selectbox(
    "Preferred Activity Type",
    ["Interesting Places", "Museums", "Parks", "Cultural", "Food/Restaurants"]
)

btn = st.sidebar.button("Generate Route")

# Map Place Categories for OpenTripMap
place_kinds = {
    "Interesting Places": "interesting_places",
    "Museums": "museums",
    "Parks": "natural",
    "Cultural": "cultural",
    "Food/Restaurants": "foods"
}

# ---------------------------------------------------------
# API FUNCTIONS
# ---------------------------------------------------------

# 1) City → Coordinates (lat/lon)
def get_city_coordinates(city):
    url = f"https://api.opentripmap.com/0.1/en/places/geoname"
    params = {"name": city, "apikey": opentripmap_key}
    res = requests.get(url, params=params).json()
    return (res.get("lat"), res.get("lon")) if "lat" in res else None

# 2) Weather Info
def get_weather(lat, lon):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": weather_key, "units": "metric"}
    return requests.get(url, params=params).json()

# 3) Search Places Nearby
def search_places(lat, lon, kind):
    url = "https://api.opentripmap.com/0.1/en/places/radius"
    params = {
        "radius": 5000,
        "lon": lon,
        "lat": lat,
        "kinds": kind,
        "format": "json",
        "apikey": opentripmap_key
    }
    return requests.get(url, params=params).json()

# 4) Place Details (description + image)
def get_place_details(xid):
    url = f"https://api.opentripmap.com/0.1/en/places/xid/{xid}"
    params = {"apikey": opentripmap_key}
    return requests.get(url, params=params).json()

# ---------------------------------------------------------
# MAIN LOGIC
# ---------------------------------------------------------
if btn:

    if not city:
        st.error("Please enter a destination city.")
        st.stop()

    st.subheader(f"📍 Your Trip to **{city}**")

    # Get Coordinates
    coords = get_city_coordinates(city)
    if not coords:
        st.error("City not found in OpenTripMap.")
        st.stop()

    lat, lon = coords

    # Weather Info
    with st.spinner("Fetching weather..."):
        weather = get_weather(lat, lon)

    weather_desc = weather["weather"][0]["description"]
    temp = weather["main"]["temp"]

    st.write(f"### 🌤 Weather on {travel_day}")
    st.write(f"- Condition: **{weather_desc}**")
    st.write(f"- Temperature: **{temp}°C**")

    # Auto-switch to indoor activities if raining
    if "rain" in weather_desc.lower():
        st.info("It may rain today. Switching to **indoor activities**.")
        preference = "Museums"

    # Search Places
    kind = place_kinds[preference]

    with st.spinner("Searching for nearby attractions..."):
        places = search_places(lat, lon, kind)

    if not places:
        st.error("No places found for this preference.")
        st.stop()

    top_places = places[:5]  # top 5 recommendations

    st.subheader("🗺️ AI-Generated 1-Day Travel Route")

    # Render Results
    for idx, p in enumerate(top_places):
        st.markdown("---")
        cols = st.columns([1, 2])

        name = p.get("name", "Unknown Place")
        distance = p.get("dist", 0)
        xid = p.get("xid", None)

        details = get_place_details(xid) if xid else {}

        # IMAGE (Left Column)
        img = details.get("preview", {}).get("source")
        if img:
            cols[0].image(img, use_container_width=True)
        else:
            cols[0].write("No image available")

        # TEXT INFO (Right Column)
        with cols[1]:
            st.write(f"### {idx + 1}. {name}")
            st.write(f"📍 Distance: {int(distance)} meters")
            st.write(f"🏷 Category: {preference}")

            desc = details.get("wikipedia_extracts", {}).get("text")
            if desc:
                st.write(desc)

    st.success("Your personalized travel route is ready! ✈️")
