import time
from django.http import JsonResponse

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.requests = {}

    def __call__(self, request):
        if request.path.startswith('/chatbot/api/'):
            ip = request.META.get('REMOTE_ADDR')
            current_time = time.time()
            
            if ip in self.requests:
                last_request_time, count = self.requests[ip]
                if current_time - last_request_time < 60:  # 1 minute
                    if count >= 30:  # Max 30 requests per minute
                        return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
                    self.requests[ip] = (last_request_time, count + 1)
                else:
                    self.requests[ip] = (current_time, 1)
            else:
                self.requests[ip] = (current_time, 1)

        response = self.get_response(request)
        return response