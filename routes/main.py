from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from models import db, Task


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():

    # admin sees all data, normal users just theirs
    if current_user.role == "admin":

        total = Task.query.count()

        completed = Task.query.filter_by(status="completed").count()

        # anything not completed = pending (rough logic for now)
        pending = Task.query.filter(Task.status != "completed").count()

        recent = Task.query.order_by(Task.created_at.desc()).limit(5).all()

    else:
        total = Task.query.filter_by(user_id=current_user.id).count()

        completed = Task.query.filter_by(
            user_id=current_user.id, status="completed"
        ).count()

        pending = Task.query.filter_by(
            user_id=current_user.id, status="pending"
        ).count()

        recent = Task.query.filter_by(user_id=current_user.id)\
            .order_by(Task.created_at.desc())\
            .limit(5).all()

    return render_template(
        "dashboard.html",
        total_tasks=total,
        completed_task=completed,
        pending_task=pending,
        recent_task=recent
    )


@main_bp.route("/analytics")
@login_required
def analytics():

    # grouping tasks by status
    if current_user.role == "admin":
        data = db.session.query(Task.status, func.count(Task.id))\
            .group_by(Task.status).all()
    else:
        data = db.session.query(Task.status, func.count(Task.id))\
            .filter(Task.user_id == current_user.id)\
            .group_by(Task.status).all()

    # quick mapping (status -> count)
    stats = {}
    for row in data:
        stats[row[0]] = row[1]

    completed = stats.get("completed", 0)
    pending = stats.get("pending", 0)

    # might expand later if more statuses added
    in_progress = stats.get("in_progress", 0)

    return render_template(
        "analytics.html",
        completed=completed,
        pending=pending,
        in_progress=in_progress
    )