# Smart Exhibition Booth Personalized Ads

A privacy-conscious exhibition booth that estimates an anonymous visitor's
age group and gender, selects a suitable advertisement, shows store locations
and QR destinations, and records anonymous interaction statistics.

## Main features

- Consent-first browser camera flow.
- Age and gender estimation with OpenCV and DeepFace.
- No face recognition, identity matching, or stored visitor photographs.
- Demographic advertisement selection with a general-ad fallback.
- Interactive exhibition store map.
- Secure administrator login.
- Advertisement create, edit, activate, pause, delete, search, and image upload.
- Anonymous visitor analytics with Chart.js.
- SQLite demo mode and MySQL-compatible production configuration.

## Technology

- Frontend: HTML, CSS, JavaScript, Chart.js
- Backend: Python 3.11 and Flask
- AI: OpenCV and DeepFace
- Database: SQLAlchemy with SQLite for demos and MySQL/MariaDB for deployment
- Authentication: Flask-Login and Flask-WTF CSRF protection

## Privacy design

The camera starts only after the visitor gives consent. One temporary frame is
sent to the server for demographic estimation and is not written to disk. The
system does not identify visitors and stores only the minimum anonymous values
needed for statistics: estimated age, gender, age group, booth, advertisement,
analysis mode, and display time.

## Local setup

Create and activate a Python 3.11 virtual environment, then install packages:

```powershell
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
python -m pip install -r requirements.txt
python -m pip install -r requirements-ai.txt
```

Copy `.env.example` to `.env` and replace `SECRET_KEY` with a long random
value. For a local SQLite demonstration, keep:

```env
FLASK_ENV=development
APP_MODE=demo
AI_ENABLED=false
```

Create the database and demo records:

```powershell
python -m flask --app run.py db upgrade
python -m flask --app run.py seed-demo
python -m flask --app run.py create-admin
```

Run the development server:

```powershell
python run.py
```

Open `http://127.0.0.1:5000`.

## Real AI analysis

After installing `requirements-ai.txt`, enable the local AI service:

```env
AI_ENABLED=true
AI_DETECTOR_BACKEND=opencv
AI_MAX_IMAGE_PIXELS=16000000
```

DeepFace may download model weights during the first analysis. Those model
files are intentionally excluded from Git.

## Production environment

Production requires HTTPS so browser camera access works outside localhost.
Configure these environment variables in the hosting platform rather than
committing a `.env` file:

```env
FLASK_ENV=production
APP_MODE=live
SECRET_KEY=replace-with-at-least-32-random-characters
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/smart_exhibition_booth
AI_ENABLED=true
BOOTH_ID=booth_1
```

Apply migrations and create the first administrator from the host's secure
console:

```bash
flask --app wsgi.py db upgrade
flask --app wsgi.py create-admin
```

The included `Dockerfile` starts the application with Gunicorn. A single
worker is used to avoid loading multiple copies of the AI models into memory.

## Important deployment notes

- GitHub stores the source code but does not run this Flask application through
  GitHub Pages.
- Use a container-capable Python host and a managed MySQL-compatible database.
- DeepFace and TensorFlow need substantially more memory than a basic Flask
  application; a small free hosting plan may not be sufficient.
- Uploaded advertisement images require persistent storage or object storage
  in production. Container filesystems may be temporary.
- Never commit `.env`, database files, passwords, visitor frames, or AI model
  weights.

## Health check

The deployment health endpoint is:

```text
GET /api/health
```
