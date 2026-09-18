"""Gom toàn bộ model để ``Base.metadata`` biết đủ các bảng.

Bất kỳ bảng mới nào cũng phải import ở đây, nếu không ``create_all`` và
``alembic revision --autogenerate`` sẽ bỏ sót.
"""

from app.models.diagnosis import Diagnosis, DiagnosisImage
from app.models.forum import ForumComment, ForumPost, ForumPostLike, ForumPostType
from app.models.medicine import DiseaseGuide, DiseaseMedicine, Medicine
from app.models.plot import Plot, PlotStatus
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole

__all__ = [
    "Diagnosis",
    "DiagnosisImage",
    "DiseaseGuide",
    "DiseaseMedicine",
    "ForumComment",
    "ForumPost",
    "ForumPostLike",
    "ForumPostType",
    "Medicine",
    "Plot",
    "PlotStatus",
    "RefreshToken",
    "User",
    "UserRole",
]
