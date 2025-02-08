# Gunakan base image Python
FROM python:3.10

# Set working directory di dalam container
WORKDIR /app

# Copy semua file ke dalam container
COPY . /app

# Install dependencies dari requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port yang digunakan Flask (default 5001)
EXPOSE 5001

# Jalankan Gunicorn sebagai WSGI server untuk Flask
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "main:app"]
