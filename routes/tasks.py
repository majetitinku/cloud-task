from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, Task, File
from utils.s3_upload import upload_file_to_s3


tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("/tasks")
@login_required
def task_list():

    # admin gets everything, others just their own stuff
    if current_user.role == "admin":
        tasks = Task.query.order_by(Task.created_at.desc()).all()
    else:
        tasks = Task.query.filter_by(user_id=current_user.id)\
            .order_by(Task.created_at.desc()).all()

    return render_template("tasks/task_list.html", tasks=tasks)


@tasks_bp.route("/tasks/add", methods=["GET", "POST"])
@login_required
def add_task():

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        desc = request.form.get("description", "").strip()
        status = request.form.get("status", "pending")

        if not title:
            flash("Need a title", "danger")
            return redirect(url_for("tasks.add_task"))

        task = Task(
            title=title,
            description=desc,
            status=status,
            user_id=current_user.id
        )

        db.session.add(task)
        db.session.commit()   # save first so we get task.id

        # handle file if user uploaded one
        file_obj = request.files.get("task_file")

        if file_obj and file_obj.filename:
            url = upload_file_to_s3(file_obj, current_user.username)

            if url:
                f = File(file_url=url, task_id=task.id)
                db.session.add(f)
                db.session.commit()   # could optimize later

        current_app.logger.info("task created: %s (user=%s)", title, current_user.username)

        flash("Task added", "success")
        return redirect(url_for("tasks.task_list"))

    return render_template("tasks/task_form.html", task=None)


@tasks_bp.route("/tasks/edit/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task(task_id):

    task = Task.query.get_or_404(task_id)

    # basic permission check
    if current_user.role != "admin" and task.user_id != current_user.id:
        flash("Not allowed", "danger")
        return redirect(url_for("tasks.task_list"))

    if request.method == "POST":

        task.title = request.form.get("title", "").strip()
        task.description = request.form.get("description", "").strip()
        task.status = request.form.get("status", "pending")

        if not task.title:
            flash("Title can't be empty", "danger")
            return redirect(url_for("tasks.edit_task", task_id=task.id))

        # file upload again (optional)
        file_obj = request.files.get("task_file")

        if file_obj and file_obj.filename:
            url = upload_file_to_s3(file_obj, current_user.username)

            if url:
                new_file = File(file_url=url, task_id=task.id)
                db.session.add(new_file)

        db.session.commit()

        current_app.logger.info("task updated: %s by %s", task.title, current_user.username)

        flash("Updated", "success")
        return redirect(url_for("tasks.task_list"))

    return render_template("tasks/task_form.html", task=task)


@tasks_bp.route("/tasks/delete/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):

    task = Task.query.get_or_404(task_id)

    # same permission logic as edit
    if current_user.role != "admin" and task.user_id != current_user.id:
        flash("Not allowed", "danger")
        return redirect(url_for("tasks.task_list"))

    db.session.delete(task)
    db.session.commit()

    current_app.logger.info("deleted task %s by %s", task.title, current_user.username)

    flash("Task removed", "info")
    return redirect(url_for("tasks.task_list"))