# Quickstart (after Construction)

Operator path matches [README.md](../../README.md). Construction must make these commands work.

## Local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# set JWT_SECRET and ADMIN_*

python -m app.cli init
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
curl -s http://127.0.0.1:8000/health
curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"<ADMIN_PASSWORD>"}'
```

Expect 200 on health. Login 200 includes `access_token`, `token_type: bearer`, and `user_id`. Use `Authorization: Bearer <access_token>` on later requests.

## Tests (TDD)

```bash
pytest
```

Each Requirements AC is a `test_ac_*` function. Do not add `.feature` files.

## Docker (optional)

Secrets via `env_file`, not the image. Init then serve:

```bash
docker compose run --rm api python -m app.cli init
docker compose up
```
