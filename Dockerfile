FROM python:3.10-bullseye
COPY . .
RUN pip install -q -r requirements.txt > /dev/null 2>&1
CMD ["python3", "-u", "main.py"]
