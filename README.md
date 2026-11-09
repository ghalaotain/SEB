# Smart Exhibition Booth Personalized Ads

A privacy-conscious exhibition booth that estimates an anonymous visitor's
age group and gender, selects a suitable advertisement, shows store locations
and QR destinations, and records anonymous interaction statistics.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2Fghalaotain%2FSEB)

**Live showcase:** [smart-exhibition-booth.onrender.com](https://smart-exhibition-booth.onrender.com)

## Interface preview

### Landing page

![Smart Exhibition Booth landing page](docs/screenshots/home.png)

| Personalized advertisement display | Interactive store map |
| --- | --- |
| ![Live personalized advertisement display](docs/screenshots/live-display.png) | ![Interactive exhibition store map](docs/screenshots/store-map.png) |

### Protected administration

![Secure administrator sign-in](docs/screenshots/admin-login.png)

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

## Project background and contributions

This system originated as a collaborative graduation project. The graduation
team contributed to the original concept, research, requirements analysis,
documentation, and system design.

The current functional software implementation was led, developed, and
extended by **Ghala Zeed Otani**. This work includes the Flask application,
frontend experience, OpenCV and DeepFace integration, privacy-conscious camera
flow, personalized advertisement selection, administrator dashboard,
advertisement management, analytics, interactive store map, image uploads,
testing, and deployment preparation.

AI-assisted development tools were used for implementation support, debugging,
code review, and documentation. Technical decisions, testing, integration, and
the final implementation were managed as part of the development process.

### Graduation project team

- **Lina Mohammed Asiri**
- **Wejdan Sulaiman Alshardi**
- **Arwa Abdullah Alghamdi**
- **Ghala Zeed Otani** — Lead developer of the extended software implementation
- **Norah Ali Abdullah**

## Technology

- Frontend: HTML, CSS, JavaScript, Chart.js
- Backend: Python 3.11 and Flask
- AI: OpenCV and DeepFace
- Database: SQLAlchemy with SQLite for demos and MySQL/MariaDB for deployment
- Authentication: Flask-Login and Flask-WTF CSRF protection

## System workflow

```mermaid
flowchart LR
    A[Visitor starts experience] --> B[Camera consent]
    B --> C[Temporary camera frame]
    C --> D[OpenCV face detection]
    D --> E[DeepFace age and gender estimation]
    E --> F[Demographic advertisement selection]
    F --> G[Advertisement and QR destination]
    G --> H[Anonymous interaction statistics]
    C -. never written to disk .-> I[Frame discarded]
```

The public visitor flow and administrator area are separated. Analytics and
advertisement-management APIs require an authenticated administrator session.

## Privacy design

The camera starts only after the visitor gives consent. One temporary frame is
sent to the server for demographic estimation and is not written to disk. The
system does not identify visitors and stores only the minimum anonymous values
needed for statistics: estimated age, gender, age group, booth, advertisement,
analysis mode, and display time.

## API overview

| Method | Endpoint | Purpose | Access |
| --- | --- | --- | --- |
| `GET` | `/api/health` | Application and AI dependency status | Public |
| `GET` | `/api/ads` | Active general advertisements | Public |
| `GET` | `/api/stores` | Searchable exhibition store directory | Public |
| `POST` | `/api/analyze` | Temporary demographic analysis and ad selection | Public, rate limited |
| `GET` | `/api/statistics` | Visitor and campaign summary | Administrator |
| `GET` | `/api/statistics/demographics` | Gender and age-group analytics | Administrator |
| `GET` | `/api/statistics/advertisements` | Advertisement performance | Administrator |
| `GET/POST` | `/api/advertisements` | List or create advertisements | Administrator |
| `PUT/DELETE` | `/api/advertisements/<id>` | Update or delete an advertisement | Administrator |
| `PATCH` | `/api/advertisements/<id>/status` | Activate or pause an advertisement | Administrator |

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

## One-click showcase deployment

The repository includes a Render Blueprint for a secure portfolio demonstration.
It runs with production-safe Flask settings, simulated demographic results, and
automatically seeded exhibition data. Real DeepFace models are intentionally
disabled on the 512 MB free instance.

1. Click **Deploy to Render** at the top of this README.
2. Sign in to Render and connect GitHub when prompted.
3. Provide the requested administrator username, email, and a password of at
   least 12 characters. These values remain in Render and are not committed.
4. Review the free web service and apply the Blueprint.
5. Open the generated `.onrender.com` address after the build completes.

The free instance can take about one minute to wake after 15 minutes of
inactivity. Its filesystem is ephemeral, so demonstration statistics and local
uploads reset after a restart. Use the production configuration with a managed
database and persistent object storage for a durable deployment.

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
