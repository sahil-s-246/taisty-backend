import numpy as np
import json
from collections import defaultdict
from typing import List
from pynndescent import NNDescent

# Load menu dishes
with open("updated_data.json", "r") as f:
    menu_data = json.load(f)

dish_names = [item["dish"] for item in menu_data]

# Mock Order class
class Order:
    def __init__(self, user_id, dish_id, order_count, feedback_score):
        self.user_id = user_id
        self.dish_id = dish_id
        self.order_count = order_count
        self.feedback_score = feedback_score

# Mock DB session
class MockSession:
    def __init__(self, data):
        self.data = data

    def all(self):
        return self.data

# Step 1: Build user-item matrix
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

# Step 2: Item-Based CF
def get_item_based_recommendations(user_id: str, db: MockSession, top_n: int = 5) -> List[str]:
    orders = db.all()
    matrix, users, dishes, user_index, dish_index = build_interaction_matrix(orders)

    if user_id not in user_index:
        return use_cb_for_user("Paneer Butter Masala")

    item_matrix = matrix.T  # Now items (dishes) are rows
    index = NNDescent(item_matrix, metric='cosine')

    # Get indices of items this user interacted with
    user_vec = matrix[user_index[user_id]]
    interacted_indices = np.where(user_vec > 0)[0]

    scores = defaultdict(float)
    for d_idx in interacted_indices:
        neighbors, distances = index.query(item_matrix[d_idx].reshape(1, -1), k=6)
        for n_idx, dist in zip(neighbors[0][1:], distances[0][1:]):  # skip self
            if user_vec[n_idx] == 0:  # Only recommend unseen items
                sim = 1 - dist
                scores[dishes[n_idx]] += sim * item_matrix[n_idx][user_index[user_id]]

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [dish for dish, _ in sorted_scores[:top_n]]

# Fallback to CB
def use_cb_for_user(query: str):
    print("Fallback to content-based recommendations for:", query)
    return ["Rajma", "Khichdi", "Raita"]

# ------------------- Test Setup -------------------
if __name__=="__main__":
    mock_data = [
        Order("user1", "Paneer Butter Masala", 4, 2),
        Order("user1", "Chole Bhature", 2, 1),
        Order("user2", "Chicken Biryani", 3, 2),
        Order("user2", "Rogan Josh", 4, 1),
        Order("user3", "Paneer Butter Masala", 1, 1),
        Order("user3", "Gulab Jamun", 5, 2),
        Order("user4", "Masala Dosa", 3, 2),
        Order("user4", "Aloo Gobi", 2, 1),
        Order("user5", "Samosa", 2, 2),
        Order("user5", "Lassi", 4, 1),
    ]

    db = MockSession(mock_data)

    print("\n🎯 Item-Based Recommendations for user2:")
    print(get_item_based_recommendations("user2", db))

    print("\n🆕 New user fallback:")
    print(get_item_based_recommendations("user_new", db))
