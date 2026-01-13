import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from .security import AccessLogging, SessionSecurity

User = get_user_model()
logger = logging.getLogger('theracare.middleware')
audit_logger = logging.getLogger('audit')


class HIPAAComplianceMiddleware(MiddlewareMixin):
    """Middleware to enforce HIPAA compliance requirements"""
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Process incoming requests for HIPAA compliance"""
        
        # Record request start time for performance monitoring
        request.start_time = time.time()
        
        # Get client IP address
        request.client_ip = self.get_client_ip(request)
        
        # Check session timeout for authenticated users
        if request.user.is_authenticated:
            session_key = request.session.session_key
            if session_key:
                last_activity = SessionSecurity.get_session_activity(session_key)
                if last_activity and SessionSecurity.is_session_expired(last_activity):
                    # Force logout for expired session
                    request.session.flush()
                    AccessLogging.log_failed_access(
                        user_id=str(request.user.id),
                        resource=request.path,
                        ip_address=request.client_ip,
                        reason="Session expired"
                    )
                    return HttpResponse(
                        json.dumps({"error": "Session expired"}),
                        status=401,
                        content_type="application/json"
                    )
                
                # Update session activity
                SessionSecurity.update_session_activity(session_key)
        
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Process outgoing responses for HIPAA compliance"""
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add HIPAA compliance headers
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response
    
    def get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address considering proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip


class AuditMiddleware(MiddlewareMixin):
    """Middleware for comprehensive audit logging"""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.sensitive_paths = [
            '/api/patients/',
            '/api/soap-notes/',
            '/api/messages/',
            '/api/billing/',
        ]
    
    def process_request(self, request: HttpRequest) -> None:
        """Log request for audit purposes"""
        
        # Skip audit logging for certain paths
        if self.should_skip_audit(request.path):
            return
        
        # Prepare audit data
        audit_data = {
            'timestamp': datetime.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'user_id': str(request.user.id) if request.user.is_authenticated else None,
            'ip_address': getattr(request, 'client_ip', 'unknown'),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],  # Limit length
            'query_params': dict(request.GET),
            'content_type': request.content_type,
        }
        
        # Add POST data for sensitive endpoints (encrypted)
        if request.method in ['POST', 'PUT', 'PATCH'] and self.is_sensitive_path(request.path):
            try:
                if request.content_type == 'application/json':
                    body_data = json.loads(request.body) if request.body else {}
                    # Mask sensitive fields
                    body_data = self.mask_sensitive_fields(body_data)
                    audit_data['request_body'] = body_data
            except json.JSONDecodeError:
                audit_data['request_body'] = 'Invalid JSON'
        
        # Store audit data in request for later use
        request.audit_data = audit_data
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Log response for audit purposes"""
        
        if not hasattr(request, 'audit_data'):
            return response
        
        # Complete audit data
        audit_data = request.audit_data
        audit_data.update({
            'response_status': response.status_code,
            'response_time': time.time() - getattr(request, 'start_time', time.time()),
        })
        
        # Log based on response status
        if response.status_code >= 400:
            audit_logger.error(f"HTTP_ERROR: {json.dumps(audit_data)}")
        elif self.is_sensitive_path(request.path):
            audit_logger.info(f"PHI_REQUEST: {json.dumps(audit_data)}")
        else:
            audit_logger.info(f"REQUEST: {json.dumps(audit_data)}")
        
        return response
    
    def is_sensitive_path(self, path: str) -> bool:
        """Check if path contains sensitive PHI data"""
        return any(sensitive_path in path for sensitive_path in self.sensitive_paths)
    
    def should_skip_audit(self, path: str) -> bool:
        """Determine if path should skip audit logging"""
        skip_paths = [
            '/api/health/',
            '/admin/jsi18n/',
            '/static/',
            '/media/',
        ]
        return any(skip_path in path for skip_path in skip_paths)
    
    def mask_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive fields in request data"""
        if not isinstance(data, dict):
            return data
        
        sensitive_fields = [
            'password', 'ssn', 'social_security_number',
            'credit_card', 'bank_account', 'routing_number',
            'medical_record_number', 'insurance_id'
        ]
        
        masked_data = data.copy()
        for key, value in masked_data.items():
            if isinstance(key, str) and key.lower() in sensitive_fields:
                masked_data[key] = '***MASKED***'
            elif isinstance(value, dict):
                masked_data[key] = self.mask_sensitive_fields(value)
        
        return masked_data


class RateLimitMiddleware(MiddlewareMixin):
    """Rate limiting middleware for security"""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.rate_limits = {
            'login': {'requests': 5, 'window': 300},  # 5 attempts per 5 minutes
            'api': {'requests': 1000, 'window': 3600},  # 1000 requests per hour
            'sensitive': {'requests': 100, 'window': 3600},  # 100 sensitive requests per hour
        }
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Check rate limits for incoming requests"""
        
        client_ip = getattr(request, 'client_ip', 'unknown')
        
        # Determine rate limit type
        limit_type = 'api'
        if 'login' in request.path:
            limit_type = 'login'
        elif any(sensitive_path in request.path for sensitive_path in ['/patients/', '/soap-notes/']):
            limit_type = 'sensitive'
        
        # Check rate limit
        if self.is_rate_limited(client_ip, limit_type, request.user):
            AccessLogging.log_failed_access(
                user_id=str(request.user.id) if request.user.is_authenticated else None,
                resource=request.path,
                ip_address=client_ip,
                reason="Rate limit exceeded"
            )
            
            return HttpResponse(
                json.dumps({"error": "Rate limit exceeded"}),
                status=429,
                content_type="application/json"
            )
        
        return None
    
    def is_rate_limited(self, client_ip: str, limit_type: str, user) -> bool:
        """Check if client has exceeded rate limit"""
        
        rate_config = self.rate_limits.get(limit_type, self.rate_limits['api'])
        
        # Create cache key
        if user.is_authenticated:
            cache_key = f"rate_limit_{limit_type}_{user.id}"
        else:
            cache_key = f"rate_limit_{limit_type}_{client_ip}"
        
        # Get current count
        current_count = cache.get(cache_key, 0)
        
        # Check if limit exceeded
        if current_count >= rate_config['requests']:
            return True
        
        # Increment counter
        cache.set(cache_key, current_count + 1, timeout=rate_config['window'])
        
        return False


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware to add security headers"""
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Add comprehensive security headers"""
        
        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' https:",
            "connect-src 'self' wss: ws:",
            "media-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        
        response['Content-Security-Policy'] = "; ".join(csp_directives)
        
        # Additional security headers
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response