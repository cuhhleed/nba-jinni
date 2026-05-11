"""Alembic migration helpers.

See ``docs/SCHEMA_AMENDMENTS.md`` for the workflow these helpers support.
"""
from alembic import op
import sqlalchemy as sa


def add_required_column(table: str, column: sa.Column) -> None:
    """Add a NOT NULL column to a populated table.

    Adds the column with its server-side default so Postgres backfills
    existing rows atomically during ``ALTER TABLE``, then immediately
    drops the default so future inserts must provide a real value. The
    synthesized defaults exist only between the migration and the next
    data-rewriting operation (a truncate on RDS, or an upsert locally).

    Use this helper when:
        - The amendment adds a NOT NULL column, AND
        - The target table contains rows in any environment that will
          run the migration (true for both the local DB and RDS via the
          loader's migrate-then-load flow).

    Use ``op.add_column`` directly when:
        - The column is nullable, OR
        - The table is known to be empty when the migration runs.

    The column must declare ``nullable=False`` and a ``server_default``
    expression. Python-side ``default=`` does not apply during
    ``ALTER TABLE`` and would leave existing rows with NULL, violating
    the NOT NULL constraint.
    """
    if column.nullable is not False:
        raise ValueError(
            f"add_required_column requires nullable=False on column {column.name!r}; "
            "use op.add_column directly for nullable columns"
        )
    if column.server_default is None:
        raise ValueError(
            f"add_required_column requires server_default on column {column.name!r} "
            "to backfill existing rows during ALTER TABLE; "
            "use op.add_column directly for columns added to known-empty tables"
        )
    op.add_column(table, column)
    op.execute(f'ALTER TABLE {table} ALTER COLUMN {column.name} DROP DEFAULT')
