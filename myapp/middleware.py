from django.utils.deprecation import MiddlewareMixin

class CacheControlMiddleware(MiddlewareMixin):
    """
    Middleware to enforce strict no-cache headers on all HTTP responses.
    This ensures that browsers never store or display cached pages when users
    click the browser Back button after logging out.
    """
    def process_response(self, request, response):
        if request.user.is_authenticated or request.path.startswith('/admin-') or request.path.startswith('/farmer-') or request.path.startswith('/consumer-'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response
