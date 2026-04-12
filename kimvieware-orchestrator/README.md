# KIMVIware Orchestrator

This is the main orchestrator for the KIMVIware system. It provides a web interface to manage and monitor the entire pipeline.

## Prerequisites

*   Python 3.8+
*   The core infrastructure is running (see `kimvieware-infrastructure`).

## Setup

1.  **Install the shared library**:
    The orchestrator depends on the `kimvieware-shared` library. To install it, navigate to the `kimvieware-shared` directory and run:

    ```bash
    pip install -e .
    ```

2.  **Install dependencies**:
    From the `kimvieware-orchestrator` directory, install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

To start the orchestrator server, run the following command from this directory:

```bash
python3 run_orchestrator.py
```

The server will be available at `http://localhost:8080`.

## Structure (code)

*   `src/kimvieware_orchestrator/` — application package
    *   `main.py` — factory `create_app()`, montage des routes
    *   `api/legacy.py` — API historique `/api/*` (dashboard actuel)
    *   `api/v1/` — API versionnée `/api/v1/*`
    *   `web/pages.py` — pages HTML (dashboard)
    *   `services/` — logique métier (jobs, stats, services pipeline)
    *   `infrastructure/` — consumer RabbitMQ `phase.updates`
*   `templates/` — Jinja2 : `layouts/`, `pages/`, `components/`
*   `static/` — CSS / JS servis sous `/static/`

## Features

*   **Submit SUT**: Upload and analyze a System Under Test (SUT).
*   **Jobs**: View all jobs in real-time.
*   **Services**: Check the status of the microservices.
*   **Statistics**: View complete statistics.
*   **API legacy**: `http://localhost:8080/api/` (chemins inchangés pour le dashboard).
*   **API v1**: `http://localhost:8080/api/v1/` (ex. `POST /api/v1/jobs` pour soumettre un SUT).
