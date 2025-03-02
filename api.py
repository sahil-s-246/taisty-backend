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
from query import recommend
app = FastAPI()
import traceback
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins; specify a list of domains to restrict
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

def filter_recommendations(recommendations: Dict, filters: FilterParams) -> Dict:
    """Filter recommendations based on user preferences"""
    if not filters:
        return recommendations
    
    filtered = {}
    for dish_name, details in recommendations.items():
        # Check category filter
        if filters.category != "Both":
            if details.get("category") != filters.category:
                continue
                
        # Check cuisine filter
        if filters.cuisine != "Both":
            if details.get("cuisine") != filters.cuisine:
                continue
                
        # Check allergy filters
        if filters.allergies:
            allergen_found = False
            for allergy in filters.allergies:
                if allergy.lower() in details.get("allergy").lower():
                    allergen_found = True
                    break
            if allergen_found:
                continue
                
        filtered[dish_name] = details
    return filtered

@app.post("/more-like-this")
async def more_like_this(request: dict):
    """Get similar dishes when a specific dish is clicked"""
    try:

        results, first = recommend(request["dish_name"])
        return results
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=traceback.format_exc())



@app.post("/personalized-recommendations")
async def personalized_recommendations(request: dict):
    """Get personalized recommendations based on user's preference query"""
    try:

        results, first = recommend(request["preference_query"])
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
