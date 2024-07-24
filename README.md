## Dish Recommender

- Connect to a weaviate collection in your weaviate cloud's sandbox, in this case FoodRecommend.
    There are two steps in this recommendation
     - Retrieval: Semantically search through the data wrt the query
     - Ranking: Use Gemini Flash API to rank the data