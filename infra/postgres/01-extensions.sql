-- Runs only once, when the Postgres volume is created empty.
-- The domain schema is not created here: that is Alembic's job, so the state
-- of the database is always reconstructible from the repository.

-- Opaque identifiers for the domain primary keys.
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Everything is stored and operated in UTC; the user's time zone is the
-- browser's concern (decision closed in Sprint 0). It is set on the database,
-- not on the session, so it also holds outside this container.
DO $$
BEGIN
  EXECUTE format('ALTER DATABASE %I SET timezone TO ''UTC''', current_database());
END
$$;
