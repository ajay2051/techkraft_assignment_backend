#!/bin/bash
set -e

# Wait for database
if [ "$DATABASE" = "postgres" ]; then
    echo "Waiting for postgres..."
    while ! nc -z "$DATABASE_HOST" "$DATABASE_PORT"; do
      echo "==========👌🙏🔥 PostgreSQL is unavailable - sleeping 👌🙏🔥=========="
      sleep 1
    done
    echo "=================👌🙏🔥 PostgreSQL started 👌🙏🔥================="
fi


# Add a small delay to ensure services are ready
sleep 2

echo "================================👌🙏🔥 Server is starting now 👌🙏🔥=================================="

# Check if this is first run by looking for alembic_version table
if ! psql -h "$DATABASE_HOST" -U "$DATABASE_USERNAME" -d "$DATABASE_NAME" -c "SELECT 1 FROM alembic_version" > /dev/null 2>&1; then
    echo "===================== 👌🙏🔥 First run - creating initial migration... 👌🙏🔥 =================="
    # alembic -n accident revision --autogenerate -m "initial"
    alembic -n tech upgrade head
else
    echo "=======================👌🙏🔥 Applying any pending migrations 👌🙏🔥===================="
    alembic -n tech upgrade head
fi

# Start FastAPI
echo "===================👌🙏🔥 Starting FastAPI server 👌🙏🔥============================"
#exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
exec fastapi run
