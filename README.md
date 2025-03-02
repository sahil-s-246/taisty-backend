## Dish Recommender

- Connect to a weaviate collection in your weaviate cloud's sandbox, in this case FoodRecommend.
    There are two steps in this recommendation
     - Retrieval: Semantically search through the data wrt the query
     - Ranking: Use Gemini Flash API to rank the data
## Steps to Run Locally

- ```pip install -r requirements.txt```
- ```python api.py```

Ensure that all environment variables are present, according to .env.sample