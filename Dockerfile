FROM python:3.11-slim

WORKDIR /app

COPY requirements_render.txt .
RUN pip install -r requirements_render.txt

COPY . .

CMD ["python", "render_deploy.py"]