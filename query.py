import json
import streamlit as st
import weaviate
import google.generativeai as genai
import random
from streamlit.errors import StreamlitAPIException
from PIL import Image
import requests
import io
from weaviate.exceptions import WeaviateQueryError
from card import Card
from filter import RecommendationFilter


genai.configure(api_key=st.secrets["API_KEY"])
model = genai.GenerativeModel(model_name="gemini-1.5-flash")


def extract_features(query_result):
    """Weaviate's Near Text returns a weaviate object.Extracts this to a dictionary"""
    extracted_data = {}
    for i, item in enumerate(query_result.objects):
        properties = item.properties
        extracted_data[item.properties["dish"]] = {
            'cuisine': properties.get('cuisine', ''),
            'category': properties.get('category', ''),
            'description': properties.get('description', ''),
            'allergy': properties.get('allergy', '')
        }
    return extracted_data


def recommend(query):
    """Connect to a weaviate collection in your weaviate cloud's sandbox, In this case FoodRecommend
    There are two steps in this recommendation \n
    Retrieval: Semantically search through the data wrt the query \n
    Ranking: Use Gemini Flash API to rank the data"""

    result =  {}
    first = {}
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=st.secrets["CLUSTER_URL"],
        auth_credentials=weaviate.auth.AuthApiKey(st.secrets["Weav_API_KEY"]),
        headers={

            "X-HuggingFace-Api-Key": st.secrets["hf_key"]
        }
    )

    try:
        questions = client.collections.get("tasty")
        # Retrieval
        response = questions.query.hybrid(
            query=query,
            limit=8,
            alpha=0.5,
            query_properties=["dish", "description", "cuisine", "category"],
        )
        data = extract_features(response)
        # with open("resp.json", 'w') as file:
        #     json.dump(data, file, indent=4)
        # Ranking

        res = model.generate_content(
            [f"Rerank json objects in this data {data} \n\n according to the query: {query}\n\n"
             f"Remove the most irrelevant ones but dont remove many"],
            generation_config={"response_mime_type": "application/json"})
        # print(res.text)
        result = json.loads(res.text)
        first = result[list(result.keys())[0]]

    except WeaviateQueryError:
        st.write("An error occurred. Please try again. Sorry, your tastes to complex to be catered for by us😝")
    finally:
        client.close()  # Close client gracefully
    return data, first
# ##################################################################
st.title("tAIsty😋")
with open("data.json", "r") as f:
    menu = json.load(f)

menu_limited = menu[30:50]
# menu_limited = random.sample(menu,20)
preference_query = st.sidebar.text_input(
    "Your Preference🍉", placeholder="Indian dessert"
)

selected_category = st.sidebar.selectbox("Select Category", ["Veg", "Non-Veg", "Both"])
selected_cuisine = st.sidebar.selectbox("Select Cuisine", ["Indian", "Japanese", "Both"])
excluded_allergies = st.sidebar.multiselect("Exclude Allergies", ["Contains dairy", "Contains gluten", "Contains nuts"])


# Fetch recommendations based on combined preferences
if preference_query:
    recommendations, _ = recommend(preference_query)
    filtered_recommendations = RecommendationFilter.filter_recommendations(
        recommendations,
        cuisine=selected_cuisine,
        category=selected_category,
        allergy=excluded_allergies
    )
    st.subheader("Recommended for You")
    recommendation_row = st.container()
    with recommendation_row:

        try:
            rec_items = list(filtered_recommendations.items())
            cols = st.columns(len(rec_items))
        except StreamlitAPIException:
            rec_items = list(recommendations.items())
            st.info("We could not find any results for your request but you might like.")
            cols = st.columns(len(rec_items))
              # Set a column for each recommendation
        for idx, (dish_name, rec) in enumerate(rec_items):
            with cols[idx]:
                card = Card(dish_name, rec)
                card.display()

# menu_limited = [random.choice(menu) for _ in range(20)]
# Initialize session state to keep track of the total orders
if "orders" not in st.session_state:
    st.session_state["orders"] = 0

# Display each menu item in an expander
for item in menu_limited:
    with st.expander(item["dish"]):
        st.write(f"**Cuisine:** {item['cuisine']}")
        st.write(f"**Category:** {item['category']}")
        st.write(f"**Description:** {item['description']}")
        st.write(f"**Allergy Information:** {item['allergy']}")

        # Add an order button
        if st.button(f"Order {item['dish']}", key=f"order_{item['dish']}"):
            st.session_state["orders"] += 1
            st.write(f"{item['dish']} added to order.")

        # Add a button to select the item, triggering recommendations
        if st.button(f"View More Like {item['dish']}", key=f"select_{item['dish']}"):
            with st.spinner(f"Generating recommendations for {item['dish']}...✨"):
                # Call your recommendation function here
                recommendations, first = recommend(item["dish"])
                filtered_recommendations = RecommendationFilter.filter_recommendations(
                    recommendations,
                    cuisine=selected_cuisine,
                    category=selected_category,
                    allergy=excluded_allergies  # Add logic to handle exclusions in RecommendationFilter
                )
                try:
                    rec_items = list(filtered_recommendations.items())
                    cols = st.columns(len(rec_items))
                except StreamlitAPIException:
                    rec_items = list(recommendations.items())
                    st.info("We could not find any results for your request but you might like.")
                    cols = st.columns(len(rec_items))
                for idx, (dish_name, rec) in enumerate(rec_items):
                    with cols[idx]:
                        card = Card(dish_name, rec)
                        card.display()


# Update the total order count banner
st.markdown(f"### 🛒 Total Orders: {st.session_state['orders']}")


# ##################################################################


def ask_ai_for_recommendations():
    """Prompt AI and gemini will retrieve and rank dishes"""
    ask_ai = st.text_input("Ask AI🤖")
    if ask_ai:
        res = model.generate_content([f"Recommend some dishes along with description, allegies etc. from the menu: "
                                      f"{menu}, \n\n ranked by relevance, according to the prompt: "
                                      f" {ask_ai} Eg. If the prompt is something like a mildly spicy gravy dish with"
                                      f" paneer then recommend paneer butter masala"])
        st.write(res.text)


def give_random():
    """Feeling Lucky? Get a Random dish!"""
    dish = random.choice(list(menu))
    return dish


st.info("Please describe your preference eg: Indian or Japanese, Veg or Non-Veg, Sweet or Spicy etc. in the sidebar"
        "Or Click 'I'm Feeling Lucky' for a random suggestion")
st.warning("Right now, there are only 2 cuisines : Indian and Japanese😅")

click = st.button("I'm Feeling Lucky✨")
if click:
    menu_item = give_random()
    st.write(menu_item)
