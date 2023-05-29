
def request_should_abort(request):
    return (
        request.resource_type == "image" or ".jpg" in request.url
    )