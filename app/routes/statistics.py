from flask_login import login_required
from datetime import (
    datetime,
    timedelta,
    timezone,
)

from flask import (
    Blueprint,
    current_app,
    jsonify,
)

from app.extensions import db
from app.models import (
    Advertisement,
    DailyStatistic,
)


statistics_bp = Blueprint(
    "statistics",
    __name__,
    url_prefix="/api/statistics",
)
@statistics_bp.before_request
@login_required
def require_admin_login():
    return None


RIYADH_TIMEZONE = timezone(
    timedelta(hours=3)
)


def get_daily_records():
    records = db.session.scalars(
        db.select(DailyStatistic)
        .order_by(
            DailyStatistic.date.desc()
        )
        .limit(30)
    ).all()

    return list(reversed(records))


def calculate_totals(records):
    totals = {
        "total_visitors": 0,
        "male_count": 0,
        "female_count": 0,
        "age_18_24": 0,
        "age_25_34": 0,
        "age_35_44": 0,
        "age_45_54": 0,
        "age_55_plus": 0,
    }

    for record in records:
        totals["total_visitors"] += (
            record.total_visitors or 0
        )

        totals["male_count"] += (
            record.male_count or 0
        )

        totals["female_count"] += (
            record.female_count or 0
        )

        totals["age_18_24"] += (
            record.age_18_24 or 0
        )

        totals["age_25_34"] += (
            record.age_25_34 or 0
        )

        totals["age_35_44"] += (
            record.age_35_44 or 0
        )

        totals["age_45_54"] += (
            record.age_45_54 or 0
        )

        totals["age_55_plus"] += (
            record.age_55_plus or 0
        )

    return totals


@statistics_bp.get("")
def statistics_summary():
    daily_records = get_daily_records()
    totals = calculate_totals(daily_records)

    advertisements = db.session.scalars(
        db.select(Advertisement)
        .order_by(Advertisement.id.asc())
    ).all()

    active_advertisements = sum(
        1
        for advertisement in advertisements
        if advertisement.is_active
    )

    total_ad_views = sum(
        advertisement.view_count or 0
        for advertisement in advertisements
    )

    today = datetime.now(
        RIYADH_TIMEZONE
    ).date()

    today_record = next(
        (
            record
            for record in daily_records
            if record.date == today
        ),
        None,
    )

    today_visitors = (
        today_record.total_visitors
        if today_record
        else 0
    )

    daily_data = [
        {
            "date": record.date.isoformat(),
            "total_visitors": (
                record.total_visitors or 0
            ),
            "male_count": (
                record.male_count or 0
            ),
            "female_count": (
                record.female_count or 0
            ),
        }
        for record in daily_records
    ]

    return jsonify(
        {
            "success": True,
            "mode": current_app.config[
                "APP_MODE"
            ],
            "summary": {
                "total_visitors": totals[
                    "total_visitors"
                ],
                "today_visitors": (
                    today_visitors or 0
                ),
                "male_count": totals[
                    "male_count"
                ],
                "female_count": totals[
                    "female_count"
                ],
                "active_advertisements": (
                    active_advertisements
                ),
                "total_ad_views": (
                    total_ad_views
                ),
            },
            "daily": daily_data,
            "generated_at": datetime.now(
                RIYADH_TIMEZONE
            ).isoformat(),
        }
    ), 200


@statistics_bp.get("/demographics")
def demographics_statistics():
    daily_records = get_daily_records()
    totals = calculate_totals(daily_records)

    known_gender_total = (
        totals["male_count"]
        + totals["female_count"]
    )

    unknown_gender_count = max(
        totals["total_visitors"]
        - known_gender_total,
        0,
    )

    return jsonify(
        {
            "success": True,
            "mode": current_app.config[
                "APP_MODE"
            ],
            "total_visitors": totals[
                "total_visitors"
            ],
            "gender": [
                {
                    "label": "Male",
                    "value": totals[
                        "male_count"
                    ],
                },
                {
                    "label": "Female",
                    "value": totals[
                        "female_count"
                    ],
                },
                {
                    "label": "Unknown",
                    "value": (
                        unknown_gender_count
                    ),
                },
            ],
            "age_groups": [
                {
                    "label": "18-24",
                    "value": totals[
                        "age_18_24"
                    ],
                },
                {
                    "label": "25-34",
                    "value": totals[
                        "age_25_34"
                    ],
                },
                {
                    "label": "35-44",
                    "value": totals[
                        "age_35_44"
                    ],
                },
                {
                    "label": "45-54",
                    "value": totals[
                        "age_45_54"
                    ],
                },
                {
                    "label": "55+",
                    "value": totals[
                        "age_55_plus"
                    ],
                },
            ],
        }
    ), 200


@statistics_bp.get("/advertisements")
def advertisement_statistics():
    advertisements = db.session.scalars(
        db.select(Advertisement)
        .order_by(
            Advertisement.view_count.desc(),
            Advertisement.title.asc(),
        )
    ).all()

    return jsonify(
        {
            "success": True,
            "mode": current_app.config[
                "APP_MODE"
            ],
            "count": len(advertisements),
            "advertisements": [
                {
                    "id": advertisement.id,
                    "title": advertisement.title,
                    "category": (
                        advertisement.category
                    ),
                    "target_gender": (
                        advertisement.target_gender
                    ),
                    "target_age_min": (
                        advertisement.target_age_min
                    ),
                    "target_age_max": (
                        advertisement.target_age_max
                    ),
                    "view_count": (
                        advertisement.view_count
                        or 0
                    ),
                    "is_active": (
                        advertisement.is_active
                    ),
                    "map_location": (
                        advertisement.map_location
                    ),
                }
                for advertisement
                in advertisements
            ],
        }
    ), 200