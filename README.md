# Final-TST-Integrasi-Layanan
## by Muhammad Dastin Fauzi - 18221062
### [FastAPI-Integrasi-API-via-FQDN](http://rasionalisasinilaiwithconsultation.dmbcfgb6hvdwftbh.southeastasia.azurecontainer.io/docs)

Library yang digunakan yaitu
- fastapi
- uvicorn
- pandas
- scikit-learn
- pyodbc
- python-multipart
- requests

### Cara Run Via Virtual Enviroment (venv) Python -- Windows
1. Pull repository ini ke dalam local folder
2. Buka terminal di VS Code atau via command prompt bisa
3. Pastikan sudah berada di folder tempat menyimpan repository ini
4. Buat virtual enviroment (venv)
```
python -m venv <nama virtual enviroment (dibebaskan)>
``` 
5. Masuk ke venv
```
<nama virtual enviroment (dibebaskan)>\Scripts\activate
```
6. Install library terkait. Disini saya menggunakan fastapi, uvicorn, pandas, scikit-learn, pyodbc, python-multipart dan requests dengan cara
```
pip install fastapi uvicorn pandas scikit-learn pyodbc python-multipart requests
```
7. Jalankan aplikasi
```
uvicorn rasionalisasiNilaiSNM:app --port 8000 --reload
```

### Cara Buat Code ini Hingga Deploy ke Microsoft Azure
#### 1. Pull code ini ke dalam suatu folder lalu masuk ke VS Code di folder itu
#### 2. Buat virtual enviroment (venv)
```
python -m venv <nama_venv_bebas>
```
#### 3. Masuk ke venv untuk windows
```
<nama_venv_bebas>\Scripts\activate
```
#### 4. Install library terkait
```
pip install fastapi uvicorn pandas scikit-learn pyodbc python-multipart
```
#### 5. Pastikan Dockerfile sudah terisi
```
# Use the official Python image from the Docker Hub
FROM python:3

# Set the working directory inside the container
ADD <file_name.py> .

# Copy the current directory contents into the container at /app
COPY . /<folder_name>
WORKDIR /<folder_name>

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

# Install any necessary dependencies
RUN pip install fastapi uvicorn <other packages>

# Command to run the FastAPI server when the container starts
CMD ["uvicorn", "<folder_name>", "--host=0.0.0.0", "--port=80"]
```
#### 6. Buat Azure Container Registry Service
#### 7. Buka folder terkait lalu login ke Azure Server Container Registry dengan Docker
```
docker login <container_server> -u <container_username> -p <container_password>
```
#### 8. Buat docker image
```
docker build -t <container_server>/<image_name>:<image_tag> .
```
#### 9. Push docker image
```
docker push <container_server>/<image_name>:<image_tag>
```
#### 10. Buat Azure Instance menyesuaikan dengan lokasi Container Registry
