"""Importing this package registers every model on Base.metadata.

SQLAlchemy only creates the tables whose mappers have been imported, so anything that calls
create_all must import this package first — otherwise it silently creates nothing.
"""

from aitsm.models import (  # noqa: F401
    change,
    kb_article,
    kb_feedback,
    service_catalog,
    ticket,
    ticket_comment,
    user,
)
