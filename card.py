import streamlit as st


class Card:
    def __init__(self, dish_name, details):
        self.dish_name = dish_name
        self.cuisine = details.get("cuisine", "")
        self.category = details.get("category", "")
        self.description = details.get("description", "")
        self.allergy = details.get("allergy", "")

    def display(self):
        """Display the card in a container with a border."""
        with st.container(border=True):
            st.markdown(f"**{self.dish_name}**")
            st.write(f"Cuisine: {self.cuisine}")
            st.write(f"Category: {self.category}")
            st.write(f"Description: {self.description}")
            st.write(f"Allergy: {self.allergy}")