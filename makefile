build:
	docker build -t patentbot:latest .

run:
	docker run --env-file ./frontend/.env -p 8000:8000 patentbot:latest
