# AWS Elastic Beanstalk Free Tier Deploy

## Required Repo Files

- `app.py`
- `requirements.txt`
- `Procfile`
- `models/ppd_logistic_regression.joblib`
- `models/ppd_logistic_regression_metadata.json`

## Elastic Beanstalk Settings

- Platform: Python
- Environment type: Single instance
- Instance type: `t2.micro` or `t3.micro`
- Start command: from `Procfile`
- Web process: `gunicorn app:app`

## Environment Variables

Set these in Elastic Beanstalk configuration:

- `FLASK_SECRET_KEY`
- `CREWAI_ENABLED=true`
- `GROQ_API_KEY`
- `GROQ_MODEL=groq/llama-3.1-8b-instant`
- `HF_TOKEN` optional

Do not upload `.env`.

## Console Steps

1. Open AWS Elastic Beanstalk.
2. Create application.
3. Choose Web server environment.
4. Choose Python platform.
5. Upload the project zip or connect deployment workflow.
6. Choose Single instance.
7. Choose `t2.micro` or `t3.micro`.
8. Add environment variables.
9. Deploy.

## Free Tier Caution

Avoid load balancer, RDS, multiple EC2 instances, and large storage.
