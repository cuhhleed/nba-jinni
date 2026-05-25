# Run with: cd <repo>/scripts && python -m pytest tests/ -v
"""Tests for scripts/lint_schema_amendments.py.

Each check gets one passing case and one failing case. Tests use tmp_path
to construct a fake repo layout and monkeypatch module-level path constants
so the lint operates on the temporary tree, not the real repo.

Monkeypatched constants (per plan Step 2, option a):
  - lint.MODELS_DIR
  - lint.UTILS_FILE
  - lint.LOADER_FILE
"""

import pathlib
import sys
import textwrap

import pytest

# Ensure the scripts/ directory is importable regardless of where pytest is run from
_SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import lint_schema_amendments as lint  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers for building fake repo trees
# ---------------------------------------------------------------------------


def write_migration(tmp_path: pathlib.Path, body: str) -> pathlib.Path:
    """Write a minimal migration file with the given upgrade() body."""
    path = tmp_path / "migration.py"
    path.write_text(
        textwrap.dedent(
            f"""\
            from alembic import op
            import sqlalchemy as sa

            def upgrade() -> None:
            {textwrap.indent(textwrap.dedent(body), '    ')}

            def downgrade() -> None:
                pass
            """
        )
    )
    return path


def write_model(models_dir: pathlib.Path, table: str, class_name: str,
                extra_fields: str = "") -> None:
    """Write a minimal SQLAlchemy model file."""
    models_dir.mkdir(parents=True, exist_ok=True)
    (models_dir / f"{table}.py").write_text(
        textwrap.dedent(
            f"""\
            from sqlalchemy.orm import Mapped, mapped_column
            from nbajinni_shared.base import Base

            class {class_name}(Base):
                __tablename__ = "{table}"

                id: Mapped[int] = mapped_column(primary_key=True)
            {textwrap.indent(textwrap.dedent(extra_fields), '    ')}
            """
        )
    )


def write_utils(utils_file: pathlib.Path, body: str) -> None:
    """Write a fake utils.py with the given body."""
    utils_file.parent.mkdir(parents=True, exist_ok=True)
    utils_file.write_text(
        textwrap.dedent(
            f"""\
            from sqlalchemy.dialects.postgresql import insert

            {textwrap.dedent(body)}
            """
        )
    )


def write_loader(loader_file: pathlib.Path, date_columns_dict: str) -> None:
    """Write a fake loader/main.py with the given DATE_COLUMNS literal."""
    loader_file.parent.mkdir(parents=True, exist_ok=True)
    loader_file.write_text(
        textwrap.dedent(
            f"""\
            DATE_COLUMNS = {date_columns_dict}
            """
        )
    )


def run_lint(
    monkeypatch,
    tmp_path: pathlib.Path,
    migration_path: pathlib.Path,
) -> tuple[int, list[str]]:
    """Run lint.main() with monkeypatched paths, capture violations, return (exit_code, violations)."""
    models_dir = tmp_path / "models"
    utils_file = tmp_path / "utils.py"
    loader_file = tmp_path / "loader" / "main.py"

    monkeypatch.setattr(lint, "MODELS_DIR", models_dir)
    monkeypatch.setattr(lint, "UTILS_FILE", utils_file)
    monkeypatch.setattr(lint, "LOADER_FILE", loader_file)

    # Collect violations by calling the core logic directly
    models = lint.build_tablename_to_model_file()
    utils = lint.parse_utils_upserts()
    dates = lint.parse_loader_date_columns()

    columns = lint.parse_migration(migration_path)

    all_violations = []
    seen_missing_model_tables: set = set()

    for col in columns:
        if col.table == "__parse_error__":
            all_violations.append(f"{migration_path}: failed to parse migration file")
            continue
        col_violations = lint.check_column(col, utils=utils, dates=dates, models=models)
        for v in col_violations:
            if (col.is_new_table and
                    f"{col.table}: create_table found" in v and
                    col.table in seen_missing_model_tables):
                continue
            if col.is_new_table and f"{col.table}: create_table found" in v:
                seen_missing_model_tables.add(col.table)
            all_violations.append(v)

    return (1 if all_violations else 0), all_violations


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


def test_passes_when_all_touchpoints_present(monkeypatch, tmp_path):
    """All four touch-points satisfied for a non-date, non-new-table column."""
    models_dir = tmp_path / "models"
    utils_file = tmp_path / "utils.py"
    loader_file = tmp_path / "loader" / "main.py"

    write_model(models_dir, "games", "Game", extra_fields="foo: Mapped[str] = mapped_column()")
    write_utils(utils_file, """\
        class Game:
            __tablename__ = "games"
        def upsert_game(session, val):
            stmt = (
                insert(Game)
                .values(foo=val)
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={"foo": val},
                )
            )
    """)
    write_loader(loader_file, '{"other": {"some_date"}}')

    mig = write_migration(tmp_path, """\
        op.add_column('games', sa.Column('foo', sa.String(), nullable=False, server_default=''))
    """)

    monkeypatch.setattr(lint, "MODELS_DIR", models_dir)
    monkeypatch.setattr(lint, "UTILS_FILE", utils_file)
    monkeypatch.setattr(lint, "LOADER_FILE", loader_file)

    exit_code, violations = run_lint(monkeypatch, tmp_path, mig)
    assert exit_code == 0, f"Expected pass, got violations: {violations}"


def test_fails_when_server_default_missing(monkeypatch, tmp_path):
    """NOT NULL column without server_default should trigger a violation."""
    models_dir = tmp_path / "models"
    utils_file = tmp_path / "utils.py"
    loader_file = tmp_path / "loader" / "main.py"

    write_model(models_dir, "games", "Game", extra_fields="foo: Mapped[str] = mapped_column()")
    utils_file.parent.mkdir(parents=True, exist_ok=True)
    utils_file.write_text("")
    write_loader(loader_file, "{}")

    # nullable=False but NO server_default
    mig = write_migration(tmp_path, """\
        op.add_column('games', sa.Column('foo', sa.String(), nullable=False))
    """)

    monkeypatch.setattr(lint, "MODELS_DIR", models_dir)
    monkeypatch.setattr(lint, "UTILS_FILE", utils_file)
    monkeypatch.setattr(lint, "LOADER_FILE", loader_file)

    exit_code, violations = run_lint(monkeypatch, tmp_path, mig)
    assert exit_code == 1
    assert any("NOT NULL column missing server_default" in v for v in violations)


def test_fails_when_not_in_model(monkeypatch, tmp_path):
    """Column added in migration but not declared in model file should fail."""
    models_dir = tmp_path / "models"
    utils_file = tmp_path / "utils.py"
    loader_file = tmp_path / "loader" / "main.py"

    # Model file exists but does NOT have 'foo' column
    write_model(models_dir, "games", "Game")
    utils_file.parent.mkdir(parents=True, exist_ok=True)
    utils_file.write_text("")
    write_loader(loader_file, "{}")

    mig = write_migration(tmp_path, """\
        op.add_column('games', sa.Column('foo', sa.String(), nullable=True))
    """)

    monkeypatch.setattr(lint, "MODELS_DIR", models_dir)
    monkeypatch.setattr(lint, "UTILS_FILE", utils_file)
    monkeypatch.setattr(lint, "LOADER_FILE", loader_file)

    exit_code, violations = run_lint(monkeypatch, tmp_path, mig)
    assert exit_code == 1
    assert any("not declared in" in v and "model touch-point" in v for v in violations)


def test_fails_when_date_type_not_in_date_columns(monkeypatch, tmp_path):
    """DateTime column not in DATE_COLUMNS should trigger a violation."""
    models_dir = tmp_path / "models"
    utils_file = tmp_path / "utils.py"
    loader_file = tmp_path / "loader" / "main.py"

    write_model(models_dir, "games", "Game", extra_fields="foo_at: Mapped[str] = mapped_column()")
    utils_file.parent.mkdir(parents=True, exist_ok=True)
    utils_file.write_text("")
    # DATE_COLUMNS["games"] exists but does NOT include "foo_at"
    write_loader(loader_file, '{"games": {"game_date"}}')

    mig = write_migration(tmp_path, """\
        op.add_column('games', sa.Column('foo_at', sa.DateTime(), nullable=True))
    """)

    monkeypatch.setattr(lint, "MODELS_DIR", models_dir)
    monkeypatch.setattr(lint, "UTILS_FILE", utils_file)
    monkeypatch.setattr(lint, "LOADER_FILE", loader_file)

    exit_code, violations = run_lint(monkeypatch, tmp_path, mig)
    assert exit_code == 1
    assert any("DATE_COLUMNS" in v and "loader touch-point" in v for v in violations)


def test_fails_when_not_in_upsert_values(monkeypatch, tmp_path):
    """Column missing from .values(...) in an existing upsert should fail."""
    models_dir = tmp_path / "models"
    utils_file = tmp_path / "utils.py"
    loader_file = tmp_path / "loader" / "main.py"

    write_model(models_dir, "games", "Game", extra_fields="foo: Mapped[str] = mapped_column()")
    # Upsert exists but .values() does NOT include 'foo'
    write_utils(utils_file, """\
        class Game:
            __tablename__ = "games"
        def upsert_game(session, val):
            stmt = (
                insert(Game)
                .values(other_col=val)
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={"other_col": val},
                )
            )
    """)
    write_loader(loader_file, "{}")

    mig = write_migration(tmp_path, """\
        op.add_column('games', sa.Column('foo', sa.String(), nullable=True))
    """)

    monkeypatch.setattr(lint, "MODELS_DIR", models_dir)
    monkeypatch.setattr(lint, "UTILS_FILE", utils_file)
    monkeypatch.setattr(lint, "LOADER_FILE", loader_file)

    exit_code, violations = run_lint(monkeypatch, tmp_path, mig)
    assert exit_code == 1
    assert any("parser touch-point" in v for v in violations)


def test_fails_when_not_in_upsert_set(monkeypatch, tmp_path):
    """Column in .values() but missing from set_={...} should fail with HIGH-RISK violation."""
    models_dir = tmp_path / "models"
    utils_file = tmp_path / "utils.py"
    loader_file = tmp_path / "loader" / "main.py"

    write_model(models_dir, "games", "Game", extra_fields="foo: Mapped[str] = mapped_column()")
    # .values() includes 'foo' but set_={} does NOT
    write_utils(utils_file, """\
        class Game:
            __tablename__ = "games"
        def upsert_game(session, val):
            stmt = (
                insert(Game)
                .values(foo=val)
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={"other_col": val},
                )
            )
    """)
    write_loader(loader_file, "{}")

    mig = write_migration(tmp_path, """\
        op.add_column('games', sa.Column('foo', sa.String(), nullable=True))
    """)

    monkeypatch.setattr(lint, "MODELS_DIR", models_dir)
    monkeypatch.setattr(lint, "UTILS_FILE", utils_file)
    monkeypatch.setattr(lint, "LOADER_FILE", loader_file)

    exit_code, violations = run_lint(monkeypatch, tmp_path, mig)
    assert exit_code == 1
    assert any("HIGH-RISK upsert touch-point" in v for v in violations)


def test_passes_when_table_has_no_upsert(monkeypatch, tmp_path):
    """If a table has no upsert in utils.py, the upsert check is silently skipped."""
    models_dir = tmp_path / "models"
    utils_file = tmp_path / "utils.py"
    loader_file = tmp_path / "loader" / "main.py"

    write_model(models_dir, "seasons", "Season", extra_fields="foo: Mapped[str] = mapped_column()")
    # utils.py has NO insert(Season) at all
    utils_file.parent.mkdir(parents=True, exist_ok=True)
    utils_file.write_text("# no upserts here\n")
    write_loader(loader_file, "{}")

    mig = write_migration(tmp_path, """\
        op.add_column('seasons', sa.Column('foo', sa.String(), nullable=True))
    """)

    monkeypatch.setattr(lint, "MODELS_DIR", models_dir)
    monkeypatch.setattr(lint, "UTILS_FILE", utils_file)
    monkeypatch.setattr(lint, "LOADER_FILE", loader_file)

    exit_code, violations = run_lint(monkeypatch, tmp_path, mig)
    assert exit_code == 0, f"Expected pass (no upsert for table), got: {violations}"


def test_create_table_skips_upsert_and_date_checks(monkeypatch, tmp_path):
    """op.create_table columns skip server_default, upsert, and DATE_COLUMNS checks."""
    models_dir = tmp_path / "models"
    utils_file = tmp_path / "utils.py"
    loader_file = tmp_path / "loader" / "main.py"

    # Model file exists and has both columns
    write_model(models_dir, "new_table", "NewTable", extra_fields="""\
        col_a: Mapped[int] = mapped_column()
        col_b: Mapped[str] = mapped_column()
    """)
    utils_file.parent.mkdir(parents=True, exist_ok=True)
    utils_file.write_text("")
    write_loader(loader_file, "{}")

    # create_table with nullable=False, no server_default, no DATE_COLUMNS entry
    mig = write_migration(tmp_path, """\
        op.create_table('new_table',
            sa.Column('col_a', sa.Integer(), nullable=False),
            sa.Column('col_b', sa.String(), nullable=False),
        )
    """)

    monkeypatch.setattr(lint, "MODELS_DIR", models_dir)
    monkeypatch.setattr(lint, "UTILS_FILE", utils_file)
    monkeypatch.setattr(lint, "LOADER_FILE", loader_file)

    exit_code, violations = run_lint(monkeypatch, tmp_path, mig)
    assert exit_code == 0, f"Expected pass for create_table, got: {violations}"


def test_skips_primary_key_and_foreign_key_columns(monkeypatch, tmp_path):
    """PK and FK columns are excluded from all checks."""
    models_dir = tmp_path / "models"
    utils_file = tmp_path / "utils.py"
    loader_file = tmp_path / "loader" / "main.py"

    # Model exists but does NOT declare 'id' or 'team_id' as AnnAssign
    write_model(models_dir, "games", "Game")
    utils_file.parent.mkdir(parents=True, exist_ok=True)
    utils_file.write_text("")
    write_loader(loader_file, "{}")

    mig = write_migration(tmp_path, """\
        op.add_column('games', sa.Column('id', sa.Integer(), primary_key=True))
        op.add_column('games', sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id')))
    """)

    monkeypatch.setattr(lint, "MODELS_DIR", models_dir)
    monkeypatch.setattr(lint, "UTILS_FILE", utils_file)
    monkeypatch.setattr(lint, "LOADER_FILE", loader_file)

    exit_code, violations = run_lint(monkeypatch, tmp_path, mig)
    assert exit_code == 0, f"Expected PK/FK to be skipped, got: {violations}"


def test_handles_add_required_column_helper(monkeypatch, tmp_path):
    """add_required_column(...) is parsed identically to op.add_column."""
    models_dir = tmp_path / "models"
    utils_file = tmp_path / "utils.py"
    loader_file = tmp_path / "loader" / "main.py"

    write_model(models_dir, "games", "Game", extra_fields="foo_at: Mapped[str] = mapped_column()")
    write_utils(utils_file, """\
        class Game:
            __tablename__ = "games"
        def upsert_game(session, val):
            stmt = (
                insert(Game)
                .values(foo_at=val)
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={"foo_at": val},
                )
            )
    """)
    # foo_at is DateTime, must appear in DATE_COLUMNS
    write_loader(loader_file, '{"games": {"foo_at"}}')

    mig = write_migration(tmp_path, """\
        add_required_column('games', sa.Column('foo_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))
    """)

    monkeypatch.setattr(lint, "MODELS_DIR", models_dir)
    monkeypatch.setattr(lint, "UTILS_FILE", utils_file)
    monkeypatch.setattr(lint, "LOADER_FILE", loader_file)

    exit_code, violations = run_lint(monkeypatch, tmp_path, mig)
    assert exit_code == 0, f"Expected add_required_column to pass, got: {violations}"


def test_no_inputs_passes_quietly(monkeypatch, capsys):
    """Calling main() with no migration args should exit 0 and print a skip message."""
    monkeypatch.setattr(sys, "argv", ["lint_schema_amendments.py"])
    exit_code = lint.main()
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "nothing to check" in captured.out


def test_malformed_migration_fails(monkeypatch, tmp_path):
    """A .py file with a syntax error should cause exit 1."""
    models_dir = tmp_path / "models"
    utils_file = tmp_path / "utils.py"
    loader_file = tmp_path / "loader" / "main.py"

    models_dir.mkdir(parents=True, exist_ok=True)
    utils_file.parent.mkdir(parents=True, exist_ok=True)
    utils_file.write_text("")
    loader_file.parent.mkdir(parents=True, exist_ok=True)
    loader_file.write_text("DATE_COLUMNS = {}")

    bad_mig = tmp_path / "bad_migration.py"
    bad_mig.write_text("def upgrade() -> None:\n    this is not valid python !!!\n")

    monkeypatch.setattr(lint, "MODELS_DIR", models_dir)
    monkeypatch.setattr(lint, "UTILS_FILE", utils_file)
    monkeypatch.setattr(lint, "LOADER_FILE", loader_file)

    exit_code, violations = run_lint(monkeypatch, tmp_path, bad_mig)
    assert exit_code == 1
    assert any("failed to parse migration file" in v for v in violations)
