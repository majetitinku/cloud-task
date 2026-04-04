# Simple EC2 Deploy (GitHub Actions)

This repo has a GitHub Actions workflow that deploys the app to an EC2 instance whenever code is pushed to the `main` branch. I wrote this README in a simple, student-style explanation so it is easy to follow.

## What it does
- Runs on every push to `main`
- Connects to an EC2 server using SSH
- Clones the repo the first time
- Pulls the latest code on each deploy
- Ensures Python3 and Git are installed
- Creates/uses a virtual environment
- Installs dependencies
- Restarts the systemd service

## Workflow file
The workflow is at `.github/workflows/deploy.yml`.

## Dependencies required
These are in `requirements.txt`:
- `Flask==3.0.3`
- `Flask-Login==0.6.3`
- `Flask-SQLAlchemy==3.1.1`
- `psycopg[binary]==3.2.9`
- `boto3==1.34.131`
- `python-dotenv==1.0.1`
- `gunicorn==22.0.0`

## Deployment files
- `.github/workflows/deploy.yml` = GitHub Actions deploy workflow
- `wsgi.py` = WSGI entry point for Gunicorn (used when running in production)
- `requirements.txt` = dependency list installed during deploy

## Configuration files
- `.env` = local environment variables (do not commit secrets)
- `.env.example` = sample env file you can copy and fill
- `instance/` = local instance data folder (if your app writes SQLite or configs)

## Required GitHub Secrets
You need to add these secrets in the repo settings:
- `EC2_HOST` = public IP or DNS of your EC2
- `EC2_USER` = SSH username (like `ec2-user` for Amazon Linux)
- `EC2_SSH_KEY` = private key content for SSH (the whole PEM file)

## What happens on the EC2 server
The workflow runs these main steps:
1. `cd /home/ec2-user`
2. If `cloud-task` folder does not exist, it clones the repo
3. Goes into `cloud-task` and pulls from `main`
4. Installs Python3 and Git if missing
5. Creates `venv` if missing
6. Activates `venv`
7. Installs requirements
8. Restarts the `task-manager` service

## Notes
- The repo URL is hardcoded to `https://github.com/majetitinku/cloud-task.git`. Change it if you forked.
- The service name is `task-manager`. Make sure your EC2 has a systemd service with that name.
- This is a simple deploy and does not handle migrations or advanced rollback.

## Quick setup checklist
1. Add the required secrets in GitHub.
2. Make sure the EC2 instance allows SSH from GitHub Actions (or your runner).
3. Confirm `task-manager` service exists on the EC2.
4. Push to `main` to trigger deploy.
