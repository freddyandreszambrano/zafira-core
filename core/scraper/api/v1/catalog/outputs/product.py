class ProductOutput:
    def __init__(self, product, request=None):
        self.product = product
        self.request = request

    @property
    def data(self):
        return self.product.to_json_api(request=self.request)


class ProductListOutput:
    def __init__(self, products, request=None):
        self.products = products
        self.request = request

    @property
    def data(self):
        return [product.to_json_api(request=self.request) for product in self.products]


class ProductLiveOutput:
    def __init__(self, product, live, request=None):
        self.product = product
        self.live = live
        self.request = request

    @property
    def data(self):
        return {
            "live": self.live,
            "product": self.product.to_json_api(request=self.request),
        }
