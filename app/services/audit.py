from flask import request

from ..extensions import db
from ..models import AuditLog


def record_action(user_id, action):
    db.session.add(
        AuditLog(
            user_id=user_id,
            action=action,
            ip_address=request.remote_addr,
        )
    )
