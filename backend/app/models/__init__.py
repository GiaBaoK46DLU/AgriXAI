"""Gom toàn bộ model để ``Base.metadata`` biết đủ các bảng.

Bất kỳ bảng mới nào cũng phải import ở đây, nếu không ``create_all`` và
``alembic revision --autogenerate`` sẽ bỏ sót.
"""

from app.models.diagnosis import Diagnosis
from app.models.plot import Plot, PlotStatus
from app.models.user import User, UserRole

__all__ = ["Diagnosis", "Plot", "PlotStatus", "User", "UserRole"]
