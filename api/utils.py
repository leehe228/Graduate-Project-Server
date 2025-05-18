from pathlib import Path
import sqlite3
import pandas as pd
from typing import Optional, Tuple, List, Union

def file_to_sqlite(
    file_path: str | Path,
    db_path: str | Path,
    table_name: Optional[str] = None,
    if_exists: str = "replace",
    chunksize: Optional[int] = None
) -> Tuple[Path, str]:
    """
    Convert a CSV or Excel file to a SQLite database and return
    the path to the .db file along with a textual representation
    of its schema (for Text2SQL use).

    Args:
        file_path: Path to .csv, .xls, or .xlsx file.
        db_path:   Path where the SQLite database will be created.
        table_name: Name of the table to create; defaults to the file stem.
        if_exists: What to do if the table already exists: "fail", "replace", or "append".
        chunksize: Number of rows per batch insert (for large files).

    Returns:
        A tuple (db_path, schema_text) where schema_text is formatted as:

            Database: your.db
            Tables:
            - table1: col1 TYPE [NOT NULL] [DEFAULT ...] [PRIMARY KEY], col2 TYPE, ...
            - table2: ...
    """
    file_path = Path(file_path)
    db_path   = Path(db_path)
    if table_name is None:
        table_name = file_path.stem

    # 1) Load the source file into a DataFrame
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(file_path)
    elif suffix in {".xls", ".xlsx"}:
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported extension: only .csv, .xls, .xlsx are allowed")

    # 2) Write DataFrame to SQLite
    with sqlite3.connect(db_path) as conn:
        df.to_sql(table_name, conn, if_exists=if_exists, index=False, chunksize=chunksize)

        # 3) Introspect schema
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row[0] for row in cursor.fetchall()]

        lines = [f"Database: {db_path.name}", "Tables:"]
        for tbl in tables:
            cursor.execute(f"PRAGMA table_info('{tbl}');")
            cols = cursor.fetchall()
            # cols columns: (cid, name, type, notnull, dflt_value, pk)
            defs = []
            for _, name, ctype, notnull, dflt_value, pk in cols:
                parts = [name, ctype]
                if notnull:
                    parts.append("NOT NULL")
                if dflt_value is not None:
                    parts.append(f"DEFAULT {dflt_value}")
                if pk:
                    parts.append("PRIMARY KEY")
                defs.append(" ".join(parts))
            lines.append(f"- {tbl}: " + ", ".join(defs))

        schema_text = "\n".join(lines)

    return db_path, schema_text


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
