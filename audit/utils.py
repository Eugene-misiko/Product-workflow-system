from .models import AuditLog

def audit_log(user, action, details=""):
    """
    create audit log entry
    """
    AuditLog.objects.create(
        user=user,
        action=action,
        details=details
    )