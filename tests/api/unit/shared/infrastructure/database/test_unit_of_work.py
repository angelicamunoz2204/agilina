"""The unit of work owns one session per ``async with`` and refuses to be used outside it."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from agilina_api.shared.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from tests.api.doubles.database import RecordingSession


def test_the_session_is_not_available_before_the_unit_of_work_is_open():
    uow = SqlAlchemyUnitOfWork(async_sessionmaker())

    with pytest.raises(RuntimeError, match="async with"):
        _ = uow.session


async def test_leaving_without_having_entered_changes_nothing():
    await SqlAlchemyUnitOfWork(async_sessionmaker()).__aexit__(None, None, None)


async def test_leaving_rolls_back_and_closes_the_session():
    session = RecordingSession()
    uow = SqlAlchemyUnitOfWork(lambda: session)  # type: ignore[arg-type,return-value]

    async with uow:
        pass

    assert session.rolled_back is True and session.closed is True


async def test_an_explicit_rollback_reaches_the_session():
    session = RecordingSession()

    async with SqlAlchemyUnitOfWork(lambda: session) as uow:  # type: ignore[arg-type,return-value]
        await uow.rollback()

    assert session.rolled_back is True
