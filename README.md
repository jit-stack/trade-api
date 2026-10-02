# Mock Trade Order API — DevOps Practice Project

A small FastAPI service that mimics a trading platform backend (login, market
data, order entry, order status). The app itself is intentionally simple —
the point of this project is everything wrapped around it: containers,
CI/CD, cloud deployment, and monitoring.

## Endpoints

| Method | Path                  | Description                       |
|--------|-----------------------|------------------------------------|
| GET    | `/`                   | Service info                       |
| GET    | `/health`             | Health check (for LB / containers) |
| POST   | `/login`              | Create a session                   |
| GET    | `/market-data/{sym}`  | Get a fake live price              |
| POST   | `/orders`             | Place an order                     |
| GET    | `/orders/{order_id}`  | Get one order's status             |
| GET    | `/orders`             | List all orders                    |

---

## Stage 1 — Run it locally (no Docker)

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs — FastAPI auto-generates interactive API
docs. Try `/login`, then `/orders`, then `/market-data/AAPL`.

Run the tests:
```bash
python -m pytest tests/ -v
```

---

## Stage 2 — Run it in Docker

Build the image:
```bash
docker build -t trade-api .
```

Run it:
```bash
docker run -p 8000:8000 trade-api
```

Visit http://localhost:8000/docs again — same app, now containerized.

Useful things to try here (this is where Docker actually clicks):
- `docker logs <container_id>` — see your app's logs
- `docker stop <container_id>` then restart it — notice all your orders/sessions vanish (no persistent storage yet — that's a good "Stage 6" upgrade later: add a real database)
- `docker exec -it <container_id> sh` — poke around inside the running container

---

## Stage 3 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: mock trade API"
git branch -M main
git remote add origin <your-empty-github-repo-url>
git push -u origin main
```

The moment you push, **GitHub Actions will try to run** (see
`.github/workflows/ci.yml`). The `test` job will run automatically. The
`build` job (which pushes a Docker image to Docker Hub) will **fail until
you add secrets** — see Stage 4.

---

## Stage 4 — Wire up CI/CD to Docker Hub

1. Create a free account at https://hub.docker.com
2. Create an access token: Account Settings → Security → New Access Token
3. In your GitHub repo: Settings → Secrets and variables → Actions → New repository secret
   - `DOCKERHUB_USERNAME` = your Docker Hub username
   - `DOCKERHUB_TOKEN` = the token you just created
4. Push a commit to `main` — watch the Actions tab. You should see `test`
   run, then `build` run, then a new image appear in your Docker Hub repo.

This is a real CI/CD pipeline: every push to `main` is tested, and if it
passes, a fresh image is built and published automatically.

---

## Stage 5 — Deploy to AWS (free tier)

Recommended path for a first deploy — **AWS App Runner** (simplest way to
run a container without managing servers):

1. Sign up for AWS free tier: https://aws.amazon.com/free
2. Push your image to Docker Hub (Stage 4 gets you here automatically)
3. In the AWS Console, go to **App Runner** → Create service → source =
   "Container registry" → point it at your Docker Hub image
   (`<your-username>/trade-api:latest`) → port `8000`
4. Deploy. App Runner gives you a public HTTPS URL when it's done.

Alternative (more manual, more "real" DevOps practice): launch a free-tier
`t2.micro` EC2 instance, SSH in, install Docker, `docker run` your image
manually. More painful — which is exactly why you'd want Terraform next.

## Stage 6 — Infrastructure as Code (Terraform)

Once you've deployed manually once and felt the pain of clicking through
the AWS console, we'll write Terraform to provision the same thing (EC2
instance or App Runner service) from code. Ask me when you're ready for
this stage and I'll build it with you.

## Stage 7 — Monitoring

Add Prometheus + Grafana (or CloudWatch, since you're already on AWS) to
watch request counts, error rates, and latency. Given your Splunk
background, this stage should feel the most familiar.

## Stage 8 — Break it on purpose

Kill the container mid-request, push a broken commit, simulate a bad
deploy. Practice diagnosing it using only your logs/metrics, then roll
back. This is the single most valuable stage for interview-readiness.

---

## Notes for later

- Orders and sessions are stored **in memory** — they vanish on restart.
  A great next feature: swap in PostgreSQL or SQLite.
- `datetime.utcnow()` is used for simplicity; it's deprecated in newer
  Python. Worth fixing later with timezone-aware datetimes.
