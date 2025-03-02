
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
            if allergy:
                if any(each.lower() in details.get("allergy", "").lower() for each in allergy):
                    continue
            filtered[dish_name] = details
        return filtered
