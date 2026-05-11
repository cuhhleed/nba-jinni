# Schema Amendments to Populated Tables

This runbook describes the workflow for adding `NOT NULL` columns to tables that already contain rows. It covers the Alembic pattern, the touch points that must be updated together, the deploy choreography, and the common pitfalls.

## When to use this workflow

Both conditions must hold:

1. The amendment adds a `NOT NULL` column (or otherwise tightens a constraint that existing rows would violate).
2. The target table contains rows in any environment that will run the migration. This includes the local DB during normal development and RDS during a `loader/main.py` `action: "migrate"` invocation — the migration runs **before** the truncate at `loader/main.py:120-138`, so the table is populated when the migration sees it.

If either condition is false, use plain `op.add_column` directly — no helper, no choreography needed.

## The Alembic pattern

Use the `add_required_column` helper. It adds the column with a `server_default` so Postgres backfills existing rows atomically during `ALTER TABLE`, then immediately drops the default so future inserts must supply a real value.

Worked example (`tipoff_at` on `games`, the live example from FEATURE-006):

```python
from alembic import op
import sqlalchemy as sa
from nbajinni_shared.alembic_utils import add_required_column


def upgrade() -> None:
    add_required_column(
        "games",
        sa.Column(
            "tipoff_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_column("games", "tipoff_at")
```

### Why `server_default` matters

`server_default` becomes part of the column DDL. Postgres applies it during `ALTER TABLE` to backfill every existing row atomically — there is no "row exists without a value" window, so the `NOT NULL` constraint is satisfied immediately.

A Python-side `default=` does **not** work here. Alembic isn't issuing INSERTs during `ALTER TABLE`, so a Python default has nothing to apply to. Existing rows would be left with NULL and the `NOT NULL` constraint would fail.

The helper enforces both requirements (`nullable=False` and `server_default` must be set) and raises `ValueError` if either is missing.

## Touch-point checklist

For each amendment, all applicable touch points must be in the same PR. Missing one risks silent failure in production.

- **Model** — `shared/nbajinni_shared/models/<table>.py` — add the field as non-nullable (`Mapped[<type>]`, no `Optional`).
- **Migration** — `shared/alembic/versions/<rev>_<name>.py` — use `add_required_column` per the pattern above.
- **Parser + upsert** — `shared/nbajinni_shared/utils.py` — extract the value from the API response **and** add the field to both the `.values(...)` and `set_={...}` blocks of the relevant upsert. The `set_` update is the highest-risk omission: without it, existing rows keep their synthesized defaults forever and propagate them to RDS via the JSON export.
- **Loader date columns** — `loader/main.py:43` (`DATE_COLUMNS`) — add the column name to the relevant table's set if (and only if) the new column is a date or datetime, so the loader hydrates ISO strings from the JSON export back to Python types.

## Deploy choreography

For amendments where the new column's real values must come from external data (an API field that wasn't previously parsed, a computed value, etc.), the sequence is:

1. **Single PR** containing all touch points listed above.
2. **Run alembic locally** — existing local rows briefly hold synthesized defaults.
3. **Run the relevant local ingestion** (e.g. `ingest_schedule`) — the upsert overwrites synthesized defaults with real values.
4. **Export JSON to S3** — captures real values.
5. **Invoke loader Lambda with `{"action": "migrate"}`** — migrates RDS, truncates, reloads with real values from JSON.

End state: both DBs have the `NOT NULL` constraint with real values. Synthesized defaults are never observed by users — they exist only inside the migration window on each DB (seconds locally, milliseconds on RDS during the same Lambda invocation).

## Common pitfalls

- **Forgetting to add the field to the upsert's `set_={...}` dict.** Symptom is "every row has the same suspicious value" rather than a constraint violation. The migration succeeds, the loader succeeds, but RDS ends up with the synthesized default for every row because the local upsert only set the field on `INSERT`, not on `ON CONFLICT DO UPDATE`.
- **Forgetting `DROP DEFAULT`.** Mitigated by the helper, but worth knowing why the helper insists on it: leaving the default in place means the application can `INSERT` without specifying a value and silently get the synthesized default — a correctness landmine.
- **Using `default=` instead of `server_default=`.** A Python-side default does nothing during `ALTER TABLE`. Existing rows would be left with NULL and the `NOT NULL` constraint would fail. The helper raises `ValueError` if `server_default` is missing.
- **Running the loader's `action: "migrate"` before the local steps complete.** RDS migrates fine, but the loader's `INSERT` phase fails because the JSON export doesn't supply the new column. Loud failure, not silent — but a wasted invocation. Always finish steps 2-4 locally before invoking the loader.
