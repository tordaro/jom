# Joint ownership manager

The joint ownership manager (JOM) is a Django-based web application focused on managing parking and electric vehicle charging for a small joint ownership company. It offers basic yet essential functionalities to streamline parking space allocation and manage charging stations efficiently.

## Key Features

- Parking Management: Simple tools to allocate and monitor parking spaces.
- EV Charging Control: Easy handling of electric vehicle charging station usage.
- Basic Billing System: Simple cost calculation for parking and charging.
- Owner Access: Basic profiles for owners to access and view pertinent information.

## Future Scope

While initially focused on car management, the project is designed to accommodate future enhancements for broader ownership management tasks as the company's needs evolve.

## Gettings started locally

Copy the tracked environment template:

`cp dotenv .env`

Start a local Postgres container with the same defaults as the template file:

`podman run --name jom-postgres -e POSTGRES_DB=postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres`

The template also includes development defaults for `SECRET_KEY`, `DEBUG`, and `DJANGO_LOG_LEVEL`, plus empty Zaptec-related variables you can fill in later if needed.
The project is only guaranteed to work for Python >= 3.11, so check your version:

`python -V`

Use [pyenv](https://github.com/pyenv/pyenv#installation) to easily upgrade Python.

Install [uv](https://docs.astral.sh/uv/getting-started/installation/).

Create the local virtual environment and install all dependencies, including the dev tools:

`uv sync --group dev`

`uv` creates and manages `.venv` for the project automatically, so you can run Django commands through `uv run` without activating the environment manually.

You can now migrate your database:

`uv run python src/manage.py migrate`

Get full access by creating a super user:

`uv run python src/manage.py createsuperuser`

Start the server:

`uv run python src/manage.py runserver`

Run the test suite:

`uv run src/python manage.py test`
