"""Schema-amendment lint for CI.

Enforces the FEATURE-007 touch-point checklist:
  1. NOT NULL columns added in a migration must declare server_default
     (or use the add_required_column helper).
  2. New columns must be declared in shared/nbajinni_shared/models/<table>.py.
  3. New columns of type Date/DateTime/TIMESTAMP must appear in
     loader/main.py DATE_COLUMNS[<table>].
  4. New columns on a table that has an upsert in shared/nbajinni_shared/utils.py
     must appear in both the .values(...) and .on_conflict_do_update(set_={...})
     blocks of at least one such upsert.

Usage:
    python scripts/lint_schema_amendments.py <migration_file> [<migration_file> ...]

Exits 0 if all checks pass, 1 if any check fails. Prints one violation per line.

Stdlib-only (ast, pathlib, argparse, sys, re) — no project dependencies required,
so CI can invoke it without `poetry install`.

See docs/SCHEMA_AMENDMENTS.md and PENDING_FEATURES.md FEATURE-010.
"""

import argparse
import ast
import dataclasses
import pathlib
import sys
from typing import Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MODELS_DIR = REPO_ROOT / "shared/nbajinni_shared/models"
UTILS_FILE = REPO_ROOT / "shared/nbajinni_shared/utils.py"
LOADER_FILE = REPO_ROOT / "loader/main.py"

# sa.<X>() node identifiers that represent date/datetime columns
DATE_TYPE_NAMES = {"Date", "DateTime", "TIMESTAMP"}

# Column keyword arguments that indicate a column should be skipped
EXCLUDED_KWARGS = {"primary_key"}


@dataclasses.dataclass(frozen=True)
class AddedColumn:
    migration_path: pathlib.Path
    table: str
    column: str
    sql_type_name: str  # "DateTime", "String", "Integer", ...
    nullable: bool
    has_server_default: bool
    is_new_table: bool


@dataclasses.dataclass
class Upsert:
    values_keys: set
    set_keys: set


def _get_str_value(node) -> Optional[str]:
    """Extract a string constant from an AST node, or None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _is_foreign_key_arg(node) -> bool:
    """Return True if the AST node looks like sa.ForeignKey(...)."""
    if isinstance(node, ast.Call):
        func = node.func
        # sa.ForeignKey(...)
        if isinstance(func, ast.Attribute) and func.attr == "ForeignKey":
            return True
        # ForeignKey(...)
        if isinstance(func, ast.Name) and func.id == "ForeignKey":
            return True
    return False


def _extract_column_info(table_name: str, col_call: ast.Call,
                          migration_path: pathlib.Path,
                          is_new_table: bool) -> Optional[AddedColumn]:
    """Parse a sa.Column(...) call node and return an AddedColumn, or None to skip."""
    args = col_call.args
    kwargs = {kw.keyword if hasattr(kw, 'keyword') else kw.arg: kw.value
              for kw in col_call.keywords}

    # Build kwarg dict keyed by arg name
    kwarg_map = {}
    for kw in col_call.keywords:
        kwarg_map[kw.arg] = kw.value

    # Skip primary key columns
    if "primary_key" in kwarg_map:
        pk_val = kwarg_map["primary_key"]
        if isinstance(pk_val, ast.Constant) and pk_val.value is True:
            return None

    # Column name is first positional arg
    if not args:
        return None
    col_name = _get_str_value(args[0])
    if col_name is None:
        return None

    # Skip if second positional arg (or any positional arg after name) is ForeignKey
    for arg in args[1:]:
        if _is_foreign_key_arg(arg):
            return None

    # sql_type: second positional arg or 'type_' kwarg
    sql_type_name = "Unknown"
    type_node = None
    if len(args) >= 2:
        type_node = args[1]
    elif "type_" in kwarg_map:
        type_node = kwarg_map["type_"]

    if type_node is not None:
        if isinstance(type_node, ast.Call):
            func = type_node.func
            if isinstance(func, ast.Attribute):
                sql_type_name = func.attr
            elif isinstance(func, ast.Name):
                sql_type_name = func.id
        elif isinstance(type_node, ast.Attribute):
            sql_type_name = type_node.attr
        elif isinstance(type_node, ast.Name):
            sql_type_name = type_node.id

    # nullable: kwarg, default True
    nullable = True
    if "nullable" in kwarg_map:
        nval = kwarg_map["nullable"]
        if isinstance(nval, ast.Constant):
            nullable = bool(nval.value)

    # server_default: present if kwarg exists and is not None constant
    has_server_default = "server_default" in kwarg_map
    if has_server_default:
        sd_val = kwarg_map["server_default"]
        if isinstance(sd_val, ast.Constant) and sd_val.value is None:
            has_server_default = False

    return AddedColumn(
        migration_path=migration_path,
        table=table_name,
        column=col_name,
        sql_type_name=sql_type_name,
        nullable=nullable,
        has_server_default=has_server_default,
        is_new_table=is_new_table,
    )


def _find_upgrade_body(tree: ast.Module) -> Optional[list]:
    """Return the body statements of the upgrade() function, or None."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "upgrade":
            return node.body
    return None


def _parse_call_in_stmt(stmt) -> Optional[ast.Call]:
    """Extract an ast.Call from a statement that is a bare Expr(Call(...))."""
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        return stmt.value
    return None


def _get_func_name(call: ast.Call) -> str:
    """Return the dotted name of a Call's function, e.g. 'op.add_column'."""
    func = call.func
    if isinstance(func, ast.Attribute):
        return f"{_get_func_name_from_node(func.value)}.{func.attr}"
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _get_func_name_from_node(node) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_get_func_name_from_node(node.value)}.{node.attr}"
    return ""


def _find_column_calls_in_args(args) -> list:
    """Find all sa.Column(...) call nodes in a list of AST args."""
    cols = []
    for arg in args:
        if isinstance(arg, ast.Call):
            name = _get_func_name(arg)
            if name in ("sa.Column", "Column"):
                cols.append(arg)
    return cols


def parse_migration(path: pathlib.Path) -> list:
    """Parse a migration file and return a list of AddedColumn instances.

    Handles three patterns:
      - op.add_column(<table>, sa.Column(...))
      - add_required_column(<table>, sa.Column(...))
      - op.create_table(<table>, sa.Column(...), sa.Column(...), ...)
    """
    try:
        source = path.read_text()
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"{path}: failed to parse (SyntaxError): {e}")
        # Return a sentinel: a single AddedColumn with empty column name signals parse error
        return [AddedColumn(
            migration_path=path,
            table="__parse_error__",
            column="__parse_error__",
            sql_type_name="Unknown",
            nullable=True,
            has_server_default=False,
            is_new_table=False,
        )]

    upgrade_body = _find_upgrade_body(tree)
    if upgrade_body is None:
        return []

    results = []

    for stmt in upgrade_body:
        call = _parse_call_in_stmt(stmt)
        if call is None:
            # May be an assignment or other statement — skip
            continue

        func_name = _get_func_name(call)

        if func_name == "op.add_column":
            # op.add_column(<table_str>, sa.Column(...))
            if len(call.args) < 2:
                continue
            table_name = _get_str_value(call.args[0])
            if table_name is None:
                continue
            col_arg = call.args[1]
            if not isinstance(col_arg, ast.Call):
                continue
            col = _extract_column_info(table_name, col_arg, path, is_new_table=False)
            if col is not None:
                results.append(col)

        elif func_name == "add_required_column":
            # add_required_column(<table_str>, sa.Column(...))
            if len(call.args) < 2:
                continue
            table_name = _get_str_value(call.args[0])
            if table_name is None:
                continue
            col_arg = call.args[1]
            if not isinstance(col_arg, ast.Call):
                continue
            col = _extract_column_info(table_name, col_arg, path, is_new_table=False)
            if col is not None:
                results.append(col)

        elif func_name == "op.create_table":
            # op.create_table(<table_str>, sa.Column(...), sa.Column(...), ...)
            if not call.args:
                continue
            table_name = _get_str_value(call.args[0])
            if table_name is None:
                continue
            for arg in call.args[1:]:
                if not isinstance(arg, ast.Call):
                    continue
                arg_func = _get_func_name(arg)
                if arg_func not in ("sa.Column", "Column"):
                    continue
                col = _extract_column_info(table_name, arg, path, is_new_table=True)
                if col is not None:
                    results.append(col)

    return results


def build_tablename_to_model_file() -> dict:
    """Scan MODELS_DIR/*.py and return {tablename: path} for each model class found.

    Finds ClassDef nodes with a __tablename__ = "<str>" assignment at class scope.
    """
    mapping = {}
    for model_file in MODELS_DIR.glob("*.py"):
        try:
            tree = ast.parse(model_file.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for stmt in node.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                for target in stmt.targets:
                    if (isinstance(target, ast.Name) and
                            target.id == "__tablename__" and
                            isinstance(stmt.value, ast.Constant)):
                        tablename = stmt.value.value
                        if isinstance(tablename, str):
                            mapping[tablename] = model_file
    return mapping


def model_has_column(model_path: pathlib.Path, col_name: str) -> bool:
    """Return True if the model file contains a `<col_name>: Mapped[...]` AnnAssign."""
    try:
        tree = ast.parse(model_path.read_text())
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and target.id == col_name:
                return True
    return False


def parse_utils_upserts() -> dict:
    """Scan UTILS_FILE for insert(<Model>).values(...).on_conflict_do_update(set_={...}).

    Returns {tablename: [Upsert(values_keys, set_keys), ...]}

    We collect the tablename by mapping the Model class name to its __tablename__
    via build_tablename_to_model_file().
    """
    # Build class name -> tablename map by reading model files
    classname_to_table = {}
    for model_file in MODELS_DIR.glob("*.py"):
        try:
            tree = ast.parse(model_file.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for stmt in node.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                for target in stmt.targets:
                    if (isinstance(target, ast.Name) and
                            target.id == "__tablename__" and
                            isinstance(stmt.value, ast.Constant) and
                            isinstance(stmt.value.value, str)):
                        classname_to_table[node.name] = stmt.value.value

    try:
        utils_source = UTILS_FILE.read_text()
        utils_tree = ast.parse(utils_source)
    except (OSError, SyntaxError):
        return {}

    result: dict = {}

    # Walk the AST looking for call chains that include insert(<Model>)
    # We look for ast.Call nodes whose function is an Attribute chain ending in
    # on_conflict_do_update or on_conflict_do_nothing, and trace back through .values()
    # to find the insert() root.
    #
    # Strategy: find every Call node in the tree, check if it represents
    # insert(<Model>) directly. Then walk forward through chained Attribute calls
    # to find .values() and .on_conflict_do_update() in the same chain.
    #
    # Since Python's AST represents method chains inside-out (the outermost call
    # is the innermost in the tree when reading left to right), we walk all Call
    # nodes and for each one check: is this an insert(<Model>) call? If so,
    # climb up through parent calls.
    #
    # Simpler alternative: collect all "interesting" call chains by walking all
    # ast.Call nodes, building a flat representation of each chain.

    class UpsertVisitor(ast.NodeVisitor):
        def __init__(self):
            # collected: list of (table_name, values_keys, set_keys)
            self.upserts = []

        def visit_Call(self, node: ast.Call):
            # Look for on_conflict_do_update calls at the end of a chain
            func = node.func
            if (isinstance(func, ast.Attribute) and
                    func.attr == "on_conflict_do_update"):
                # Walk the chain to find insert(...) and .values(...) calls
                self._handle_on_conflict_chain(node)
            self.generic_visit(node)

        def _handle_on_conflict_chain(self, on_conflict_call: ast.Call):
            # Extract set_={...} from this call's kwargs
            set_keys = set()
            for kw in on_conflict_call.keywords:
                if kw.arg == "set_":
                    set_keys = self._extract_dict_keys(kw.value)

            # Walk backward through the chain: the value of on_conflict_call.func
            # is <expr>.on_conflict_do_update, so we look at on_conflict_call.func.value
            chain_node = on_conflict_call.func.value  # type: ignore[union-attr]

            values_keys = set()
            table_name = None

            # Traverse the chain until we find insert(Model)
            while isinstance(chain_node, ast.Call):
                chain_func = chain_node.func
                if isinstance(chain_func, ast.Attribute):
                    method = chain_func.attr
                    if method == "values":
                        values_keys = self._extract_call_keys(chain_node)
                    # Move further back in the chain
                    chain_node = chain_func.value
                elif isinstance(chain_func, ast.Name) and chain_func.id == "insert":
                    # Found insert(Model) — resolve tablename
                    if chain_node.args:
                        model_arg = chain_node.args[0]
                        if isinstance(model_arg, ast.Name):
                            table_name = classname_to_table.get(model_arg.id)
                    break
                else:
                    break

            if table_name is not None:
                self.upserts.append((table_name, values_keys, set_keys))

        def _extract_dict_keys(self, node) -> set:
            """Extract string keys from an ast.Dict node."""
            keys = set()
            if isinstance(node, ast.Dict):
                for k in node.keys:
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        keys.add(k.value)
            return keys

        def _extract_call_keys(self, call_node: ast.Call) -> set:
            """Extract kwarg names from a .values(...) call."""
            keys = set()
            for kw in call_node.keywords:
                if kw.arg is not None:
                    keys.add(kw.arg)
            return keys

    visitor = UpsertVisitor()
    visitor.visit(utils_tree)

    for table_name, values_keys, set_keys in visitor.upserts:
        upsert = Upsert(values_keys=values_keys, set_keys=set_keys)
        result.setdefault(table_name, []).append(upsert)

    return result


def parse_loader_date_columns() -> dict:
    """Parse loader/main.py to extract the DATE_COLUMNS dict literal.

    Returns {table_name: set_of_column_names}.
    """
    try:
        source = LOADER_FILE.read_text()
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "DATE_COLUMNS":
                if isinstance(node.value, ast.Dict):
                    result = {}
                    for key_node, val_node in zip(node.value.keys, node.value.values):
                        if not (isinstance(key_node, ast.Constant) and
                                isinstance(key_node.value, str)):
                            continue
                        table_key = key_node.value
                        # value should be a set literal or dict
                        col_names = set()
                        if isinstance(val_node, ast.Set):
                            for elt in val_node.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    col_names.add(elt.value)
                        result[table_key] = col_names
                    return result

    return {}


def _get_model_class_name_for_table(table_name: str) -> str:
    """Return the best-guess model class name for error messages."""
    # Try to find the class name from the model file
    table_to_model = build_tablename_to_model_file()
    model_path = table_to_model.get(table_name)
    if model_path is None:
        # Fall back to TitleCase table name
        return "".join(part.title() for part in table_name.split("_"))

    try:
        tree = ast.parse(model_path.read_text())
    except (OSError, SyntaxError):
        return "".join(part.title() for part in table_name.split("_"))

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign):
                continue
            for target in stmt.targets:
                if (isinstance(target, ast.Name) and
                        target.id == "__tablename__" and
                        isinstance(stmt.value, ast.Constant) and
                        stmt.value.value == table_name):
                    return node.name

    return "".join(part.title() for part in table_name.split("_"))


def check_column(
    added: AddedColumn,
    *,
    utils: dict,
    dates: dict,
    models: dict,
) -> list:
    """Orchestrate the four FEATURE-007 checks for a single added column.

    Returns a list of violation strings (empty list means pass).

    Checks skipped per Locked Decisions:
    - is_new_table: skip server_default, upsert, and DATE_COLUMNS checks;
      still verify model file exists.
    - Tables with no upsert in utils.py: skip the upsert checks silently.
    """
    violations = []
    migration_path = added.migration_path
    table = added.table
    column = added.column

    # Check 1 — server_default required for NOT NULL on existing tables
    if not added.is_new_table and not added.nullable and not added.has_server_default:
        violations.append(
            f"{migration_path}: {table}.{column}: NOT NULL column missing "
            f"server_default (FEATURE-007: migration touch-point)"
        )

    # Check 2 — model file must declare the column
    model_path = models.get(table)
    if model_path is None:
        if added.is_new_table:
            # For new tables, this is a "model file missing" violation (checked once
            # per table, not per column — but we emit it per column since we don't
            # have a dedup mechanism here; the caller deduplicates)
            violations.append(
                f"{migration_path}: {table}: create_table found but no "
                f"shared/nbajinni_shared/models/{table}.py exists "
                f"(FEATURE-007: model touch-point)"
            )
        else:
            violations.append(
                f"{migration_path}: {table}.{column}: not declared in "
                f"shared/nbajinni_shared/models/{table}.py "
                f"(FEATURE-007: model touch-point)"
            )
    else:
        if not model_has_column(model_path, column):
            violations.append(
                f"{migration_path}: {table}.{column}: not declared in "
                f"shared/nbajinni_shared/models/{table}.py "
                f"(FEATURE-007: model touch-point)"
            )

    # Check 3 — DATE_COLUMNS check for date/datetime types (skip for new tables)
    if not added.is_new_table and added.sql_type_name in DATE_TYPE_NAMES:
        table_date_cols = dates.get(table, set())
        if column not in table_date_cols:
            violations.append(
                f"{migration_path}: {table}.{column}: date/datetime column missing "
                f"from loader/main.py DATE_COLUMNS[{table!r}] "
                f"(FEATURE-007: loader touch-point — see ADR-005)"
            )

    # Check 4 — upsert checks (skip for new tables)
    if not added.is_new_table:
        table_upserts = utils.get(table)
        if table_upserts is not None:
            # Table has at least one upsert — both .values() and set_={} must include column
            in_any_values = any(column in u.values_keys for u in table_upserts)
            in_any_set = any(column in u.set_keys for u in table_upserts)

            if not in_any_values:
                model_class = _get_model_class_name_for_table(table)
                violations.append(
                    f"{migration_path}: {table}.{column}: not present in any "
                    f"insert({model_class}).values(...) in "
                    f"shared/nbajinni_shared/utils.py "
                    f"(FEATURE-007: parser touch-point)"
                )

            if not in_any_set:
                model_class = _get_model_class_name_for_table(table)
                violations.append(
                    f"{migration_path}: {table}.{column}: not present in any "
                    f".on_conflict_do_update(set_={{...}}) for insert({model_class}) in "
                    f"shared/nbajinni_shared/utils.py "
                    f"(FEATURE-007: HIGH-RISK upsert touch-point — synthesized defaults will persist)"
                )
        # If table_upserts is None, the table has no upsert — skip silently

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Schema-amendment lint: verify FEATURE-007 touch-points."
    )
    parser.add_argument(
        "migrations",
        nargs="*",
        type=pathlib.Path,
        help="Migration file paths to lint.",
    )
    args = parser.parse_args()

    if not args.migrations:
        print("schema-amendment lint: no migration files provided, nothing to check.")
        return 0

    # Build shared state once — avoids re-reading files per column
    models = build_tablename_to_model_file()
    utils = parse_utils_upserts()
    dates = parse_loader_date_columns()

    all_violations = []

    for migration_path in args.migrations:
        migration_path = migration_path.resolve()
        columns = parse_migration(migration_path)

        # Detect parse errors (sentinel column name)
        for col in columns:
            if col.table == "__parse_error__":
                all_violations.append(f"{migration_path}: failed to parse migration file")

        real_columns = [c for c in columns if c.table != "__parse_error__"]

        # Deduplicate model-missing violations for create_table (one per table)
        seen_missing_model_tables = set()

        for col in real_columns:
            col_violations = check_column(col, utils=utils, dates=dates, models=models)
            for v in col_violations:
                # Deduplicate "create_table found but no model" violations per table
                if (col.is_new_table and
                        f"{col.table}: create_table found" in v and
                        col.table in seen_missing_model_tables):
                    continue
                if col.is_new_table and f"{col.table}: create_table found" in v:
                    seen_missing_model_tables.add(col.table)
                all_violations.append(v)

    for violation in all_violations:
        print(violation)

    return 1 if all_violations else 0


if __name__ == "__main__":
    sys.exit(main())
