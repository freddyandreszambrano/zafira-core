from core.scraper.api.v1.catalog.outputs import ProductOutput


class ErrorOutput:
    def __init__(self, error):
        self.error = error

    @property
    def data(self):
        return {"error": self.error}


class RecommendOutput:
    def __init__(self, data, outfit_list, request=None):
        self.data = data
        self.outfit_list = outfit_list
        self.request = request

    @property
    def data_response(self):
        return {
            "occasion": self.data["occasion"],
            "gender": self.data.get("gender", "hombre"),
            "store": self.data.get("store", "all"),
            "outfits": [
                {
                    "top": ProductOutput(outfit["top"], request=self.request).data,
                    "bottom": ProductOutput(outfit["bottom"], request=self.request).data
                    if outfit["bottom"]
                    else None,
                }
                for outfit in self.outfit_list
            ],
        }
