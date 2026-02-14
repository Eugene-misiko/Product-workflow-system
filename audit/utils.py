from .models import AuditLog

def audit_log(user, action, details=""):
    """
    Create an audit log entry for tracking
    important admin/system actions.    
    """
    AuditLog.objects.create(
        user=user,
        action=action,
        details=details
    )