-- Se ejecuta una sola vez, cuando el volumen de Postgres se crea vacío.
-- El esquema del dominio no se crea aquí: eso es trabajo de Alembic, para que
-- el estado de la base de datos siempre sea reconstruible desde el repositorio.

-- Identificadores opacos para las claves primarias del dominio.
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Todo se almacena y se opera en UTC; la zona horaria del usuario es cosa del
-- navegador (decisión cerrada en el Sprint 0). Se fija en la base, no en la
-- sesión, para que valga también fuera de este contenedor.
DO $$
BEGIN
  EXECUTE format('ALTER DATABASE %I SET timezone TO ''UTC''', current_database());
END
$$;
