import base64
import binascii
from dataclasses import dataclass
from importlib.util import find_spec


class AIAnalysisError(Exception):
    """Base exception for safe visitor-analysis errors."""


class AIUnavailableError(AIAnalysisError):
    """Raised when AI dependencies cannot be loaded."""


class InvalidImageError(AIAnalysisError):
    """Raised when the submitted frame cannot be decoded."""


class NoFaceDetectedError(AIAnalysisError):
    """Raised when no usable face is visible in the frame."""


@dataclass(frozen=True)
class DemographicAnalysis:
    age: int
    gender: str
    age_group: str

    def to_dict(self):
        return {
            "age": self.age,
            "gender": self.gender,
            "age_group": self.age_group,
            "is_demo": False,
        }


def dependency_status():
    return {
        "opencv": find_spec("cv2") is not None,
        "deepface": find_spec("deepface") is not None,
    }


def age_group_for(age):
    if age < 18:
        return "Under 18"
    if age <= 24:
        return "18-24"
    if age <= 34:
        return "25-34"
    if age <= 44:
        return "35-44"
    if age <= 54:
        return "45-54"
    return "55+"


def decode_data_url(image_data, maximum_pixels=16_000_000):
    try:
        header, encoded_image = image_data.split(",", 1)
    except ValueError as error:
        raise InvalidImageError(
            "The camera frame is not a valid data URL."
        ) from error

    allowed_headers = {
        "data:image/jpeg;base64",
        "data:image/jpg;base64",
        "data:image/png;base64",
        "data:image/webp;base64",
    }

    if header.lower() not in allowed_headers:
        raise InvalidImageError(
            "The camera frame must be a JPEG, PNG, or WebP image."
        )

    try:
        image_bytes = base64.b64decode(
            encoded_image,
            validate=True,
        )
    except (binascii.Error, ValueError) as error:
        raise InvalidImageError(
            "The camera frame contains invalid image data."
        ) from error

    if not image_bytes:
        raise InvalidImageError(
            "The submitted camera frame is empty."
        )

    try:
        import cv2
        import numpy as np
    except ImportError as error:
        raise AIUnavailableError(
            "OpenCV is not installed on the server."
        ) from error

    image_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8,
    )
    frame = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR,
    )

    if frame is None or frame.size == 0:
        raise InvalidImageError(
            "The submitted camera frame could not be decoded."
        )

    height, width = frame.shape[:2]

    if height * width > maximum_pixels:
        raise InvalidImageError(
            "The submitted camera frame is too large."
        )

    return frame


def normalize_gender(result):
    dominant_gender = result.get("dominant_gender")

    if not dominant_gender:
        scores = result.get("gender") or {}

        if scores:
            dominant_gender = max(
                scores,
                key=scores.get,
            )

    normalized = str(
        dominant_gender or ""
    ).strip().lower()

    if normalized in {"woman", "female"}:
        return "female"

    if normalized in {"man", "male"}:
        return "male"

    raise AIAnalysisError(
        "Gender estimation was unavailable for this frame."
    )


def face_area(result):
    region = result.get("region") or {}

    try:
        return int(region.get("w", 0)) * int(
            region.get("h", 0)
        )
    except (TypeError, ValueError):
        return 0


def analyze_demographics(
    image_data,
    *,
    detector_backend="opencv",
    maximum_pixels=16_000_000,
):
    frame = decode_data_url(
        image_data,
        maximum_pixels=maximum_pixels,
    )

    try:
        from deepface import DeepFace
    except ImportError as error:
        raise AIUnavailableError(
            "DeepFace is not installed on the server."
        ) from error

    try:
        results = DeepFace.analyze(
            img_path=frame,
            actions=["age", "gender"],
            detector_backend=detector_backend,
            enforce_detection=True,
            align=True,
            silent=True,
        )
    except ValueError as error:
        message = str(error).lower()

        if "face" in message:
            raise NoFaceDetectedError(
                "No face was detected. Look toward the camera and try again."
            ) from error

        raise AIAnalysisError(
            "The visitor analysis could not be completed."
        ) from error
    except Exception as error:
        raise AIAnalysisError(
            "The AI model could not analyze this frame."
        ) from error

    if isinstance(results, dict):
        results = [results]

    if not results:
        raise NoFaceDetectedError(
            "No face was detected. Look toward the camera and try again."
        )

    primary_result = max(
        results,
        key=face_area,
    )

    try:
        estimated_age = round(
            float(primary_result.get("age"))
        )
    except (TypeError, ValueError) as error:
        raise AIAnalysisError(
            "Age estimation was unavailable for this frame."
        ) from error

    estimated_age = max(
        0,
        min(estimated_age, 120),
    )
    estimated_gender = normalize_gender(
        primary_result
    )

    return DemographicAnalysis(
        age=estimated_age,
        gender=estimated_gender,
        age_group=age_group_for(estimated_age),
    )
