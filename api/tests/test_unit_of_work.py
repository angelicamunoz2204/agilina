"""The unit of work refuses to be used outside ``async with`` (no database needed)."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from agilina_api.shared.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def test_the_session_is_not_available_before_the_unit_of_work_is_open():
    uow = SqlAlchemyUnitOfWork(async_sessionmaker())

    with pytest.raises(RuntimeError, match="async with"):
        _ = uow.session
