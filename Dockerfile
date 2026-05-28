# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Khu vực làm việc trong container.
WORKDIR /app

# Cài dependencies trước (cache layer khi đổi code thường).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source.
COPY . .

# Thư mục giữ SQLite DB (gắn volume từ host để dữ liệu sống lâu hơn container).
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
