FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./

RUN python -m pip install --upgrade pip && pip install --upgrade setuptools
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend frontend

EXPOSE 8000

CMD ["chainlit", "run", "frontend/demo.py"]