class TryOnJobOutput:
    def __init__(self, job, request=None):
        self.job = job
        self.request = request

    @property
    def data(self):
        return {"job": self.job.to_json_api(request=self.request)}
