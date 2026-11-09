from pathlib import Path
from uuid import uuid4

from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
)
from flask_login import login_required

from app.extensions import db
from app.models import Advertisement, Store


advertisements_bp = Blueprint(
    "advertisements",
    __name__,
    url_prefix="/api/advertisements",
)

ALLOWED_GENDERS = {"all", "male", "female"}
ALLOWED_THEMES = {
    "violet",
    "cyan",
    "pink",
    "yellow",
}
ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}
MAX_ADVERTISEMENT_IMAGE_BYTES = 5 * 1024 * 1024
MAX_ADVERTISEMENT_IMAGE_PIXELS = 16_000_000


@advertisements_bp.before_request
@login_required
def require_admin_login():
    return None


def error_response(code, message, status_code):
    return jsonify(
        {
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        }
    ), status_code


@advertisements_bp.post("/upload")
def upload_advertisement_image():
    uploaded_file = request.files.get("image")

    if uploaded_file is None or not uploaded_file.filename:
        return error_response(
            "IMAGE_REQUIRED",
            "Choose an advertisement image to upload.",
            400,
        )

    extension = Path(
        uploaded_file.filename
    ).suffix.lower()

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return error_response(
            "UNSUPPORTED_IMAGE_TYPE",
            "Use a JPEG, PNG, or WebP image.",
            400,
        )

    image_bytes = uploaded_file.stream.read(
        MAX_ADVERTISEMENT_IMAGE_BYTES + 1
    )

    if len(image_bytes) > MAX_ADVERTISEMENT_IMAGE_BYTES:
        return error_response(
            "IMAGE_TOO_LARGE",
            "Advertisement images must be 5 MB or smaller.",
            413,
        )

    if not image_bytes:
        return error_response(
            "INVALID_IMAGE",
            "The selected image is empty.",
            400,
        )

    try:
        import cv2
        import numpy as np
    except ImportError:
        return error_response(
            "IMAGE_PROCESSOR_UNAVAILABLE",
            "The server image processor is unavailable.",
            503,
        )

    image_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8,
    )
    image = cv2.imdecode(
        image_array,
        cv2.IMREAD_UNCHANGED,
    )

    if image is None or image.size == 0:
        return error_response(
            "INVALID_IMAGE",
            "The selected file is not a valid image.",
            400,
        )

    height, width = image.shape[:2]

    if height * width > MAX_ADVERTISEMENT_IMAGE_PIXELS:
        return error_response(
            "IMAGE_DIMENSIONS_TOO_LARGE",
            "Advertisement images must be smaller than 16 megapixels.",
            400,
        )

    output_extension = (
        ".png"
        if image.ndim == 3 and image.shape[2] == 4
        else ".jpg"
    )
    output_directory = Path(
        current_app.static_folder
    ) / "uploads" / "advertisements"
    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = f"{uuid4().hex}{output_extension}"
    output_path = output_directory / filename
    encoding_parameters = (
        [cv2.IMWRITE_PNG_COMPRESSION, 7]
        if output_extension == ".png"
        else [cv2.IMWRITE_JPEG_QUALITY, 88]
    )

    encoding_succeeded, encoded_image = cv2.imencode(
        output_extension,
        image,
        encoding_parameters,
    )

    if not encoding_succeeded:
        return error_response(
            "IMAGE_SAVE_FAILED",
            "The advertisement image could not be saved.",
            500,
        )

    try:
        output_path.write_bytes(
            encoded_image.tobytes()
        )
    except OSError:
        current_app.logger.exception(
            "Advertisement image could not be written."
        )
        return error_response(
            "IMAGE_SAVE_FAILED",
            "The advertisement image could not be saved.",
            500,
        )

    image_url = (
        "/static/uploads/advertisements/"
        f"{filename}"
    )

    return jsonify(
        {
            "success": True,
            "message": "Advertisement image uploaded.",
            "image_url": image_url,
            "width": width,
            "height": height,
        }
    ), 201


def clean_text(value, maximum_length=None):
    if value is None:
        return None

    cleaned = str(value).strip()

    if not cleaned:
        return None

    if maximum_length is not None:
        cleaned = cleaned[:maximum_length]

    return cleaned


def parse_optional_age(value, field_name):
    if value in (None, ""):
        return None, None

    if isinstance(value, bool):
        return None, f"{field_name} must be a number."

    try:
        age = int(value)
    except (TypeError, ValueError):
        return None, f"{field_name} must be a number."

    if age < 0 or age > 120:
        return None, f"{field_name} must be between 0 and 120."

    return age, None


def parse_boolean(value, default=None):
    if isinstance(value, bool):
        return value

    if value in (1, "1", "true", "True"):
        return True

    if value in (0, "0", "false", "False"):
        return False

    return default


def validate_payload(payload, *, partial=False):
    if not isinstance(payload, dict):
        return None, "Request body must be a JSON object."

    values = {}

    if not partial or "title" in payload:
        title = clean_text(payload.get("title"), 200)

        if not title:
            return None, "Advertisement title is required."

        values["title"] = title

    if not partial or "category" in payload:
        category = clean_text(payload.get("category"), 80)

        if not category:
            return None, "Advertisement category is required."

        values["category"] = category

    text_fields = {
        "description": None,
        "image_path": 500,
        "qr_code_url": 500,
        "map_location": 150,
    }

    for field_name, maximum_length in text_fields.items():
        if field_name in payload:
            values[field_name] = clean_text(
                payload.get(field_name),
                maximum_length,
            )
        elif not partial:
            values[field_name] = None

    if not partial or "target_gender" in payload:
        gender = clean_text(
            payload.get("target_gender") or "all",
            20,
        ).lower()

        if gender not in ALLOWED_GENDERS:
            return None, "Target gender must be all, male, or female."

        values["target_gender"] = gender

    if not partial or "theme" in payload:
        theme = clean_text(
            payload.get("theme") or "violet",
            20,
        ).lower()

        if theme not in ALLOWED_THEMES:
            return None, "Advertisement theme is not supported."

        values["theme"] = theme

    age_minimum = None
    age_maximum = None

    if "target_age_min" in payload or not partial:
        age_minimum, age_error = parse_optional_age(
            payload.get("target_age_min"),
            "Minimum age",
        )

        if age_error:
            return None, age_error

        values["target_age_min"] = age_minimum

    if "target_age_max" in payload or not partial:
        age_maximum, age_error = parse_optional_age(
            payload.get("target_age_max"),
            "Maximum age",
        )

        if age_error:
            return None, age_error

        values["target_age_max"] = age_maximum

    if (
        age_minimum is not None
        and age_maximum is not None
        and age_maximum < age_minimum
    ):
        return None, "Maximum age cannot be lower than minimum age."

    if "store_id" in payload:
        store_id = payload.get("store_id")

        if store_id in (None, ""):
            values["store_id"] = None
        else:
            try:
                store_id = int(store_id)
            except (TypeError, ValueError):
                return None, "Store selection is invalid."

            store = db.session.get(Store, store_id)

            if store is None:
                return None, "Selected store was not found."

            values["store_id"] = store.id

            if not values.get("map_location"):
                values["map_location"] = store.map_location
    elif not partial:
        values["store_id"] = None

    if "is_active" in payload or not partial:
        is_active = parse_boolean(
            payload.get("is_active"),
            True,
        )
        values["is_active"] = is_active

    return values, None


@advertisements_bp.get("")
def list_advertisements():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "all").strip().lower()

    statement = db.select(Advertisement)

    if search:
        search_term = f"%{search}%"
        statement = statement.where(
            db.or_(
                Advertisement.title.ilike(search_term),
                Advertisement.description.ilike(search_term),
                Advertisement.category.ilike(search_term),
            )
        )

    if category:
        statement = statement.where(
            Advertisement.category == category
        )

    if status == "active":
        statement = statement.where(
            Advertisement.is_active.is_(True)
        )
    elif status == "inactive":
        statement = statement.where(
            Advertisement.is_active.is_(False)
        )

    advertisements = db.session.scalars(
        statement.order_by(
            Advertisement.created_at.desc(),
            Advertisement.id.desc(),
        )
    ).all()

    return jsonify(
        {
            "success": True,
            "count": len(advertisements),
            "advertisements": [
                advertisement.to_dict()
                for advertisement in advertisements
            ],
        }
    ), 200


@advertisements_bp.post("")
def create_advertisement():
    payload = request.get_json(silent=True)
    values, validation_error = validate_payload(payload)

    if validation_error:
        return error_response(
            "VALIDATION_ERROR",
            validation_error,
            400,
        )

    advertisement = Advertisement(**values)

    try:
        db.session.add(advertisement)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error_response(
            "DATABASE_ERROR",
            "Advertisement could not be created.",
            500,
        )

    return jsonify(
        {
            "success": True,
            "message": "Advertisement created.",
            "advertisement": advertisement.to_dict(),
        }
    ), 201


@advertisements_bp.put("/<int:advertisement_id>")
def update_advertisement(advertisement_id):
    advertisement = db.session.get(
        Advertisement,
        advertisement_id,
    )

    if advertisement is None:
        return error_response(
            "ADVERTISEMENT_NOT_FOUND",
            "Advertisement was not found.",
            404,
        )

    payload = request.get_json(silent=True)
    values, validation_error = validate_payload(payload)

    if validation_error:
        return error_response(
            "VALIDATION_ERROR",
            validation_error,
            400,
        )

    for field_name, value in values.items():
        setattr(advertisement, field_name, value)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error_response(
            "DATABASE_ERROR",
            "Advertisement could not be updated.",
            500,
        )

    return jsonify(
        {
            "success": True,
            "message": "Advertisement updated.",
            "advertisement": advertisement.to_dict(),
        }
    ), 200


@advertisements_bp.patch("/<int:advertisement_id>/status")
def update_advertisement_status(advertisement_id):
    advertisement = db.session.get(
        Advertisement,
        advertisement_id,
    )

    if advertisement is None:
        return error_response(
            "ADVERTISEMENT_NOT_FOUND",
            "Advertisement was not found.",
            404,
        )

    payload = request.get_json(silent=True) or {}
    is_active = parse_boolean(payload.get("is_active"))

    if is_active is None:
        return error_response(
            "VALIDATION_ERROR",
            "is_active must be true or false.",
            400,
        )

    advertisement.is_active = is_active

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error_response(
            "DATABASE_ERROR",
            "Advertisement status could not be updated.",
            500,
        )

    return jsonify(
        {
            "success": True,
            "message": (
                "Advertisement activated."
                if is_active
                else "Advertisement deactivated."
            ),
            "advertisement": advertisement.to_dict(),
        }
    ), 200


@advertisements_bp.delete("/<int:advertisement_id>")
def delete_advertisement(advertisement_id):
    advertisement = db.session.get(
        Advertisement,
        advertisement_id,
    )

    if advertisement is None:
        return error_response(
            "ADVERTISEMENT_NOT_FOUND",
            "Advertisement was not found.",
            404,
        )

    try:
        db.session.delete(advertisement)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error_response(
            "DATABASE_ERROR",
            "Advertisement could not be deleted.",
            500,
        )

    return jsonify(
        {
            "success": True,
            "message": "Advertisement deleted.",
        }
    ), 200
