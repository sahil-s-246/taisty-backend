
class RecommendationFilter:
    @staticmethod
    def filter_recommendations(recommendations, cuisine=None, category=None, allergy=None):
        filtered = {}
        for dish_name, details in recommendations.items():
            if category != "Both":
                if details.get("category") != category:
                    continue
            if cuisine != "Both":
                if details.get("cuisine") != cuisine:
                    continue
            for each in allergy:
                if each.lower() in details.get("allergy").lower():
                    break
            filtered[dish_name] = details
        return filtered
