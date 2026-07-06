# MovieHub

A Flask-based movie hosting/download platform with user accounts, an admin
panel for uploading movies, and per-user download history tracking.

## Features

- User signup/login by **username** + password (hashed via Werkzeug, sessions via Flask-Login)
- Browse/search movies by title and genre, with pagination
- Movie detail pages with poster, description, and download link
- Movies can only be uploaded by admins, and downloading requires being logged in
- A dedicated admin dashboard (`/admin/`), separate from the regular user
  dashboard (`/dashboard`), for uploading movies, deleting movies, and
  promoting/revoking admin users
- Admin can change their own username/password from `/admin/settings`
- Download tracking (who downloaded what, and when)
- Admin security tools, each with its own icon on the admin dashboard:
  - 🌐 **User & Device Info** (`/admin/users-info`) — every user's role, last
    login IP, and last device (user-agent)
  - 🛡️ **Firewall** (`/admin/firewall`) — block/unblock any non-admin user;
    a blocked user is logged out on their very next request, even mid-session
  - 🔐 **Login Attempts** (`/admin/login-attempts`) — log of every login
    attempt (successful or failed) with username, IP, device, and time
- CSRF protection on all forms (Flask-WTF)

## Default admin login

- **Username:** `admin`
- **Password:** `admin123`

Change these via `ADMIN_USERNAME` / `ADMIN_PASSWORD` in `.env` before running
`flask create-admin`, or change them later from `/admin/settings` once logged in.

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

Copy `.env` and adjust `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_EMAIL`, and
`ADMIN_PASSWORD` for your environment. Never commit a real `.env` with
production secrets.

## Database

```bash
flask db init        # first time only
flask db migrate -m "Initial migration"
flask db upgrade
flask create-admin   # creates the admin user from .env
```

## Run

```bash
flask run
```

Visit http://127.0.0.1:5000

## Deploying to Render

This repo includes `render.yaml` (Blueprint) and a `Procfile`. To deploy:

1. Push this repo to GitHub (already done if you're reading this on GitHub).
2. In the Render dashboard: **New +** → **Blueprint** → connect this GitHub
   repo. Render reads `render.yaml` and provisions a free Postgres database
   plus a web service automatically.
3. Render will ask you to fill in the `ADMIN_PASSWORD` env var (marked
   `sync: false` in `render.yaml` so it isn't committed to git). `SECRET_KEY`
   is auto-generated.
4. Deploy. The start command (`flask db upgrade && flask create-admin && gunicorn ...`)
   runs migrations and creates the admin user on every deploy — safe to
   re-run, it no-ops if the admin already exists.

If you'd rather create the service manually instead of via Blueprint:
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `flask db upgrade && flask create-admin && gunicorn --bind 0.0.0.0:$PORT app:app`
- **Environment variables:** `FLASK_APP=app.py`, `SECRET_KEY`, `ADMIN_USERNAME`,
  `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and `DATABASE_URL` (a Postgres connection
  string — see caveat below).

**Important limitation:** Render's free web services use an ephemeral
filesystem — anything written to local disk (uploaded movie files, poster
images, and a SQLite database if you don't configure Postgres) is wiped on
every deploy and restart. Use the provisioned Postgres database for
users/movies/downloads metadata (handled automatically by `render.yaml`), and
be aware that **uploaded video/poster files will not survive a redeploy**
unless you attach a paid persistent disk or move file storage to something
like S3/Cloudinary.

## Project Structure

```
MovieHub/
├── app.py              # App factory, blueprint registration, CLI commands
├── config.py           # Config loaded from .env
├── database.py         # SQLAlchemy, Migrate, LoginManager instances
├── models/              # User, Movie, Download ORM models
├── routes/              # auth, admin, movies, users blueprints
├── templates/           # Jinja2 templates
├── static/              # css/, js/, posters/
├── uploads/             # Uploaded movie files (not served statically)
└── migrations/          # Alembic migration scripts
```

## Notes

- Uploaded video files are stored outside `static/` and served only through
  the authenticated `/movie/<id>/download` route, so downloads require login
  and are logged.
- File uploads are restricted to an extension allowlist and validated with
  `secure_filename`.
- Only users with `is_admin=True` can reach `/admin/*` routes.
