# ============================================================

# SMART TOURIST GUIDE

# Introduction to AI Lab Project

# ============================================================

import streamlit as st

def render_html(markup):
    """Render presentation HTML without Markdown code-block interpretation."""
    # Removing indentation and empty lines also supports older Streamlit releases.
    markup = "\n".join(line.strip() for line in markup.splitlines() if line.strip())
    if hasattr(st, "html"):
        st.html(markup)
    else:
        st.markdown(markup, unsafe_allow_html=True)



from pathlib import Path
import base64
import re
from html import escape


APP_DIR = Path(__file__).resolve().parent
IMAGE_DIRS = (APP_DIR / "assets", APP_DIR / "assets" / "images")
IMAGE_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
PLACE_IMAGE_ALIASES = {
    "amberfort": ("Jaipur_Amber_Fort", "amber_fort", "amer_fort"),
    "amerfort": ("Jaipur_Amber_Fort", "amber_fort", "amer_fort"),
    "alberthall": ("albert_hall_museum", "albert_hall"),
    "alberthallmuseum": ("albert_hall_museum", "albert_hall"),
    "chokhidhani": ("chokhi_dhani", "choki_dhani"),
    "chokidhani": ("choki_dhani", "chokhi_dhani"),
    "citypalace": ("city_palace", "city-palace-jaipur"),
    "citypalacejaipur": ("city_palace", "city-palace-jaipur"),
    "hawamahal": ("hawa_mahal",),
    "jaigarhfort": ("jaigarh_fort",),
    "jalmahal": ("jal_mahal",),
    "jantarmantar": ("jantar_mantar",),
    "nahargarhfort": ("nahargarh_fort",),
    "ramniwasgarden": ("ram_niwas_garden",),
    "ramniwasbagh": ("ram_niwas_garden",),
    "jaipurhero": ("jaipur_hero",),
}


def image_key(value):
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def find_place_image(place_name):
    """Resolve only matching local photos in either supported assets folder."""
    key = image_key(place_name)
    aliases = PLACE_IMAGE_ALIASES.get(key, (str(place_name),))
    wanted = tuple(dict.fromkeys(image_key(name) for name in aliases))
    files = []
    for folder in IMAGE_DIRS:
        if folder.is_dir():
            files.extend(sorted((p for p in folder.iterdir()
                                 if p.is_file() and p.suffix.lower() in IMAGE_TYPES),
                                key=lambda p: p.name.casefold()))
    for stem in wanted:
        for path in files:
            if image_key(path.stem) == stem:
                return path
    # The screenshot's City Palace filename has an extra Jaipur/Rajasthan suffix.
    # Accept that suffix only when it identifies one unambiguous local image.
    if key in ("citypalace", "citypalacejaipur"):
        candidates = [p for p in files if image_key(p.stem).startswith("citypalace")]
        if len(candidates) == 1:
            return candidates[0]
    return None


@st.cache_data(show_spinner=False)
def image_data_uri(path_text, modified_ns):
    """Cache image bytes, with the modification time invalidating replacements."""
    path = Path(path_text)
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{IMAGE_TYPES[path.suffix.lower()]};base64,{payload}"


def render_place_photo(place_name, hero=False):
    path = find_place_image(place_name)
    uri = None
    if path is not None:
        try:
            uri = image_data_uri(str(path), path.stat().st_mtime_ns)
        except OSError:
            pass
    title = "Explore the Pink City" if hero else str(place_name)
    if uri:
        if hero:
            render_html(f"""
                <figure class="tourist-hero-photo">
                    <img src="{uri}" alt="Jaipur cityscape" />
                    <figcaption><span>JAIPUR • RAJASTHAN</span>
                    <h2>Explore the Pink City</h2>
                    <p>Heritage • Culture • Nature • Food</p></figcaption>
                </figure>
            """)
        else:
            render_html(f'<img class="tourist-place-photo" src="{uri}" '
                        f'alt="{escape(title, quote=True)}" loading="lazy" />')
    else:
        kind = "tourist-photo-placeholder tourist-hero-placeholder" if hero else "tourist-photo-placeholder"
        render_html(f'<div class="{kind}"><span>📍</span>'
                    f'<strong>{escape(title)}</strong><small>Photo unavailable</small></div>')


import pandas as pd

import folium

from streamlit_folium import st_folium

from ai.recommender import (

    recommend_places,

    get_recommendation_reason

)

from ai.itinerary import (

    generate_itinerary,

    calculate_itinerary_summary

)

from ai.pathfinding import find_route

from ai.restaurant import recommend_restaurant

# ============================================================

# 1. PAGE CONFIGURATION

# ============================================================

st.set_page_config(

    page_title="Smart Tourist | AI Tourist Guide",

    page_icon="🌍",

    layout="wide",

    initial_sidebar_state="expanded"

)

# ============================================================

# 2. MODERN TRAVEL APP CSS

# ============================================================

render_html("""

<style>

/* ---------------------------------------------------------

   GLOBAL

--------------------------------------------------------- */

html {

    scroll-behavior: smooth;

}

.stApp {

    background:

        radial-gradient(

            circle at 90% 5%,

            rgba(45, 212, 191, 0.10),

            transparent 24%

        ),

        #f4fafb;

    color: #123f46;

}

.block-container {

    max-width: 1220px;

    padding-top: 6rem;

    padding-bottom: 5rem;

}

#MainMenu {

    visibility: hidden;

}

footer {

    visibility: hidden;

}

[data-testid="stHeader"] {

    background: #f4fafb;

}

/* ---------------------------------------------------------

   SIDEBAR

--------------------------------------------------------- */

[data-testid="stSidebar"] {

    background: #ffffff;

    border-right: 1px solid #dfecec;

}

[data-testid="stSidebar"] > div:first-child {

    padding-top: 1.5rem;

}

[data-testid="stSidebar"] h1,

[data-testid="stSidebar"] h2,

[data-testid="stSidebar"] h3 {

    color: #073f46 !important;

}

[data-testid="stSidebar"] label {

    color: #315d63 !important;

    font-weight: 650 !important;

}

/* ---------------------------------------------------------

   HEADINGS

--------------------------------------------------------- */

h1,

h2,

h3 {

    color: #073f46 !important;

}

h1 {

    font-weight: 850 !important;

}

h2 {

    font-weight: 800 !important;

}

/* ---------------------------------------------------------

   INPUTS

--------------------------------------------------------- */

[data-baseweb="select"] > div {

    background: #f7fbfb !important;

    border: 1px solid #d4e7e7 !important;

    border-radius: 12px !important;

}

[data-baseweb="tag"] {

    background: #16c79a !important;

    color: white !important;

    border-radius: 8px !important;

}

/* ---------------------------------------------------------

   SLIDERS

--------------------------------------------------------- */

[data-testid="stSlider"] [role="slider"] {

    background: #13c79a !important;

}

[data-testid="stSlider"] div[data-baseweb="slider"] > div > div {

    color: #13c79a;

}

/* ---------------------------------------------------------

   BUTTONS

--------------------------------------------------------- */

.stButton > button {

    width: 100%;

    min-height: 48px;

    border: 0;

    border-radius: 14px;

    background:

        linear-gradient(

            90deg,

            #12c99b,

            #0fb99c

        );

    color: #ffffff;

    font-size: 0.95rem;

    font-weight: 750;

    box-shadow:

        0 9px 24px rgba(18, 201, 155, 0.20);

    transition:

        transform 0.20s ease,

        box-shadow 0.20s ease;

}

.stButton > button:hover {

    background:

        linear-gradient(

            90deg,

            #0eb98e,

            #0da68d

        );

    color: white;

    transform: translateY(-2px);

    box-shadow:

        0 13px 28px rgba(18, 201, 155, 0.28);

}

/* ---------------------------------------------------------

   METRIC CARDS

--------------------------------------------------------- */

[data-testid="stMetric"] {

    background: #ffffff;

    border:

        1px solid #deebeb;

    border-radius:

        18px;

    padding:

        18px 20px;

    box-shadow:

        0 8px 28px rgba(18, 72, 78, 0.06);

}

[data-testid="stMetricLabel"] {

    color: #66868a !important;

    font-weight: 600 !important;

}

[data-testid="stMetricValue"] {

    color: #073f46 !important;

    font-weight: 800 !important;

}

/* ---------------------------------------------------------

   STREAMLIT CONTAINER CARDS

--------------------------------------------------------- */

[data-testid="stVerticalBlockBorderWrapper"] {

    background: #ffffff;

    border:

        1px solid #dfeaea !important;

    border-radius:

        20px !important;

    box-shadow:

        0 10px 30px rgba(20, 71, 78, 0.06);

    transition:

        transform 0.20s ease,

        box-shadow 0.20s ease;

}

[data-testid="stVerticalBlockBorderWrapper"]:hover {

    transform: translateY(-3px);

    box-shadow:

        0 15px 35px rgba(20, 71, 78, 0.10);

}

/* ---------------------------------------------------------

   ALERTS

--------------------------------------------------------- */

[data-testid="stAlert"] {

    border-radius: 15px;

}

/* ---------------------------------------------------------

   EXPANDER

--------------------------------------------------------- */

[data-testid="stExpander"] {

    background: #ffffff;

    border:

        1px solid #dfeaea;

    border-radius:

        16px;

}

/* ---------------------------------------------------------

   DATAFRAME

--------------------------------------------------------- */

[data-testid="stDataFrame"] {

    background: white;

    border-radius: 16px;

    overflow: hidden;

}

/* ---------------------------------------------------------

   CAPTION

--------------------------------------------------------- */

.stCaption {

    color: #718d91 !important;

}

/* ---------------------------------------------------------

   DIVIDER

--------------------------------------------------------- */

hr {

    border-color:

        #dfebeb !important;

}

/* ---------------------------------------------------------

   SCROLLBAR

--------------------------------------------------------- */

::-webkit-scrollbar {

    width: 8px;

}

::-webkit-scrollbar-track {

    background: #edf6f6;

}

::-webkit-scrollbar-thumb {

    background: #9bded1;

    border-radius: 10px;

}

::-webkit-scrollbar-thumb:hover {

    background: #13bd94;

}

/* ---------------------------------------------------------

   MOBILE

--------------------------------------------------------- */

@media (max-width: 768px) {

    .block-container {

        padding-left: 1rem;

        padding-right: 1rem;

    }

}


/* Local destination photography */
.tourist-hero-photo {
    position: relative; margin: 20px 0 0; height: 470px;
    border-radius: 32px; overflow: hidden; background: #c9f3eb;
    box-shadow: 0 22px 50px rgba(19,80,78,.18);
}
.tourist-hero-photo img { width: 100%; height: 100%; object-fit: cover; display: block; }
.tourist-hero-photo figcaption {
    position: absolute; inset: auto 0 0; padding: 80px 28px 28px;
    background: linear-gradient(transparent, rgba(3,40,43,.94)); color: white;
}
.tourist-hero-photo figcaption span { font-size: 12px; font-weight: 750; letter-spacing: 2px; }
.tourist-hero-photo figcaption h2 { color: white !important; font-size: 32px; margin: 8px 0; }
.tourist-hero-photo figcaption p { color: #e5faf5; margin: 0; font-size: 14px; }
.tourist-place-photo {
    display: block; width: 100%; height: 195px; object-fit: cover;
    border-radius: 14px; margin: 0 0 12px;
}
.tourist-photo-placeholder {
    height: 195px; display: flex; flex-direction: column; align-items: center;
    justify-content: center; gap: 8px; border-radius: 14px; margin-bottom: 12px;
    color: #073f46; background: linear-gradient(135deg,#d8f5eb,#d8eef9);
}
.tourist-photo-placeholder span { font-size: 32px; }
.tourist-photo-placeholder small { color: #50777b; }
.tourist-hero-placeholder { height: 470px; margin-top: 20px; border-radius: 32px; }
@media (max-width:768px) {
    .tourist-hero-photo, .tourist-hero-placeholder { height: 340px; }
}


button[kind="secondary"] {
    background: white !important; color: #073f46 !important;
    border: 1px solid #bde5dc !important; box-shadow: none !important;
}
button[kind="secondary"]:hover { background: #e5faf5 !important; }
</style>

""")

# ============================================================

# 3. LOAD DATA

# ============================================================

@st.cache_data

def load_data():

    places_df = pd.read_csv(

        "data/places.csv"

    )

    routes_df = pd.read_csv(

        "data/routes.csv"

    )

    restaurants_df = pd.read_csv(

        "data/restaurants.csv"

    )

    return (

        places_df,

        routes_df,

        restaurants_df

    )

try:

    places, routes, restaurants = load_data()

except Exception as error:

    st.error(

        "Unable to load project data."

    )

    st.code(

        str(error)

    )

    st.stop()

# ============================================================

# 4. CLEAN PLACES DATA

# ============================================================

place_numeric_columns = [

    "rating",

    "entry_fee",

    "visit_duration",

    "latitude",

    "longitude"

]

for column in place_numeric_columns:

    if column in places.columns:

        places[column] = pd.to_numeric(

            places[column],

            errors="coerce"

        )

places = places.dropna(

    subset=[

        "name",

        "category",

        "rating",

        "latitude",

        "longitude"

    ]

)

# ============================================================

# 5. CLEAN RESTAURANT DATA

# ============================================================

restaurant_numeric_columns = [

    "rating",

    "average_cost",

    "latitude",

    "longitude"

]

for column in restaurant_numeric_columns:

    if column in restaurants.columns:

        restaurants[column] = pd.to_numeric(

            restaurants[column],

            errors="coerce"

        )

# ============================================================

# 6. SESSION STATE

# ============================================================

if "trip_generated" not in st.session_state:
    st.session_state.trip_generated = False
if "active_page" not in st.session_state:
    st.session_state.active_page = "AI Planner" if st.session_state.get("planner_open", False) else "Explore"
if "favourites" not in st.session_state:
    st.session_state.favourites = set()


def start_planning():
    st.session_state.trip_generated = True
    st.session_state.active_page = "AI Planner"


def navigate(page):
    st.session_state.active_page = page


def show_home():
    navigate("Explore")


def toggle_favourite(name):
    saved = set(st.session_state.favourites)
    if name in saved:
        saved.remove(name)
    else:
        saved.add(name)
    st.session_state.favourites = saved


def place_detail_text(place, fields, fallback):
    for field in fields:
        value = place.get(field)
        if value is not None and pd.notna(value) and str(value).strip():
            return str(value)
    return fallback


def render_place_actions(place):
    name = str(place["name"])
    saved = name in st.session_state.favourites
    st.button(
        "♥ Saved · Remove" if saved else "♡ Save place",
        key="favourite_" + name,
        on_click=toggle_favourite,
        args=(name,),
        use_container_width=True,
    )
    with st.expander("View place details"):
        st.write(place_detail_text(place, ("description", "about", "details"),
                                  "A description has not been added for this destination yet."))
        st.write("**Opening hours:** " + place_detail_text(
            place, ("opening_hours", "opening_times", "timings"), "Not listed in the project data."))
        st.write("**Best time to visit:** " + place_detail_text(
            place, ("best_time",), "Not listed."))
        address = place_detail_text(place, ("address", "location"), "")
        if address:
            st.write("**Location:** " + address)
        latitude, longitude = float(place["latitude"]), float(place["longitude"])
        if -90 <= latitude <= 90 and -180 <= longitude <= 180:
            url = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
            st.markdown(f"[📍 Open location in Google Maps]({url})")

# ============================================================

# 7. SIDEBAR PLANNER

# ============================================================

with st.sidebar:

    render_html("""

        <div style="

            font-size:26px;

            font-weight:850;

            color:#073f46;

            margin-bottom:5px;

        ">

            🌍 Smart Tourist

        </div>

        <div style="

            color:#759094;

            font-size:13px;

            margin-bottom:25px;

        ">

            Your AI travel companion

        </div>

        """)

    st.divider()

    st.subheader(

        "🧭 Plan Your Trip"

    )

    # START LOCATION

    start_location = st.selectbox(

        "📍 Starting Location",

        places["name"].tolist()

    )

    # INTERESTS

    categories = sorted(

        places["category"]

        .dropna()

        .unique()

        .tolist()

    )

    interests = st.multiselect(

        "💚 Your Interests",

        categories,

        default=categories[:1]

    )

    # BUDGET

    max_fee = places[

        "entry_fee"

    ].max()

    if pd.isna(max_fee):

        max_fee = 1000

    max_budget = max(

        1000,

        int(max_fee)

    )

    budget = st.slider(

        "💰 Budget (₹)",

        min_value=0,

        max_value=max_budget,

        value=min(

            1000,

            max_budget

        ),

        step=50

    )

    # TIME

    available_time = st.slider(

        "⏰ Available Time",

        min_value=1,

        max_value=12,

        value=8,

        step=1,

        format="%d hours"

    )

    # RATING

    minimum_rating = st.slider(

        "⭐ Minimum Rating",

        min_value=0.0,

        max_value=5.0,

        value=4.0,

        step=0.1

    )

    st.divider()

    generate_trip = st.button(

        "✨ Plan with AI",

        use_container_width=True,

        type="primary",
        on_click=start_planning

    )

# ============================================================

# 8. BUTTON STATE

# ============================================================

if generate_trip:

    start_planning()

# ============================================================

# 9. NAVIGATION

# ============================================================

nav_left, nav_right = st.columns(

    [1.2, 2.4]

)

with nav_left:

    render_html("""

        <div style="

            font-size:28px;

            font-weight:850;

            color:#073f46;

            padding-top:5px;

        ">

            🌍 Smart Tourist

        </div>

        """)

with nav_right:
    navigation = st.columns(4)
    for column, page in zip(navigation, ("Explore", "AI Planner", "Map", "Saved")):
        with column:
            label = f"Saved ({len(st.session_state.favourites)})" if page == "Saved" else page
            st.button(label, key="nav_" + page, on_click=navigate, args=(page,),
                      type="primary" if st.session_state.active_page == page else "secondary",
                      use_container_width=True)

st.divider()

# ============================================================

# 10. HERO

# ============================================================

if st.session_state.active_page == "Explore":
    hero_left, hero_right = st.columns(

        [1.05, 0.95],

        gap="large"

    )

    with hero_left:

        render_html("""

            <div style="

                padding-top:38px;

            ">

                <div style="

                    display:inline-block;

                    background:#e5faf5;

                    color:#089879;

                    border:1px solid #bdeee2;

                    padding:8px 14px;

                    border-radius:999px;

                    font-size:14px;

                    font-weight:750;

                    margin-bottom:22px;

                ">

                    ✨ Meet your AI travel planner

                </div>

                <div style="

                    font-size:58px;

                    line-height:1.04;

                    letter-spacing:-2px;

                    font-weight:900;

                    color:#073f46;

                    margin-bottom:22px;

                ">

                    Where to next?<br>

                    <span style="

                        color:#12bd94;

                    ">

                        Let's plan Jaipur.

                    </span>

                </div>

                <div style="

                    color:#52767b;

                    font-size:17px;

                    line-height:1.7;

                    max-width:540px;

                    margin-bottom:28px;

                ">

                    Tell our AI what you love, your budget and how

                    much time you have. Smart Tourist creates personalized

                    recommendations, an itinerary and an optimized

                    Jaipur travel route.

                </div>

                <div style="

                    display:flex;

                    gap:12px;

                    flex-wrap:wrap;

                    margin-bottom:25px;

                ">

                    <span style="

                        background:white;

                        border:1px solid #dceaea;

                        padding:9px 13px;

                        border-radius:999px;

                        color:#476d72;

                        font-size:13px;

                    ">

                        🧠 AI Recommendations

                    </span>

                    <span style="

                        background:white;

                        border:1px solid #dceaea;

                        padding:9px 13px;

                        border-radius:999px;

                        color:#476d72;

                        font-size:13px;

                    ">

                        🧭 A* Routes

                    </span>

                    <span style="

                        background:white;

                        border:1px solid #dceaea;

                        padding:9px 13px;

                        border-radius:999px;

                        color:#476d72;

                        font-size:13px;

                    ">

                        🗺️ Interactive Map

                    </span>

                </div>

            </div>

            """)

        hero_button = st.button(

            "✨ Start Planning",

            key="hero_plan",
            type="primary",
            on_click=start_planning

        )

    with hero_right:
        render_place_photo("jaipur_hero", hero=True)

# ============================================================

# 11. SECTION INTRO

# ============================================================

if st.session_state.active_page == "Explore":

    render_html("<br><br>")

    render_html("""

        <div style="

            text-align:center;

            margin-bottom:25px;

        ">

            <div style="

                color:#073f46;

                font-size:36px;

                font-weight:850;

            ">

                Explore Jaipur your way

            </div>

            <div style="

                color:#6a888c;

                margin-top:8px;

                font-size:16px;

            ">

                Personalized recommendations powered by your preferences

            </div>

        </div>

        """)


# ============================================================

# 12. RECOMMENDATION ENGINE

# ============================================================

try:

    filtered_places = recommend_places(

        places=places,

        interests=interests,

        budget=budget,

        available_time=available_time,

        minimum_rating=minimum_rating

    )

except Exception as error:

    st.error(

        "Recommendation engine error."

    )

    st.code(

        str(error)

    )

    st.stop()

# ============================================================

# 13. QUICK STATS

# ============================================================

if st.session_state.active_page == "Explore":

    average_rating = (

        round(

            places["rating"].mean(),

            1

        )

        if not places.empty

        else 0

    )

    stat1, stat2, stat3, stat4 = st.columns(4)

    with stat1:

        st.metric(

            "📍 Places to Explore",

            len(places)

        )

    with stat2:

        st.metric(

            "🧭 Smart Routes",

            len(routes)

        )

    with stat3:

        st.metric(

            "🍴 Restaurants",

            len(restaurants)

        )

    with stat4:

        st.metric(

            "⭐ Average Rating",

            average_rating

        )


# ============================================================

# 14. RECOMMENDATIONS

# ============================================================

if st.session_state.active_page in ("Explore", "Saved"):

    render_html("<br>")

    st.header(

        "♥ Your saved places" if st.session_state.active_page == "Saved" else "✨ Recommended for you"

    )

    if st.session_state.active_page == "Saved":
        st.caption("Saved places stay available while this browser session is open.")
        display_places = places[places["name"].isin(st.session_state.favourites)].copy()
        display_places["ai_score"] = float("nan")
    else:
        st.caption("AI-ranked destinations based on your interests, budget, time and minimum rating.")
        display_places = filtered_places

    display_places = display_places.drop_duplicates(subset="name")

    if display_places.empty:

        st.warning(

            "No saved places yet. Open Explore and choose Save place."
            if st.session_state.active_page == "Saved" else
            "No destinations match these preferences. Try changing your interests, budget or rating."

        )

    else:

        top_places = display_places if st.session_state.active_page == "Saved" else display_places.head(6)

        for row_start in range(

            0,

            len(top_places),

            3

        ):

            recommendation_columns = st.columns(

                3,

                gap="medium"

            )

            row_places = top_places.iloc[

                row_start:row_start + 3

            ]

            for column, (_, place) in zip(

                recommendation_columns,

                row_places.iterrows()

            ):

                with column:

                    with st.container(

                        border=True

                    ):

                        render_place_photo(place["name"])

                        category = str(

                            place["category"]

                        ).upper()

                        st.caption(

                            f"📍 {category}"

                        )

                        st.subheader(

                            place["name"]

                        )

                        if pd.notna(place.get("ai_score")):
                            st.progress(

                                min(

                                    max(

                                        float(

                                            place["ai_score"]

                                        ) / 100,

                                        0.0

                                    ),

                                    1.0

                                ),

                                text=(

                                    f'🧠 '

                                    f'{place["ai_score"]:.1f}% AI Match'

                                )

                            )

                        info1, info2 = st.columns(2)

                        with info1:

                            st.write(

                                f'⭐ **{place["rating"]}/5**'

                            )

                        with info2:

                            if float(

                                place["entry_fee"]

                            ) == 0:

                                st.write(

                                    "🎟️ **Free**"

                                )

                            else:

                                st.write(

                                    f'🎟️ **₹'

                                    f'{place["entry_fee"]:.0f}**'

                                )

                        st.write(

                            f'⏱️ '

                            f'{place["visit_duration"]:.0f} min'

                        )

                        st.write(

                            f'🌅 Best time: '

                            f'**{place.get("best_time", "Not listed")}**'

                        )

                        try:

                            reason = (

                                get_recommendation_reason(

                                    place,

                                    interests,

                                    budget,

                                    available_time

                                )

                            )

                            st.caption(

                                f"💡 {reason}"

                            )

                        except Exception:

                            pass

                        render_place_actions(place)

# ============================================================

# 15. RECOMMENDATION DATA

# ============================================================

if st.session_state.active_page == "Explore":

    with st.expander(

        "📊 View AI scoring details"

    ):

        columns_to_show = [

            "name",

            "category",

            "rating",

            "entry_fee",

            "visit_duration",

            "best_time",

            "ai_score"

        ]

        valid_columns = [

            column

            for column in columns_to_show

            if column in filtered_places.columns

        ]

        st.dataframe(

            filtered_places[

                valid_columns

            ],

            use_container_width=True,

            hide_index=True

        )


# ============================================================

# 16. GENERATE ITINERARY

# ============================================================

itinerary = []

if st.session_state.trip_generated:

    try:

        itinerary = generate_itinerary(

            recommendations=filtered_places,

            start_location=start_location,

            available_time=available_time,

            budget=budget

        )

    except Exception as error:

        st.error(

            "Unable to generate itinerary."

        )

        st.code(

            str(error)

        )

# ============================================================

# 17. A* ROUTE CALCULATION

# ============================================================

optimized_routes = []

if itinerary:

    current_location = start_location

    for item in itinerary:

        destination = item["name"]

        if current_location == destination:

            current_location = destination

            continue

        try:

            path, distance = find_route(

                routes=routes,

                places=places,

                start=current_location,

                goal=destination

            )

        except Exception:

            path = []

            distance = float("inf")

        optimized_routes.append(

            {

                "from": current_location,

                "to": destination,

                "path": path,

                "distance": distance

            }

        )

        current_location = destination

# ============================================================

# 18. ITINERARY

# ============================================================

if st.session_state.active_page == "AI Planner":

    with st.container():
        render_html("<br>")

        st.header(

            "🗓️ Your AI itinerary"

        )

        if not st.session_state.trip_generated:

            st.info(

                "👈 Choose your preferences and click "

                "**Plan with AI** to generate your trip."

            )

        elif not itinerary:

            st.warning(

                "No itinerary could be created with the "

                "current preferences. Try increasing the "

                "budget or available time."

            )

        else:

            try:

                itinerary_summary = (

                    calculate_itinerary_summary(

                        itinerary

                    )

                )

            except Exception:

                itinerary_summary = {

                    "places": len(itinerary),

                    "total_time": sum(

                        float(

                            item.get(

                                "visit_duration",

                                0

                            )

                        )

                        for item in itinerary

                    ),

                    "budget": sum(

                        float(

                            item.get(

                                "entry_fee",

                                0

                            )

                        )

                        for item in itinerary

                    )

                }

            trip1, trip2, trip3 = st.columns(3)

            with trip1:

                st.metric(

                    "📍 Stops",

                    itinerary_summary["places"]

                )

            with trip2:

                st.metric(

                    "⏱️ Visit Time",

                    f'{itinerary_summary["total_time"]} min'

                )

            with trip3:

                st.metric(

                    "💰 Entry Cost",

                    f'₹{itinerary_summary["budget"]:.0f}'

                )

            render_html("<br>")

            current_minutes = 9 * 60

            for index, item in enumerate(

                itinerary

            ):

                hour = (

                    current_minutes // 60

                )

                minute = (

                    current_minutes % 60

                )

                time_string = (

                    f"{hour:02d}:{minute:02d}"

                )

                with st.container(

                    border=True

                ):

                    stop_left, stop_right = st.columns(

                        [3, 1]

                    )

                    with stop_left:

                        st.caption(

                            f"STOP {index + 1}"

                        )

                        st.subheader(

                            item["name"]

                        )

                        st.write(

                            f'🏷️ {item["category"]}'

                        )

                        st.write(

                            f'⭐ {item["rating"]}/5'

                            f' &nbsp;&nbsp; • &nbsp;&nbsp; '

                            f'🎟️ ₹{item["entry_fee"]:.0f}'

                        )

                    with stop_right:

                        st.metric(

                            "Arrival",

                            time_string

                        )

                        st.caption(

                            f'⏱️ '

                            f'{item["visit_duration"]} min visit'

                        )

                current_minutes += int(

                    item["visit_duration"]

                )

                if index < len(itinerary) - 1:

                    travel_time = int(

                        item.get(

                            "travel_time",

                            20

                        )

                    )

                    current_minutes += travel_time

                    st.caption(

                        f"↓ 🚗 Approx. {travel_time} min "

                        "to the next stop"

                    )


# ============================================================

# 19. RESTAURANT RECOMMENDATION

# ============================================================

recommended_restaurant = None

if itinerary:

    try:

        restaurant_summary = (

            calculate_itinerary_summary(

                itinerary

            )

        )

        recommended_restaurant = (

            recommend_restaurant(

                restaurants=restaurants,

                budget=budget,

                itinerary_cost=(

                    restaurant_summary[

                        "budget"

                    ]

                )

            )

        )

    except Exception:

        recommended_restaurant = None


if st.session_state.active_page == "AI Planner":
    render_html("<br>")

    st.header(

        "🍴 Food stop"

    )

    if not st.session_state.trip_generated:

        st.info(

            "Your restaurant recommendation will appear "

            "after the trip is generated."

        )

    elif recommended_restaurant is None:

        st.info(

            "No suitable restaurant recommendation "

            "is currently available."

        )

    else:

        with st.container(

            border=True

        ):

            food_left, food_right = st.columns(

                [2.5, 1]

            )

            with food_left:

                st.caption(

                    "RECOMMENDED FOR YOUR TRIP"

                )

                st.subheader(

                    recommended_restaurant["name"]

                )

                if "category" in recommended_restaurant:

                    st.write(

                        f'🍽️ '

                        f'{recommended_restaurant["category"]}'

                    )

                if "rating" in recommended_restaurant:

                    st.write(

                        f'⭐ '

                        f'**{recommended_restaurant["rating"]}/5**'

                    )

                st.caption(

                    "Selected using your remaining budget "

                    "and restaurant rating."

                )

            with food_right:

                if "average_cost" in recommended_restaurant:

                    st.metric(

                        "Estimated Cost",

                        f'₹'

                        f'{recommended_restaurant["average_cost"]:.0f}'

                    )


# ============================================================

# 20. A* ROUTE

# ============================================================

if st.session_state.active_page == "AI Planner":

    render_html("<br>")

    st.header(

        "🧭 Smart route"

    )

    st.caption(

        "A* Search uses f(n) = g(n) + h(n) "

        "to find efficient routes between destinations."

    )

    if not st.session_state.trip_generated:

        st.info(

            "Generate your trip to calculate "

            "the optimized route."

        )

    elif not optimized_routes:

        st.info(

            "No additional route calculation is "

            "required for this itinerary."

        )

    else:

        for index, route in enumerate(

            optimized_routes

        ):

            with st.container(

                border=True

            ):

                st.caption(

                    f"ROUTE {index + 1}"

                )

                if route["path"]:

                    path_text = " → ".join(

                        route["path"]

                    )

                    st.write(

                        f"🧭 **{path_text}**"

                    )

                    st.write(

                        f"📏 Distance: "

                        f"**{route['distance']:.2f} km**"

                    )

                else:

                    st.warning(

                        f"No route found from "

                        f"{route['from']} to "

                        f"{route['to']}."

                    )


# ============================================================

# 21. MAP

# ============================================================

if st.session_state.active_page == "Map":

    render_html("<br>")

    st.header(

        "🗺️ Explore on the map"

    )

    st.caption(

        "Recommended destinations, itinerary stops "

        "and optimized routes around Jaipur."

    )

    tourist_map = folium.Map(

        location=[

            26.9124,

            75.7873

        ],

        zoom_start=12,

        control_scale=True,

        tiles="OpenStreetMap"

    )

    # ------------------------------------------------------------

    # RECOMMENDED PLACE MARKERS

    # ------------------------------------------------------------

    for _, place in filtered_places.iterrows():

        try:

            latitude = float(

                place["latitude"]

            )

            longitude = float(

                place["longitude"]

            )

        except (

            ValueError,

            TypeError

        ):

            continue

        popup = (

            f'<b>{place["name"]}</b><br>'

            f'{place["category"]}<br>'

            f'⭐ {place["rating"]}/5<br>'

            f'🧠 {place["ai_score"]:.1f}% match<br>'

            f'🎟️ ₹{place["entry_fee"]:.0f}'

        )

        folium.CircleMarker(

            location=[

                latitude,

                longitude

            ],

            radius=7,

            tooltip=place["name"],

            popup=folium.Popup(

                popup,

                max_width=260

            ),

            color="#0cae8a",

            fill=True,

            fill_color="#16c79a",

            fill_opacity=0.85

        ).add_to(

            tourist_map

        )

    # ------------------------------------------------------------

    # NUMBERED ITINERARY MARKERS

    # ------------------------------------------------------------

    if itinerary:

        for stop_number, item in enumerate(

            itinerary,

            start=1

        ):

            location_row = places[

                places["name"]

                == item["name"]

            ]

            if location_row.empty:

                continue

            latitude = float(

                location_row.iloc[0][

                    "latitude"

                ]

            )

            longitude = float(

                location_row.iloc[0][

                    "longitude"

                ]

            )

            marker_html = f"""

            <div style="

                background:#073f46;

                color:white;

                width:34px;

                height:34px;

                border-radius:50%;

                display:flex;

                justify-content:center;

                align-items:center;

                font-weight:800;

                border:3px solid white;

                box-shadow:0 3px 10px rgba(0,0,0,0.25);

            ">

                {stop_number}

            </div>

            """

            folium.Marker(

                location=[

                    latitude,

                    longitude

                ],

                tooltip=(

                    f"Stop {stop_number}: "

                    f"{item['name']}"

                ),

                icon=folium.DivIcon(

                    html=marker_html

                )

            ).add_to(

                tourist_map

            )

    # ------------------------------------------------------------

    # A* ROUTE LINES

    # ------------------------------------------------------------

    for route in optimized_routes:

        if not route["path"]:

            continue

        route_coordinates = []

        for place_name in route["path"]:

            row = places[

                places["name"]

                == place_name

            ]

            if row.empty:

                continue

            route_coordinates.append(

                [

                    float(

                        row.iloc[0][

                            "latitude"

                        ]

                    ),

                    float(

                        row.iloc[0][

                            "longitude"

                        ]

                    )

                ]

            )

        if len(

            route_coordinates

        ) >= 2:

            folium.PolyLine(

                route_coordinates,

                color="#13b894",

                weight=5,

                opacity=0.8,

                tooltip="A* optimized route"

            ).add_to(

                tourist_map

            )

    # ------------------------------------------------------------

    # RESTAURANT MARKER

    # ------------------------------------------------------------

    if recommended_restaurant is not None:

        try:

            restaurant_latitude = float(

                recommended_restaurant[

                    "latitude"

                ]

            )

            restaurant_longitude = float(

                recommended_restaurant[

                    "longitude"

                ]

            )

            folium.Marker(

                location=[

                    restaurant_latitude,

                    restaurant_longitude

                ],

                tooltip=(

                    "🍴 "

                    + str(

                        recommended_restaurant[

                            "name"

                        ]

                    )

                ),

                popup=(

                    f'🍴 '

                    f'{recommended_restaurant["name"]}'

                ),

                icon=folium.Icon(

                    color="green",

                    icon="cutlery",

                    prefix="fa"

                )

            ).add_to(

                tourist_map

            )

        except (

            KeyError,

            TypeError,

            ValueError

        ):

            pass

    st_folium(

        tourist_map,

        width=None,

        height=560

    )


# ============================================================

# 22. FINAL TRIP SUMMARY

# ============================================================

if st.session_state.active_page == "AI Planner":

    if (

        st.session_state.trip_generated

        and itinerary

    ):

        render_html("<br>")

        st.header(

            "✨ Your Smart Tourist"

        )

        try:

            final_summary = (

                calculate_itinerary_summary(

                    itinerary

                )

            )

        except Exception:

            final_summary = {

                "places": len(itinerary),

                "total_time": sum(

                    float(

                        item.get(

                            "visit_duration",

                            0

                        )

                    )

                    for item in itinerary

                ),

                "budget": sum(

                    float(

                        item.get(

                            "entry_fee",

                            0

                        )

                    )

                    for item in itinerary

                )

            }

        ai_scores = [

            float(

                item.get(

                    "ai_score",

                    0

                )

            )

            for item in itinerary

        ]

        average_ai_match = (

            sum(ai_scores) / len(ai_scores)

            if ai_scores

            else 0

        )

        final1, final2, final3, final4 = (

            st.columns(4)

        )

        with final1:

            st.metric(

                "📍 Destinations",

                final_summary["places"]

            )

        with final2:

            st.metric(

                "⏱️ Visit Time",

                f'{final_summary["total_time"]} min'

            )

        with final3:

            st.metric(

                "💰 Entry Cost",

                f'₹{final_summary["budget"]:.0f}'

            )

        with final4:

            st.metric(

                "🧠 Avg AI Match",

                f"{average_ai_match:.1f}%"

            )

        st.success(

            "Your personalized Jaipur trip is ready! ✨"

        )


# ============================================================

# 23. AI EXPLANATION

# ============================================================

if st.session_state.active_page in ("Explore", "AI Planner"):

    render_html("<br><br>")

    render_html("""

        <div style="

            text-align:center;

            margin-bottom:25px;

        ">

            <div style="

                color:#073f46;

                font-size:34px;

                font-weight:850;

            ">

                How Smart Tourist thinks

            </div>

            <div style="

                color:#6d898d;

                margin-top:8px;

            ">

                AI concepts working behind your travel plan

            </div>

        </div>

        """)

    concept1, concept2, concept3 = st.columns(3)

    with concept1:

        with st.container(

            border=True

        ):

            st.subheader(

                "🧠 Recommendation"

            )

            st.write(

                "Places are ranked using interests, "

                "ratings, budget and available time."

            )

    with concept2:

        with st.container(

            border=True

        ):

            st.subheader(

                "🧭 A* Search"

            )

            st.write(

                "A* finds efficient travel routes using "

                "`f(n) = g(n) + h(n)`."

            )

    with concept3:

        with st.container(

            border=True

        ):

            st.subheader(

                "✨ Decision Making"

            )

            st.write(

                "The itinerary planner selects suitable "

                "destinations while respecting user constraints."

            )


# ============================================================

# 24. AI DETAILS

# ============================================================

if st.session_state.active_page in ("Explore", "AI Planner"):

    with st.expander(

        "🎓 AI concepts used in this project"

    ):

        st.markdown(

            """

    ### Recommendation System

    The system ranks Jaipur tourist destinations according to

    the user's interests, ratings, budget and available time.

    ### Heuristic Scoring

    Each destination receives an **AI Match score** representing

    how closely it matches the user's preferences.

    ### A* Search Algorithm

    The project uses:

    `f(n) = g(n) + h(n)`

    where:

    - **g(n)** = actual cost from the starting node

    - **h(n)** = estimated cost to the destination

    - **f(n)** = estimated total route cost

    ### Constraint-Based Itinerary Planning

    The itinerary considers available time and budget before

    selecting destinations.

    ### Rule-Based Restaurant Recommendation

    Restaurants are selected using remaining budget and rating.

    ### Intelligent Agent

    The application receives user preferences, processes the

    environment data and automatically generates travel decisions.

            """

        )


# ============================================================

# 25. FOOTER

# ============================================================

render_html("<br><br>")

st.divider()

footer_left, footer_right = st.columns(

    [2, 1]

)

with footer_left:

    st.caption(

        "🌍 Smart Tourist — AI-powered Smart Tourist Guide"

    )

with footer_right:

    st.caption(

        "Introduction to AI Lab Project"

    )