FROM agrigorev/zoomcamp-model:mlops-2024-3.10.13-slim

WORKDIR /app
RUN mkdir -p /app/data
COPY ./starter.py ./requirements.txt /app 
RUN pip install -r requirements.txt

CMD ["sleep", "infinity"]