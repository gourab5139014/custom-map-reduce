FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY generate_data.py topx.py ./

RUN mkdir -p /data

EXPOSE 8080

ENTRYPOINT ["python"]
CMD ["topx.py", "--mode", "reducer"]
