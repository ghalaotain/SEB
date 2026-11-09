# Changelog

All notable changes to the Smart Exhibition Booth project are documented in
this file.

## [1.0.0] - 2026-11-10

### Added

- Consent-first visitor camera experience.
- OpenCV and DeepFace demographic-estimation service for supported hosts.
- Secure hosted showcase mode with simulated demographic results.
- Demographic advertisement selection with a general-ad fallback.
- Automatic anonymous interaction and daily-statistics recording.
- Interactive exhibition map with store search and category filtering.
- Secure administrator authentication and protected analytics APIs.
- Advertisement creation, editing, activation, pausing, deletion, and image
  upload.
- Chart.js visitor, demographic, daily, and campaign analytics.
- SQLite demo configuration and MySQL-compatible production configuration.
- Docker, Gunicorn, database migration, and Render Blueprint deployment.
- Public interface screenshots and complete setup documentation.

### Privacy and security

- Visitor photographs are not written to disk.
- No facial recognition or identity matching is performed.
- Only anonymous demographic and advertisement-interaction data is recorded.
- Camera access begins only after explicit visitor consent.
- Administrator sessions use secure cookie settings on hosted deployments.
- Analysis and login endpoints use rate limiting and validated input.

### Hosted showcase

- Live demo: https://smart-exhibition-booth.onrender.com
- The free showcase uses simulated AI results and ephemeral demonstration
  data. Real DeepFace analysis remains available for appropriately resourced
  deployments.
