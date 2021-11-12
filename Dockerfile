FROM python:3.10-bullseye
COPY . .
RUN pip install -q -U setuptools wheel > /dev/null 2>&1
RUN pip install -q -r requirements.txt
CMD ["python3", "-u", "main.py"]
