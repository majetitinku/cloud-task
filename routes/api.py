from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from models import db, Task


api_bp = Blueprint("api", __name__)


def _task_to_dict(task):
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "created_at": task.created_at.isoformat(),
        "user_id": task.user_id,
    }


@api_bp.route("/tasks", methods=["GET"])
@login_required
def get_tasks():
    if current_user.role == "admin":
        tasks = Task.query.order_by(Task.created_at.desc()).all()
    else:
        tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.created_at.desc()).all()
    return jsonify([_task_to_dict(t) for t in tasks]), 200


@api_bp.route("/tasks", methods=["POST"])
@login_required
def create_task_api():
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    status = data.get("status", "pending")

    if not title:
        return jsonify({"error": "title is required"}), 400

    task = Task(
        title=title,
        description=description,
        status=status,
        user_id=current_user.id,
    )
    db.session.add(task)
    db.session.commit()

    return jsonify(_task_to_dict(task)), 201


@api_bp.route("/tasks/<int:task_id>", methods=["PUT"])
@login_required
def update_task_api(task_id):
    task = Task.query.get_or_404(task_id)

    if current_user.role != "admin" and task.user_id != current_user.id:
        return jsonify({"error": "not allowed"}), 403

    data = request.get_json() or {}
    task.title = (data.get("title") or task.title).strip()
    task.description = (data.get("description") or task.description or "").strip()
    task.status = data.get("status", task.status)

    db.session.commit()
    return jsonify(_task_to_dict(task)), 200


@api_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task_api(task_id):
    task = Task.query.get_or_404(task_id)

    if current_user.role != "admin" and task.user_id != current_user.id:
        return jsonify({"error": "not allowed"}), 403

    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "task deleted"}), 200
