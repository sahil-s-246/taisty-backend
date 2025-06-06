from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import weaviate
import google.generativeai as genai
import json
from dotenv import load_dotenv
import os
load_dotenv()
from fastapi.middleware.cors import CORSMiddleware
from query import recommend, preference_query
from filter import RecommendationFilter
from collab import get_user_history, get_collab_recommendations, use_cb_for_user
from fastapi import Depends
from sqlalchemy.orm import Session
from database import get_db
import pandas as pd
from test_col import Order, get_item_based_recommendations
app = FastAPI()
import traceback
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # Allows all origins; specify a list of domains to restrict
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)
weaviate_url = os.getenv('CLUSTER_URL')
weaviate_api_key = os.getenv('Weav_API_KEY')
hf_api_key = os.getenv('hf_key')
gemini_api_key = os.getenv('API_KEY')
# Pydantic models for request/response

class DishDetails(BaseModel):
    cuisine: str
    category: str
    description: str
    allergy: str

class FilterParams(BaseModel):
    cuisine: Optional[str] = "Both"
    category: Optional[str] = "Both"
    allergies: Optional[List[str]] = []

class MoreLikeThisRequest(BaseModel):
    dish_name: str
    filters: Optional[FilterParams] = None

class PersonalizedRecommendationRequest(BaseModel):
    preference_query: str
    filters: Optional[FilterParams] = None
    user_id : Optional[str] = None

class RecommendationResponse(BaseModel):
    recommendations: Dict[str, DishDetails]

def init_clients(weaviate_url: str, weaviate_api_key: str, hf_api_key: str, gemini_api_key: str):
    weaviate_url = os.getenv('CLUSTER_URL', weaviate_url)
    weaviate_api_key = os.getenv('Weav_API_KEY', weaviate_api_key)
    hf_api_key = os.getenv('hf_key', hf_api_key)
    gemini_api_key = os.getenv('API_KEY', gemini_api_key)
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=weaviate.auth.AuthApiKey(weaviate_api_key),
        headers={"X-HuggingFace-Api-Key": hf_api_key}
    )
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    return client, model

def extract_features(query_result) -> Dict:
    """Extract features from Weaviate query result"""
    extracted_data = {}
    for item in query_result.objects:
        properties = item.properties
        extracted_data[item.properties["dish"]] = {
            'cuisine': properties.get('cuisine', ''),
            'category': properties.get('category', ''),
            'description': properties.get('description', ''),
            'allergy': properties.get('allergy', '')
        }
    return extracted_data


class RecommendationRequest(BaseModel):
    user_id: Optional[str]
    preference_query: Optional[str]

def load_orders(csv_path="user_orders.csv"):
    df = pd.read_csv(csv_path)
    return [
        Order(row["user_id"], row["dish_id"], row["order_count"], row["feedback_score"])
        for _, row in df.iterrows()
    ]
with open("updated_data.json", "r") as f:
    DISH_METADATA = {item["dish"]: item for item in json.load(f)}

def format_dishes(dish_names: List[str]):
    return [
        {
            "dish": name,
            "cuisine": DISH_METADATA[name]["cuisine"],
            "category": DISH_METADATA[name]["category"],
            "description": DISH_METADATA[name]["description"],
            "allergy": DISH_METADATA[name]["allergy"]
        }
        for name in dish_names if name in DISH_METADATA
    ]
@app.post("/recommend")
def recommend_user_items(request: RecommendationRequest):
    orders = load_orders()
    user_id = request.user_id

    if user_id:
        user_orders = [o for o in orders if o.user_id == user_id]
        if not request.preference_query:
            from test_col import MockSession
            session = MockSession(orders)
            dish_names = get_item_based_recommendations(user_id, session)
            return {"recommendations": format_dishes(dish_names)}
        else:
            names, _ = recommend(request.preference_query)
            return {"recommendations": format_dishes(names)}
    else:
        names, _ = recommend(request.preference_query)
        return {"recommendations": format_dishes(names)}
@app.post("/more-like-this")
async def more_like_this(request: dict):
    """Get similar dishes when a specific dish is clicked
    Input -> {dish_name: str, filters:{cuisine:str,category:str,allergy:str}"""
    try:
        results, first = recommend(request["dish_name"])
        if "filters" in request.keys():
            results = RecommendationFilter.filter_recommendations(
                results,
                cuisine=request["filters"].cuisine,
                category=request["filters"].category,
                allergy=request["filters"].allergies
            )
        return results
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=traceback.format_exc())


@app.post("/personalized-recommendations")
async def personalized_recommendations(request: PersonalizedRecommendationRequest, db: Session = Depends(get_db)):
    try:

        if "user_id" not in request.model_dump().keys():
            results, first = recommend(request.preference_query)
            return results

        user_id = request.user_id


        history = get_user_history(db, user_id)

        if history:
            dish_ids = get_collab_recommendations(user_id, db)
            # You can enhance with vector reranking if desired
            return {"recommendations": dish_ids}
        else:
            return use_cb_for_user(request.preference_query)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
