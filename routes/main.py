from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from models import db, Task
from permissions_lib import is_admin, task_scope_query


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():

    # admin sees all data, normal users just theirs
    base_query = task_scope_query(current_user, Task)
    total = base_query.count()
    completed = base_query.filter_by(status="completed").count()
    if is_admin(current_user):
        pending = base_query.filter(Task.status != "completed").count()
    else:
        pending = base_query.filter_by(status="pending").count()
    recent = base_query.order_by(Task.created_at.desc()).limit(5).all()

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
    if is_admin(current_user):
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
