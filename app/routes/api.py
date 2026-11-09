from datetime import (
    datetime,
    timedelta,
    timezone,
)
from secrets import choice

from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
)

from app.extensions import csrf, db, limiter
from app.models import (
    Advertisement,
    DailyStatistic,
    Store,
    VisitorInteraction,
)
from app.services.ai_analysis import (
    AIAnalysisError,
    AIUnavailableError,
    InvalidImageError,
    NoFaceDetectedError,
    analyze_demographics,
    dependency_status,
)


api_bp = Blueprint(
    "api",
    __name__,
    url_prefix="/api",
)


RIYADH_TIMEZONE = timezone(
    timedelta(hours=3)
)


DEMO_PROFILES = [
    {
        "age": 23,
        "gender": "Woman",
        "age_group": "18-24",
    },
    {
        "age": 29,
        "gender": "Man",
        "age_group": "25-34",
    },
    {
        "age": 41,
        "gender": "Woman",
        "age_group": "35-44",
    },
]


def error_response(
    code: str,
    message: str,
    status_code: int,
):
    return jsonify(
        {
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        }
    ), status_code


@api_bp.get("/health")
def health():
    dependencies = dependency_status()
    ai_status = "disabled"

    if current_app.config["AI_ENABLED"]:
        ai_status = (
            "available"
            if all(dependencies.values())
            else "dependencies_missing"
        )

    database_status = "configured"

    if current_app.config["DEMO_MODE"]:
        database_status = "demo"

    return jsonify(
        {
            "success": True,
            "status": "healthy",
            "mode": current_app.config["APP_MODE"],
            "services": {
                "application": "available",
                "database": database_status,
                "ai": ai_status,
                "ai_dependencies": dependencies,
            },
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }
    ), 200


@api_bp.get("/ads")
def get_ads():
    advertisements = db.session.scalars(
        db.select(Advertisement)
        .where(
            Advertisement.is_active.is_(True),
            Advertisement.target_gender == "all",
        )
        .order_by(Advertisement.id.asc())
    ).all()

    serialized_ads = []

    for advertisement in advertisements:
        advertisement_data = (
            advertisement.to_dict()
        )

        advertisement_data["is_demo"] = (
            current_app.config["DEMO_MODE"]
        )

        serialized_ads.append(
            advertisement_data
        )

    return jsonify(
        {
            "success": True,
            "mode": current_app.config["APP_MODE"],
            "notice": (
                "These advertisements use demo data."
                if current_app.config["DEMO_MODE"]
                else None
            ),
            "ads": serialized_ads,
        }
    ), 200


@api_bp.get("/stores")
def get_stores():
    category = request.args.get(
        "category",
        "",
    ).strip().lower()

    search = request.args.get(
        "search",
        "",
    ).strip()

    statement = (
        db.select(Store)
        .where(
            Store.is_active.is_(True)
        )
        .order_by(
            Store.hall.asc(),
            Store.store_number.asc(),
        )
    )

    if category and category != "all":
        statement = statement.where(
            db.func.lower(Store.category)
            == category
        )

    if search:
        search_pattern = f"%{search}%"

        statement = statement.where(
            db.or_(
                Store.name.ilike(
                    search_pattern
                ),
                Store.category.ilike(
                    search_pattern
                ),
                Store.map_location.ilike(
                    search_pattern
                ),
            )
        )

    stores = db.session.scalars(
        statement
    ).all()

    return jsonify(
        {
            "success": True,
            "mode": current_app.config["APP_MODE"],
            "count": len(stores),
            "stores": [
                store.to_dict()
                for store in stores
            ],
        }
    ), 200


def select_personalized_advertisement(
    age: int,
    gender: str,
):
    personalized_ads = db.session.scalars(
        db.select(Advertisement)
        .where(
            Advertisement.is_active.is_(True),
            Advertisement.target_gender != "all",
        )
        .order_by(Advertisement.id.asc())
    ).all()

    matching_ads = [
        advertisement
        for advertisement in personalized_ads
        if advertisement.matches_demographic(
            age,
            gender,
        )
    ]

    if matching_ads:
        return choice(matching_ads)

    general_ads = db.session.scalars(
        db.select(Advertisement)
        .where(
            Advertisement.is_active.is_(True),
            Advertisement.target_gender == "all",
        )
        .order_by(Advertisement.id.asc())
    ).all()

    if general_ads:
        return choice(general_ads)

    return None


def get_or_create_daily_statistic():
    statistic_date = datetime.now(
        RIYADH_TIMEZONE
    ).date()

    daily_statistic = db.session.scalar(
        db.select(DailyStatistic).where(
            DailyStatistic.date
            == statistic_date
        )
    )

    if daily_statistic is None:
        daily_statistic = DailyStatistic(
            date=statistic_date,
            total_visitors=0,
            male_count=0,
            female_count=0,
            age_18_24=0,
            age_25_34=0,
            age_35_44=0,
            age_45_54=0,
            age_55_plus=0,
        )

        db.session.add(daily_statistic)

    return daily_statistic


def record_anonymous_interaction(
    *,
    age: int,
    gender: str,
    age_group: str,
    advertisement: Advertisement,
    analysis_mode: str,
) -> None:
    daily_statistic = (
        get_or_create_daily_statistic()
    )

    interaction = VisitorInteraction(
        detected_age=age,
        detected_gender=gender,
        age_group=age_group,
        advertisement=advertisement,
        booth_id=current_app.config["BOOTH_ID"],
        analysis_mode=analysis_mode,
    )

    db.session.add(interaction)

    advertisement.view_count = (
        advertisement.view_count or 0
    ) + 1

    daily_statistic.total_visitors = (
        daily_statistic.total_visitors or 0
    ) + 1

    normalized_gender = (
        gender or ""
    ).strip().lower()

    if normalized_gender in {
        "man",
        "male",
    }:
        daily_statistic.male_count = (
            daily_statistic.male_count or 0
        ) + 1

    elif normalized_gender in {
        "woman",
        "female",
    }:
        daily_statistic.female_count = (
            daily_statistic.female_count or 0
        ) + 1

    age_group_fields = {
        "18-24": "age_18_24",
        "25-34": "age_25_34",
        "35-44": "age_35_44",
        "45-54": "age_45_54",
        "55+": "age_55_plus",
    }

    age_field = age_group_fields.get(
        age_group
    )

    if age_field:
        current_value = (
            getattr(
                daily_statistic,
                age_field,
            )
            or 0
        )

        setattr(
            daily_statistic,
            age_field,
            current_value + 1,
        )

    db.session.commit()


@api_bp.post("/analyze")
@csrf.exempt
@limiter.limit("20 per minute")
def analyze_visitor():
    payload = request.get_json(
        silent=True
    )

    if not payload:
        return error_response(
            "INVALID_REQUEST",
            "A JSON request body is required.",
            400,
        )

    image_data = payload.get("image")

    if not isinstance(image_data, str):
        return error_response(
            "IMAGE_REQUIRED",
            (
                "A camera frame is required "
                "for analysis."
            ),
            400,
        )

    if not image_data.startswith(
        "data:image/"
    ):
        return error_response(
            "INVALID_IMAGE",
            (
                "The submitted camera frame "
                "is invalid."
            ),
            400,
        )

    if (
        current_app.config["DEMO_MODE"]
        and not current_app.config["AI_ENABLED"]
    ):
        demo_profile = choice(
            DEMO_PROFILES
        )

        advertisement = (
            select_personalized_advertisement(
                demo_profile["age"],
                demo_profile["gender"],
            )
        )

        if advertisement is None:
            return error_response(
                "NO_ACTIVE_ADVERTISEMENT",
                (
                    "No active advertisement is "
                    "available for this visitor."
                ),
                404,
            )

        try:
            record_anonymous_interaction(
                age=demo_profile["age"],
                gender=demo_profile["gender"],
                age_group=(
                    demo_profile["age_group"]
                ),
                advertisement=advertisement,
                analysis_mode="demo",
            )

        except Exception:
            db.session.rollback()

            current_app.logger.exception(
                (
                    "Failed to record "
                    "visitor interaction."
                )
            )

            return error_response(
                "STATISTICS_ERROR",
                (
                    "The interaction could not "
                    "be recorded."
                ),
                500,
            )

        advertisement_data = (
            advertisement.to_dict()
        )

        advertisement_data[
            "is_demo"
        ] = True

        return jsonify(
            {
                "success": True,
                "mode": "demo",
                "notice": (
                    "This is a simulated AI result. "
                    "It is not a real demographic "
                    "analysis."
                ),
                "analysis": {
                    "age": demo_profile["age"],
                    "gender": (
                        demo_profile["gender"]
                    ),
                    "age_group": (
                        demo_profile["age_group"]
                    ),
                    "is_demo": True,
                },
                "advertisement": (
                    advertisement_data
                ),
            }
        ), 200

    if not current_app.config["AI_ENABLED"]:
        return error_response(
            "AI_UNAVAILABLE",
            (
                "AI analysis is not enabled "
                "on this system."
            ),
            503,
        )

    try:
        analysis = analyze_demographics(
            image_data,
            detector_backend=current_app.config[
                "AI_DETECTOR_BACKEND"
            ],
            maximum_pixels=current_app.config[
                "AI_MAX_IMAGE_PIXELS"
            ],
        )
    except AIUnavailableError as error:
        current_app.logger.warning(
            "AI dependencies are unavailable: %s",
            error,
        )
        return error_response(
            "AI_UNAVAILABLE",
            str(error),
            503,
        )
    except InvalidImageError as error:
        return error_response(
            "INVALID_IMAGE",
            str(error),
            400,
        )
    except NoFaceDetectedError as error:
        return error_response(
            "NO_FACE_DETECTED",
            str(error),
            422,
        )
    except AIAnalysisError as error:
        current_app.logger.warning(
            "Visitor analysis failed: %s",
            error,
        )
        return error_response(
            "ANALYSIS_FAILED",
            str(error),
            422,
        )

    advertisement = select_personalized_advertisement(
        analysis.age,
        analysis.gender,
    )

    if advertisement is None:
        return error_response(
            "NO_ACTIVE_ADVERTISEMENT",
            (
                "No active advertisement is "
                "available for this visitor."
            ),
            404,
        )

    try:
        record_anonymous_interaction(
            age=analysis.age,
            gender=analysis.gender,
            age_group=analysis.age_group,
            advertisement=advertisement,
            analysis_mode="deepface",
        )
    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Failed to record visitor interaction."
        )
        return error_response(
            "STATISTICS_ERROR",
            "The interaction could not be recorded.",
            500,
        )

    advertisement_data = advertisement.to_dict()
    advertisement_data["is_demo"] = False

    return jsonify(
        {
            "success": True,
            "mode": "ai",
            "notice": (
                "The frame was processed temporarily "
                "and was not stored."
            ),
            "analysis": analysis.to_dict(),
            "advertisement": advertisement_data,
        }
    ), 200
