FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir 'flask>=3.0,<4' 'requests>=2.31,<3'
COPY api/app.py /app/app.py
EXPOSE 5000
CMD ["python", "app.py"]
