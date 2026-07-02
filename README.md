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