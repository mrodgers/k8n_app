#!/bin/bash
# Setup script for initializing and configuring the database

set -e

# Default values
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="research"
DB_USER="postgres"
DB_PASSWORD="postgres-password"
MIGRATE_DATA="false"
TINYDB_PATH="./data/research.json"

# Parse arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --host)
      DB_HOST="$2"
      shift 2
      ;;
    --port)
      DB_PORT="$2"
      shift 2
      ;;
    --db)
      DB_NAME="$2"
      shift 2
      ;;
    --user)
      DB_USER="$2"
      shift 2
      ;;
    --password)
      DB_PASSWORD="$2"
      shift 2
      ;;
    --migrate)
      MIGRATE_DATA="true"
      shift
      ;;
    --tinydb-path)
      TINYDB_PATH="$2"
      shift 2
      ;;
    --help)
      echo "Usage: setup_db.sh [options]"
      echo "Options:"
      echo "  --host HOST       Database host (default: localhost)"
      echo "  --port PORT       Database port (default: 5432)"
      echo "  --db NAME         Database name (default: research)"
      echo "  --user USER       Database user (default: postgres)"
      echo "  --password PASS   Database password (default: postgres-password)"
      echo "  --migrate         Migrate data from TinyDB to PostgreSQL"
      echo "  --tinydb-path PATH TinyDB file path (default: ./data/research.json)"
      echo "  --help            Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $key"
      exit 1
      ;;
  esac
done

echo "Database Setup Script"
echo "====================="
echo "Host: $DB_HOST"
echo "Port: $DB_PORT"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Migrate data: $MIGRATE_DATA"
if [ "$MIGRATE_DATA" = "true" ]; then
  echo "TinyDB path: $TINYDB_PATH"
fi
echo

# Build connection string
export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
export USE_POSTGRES="true"

# Check if PostgreSQL is available
echo "Checking database connection..."
if ! command -v pg_isready &> /dev/null; then
  echo "pg_isready not found. Installing PostgreSQL client..."
  if command -v apt-get &> /dev/null; then
    sudo apt-get update && sudo apt-get install -y postgresql-client
  elif command -v yum &> /dev/null; then
    sudo yum install -y postgresql
  elif command -v brew &> /dev/null; then
    brew install libpq
    brew link --force libpq
  else
    echo "Error: Could not install PostgreSQL client. Please install it manually."
    exit 1
  fi
fi

# Check database connection
echo "Checking database connection..."
if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; then
  echo "Database connection successful."
else
  echo "Error: Could not connect to database."
  exit 1
fi

# Create database if it doesn't exist
echo "Creating database if it doesn't exist..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE $DB_NAME"

# Initialize database schema
echo "Initializing database schema..."
python -c "
from research_system.models.db import PostgreSQLDatabase
db = PostgreSQLDatabase('$DATABASE_URL')
print('Database schema initialized successfully.')
"

# Migrate data if requested
if [ "$MIGRATE_DATA" = "true" ]; then
  echo "Migrating data from TinyDB to PostgreSQL..."
  python -m research_system.models.db_migration --source "$TINYDB_PATH" --target "$DATABASE_URL"
fi

echo "Database setup complete."