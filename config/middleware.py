from datetime import timedelta

from django.conf import settings
from django.contrib.auth import logout
from django.http import JsonResponse
from django.utils import timezone


class SessionAbsoluteTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            login_at_raw = request.session.get('login_at')
            if login_at_raw:
                login_at = timezone.datetime.fromisoformat(login_at_raw)
                if timezone.is_naive(login_at):
                    login_at = timezone.make_aware(login_at)
                timeout_seconds = getattr(settings, 'ABSOLUTE_SESSION_TIMEOUT', 28800)
                if timezone.now() - login_at > timedelta(seconds=timeout_seconds):
                    logout(request)
                    return JsonResponse({'detail': 'Session expired.'}, status=401)
        return self.get_response(request)