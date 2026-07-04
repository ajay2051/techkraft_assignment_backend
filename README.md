alembic -n tech revision --autogenerate -m "initial"

alembic -n tech upgrade head

    
            Users

            +------------+
            | id         |
            | name       |
            +------------+
                  |
                  | 1
                  |
                  | *
            +------------+
            | Scores     |
            +------------+
            | id         |
            | category   |
            | score      |
            | reviewer_id|
            |candidate_id|
            +------------+
                  |
                  | *
                  |
                  | 1
           +---------------+
           | Candidates    |
           +---------------+
           | id            |
           | name          |
           +---------------+


The core issue is that the code retrieves every row from the database and performs filtering and pagination in application code instead of letting the database do that work.

What's wrong?
all_candidates = db.execute("SELECT * FROM candidates").fetchall()

This statement loads the entire candidates table into memory regardless of:

the requested status
the search keyword
the requested page
the requested page size

Then the application performs:

filtered = [c for c in all_candidates if c["status"] == status]

and later slices the list for pagination.

Why this matters at scale

This pattern works on a small development database but becomes increasingly expensive as the dataset grows.

Problems include:

Unnecessary I/O
Every request transfers the entire table from the database.
Network traffic grows linearly with table size.
High memory usage
The application stores every candidate in memory.
Large tables can significantly increase memory consumption or even exhaust available memory.
Poor CPU utilization
Filtering in Python is much slower than using indexed database queries.
Every request scans every record.
Inefficient pagination
To return 20 records on page 50, the application still reads all rows first.
Pagination provides no performance benefit because the full dataset has already been loaded.
Poor scalability
As the table grows from thousands to millions of rows, response times increase dramatically.
Concurrent requests multiply the wasted work.
The correct approach

Filtering and pagination should be performed in SQL so the database optimizer can use indexes and return only the requested rows.

Example:

def search_candidates(status: str, keyword: str, page: int, page_size: int):
    offset = (page - 1) * page_size

    return db.execute(
        """
        SELECT *
        FROM candidates
        WHERE status = ?
          AND (
                name LIKE ?
                OR resume_text LIKE ?
              )
        ORDER BY id
        LIMIT ? OFFSET ?
        """,
        (
            status,
            f"%{keyword}%",
            f"%{keyword}%",
            page_size,
            offset,
        ),
    ).fetchall()