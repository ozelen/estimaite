#!/usr/bin/env bash
set -euo pipefail

# Change to backend directory if it exists (for Docker container structure)
if [[ -d "/app/backend" ]]; then
  cd /app/backend
elif [[ -d "./backend" ]]; then
  cd ./backend
fi

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for Postgres at ${POSTGRES_HOST:-localhost}:${POSTGRES_PORT:-5432}…"
until pg_isready -q -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-postgres}"; do
  sleep 1
done
echo "✅ Postgres is up"

# Set Django settings module
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-estimaite.settings}"

# Run makemigrations if enabled (dev/staging only)
if [[ "${ALLOW_MAKEMIGRATIONS:-0}" == "1" ]]; then
  echo "⚙️ Running makemigrations"
  uv run manage.py makemigrations || true
fi

# Run migrations
echo "📦 Running migrations"
uv run manage.py migrate --noinput

# Create superuser if enabled
if [[ "${CREATE_SUPERUSER:-0}" == "1" ]]; then
  echo "👤 Ensuring superuser"
  uv run manage.py shell <<PY
from django.contrib.auth import get_user_model
User = get_user_model()
email = "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}"
pwd = "${DJANGO_SUPERUSER_PASSWORD:-ChangeMe123}"
username = "${DJANGO_SUPERUSER_USERNAME:-admin}"

# Check if user exists by email or username
user = None
if User.objects.filter(email=email).exists():
    user = User.objects.get(email=email)
    print(f"📧 Found existing user by email: {email}")
elif User.objects.filter(username=username).exists():
    user = User.objects.get(username=username)
    print(f"👤 Found existing user by username: {username}")

if user:
    # Update existing user
    user.email = email
    user.username = username
    user.set_password(pwd)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"✅ Superuser updated: {email} (username: {username})")
else:
    # Create new superuser
    User.objects.create_superuser(email=email, password=pwd, username=username)
    print(f"✅ Superuser created: {email} (username: {username})")
PY
fi

# Setup debugpy if enabled
DEBUGPY_PREFIX=()
if [[ "${DEBUGPY:-0}" == "1" ]]; then
  export DEBUGPY_PORT="${DEBUGPY_PORT:-5678}"
  echo "🔧 debugpy listening on 0.0.0.0:${DEBUGPY_PORT}"
  DEBUGPY_PREFIX=(python -Xfrozen_modules=off -m debugpy ${WAIT_FOR_DEBUGGER:+--wait-for-client} --listen 0.0.0.0:"$DEBUGPY_PORT")
fi

# Start the server
SERVER="${SERVER:-runserver}"
DJANGO_PORT="${DJANGO_PORT:-8008}"

case "$SERVER" in
  daphne)
    echo "🚀 Starting Daphne (ASGI)"
    if [[ "${#DEBUGPY_PREFIX[@]}" -gt 0 ]]; then
      exec "${DEBUGPY_PREFIX[@]}" -m daphne -b 0.0.0.0 -p "$DJANGO_PORT" estimaite.asgi:application
    else
      exec python -m daphne -b 0.0.0.0 -p "$DJANGO_PORT" estimaite.asgi:application
    fi
    ;;

  gunicorn)
    echo "🚀 Starting Gunicorn (WSGI)"
    GUNI_WORKERS="${GUNI_WORKERS:-2}"
    GUNI_THREADS="${GUNI_THREADS:-4}"
    EXTRA="${GUNI_EXTRA:---reload --timeout 120 --access-logfile - --error-logfile -}"
    if [[ "${DEBUGPY:-0}" == "1" ]]; then
      exec "${DEBUGPY_PREFIX[@]}" -m gunicorn estimaite.wsgi:application --bind 0.0.0.0:"$DJANGO_PORT" \
           --workers "$GUNI_WORKERS" --threads "$GUNI_THREADS" $EXTRA
    else
      exec gunicorn estimaite.wsgi:application --bind 0.0.0.0:"$DJANGO_PORT" \
           --workers "$GUNI_WORKERS" --threads "$GUNI_THREADS" $EXTRA
    fi
    ;;

  runserver|*)
    echo "🚀 Starting Django runserver"
    if [[ "${DEBUGPY:-0}" == "1" ]]; then
      exec "${DEBUGPY_PREFIX[@]}" uv run manage.py runserver 0.0.0.0:"$DJANGO_PORT"
    else
      exec uv run manage.py runserver 0.0.0.0:"$DJANGO_PORT"
    fi
    ;;
esac
