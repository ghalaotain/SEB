import re
from datetime import datetime, timezone

import click
from email_validator import (
    EmailNotValidError,
    validate_email,
)
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    session,
    url_for,
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)

from app.extensions import db, limiter
from app.forms import AdminLoginForm
from app.models import AdminUser


auth_bp = Blueprint(
    "auth",
    __name__,
    cli_group=None,
)


@auth_bp.route(
    "/admin/login",
    methods=["GET", "POST"],
)
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(
            url_for(
                "pages.admin_dashboard"
            )
        )

    form = AdminLoginForm()

    if form.validate_on_submit():
        username = (
            form.username.data
            .strip()
            .lower()
        )

        admin = db.session.scalar(
            db.select(AdminUser).where(
                AdminUser.username == username
            )
        )

        valid_login = (
            admin is not None
            and admin.is_active
            and admin.check_password(
                form.password.data
            )
        )

        if not valid_login:
            flash(
                (
                    "The username or password "
                    "is incorrect."
                ),
                "error",
            )

            return render_template(
                "admin/login.html",
                form=form,
            ), 401

        session.clear()

        login_user(
            admin,
            remember=False,
            fresh=True,
        )

        admin.last_login_at = datetime.now(
            timezone.utc
        )

        db.session.commit()

        return redirect(
            url_for(
                "pages.admin_dashboard"
            )
        )

    return render_template(
        "admin/login.html",
        form=form,
    )


@auth_bp.post("/admin/logout")
@login_required
def logout():
    logout_user()
    session.clear()

    flash(
        "You have signed out.",
        "success",
    )

    return redirect(
        url_for("auth.login")
    )


@auth_bp.cli.command("create-admin")
@click.option(
    "--username",
    prompt="Admin username",
)
@click.option(
    "--email",
    prompt="Admin email",
)
@click.password_option(
    prompt="Admin password",
    confirmation_prompt=True,
)
def create_admin(
    username: str,
    email: str,
    password: str,
) -> None:
    normalized_username = (
        username.strip().lower()
    )

    if not re.fullmatch(
        r"[a-z0-9_.-]{3,40}",
        normalized_username,
    ):
        raise click.ClickException(
            (
                "Username must contain 3 to 40 "
                "letters, numbers, dots, "
                "underscores, or hyphens."
            )
        )

    try:
        validated_email = validate_email(
            email.strip(),
            check_deliverability=False,
        )

        normalized_email = (
            validated_email.normalized.lower()
        )

    except EmailNotValidError as error:
        raise click.ClickException(
            str(error)
        ) from error

    if len(password) < 12:
        raise click.ClickException(
            (
                "Password must contain at least "
                "12 characters."
            )
        )

    existing_admin = db.session.scalar(
        db.select(AdminUser).where(
            db.or_(
                AdminUser.username
                == normalized_username,
                AdminUser.email
                == normalized_email,
            )
        )
    )

    if existing_admin is not None:
        raise click.ClickException(
            (
                "An administrator with this "
                "username or email already exists."
            )
        )

    admin = AdminUser(
        username=normalized_username,
        email=normalized_email,
        is_active=True,
    )

    admin.set_password(password)

    db.session.add(admin)
    db.session.commit()

    click.echo(
        "Administrator created successfully."
    )