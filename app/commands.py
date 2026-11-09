import os

import click
from flask import Flask

from .extensions import db
from .models import (
    AdminUser,
    Advertisement,
    Store,
)


DEMO_STORES = [
    {
        "name": "Future Mobility",
        "description": (
            "Explore intelligent mobility products and "
            "connected exhibition experiences."
        ),
        "category": "technology",
        "hall": "Hall A",
        "store_number": "12",
        "map_location": "Hall A · Store 12",
        "opening_hours": "9:00 AM – 9:00 PM",
        "icon": "FM",
        "color": "#7565ff",
        "map_position": {
            "left": "4%",
            "top": "7%",
            "width": "25%",
            "height": "24%",
        },
        "is_active": True,
    },
    {
        "name": "Calm House",
        "description": (
            "Discover thoughtful products created for "
            "comfortable everyday living."
        ),
        "category": "services",
        "hall": "Hall B",
        "store_number": "07",
        "map_location": "Hall B · Store 07",
        "opening_hours": "10:00 AM – 9:00 PM",
        "icon": "CH",
        "color": "#65e5d8",
        "map_position": {
            "left": "62%",
            "top": "7%",
            "width": "32%",
            "height": "24%",
        },
        "is_active": True,
    },
    {
        "name": "Form Market",
        "description": (
            "A curated collection of limited exhibition "
            "products and accessories."
        ),
        "category": "fashion",
        "hall": "Hall C",
        "store_number": "21",
        "map_location": "Hall C · Store 21",
        "opening_hours": "9:00 AM – 10:00 PM",
        "icon": "FM",
        "color": "#ed72c5",
        "map_position": {
            "left": "62%",
            "top": "58%",
            "width": "32%",
            "height": "25%",
        },
        "is_active": True,
    },
    {
        "name": "Atelier Four",
        "description": (
            "Explore contemporary fashion selected for "
            "the exhibition audience."
        ),
        "category": "fashion",
        "hall": "Hall A",
        "store_number": "04",
        "map_location": "Hall A · Store 04",
        "opening_hours": "10:00 AM – 10:00 PM",
        "icon": "A4",
        "color": "#ed72c5",
        "map_position": {
            "left": "4%",
            "top": "58%",
            "width": "25%",
            "height": "25%",
        },
        "is_active": True,
    },
    {
        "name": "Motion Lab",
        "description": (
            "Try wearable technology and connected "
            "products designed for movement."
        ),
        "category": "technology",
        "hall": "Hall B",
        "store_number": "14",
        "map_location": "Hall B · Store 14",
        "opening_hours": "9:00 AM – 9:00 PM",
        "icon": "ML",
        "color": "#7565ff",
        "map_position": {
            "left": "34%",
            "top": "7%",
            "width": "17%",
            "height": "24%",
        },
        "is_active": True,
    },
    {
        "name": "Well Studio",
        "description": (
            "A calm destination for wellbeing products "
            "and guided demonstrations."
        ),
        "category": "services",
        "hall": "Hall C",
        "store_number": "09",
        "map_location": "Hall C · Store 09",
        "opening_hours": "10:00 AM – 8:00 PM",
        "icon": "WS",
        "color": "#65e5d8",
        "map_position": {
            "left": "34%",
            "top": "58%",
            "width": "17%",
            "height": "25%",
        },
        "is_active": True,
    },
    {
        "name": "Exhibition Kitchen",
        "description": (
            "Fresh snacks, drinks, and a comfortable "
            "break during your exhibition visit."
        ),
        "category": "food",
        "hall": "Hall A",
        "store_number": "18",
        "map_location": "Hall A · Store 18",
        "opening_hours": "8:00 AM – 10:00 PM",
        "icon": "EK",
        "color": "#f5c86b",
        "map_position": {
            "left": "54%",
            "top": "34%",
            "width": "18%",
            "height": "16%",
        },
        "is_active": True,
    },
]


DEMO_ADVERTISEMENTS = [
    {
        "title": "Move into the future",
        "description": (
            "Discover intelligent mobility designed "
            "for modern exhibition spaces."
        ),
        "category": "Technology",
        "theme": "violet",
        "target_gender": "all",
        "target_age_min": None,
        "target_age_max": None,
        "store_location": "Hall A · Store 12",
        "is_active": True,
    },
    {
        "title": "A better everyday experience",
        "description": (
            "Explore products created around comfort, "
            "clarity, and thoughtful design."
        ),
        "category": "Lifestyle",
        "theme": "cyan",
        "target_gender": "all",
        "target_age_min": None,
        "target_age_max": None,
        "store_location": "Hall B · Store 07",
        "is_active": True,
    },
    {
        "title": "Made to stand out",
        "description": (
            "A curated collection of exhibition offers "
            "and limited product experiences."
        ),
        "category": "Retail",
        "theme": "pink",
        "target_gender": "all",
        "target_age_min": None,
        "target_age_max": None,
        "store_location": "Hall C · Store 21",
        "is_active": True,
    },
    {
        "title": "Discover your next style",
        "description": (
            "A personalized demo campaign selected "
            "for the 18-24 visitor group."
        ),
        "category": "Fashion",
        "theme": "pink",
        "target_gender": "female",
        "target_age_min": 18,
        "target_age_max": 24,
        "store_location": "Hall A · Store 04",
        "is_active": True,
    },
    {
        "title": "Technology that moves with you",
        "description": (
            "A personalized demo campaign selected "
            "for the 25-34 visitor group."
        ),
        "category": "Technology",
        "theme": "violet",
        "target_gender": "male",
        "target_age_min": 25,
        "target_age_max": 34,
        "store_location": "Hall B · Store 14",
        "is_active": True,
    },
    {
        "title": "Wellbeing, thoughtfully designed",
        "description": (
            "A personalized demo campaign selected "
            "for the 35-44 visitor group."
        ),
        "category": "Wellbeing",
        "theme": "cyan",
        "target_gender": "female",
        "target_age_min": 35,
        "target_age_max": 44,
        "store_location": "Hall C · Store 09",
        "is_active": True,
    },
]


def upsert_store(store_data: dict) -> Store:
    store = db.session.scalar(
        db.select(Store).where(
            Store.map_location
            == store_data["map_location"]
        )
    )

    if store is None:
        store = Store()
        db.session.add(store)

    for field, value in store_data.items():
        setattr(store, field, value)

    return store


def upsert_advertisement(
    advertisement_data: dict,
) -> Advertisement:
    title = advertisement_data["title"]

    advertisement = db.session.scalar(
        db.select(Advertisement).where(
            Advertisement.title == title
        )
    )

    store_location = advertisement_data[
        "store_location"
    ]

    store = db.session.scalar(
        db.select(Store).where(
            Store.map_location == store_location
        )
    )

    if store is None:
        raise RuntimeError(
            f"Store not found: {store_location}"
        )

    if advertisement is None:
        advertisement = Advertisement()

    fields = {
        key: value
        for key, value in advertisement_data.items()
        if key != "store_location"
    }

    for field, value in fields.items():
        setattr(advertisement, field, value)

    advertisement.store = store
    advertisement.map_location = store.map_location

    db.session.add(advertisement)

    return advertisement


def save_initial_data() -> None:
    try:
        for store_data in DEMO_STORES:
            upsert_store(store_data)

        db.session.flush()

        for advertisement_data in DEMO_ADVERTISEMENTS:
            upsert_advertisement(
                advertisement_data
            )

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def register_commands(app: Flask) -> None:
    @app.cli.command("seed-demo")
    def seed_demo() -> None:
        """Insert or update demo stores and advertisements."""

        save_initial_data()

        store_count = db.session.scalar(
            db.select(
                db.func.count(Store.id)
            )
        )

        advertisement_count = db.session.scalar(
            db.select(
                db.func.count(Advertisement.id)
            )
        )

        click.echo(
            "Demo data saved successfully."
        )

        click.echo(
            f"Stores: {store_count}"
        )

        click.echo(
            f"Advertisements: {advertisement_count}"
        )

    @app.cli.command("bootstrap-deployment")
    def bootstrap_deployment() -> None:
        """Idempotently seed data and create the first hosted admin."""

        should_seed = os.getenv(
            "SEED_INITIAL_DATA",
            "false",
        ).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        if should_seed:
            save_initial_data()
            click.echo("Initial exhibition data is ready.")

        username = os.getenv(
            "ADMIN_BOOTSTRAP_USERNAME",
            "",
        ).strip().lower()
        email = os.getenv(
            "ADMIN_BOOTSTRAP_EMAIL",
            "",
        ).strip().lower()
        password = os.getenv(
            "ADMIN_BOOTSTRAP_PASSWORD",
            "",
        )

        supplied_values = [
            username,
            email,
            password,
        ]

        if not any(supplied_values):
            click.echo("No administrator bootstrap requested.")
            return

        if not all(supplied_values):
            raise click.ClickException(
                "All ADMIN_BOOTSTRAP variables are required together."
            )

        if len(username) < 3 or len(username) > 40:
            raise click.ClickException(
                "Bootstrap username must contain 3 to 40 characters."
            )

        if "@" not in email or len(email) > 255:
            raise click.ClickException(
                "Bootstrap email is invalid."
            )

        if len(password) < 12:
            raise click.ClickException(
                "Bootstrap password must contain at least 12 characters."
            )

        existing_admin = db.session.scalar(
            db.select(AdminUser).where(
                db.or_(
                    AdminUser.username == username,
                    AdminUser.email == email,
                )
            )
        )

        if existing_admin is not None:
            click.echo("Hosted administrator already exists.")
            return

        admin = AdminUser(
            username=username,
            email=email,
            is_active=True,
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo("Hosted administrator created.")
