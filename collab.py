# collab.py
from sqlalchemy.orm import Session
from models import Order
from collections import defaultdict
import numpy as np
from typing import List
from pynndescent import NNDescent

# Step 1: Retrieve user history from DB
def get_user_history(db: Session, user_id: str):
    return db.query(Order).filter(Order.user_id == user_id).all()

# Step 2: Build user-item interaction matrix (in-memory)
def build_interaction_matrix(order_data):
    users = list(set([row.user_id for row in order_data]))
    dishes = list(set([row.dish_id for row in order_data]))
    user_index = {u: i for i, u in enumerate(users)}
    dish_index = {d: i for i, d in enumerate(dishes)}

    matrix = np.zeros((len(users), len(dishes)))
    for row in order_data:
        u_idx = user_index[row.user_id]
        d_idx = dish_index[row.dish_id]
        matrix[u_idx][d_idx] = row.order_count + row.feedback_score

    return matrix, users, dishes, user_index, dish_index

# Step 3: Recommend items for a user using PyNNDescent
def get_collab_recommendations(user_id: str, db: Session, top_n: int = 5) -> List[str]:
    orders = db.query(Order).all()
    matrix, users, dishes, user_index, dish_index = build_interaction_matrix(orders)

    if user_id not in user_index:
        return []

    index = NNDescent(matrix, metric='cosine')
    user_vec = matrix[user_index[user_id]].reshape(1, -1)
    neighbors, distances = index.query(user_vec, k=6)  # 1st will be the user themselves

    scores = defaultdict(float)
    for idx, dist in zip(neighbors[0][1:], distances[0][1:]):  # skip self
        sim = 1 - dist
        for d_idx, score in enumerate(matrix[idx]):
            if score > 0 and matrix[user_index[user_id]][d_idx] == 0:
                scores[dishes[d_idx]] += sim * score

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [dish for dish, _ in sorted_scores[:top_n]]

# Step 4: Fallback to content-based if no history exists
def use_cb_for_user(query: str):
    from query import recommend  # Avoid circular import
    results, _ = recommend(query)
    return results
