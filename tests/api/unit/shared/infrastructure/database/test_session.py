"""One engine and one session factory per database: the catalog's and each tenant's."""

from sqlalchemy.ext.asyncio import AsyncSession

from agilina_api.shared.infrastructure.database.session import (
    create_engine_for,
    create_session_factory,
)

DSN = "postgresql+psycopg://user:secret@db.test:5432/agilina_acme"


def test_an_engine_points_to_its_own_database_without_connecting():
    engine = create_engine_for(DSN)

    assert engine.url.database == "agilina_acme"
    assert engine.url.host == "db.test"


def test_two_databases_have_two_engines():
    acme = create_engine_for(DSN)
    ecomoda = create_engine_for(DSN.replace("acme", "ecomoda"))

    assert acme is not ecomoda
    assert acme.url.database != ecomoda.url.database


def test_the_sql_is_only_echoed_when_asked_for():
    assert create_engine_for(DSN).echo is False
    assert create_engine_for(DSN, echo=True).echo is True


def test_a_session_belongs_to_the_engine_of_its_factory():
    engine = create_engine_for(DSN)

    session = create_session_factory(engine)()

    assert isinstance(session, AsyncSession)
    assert session.bind is engine
