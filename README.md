# NTI DevOps Platform

A Django app deployed to AWS through the full DevOps lifecycle:
Terraform → Ansible → Docker → EKS → Helm → Jenkins (SonarQube, Trivy) → Argo CD → Prometheus/Grafana.

Rebuilt from scratch, following the architecture of the
[19-lab NTI project](https://github.com/Waleeddarwesh/StepByStep_Final_NTI_Project),
with its missing pieces (the application itself, SonarQube, EBS CSI, Argo CD) added
and its known bugs fixed.

## The application

**NTI DevOps Notes**: create notes (stored in **PostgreSQL**), a visit counter (**Redis**),
optional attachments (**S3**), and a page that shows which pod answered the request.

| Endpoint | Purpose | Used by |
|---|---|---|
| `/` | Notes page | Users |
| `/health/` | Liveness: process is alive, touches no dependency | Docker HEALTHCHECK, K8s liveness/startup, ALB |
| `/health/ready/` | Readiness: DB + Redis reachable, else **503** | K8s readiness probe |
| `/metrics` | Prometheus metrics (blocked at Nginx/ALB) | Prometheus ServiceMonitor |
| `/admin/` | Django admin | You |

Settings: `config.settings.development` (Compose), `.test` (CI), `.production` (EKS).
All configuration comes from environment variables. The database is configured with
`DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD` (safe for RDS passwords with special characters),
or with `DATABASE_URL`.

## Repository layout

```
app/                 Lab 09  Django source, Dockerfile, entrypoint, tests
docker-compose.yml   Lab 10  Local stack: Nginx → app → Postgres + Redis
docker-compose.test.yml      Test override for CI
nginx/               Lab 10  Reverse proxy config
terraform/           Labs 01–06  (added step by step)
ansible/             Labs 07–08
k8s/                 Labs 11–13
helm/                Labs 14–15
jenkins/             Lab 16
monitoring/          Labs 17–18
gitops/              Argo CD extension
docs/                Lab 19 runbooks
```

## Run locally (Lab 10)

```bash
cp .env.example .env        # then edit SECRET_KEY and DB_PASSWORD
docker compose up -d --build
docker compose ps           # all services "healthy"
curl http://localhost:8080/health/ready/
# open http://localhost:8080
```

Run the tests (same command Jenkins uses):

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml \
  run --rm app python manage.py test --verbosity=2
docker compose -f docker-compose.yml -f docker-compose.test.yml down -v
```

Stop everything: `docker compose down` (add `-v` to also delete the database volume).
