from typing import List

from fastapi import Depends

from app.auth.jwt_token import get_current_user
from app.custom_exceptions import NotAuthorized, UserNotVerified
from app.models import User


class AllowedUsers:
    """
    Provides permission to user types
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)):
        if current_user.role not in self.allowed_roles:
            raise NotAuthorized
        return True
