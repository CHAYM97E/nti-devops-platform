"""
Answer infrastructure endpoints before Django's ALLOWED_HOSTS check.

Kubernetes probes, the ALB health check and Prometheus all call the pod by
its IP address (Host: 10.0.10.37:8000). That IP is not in ALLOWED_HOSTS, so
CommonMiddleware would answer 400 and Kubernetes would kill healthy pods.
Rather than weaken ALLOWED_HOSTS to "*" for everyone, we short-circuit only
these three read-only paths. Must be the FIRST middleware in settings.
"""
from django_prometheus.exports import ExportToDjangoView

from . import views

_ROUTES = {
    "/health/": views.health,
    "/health/ready/": views.ready,
    "/metrics": ExportToDjangoView,
}


class InfraEndpointsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        view = _ROUTES.get(request.path_info)
        if view is not None and request.method == "GET":
            return view(request)
        return self.get_response(request)
