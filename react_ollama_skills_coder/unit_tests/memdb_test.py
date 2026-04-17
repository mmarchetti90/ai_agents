#!/usr/bin/env python3

"""
Simple utility to print the memory log to stdout
"""

### IMPORTS -------------------------------- ###

import sqlite3

### MAIN ----------------------------------- ###

if __name__ == '__main__':

    # Extract memories
    db = '/Users/earthsea/Desktop/development/github/react_skills_codingagent/memory/memory.db'
    db_con = sqlite3.Connection(db)
    db_cur = db_con.cursor()
    select_origins = ['user', 'assistant']
    select_string = f"""
    SELECT
        *
    FROM
        ai_user_interactions as i
    WHERE
        origin {("= ?" if len(select_origins) == 1 else "IN (" + ", ".join(["?"] * len(select_origins)) + ")")}
    """
    print('#' * 40)
    print("SELECT statement:")
    print(select_string.strip())
    print('#' * 40)
    memories = db_cur.execute(select_string, select_origins).fetchall()
    db_con.close()

    # Print log
    for m in memories:
        print(f'<{m[1]}> ({m[0]})')
        print(m[3].strip())
        print('-' * 40)