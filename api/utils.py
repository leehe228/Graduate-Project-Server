from pathlib import Path
import sqlite3
import pandas as pd
import types
from typing import Optional, Tuple, List, Union

import matplotlib
matplotlib.use("Agg")   # non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

def file_to_sqlite(
    file_path: str | Path,
    db_path: str | Path,
    if_exists: str = "replace",
    chunksize: Optional[int] = None
) -> Tuple[Path, str]:
    """
    Load a CSV/Excel file into SQLite using an auto-generated table name (table1, table2 …).

    Returns
    -------
    (db_path, schema_text)
    """
    file_path = Path(file_path)
    db_path   = Path(db_path)

    # ── 1. read file into DataFrame ──────────────────────────
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(file_path)
    elif suffix in {".xls", ".xlsx"}:
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Extension must be .csv / .xls / .xlsx")

    # ── 2. decide table name (table1, table2, …) ─────────────
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing = {r[0] for r in cur.fetchall()}
        idx = 1
        while f"table{idx}" in existing:
            idx += 1
        table_name = f"table{idx}"

        # ── 3. write DataFrame ───────────────────────────────
        df.to_sql(table_name, conn,
                  if_exists=if_exists, index=False, chunksize=chunksize)

        # ── 4. build human-readable schema text ──────────────
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [r[0] for r in cur.fetchall()]

        lines = [f"Database: {db_path.name}", "Tables:"]
        for tbl in tables:
            cur.execute(f"PRAGMA table_info('{tbl}');")
            cols = cur.fetchall()     # (cid, name, type, notnull, dflt_value, pk)
            col_defs = []
            for _, name, ctype, notnull, default, pk in cols:
                bits = [name, ctype]
                if notnull:              bits.append("NOT NULL")
                if default is not None:  bits.append(f"DEFAULT {default}")
                if pk:                   bits.append("PRIMARY KEY")
                col_defs.append(" ".join(bits))
            lines.append(f"- {tbl}: " + ", ".join(col_defs))

    return db_path, "\n".join(lines)


def execute_sqlite_query(
    db_path: Union[str, Path],
    query: str,
    return_dataframe: bool = True
) -> Union[pd.DataFrame, List[Tuple], int]:
    """
    Execute a SQL query against a SQLite database file and return the result.

    Args:
        db_path: Path to the .db or .sqlite file.
        query:   The SQL statement to execute (SELECT, INSERT, UPDATE, etc.).
        return_dataframe: 
            - If True and the query is a SELECT, returns a pandas.DataFrame.
            - If False and the query is a SELECT, returns a list of row tuples.
            - For non-SELECT queries, returns the number of affected rows (int).

    Returns:
        DataFrame or list of tuples for SELECT queries, or int for other statements.
    """
    db_path = Path(db_path)
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(query)

        if query.lstrip().upper().startswith("SELECT"):
            rows = cur.fetchall()
            columns = [col[0] for col in cur.description] if cur.description else []
            if return_dataframe:
                return pd.DataFrame(rows, columns=columns)
            return rows

        conn.commit()
        return cur.rowcount

def run_pyplot_code(
    code: str,
    save_path: Optional[str | Path] = None,
) -> Optional[Figure]:
    """
    Execute pyplot code safely in headless mode.
    * GUI backend disabled via matplotlib.use("Agg")
    * plt.show() is monkey-patched to NO-OP.
    """
    try:
        plt.close("all")

        # 1) show() 무력화
        plt.show = lambda *args, **kwargs: None

        exec_globals: dict[str, object] = {"plt": plt}
        exec_locals: dict[str, object]  = {}

        exec(code, exec_globals, exec_locals)

        fig: Figure = plt.gcf()

        if save_path:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(save_path, bbox_inches="tight")
            print(f"[run_pyplot_code] Figure saved → {save_path}")

        return fig

    except Exception as e:
        print(f"[run_pyplot_code] Error: {e}")
        return None
