FROM python:3

ADD rasionalisasi.py .

COPY . /rasionalisasiNilaiSNMFixTerbaru
WORKDIR /rasionalisasiNilaiSNMFixTerbaru
# Install the Microsoft ODBC Driver for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install FreeTDS and other required libraries for pyodbc
RUN apt-get update && \
    apt-get install -y --no-install-recommends unixodbc-dev freetds-bin freetds-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install fastapi uvicorn pandas scikit-learn pyodbc python-multipart requests
CMD ["uvicorn", "rasionalisasi:app", "--host=0.0.0.0", "--port=80"]