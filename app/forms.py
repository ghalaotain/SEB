from flask_wtf import FlaskForm
from wtforms import (
    PasswordField,
    StringField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    Length,
)


class AdminLoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(
                message="Enter your username."
            ),
            Length(
                min=3,
                max=80,
                message=(
                    "Username must contain "
                    "3 to 80 characters."
                ),
            ),
        ],
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(
                message="Enter your password."
            ),
            Length(
                min=8,
                max=128,
                message=(
                    "Password must contain "
                    "8 to 128 characters."
                ),
            ),
        ],
    )

    submit = SubmitField("Sign in")