from uuid import uuid4

from flask_login import UserMixin
from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

from .extensions import db


class TimestampMixin:
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )


class AdminUser(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "admin_users"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False,
        index=True,
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    last_login_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(
            password
        )

    def check_password(self, password: str) -> bool:
        return check_password_hash(
            self.password_hash,
            password,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
        }


class Store(TimestampMixin, db.Model):
    __tablename__ = "stores"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    name = db.Column(
        db.String(150),
        nullable=False,
        index=True,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    category = db.Column(
        db.String(80),
        nullable=False,
        index=True,
    )

    hall = db.Column(
        db.String(30),
        nullable=False,
    )

    store_number = db.Column(
        db.String(30),
        nullable=False,
    )

    map_location = db.Column(
        db.String(150),
        nullable=False,
        unique=True,
        index=True,
    )

    opening_hours = db.Column(
        db.String(120),
        nullable=True,
    )

    qr_code_url = db.Column(
        db.String(500),
        nullable=True,
    )

    icon = db.Column(
        db.String(10),
        nullable=True,
    )

    color = db.Column(
        db.String(20),
        nullable=False,
        default="#7565ff",
    )

    map_position = db.Column(
        db.JSON,
        nullable=True,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    advertisements = db.relationship(
        "Advertisement",
        back_populates="store",
        lazy="dynamic",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "hall": self.hall,
            "store_number": self.store_number,
            "map_location": self.map_location,
            "opening_hours": self.opening_hours,
            "qr_code_url": self.qr_code_url,
            "icon": self.icon,
            "color": self.color,
            "map_position": self.map_position or {},
            "is_active": self.is_active,
        }


class Advertisement(TimestampMixin, db.Model):
    __tablename__ = "advertisements"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    title = db.Column(
        db.String(200),
        nullable=False,
        index=True,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    image_path = db.Column(
        db.String(500),
        nullable=True,
    )

    target_gender = db.Column(
        db.String(20),
        nullable=False,
        default="all",
        index=True,
    )

    target_age_min = db.Column(
        db.Integer,
        nullable=True,
    )

    target_age_max = db.Column(
        db.Integer,
        nullable=True,
    )

    category = db.Column(
        db.String(80),
        nullable=False,
        index=True,
    )

    theme = db.Column(
        db.String(20),
        nullable=False,
        default="violet",
    )

    qr_code_url = db.Column(
        db.String(500),
        nullable=True,
    )

    map_location = db.Column(
        db.String(150),
        nullable=True,
    )

    store_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "stores.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    view_count = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    store = db.relationship(
        "Store",
        back_populates="advertisements",
    )

    interactions = db.relationship(
        "VisitorInteraction",
        back_populates="advertisement",
        lazy="dynamic",
    )

    __table_args__ = (
        db.CheckConstraint(
            "target_age_min IS NULL "
            "OR target_age_min >= 0",
            name="ck_ad_target_age_min",
        ),
        db.CheckConstraint(
            "target_age_max IS NULL "
            "OR target_age_max >= target_age_min",
            name="ck_ad_target_age_range",
        ),
    )

    def matches_demographic(
        self,
        age: int,
        gender: str,
    ) -> bool:
        normalized_gender = (gender or "").strip().lower()

        gender_matches = (
            self.target_gender == "all"
            or self.target_gender.lower()
            == normalized_gender
        )

        minimum_matches = (
            self.target_age_min is None
            or age >= self.target_age_min
        )

        maximum_matches = (
            self.target_age_max is None
            or age <= self.target_age_max
        )

        return (
            self.is_active
            and gender_matches
            and minimum_matches
            and maximum_matches
        )

    def to_dict(self) -> dict:
        location = self.map_location

        if not location and self.store:
            location = self.store.map_location

        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "image_path": self.image_path,
            "image_url": self.image_path,
            "target_gender": self.target_gender,
            "target_age_min": self.target_age_min,
            "target_age_max": self.target_age_max,
            "category": self.category,
            "theme": self.theme,
            "qr_code_url": self.qr_code_url,
            "map_location": location,
            "store_id": self.store_id,
            "is_active": self.is_active,
            "view_count": self.view_count,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else None
            ),
        }


class VisitorInteraction(db.Model):
    __tablename__ = "visitor_interactions"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    visitor_id = db.Column(
        db.String(32),
        nullable=False,
        default=lambda: uuid4().hex,
        index=True,
    )

    detected_age = db.Column(
        db.Integer,
        nullable=True,
    )

    detected_gender = db.Column(
        db.String(20),
        nullable=True,
        index=True,
    )

    age_group = db.Column(
        db.String(20),
        nullable=True,
        index=True,
    )

    advertisement_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "advertisements.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    displayed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        index=True,
    )

    booth_id = db.Column(
        db.String(80),
        nullable=False,
        default="booth_1",
        index=True,
    )

    analysis_mode = db.Column(
        db.String(20),
        nullable=False,
        default="demo",
    )

    advertisement = db.relationship(
        "Advertisement",
        back_populates="interactions",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "visitor_id": self.visitor_id,
            "detected_age": self.detected_age,
            "detected_gender": self.detected_gender,
            "age_group": self.age_group,
            "advertisement_id": self.advertisement_id,
            "displayed_at": (
                self.displayed_at.isoformat()
                if self.displayed_at
                else None
            ),
            "booth_id": self.booth_id,
            "analysis_mode": self.analysis_mode,
        }


class DailyStatistic(db.Model):
    __tablename__ = "daily_statistics"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    date = db.Column(
        db.Date,
        unique=True,
        nullable=False,
        index=True,
    )

    total_visitors = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    male_count = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    female_count = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    age_18_24 = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    age_25_34 = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    age_35_44 = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    age_45_54 = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    age_55_plus = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "total_visitors": self.total_visitors,
            "male_count": self.male_count,
            "female_count": self.female_count,
            "age_groups": {
                "18-24": self.age_18_24,
                "25-34": self.age_25_34,
                "35-44": self.age_35_44,
                "45-54": self.age_45_54,
                "55+": self.age_55_plus,
            },
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else None
            ),
        }