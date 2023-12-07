from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sklearn.ensemble import RandomForestClassifier
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

import pandas as pd
import pyodbc
import hashlib
import requests

app = FastAPI()

# Inisialisasi OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

server = 'mysqlserver18221062.database.windows.net,1433'
database = 'myEducationTechDB'
username = 'azureuser'
password = 'Dastin1012'
driver = '{ODBC Driver 18 for SQL Server}'

connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;Login Timeout=60'
def create_connection():
    return pyodbc.connect(connection_string)

# Model Pydantic untuk data rasionalisasi via input user
class InputUser(BaseModel):
    idUser: int
    userName: str
    kampusTujuan: str
    nilaiMatW: int
    nilaiMatM: int
    nilaiFis: int
    nilaiKim: int
    nilaiBio: int
    nilaiInd: int
    nilaiIng: int

# Model Pydantic untuk data pengguna
class UserData(BaseModel):
    userName: str
    emailUser: str
    passwordUser: str

# Model Pydantic untuk Update Konsultasi Sneakers
class updateMe(BaseModel):
    age: int
    footsize: int
    category: str
    budget: int

# Membaca file dataset nilai SNM untuk ITB UI dan UGM
dataNilaiITB = pd.read_csv("mockDatasetSNMITBFix.csv")
dataNilaiUI = pd.read_csv("mockDatasetSNMUIFix.csv")
dataNilaiUGM = pd.read_csv("mockDatasetSNMUGMFix.csv")

# Memisahkan fitur (X) dan label (y)
X_itb = dataNilaiITB[["NilaiMatW", "NilaiMatM", "NilaiFis", "NilaiKim", "NilaiBio", "NilaiInd", "NilaiIng"]]
y_itb = dataNilaiITB["Status"]

X_ui = dataNilaiUI[["NilaiMatW", "NilaiMatM", "NilaiFis", "NilaiKim", "NilaiBio", "NilaiInd", "NilaiIng"]]
y_ui = dataNilaiUI["Status"]

X_ugm = dataNilaiUGM[["NilaiMatW", "NilaiMatM", "NilaiFis", "NilaiKim", "NilaiBio", "NilaiInd", "NilaiIng"]]
y_ugm = dataNilaiUGM["Status"]

# Inisialisasi model RandomForestClassifier dan melatih model
model_itb = RandomForestClassifier()
model_itb.fit(X_itb.values, y_itb.values)

model_ui = RandomForestClassifier()
model_ui.fit(X_ui.values, y_ui.values)

model_ugm = RandomForestClassifier()
model_ugm.fit(X_ugm.values, y_ugm.values)

# Fungsi untuk hash password
def hash_password(password: str):
    # Pada contoh ini, menggunakan SHA-256
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return hashed_password

# Endpoint untuk pendaftaran pengguna (register)
@app.post("/register", tags=["Register Account"])
async def register_user(user: UserData):
    connection = create_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT MAX(idUser) FROM user_data")
        last_user_id = cursor.fetchone()[0]
        next_user_id = last_user_id + 1 if last_user_id is not None else 1

        # Memeriksa apakah pengguna sudah terdaftar
        cursor.execute(f"SELECT * FROM user_data WHERE userName = '{user.userName}'")
        existingUser = cursor.fetchone()

        # Memeriksa apakah pengguna sudah terdaftar
        if existingUser:
            raise HTTPException(status_code=400, detail=f"Account with username {existingUser.userName} already registered")
        
    url = 'http://sneakersbandung.hzgecqhehxbtanhv.southeastasia.azurecontainer.io/register'
    headers = {
        'accept': 'application/json',
    }
    data = {
        'username': user.userName,
        'password': user.passwordUser,
    }
    response = requests.post(url, headers=headers, json=data, timeout=100)
    if (response.status_code == 200) :
        url = 'http://sneakersbandung.hzgecqhehxbtanhv.southeastasia.azurecontainer.io/token'
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        data = {
            'grant_type': '',
            'username': user.userName,
            'password': user.passwordUser,
            'scope': '',
            'client_id': '',
            'client_secret': '',
        }

        response = requests.post(url, headers=headers, data=data, timeout=100)

        if (response.status_code == 200):
            result = response.json()
            access_token = result.get('access_token')

        try:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO user_data VALUES (?, ?, ?, ?, ?)", (next_user_id, user.userName, user.emailUser, hash_password(user.passwordUser), access_token))
                connection.commit()
                return f"Username `{user.userName}` successfully registered"
        finally:
            connection.close()

# Endpoint untuk mendapatkan token (login)
@app.post("/token", tags=["Generate Token"])
async def token_generate(form_data: OAuth2PasswordRequestForm = Depends()):
    connection = create_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM user_data WHERE userName = '{form_data.username}' AND passwordUser = '{hash_password(form_data.password)}'")
            verifyUser = cursor.fetchone()
            if not verifyUser:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            return {"access_token": form_data.username, "token_type": "bearer"} 
    finally:
        connection.close()

# Mendapatkan seluruh riwayat hasil rasionalisasi
@app.get('/hasil', tags=["Layanan Rasionalisasi Nilai"])
async def read_data_hasil_rasionalisasi(token: str = Depends(oauth2_scheme)):
    connection = create_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM hasil_rasionalisasi_data")
            data = cursor.fetchall()
            json_data = [
                {'idHasil': item[0], 
                 'idUser': item[1], 
                 'nameUser': item[2], 
                 'kampusTujuan': item[3], 
                 'nilaiMatW': item[4], 
                 'nilaiMatM': item[5], 
                 'nilaiFis': item[6], 
                 'nilaiKim': item[7], 
                 'nilaiBio': item[8], 
                 'nilaiInd': item[9], 
                 'nilaiIng': item[10], 
                 'hasilRasionalisasi': item[11]
                } for item in data]
            return json_data
    finally:
        connection.close()

# Mendapatkan riwayat hasil rasionalisasi untuk user_id tertentu
@app.get('/hasil/{user_id}', tags=["Layanan Rasionalisasi Nilai"])
async def get_data_hasil_rasionalisasi_user(user_id: int, token: str = Depends(oauth2_scheme)):
    connection = create_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM hasil_rasionalisasi_data WHERE idUser={user_id}")
            items = cursor.fetchall()

            if not items:
                raise HTTPException(
                    status_code=404, detail=f'User ID {user_id} belum pernah melakukan rasionalisasi atau tidak terdaftar'
                )

            hasil = []
            for item in items:
                hasil.append({
                    "idHasil": item[0],
                    "idUser": item[1],
                    "nameUser": item[2],
                    "kampusTujuan": item[3],
                    "nilaiMatW": item[4],
                    "nilaiMatM": item[5],
                    "nilaiFis": item[6],
                    "nilaiKim": item[7],
                    "nilaiBio": item[8],
                    "nilaiInd": item[9],
                    "nilaiIng": item[10],
                    "hasilRasionalisasi": item[11]
                })

            return hasil
    finally:
        connection.close()

# Mendapatkan seluruh user yang berhak melakukan rasionalisasi
@app.get('/user', tags=["Layanan Rasionalisasi Nilai"])
async def read_data_user_rasionalisasi(token: str = Depends(oauth2_scheme)):
    connection = create_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM user_data")
            data = cursor.fetchall()
            json_data = [{
                    'idUser': item[0], 
                    'userName': item[1],
                    'emailUser': item[2]
                } for item in data]
            return json_data
    finally:
        connection.close()

# Mengecek apakah user ini berhak melakukan rasionalisasi
@app.get('/user/{user_id}', tags=["Layanan Rasionalisasi Nilai"])
async def get_data_user_rasionalisasi(user_id: int):
    connection = create_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM user_data WHERE idUser={user_id}")
            item = cursor.fetchone()

            if not item:
                raise HTTPException(
                    status_code=404, detail=f'User ID {user_id} tidak ada, silahkan register program rasionalisasi'
                )

            item = ({
                    'idUser': item[0], 
                    'userName': item[1],
                    'emailUser': item[2],
                    'status': "Berhak melakukan rasionalisasi"
                })

            return item
    finally:
        connection.close()

@app.post('/rasionalisasikan', tags=["Layanan Rasionalisasi Nilai"])
async def add_hasil_rasionalisasi(item: InputUser, token: str = Depends(oauth2_scheme)):
    connection = create_connection()
    try:
        with connection.cursor() as cursor:
            user = get_user_by_id(cursor, item.idUser)
            if not user:
                raise HTTPException(
                    status_code=404, detail=f'User belum terdaftar ke dalam program rasionalisasi SNMPTN.'
                )

            arr_input = [item.nilaiMatW, item.nilaiMatM, item.nilaiFis, item.nilaiKim, item.nilaiBio, item.nilaiInd, item.nilaiIng]

            rasionalisasi_result = calculate_rasionalisasi(item.kampusTujuan, arr_input)

            insert_rasionalisasi_result(cursor, item, rasionalisasi_result)
            connection.commit()

            return rasionalisasi_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing database: {str(e)}")
    finally:
        connection.close()

def get_user_by_id(cursor, user_id):
    cursor.execute("SELECT * FROM user_data WHERE idUser = ?", user_id)
    return cursor.fetchone()

def calculate_rasionalisasi(kampus_tujuan, arr_input):
    rasionalisasi_ITB = model_itb.predict([arr_input])
    rasionalisasi_UI = model_ui.predict([arr_input])
    rasionalisasi_UGM = model_ugm.predict([arr_input])

    rasionalisasi_ITB = (rasionalisasi_ITB.tolist())[0]
    rasionalisasi_UI = (rasionalisasi_UI.tolist())[0]
    rasionalisasi_UGM = (rasionalisasi_UGM.tolist())[0]

    if kampus_tujuan not in ["ITB", "UI", "UGM"]:
        return "Masukkan kampus yang benar. Pilihan rasionalisasi saat ini hanya ITB/UI/UGM."

    if kampus_tujuan == "ITB":
        if 0 <= min(arr_input) <= 75:
            return f"Anda berpeluang TIDAK LULUS {kampus_tujuan} pada SNMPTN 2024."
        else:
            if any((x >= 101 or x <= -1) for x in arr_input):
                hasil_prediksi = "Anda berpeluang TIDAK LULUS ITB pada SNMPTN 2024. Periksa kembali input nilai Anda!"
            else: 
                if (rasionalisasi_ITB) == 1:
                    hasil_prediksi = "Anda berpeluang LULUS ITB pada SNMPTN 2024."
                elif (rasionalisasi_ITB) == 0:
                    hasil_prediksi = "Anda berpeluang TIDAK LULUS ITB pada SNMPTN 2024."
    
    elif kampus_tujuan == "UI":
        if 0 <= min(arr_input) <= 75:
            return f"Anda berpeluang TIDAK LULUS {kampus_tujuan} pada SNMPTN 2024."
        else:
            if any((x >= 101 or x <= -1) for x in arr_input):
                hasil_prediksi = f"Anda berpeluang TIDAK LULUS {kampus_tujuan} pada SNMPTN 2024. Periksa kembali input nilai Anda!"
            else: 
                if (rasionalisasi_UI) == 1:
                    hasil_prediksi = f"Anda berpeluang LULUS {kampus_tujuan} pada SNMPTN 2024."
                elif (rasionalisasi_UI) == 0:
                    hasil_prediksi = f"Anda berpeluang TIDAK LULUS {kampus_tujuan} pada SNMPTN 2024."

    elif kampus_tujuan == "UGM":
        if 0 <= min(arr_input) <= 75:
            return f"Anda berpeluang TIDAK LULUS {kampus_tujuan} pada SNMPTN 2024."
        else:
            if any((x >= 101 or x <= -1) for x in arr_input):
                hasil_prediksi = f"Anda berpeluang TIDAK LULUS {kampus_tujuan} pada SNMPTN 2024. Periksa kembali input nilai Anda!"
            else: 
                if (rasionalisasi_UGM) == 1:
                    hasil_prediksi = f"Anda berpeluang LULUS {kampus_tujuan} pada SNMPTN 2024."
                elif (rasionalisasi_UGM) == 0:
                    hasil_prediksi = f"Anda berpeluang TIDAK LULUS {kampus_tujuan} pada SNMPTN 2024."

    return hasil_prediksi

def insert_rasionalisasi_result(cursor, item, hasil_prediksi):
    i = get_next_result_id(cursor)
    result = {
        "idHasil": i,
        "idUser": item.idUser,
        "nameUser": item.userName,
        "kampusTujuan": item.kampusTujuan,
        "nilaiMatW": item.nilaiMatW,
        "nilaiMatM": item.nilaiMatM,
        "nilaiFis": item.nilaiFis,
        "nilaiKim": item.nilaiKim,
        "nilaiBio": item.nilaiBio,
        "nilaiInd": item.nilaiInd,
        "nilaiIng": item.nilaiIng,
        "hasilRasionalisasi": hasil_prediksi
    }
    cursor.execute("""
        INSERT INTO hasil_rasionalisasi_data
        (idHasil, idUser, nameUser, kampusTujuan, nilaiMatW, nilaiMatM, nilaiFis, nilaiKim, nilaiBio, nilaiInd, nilaiIng, hasilRasionalisasi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (i, item.idUser, item.userName, item.kampusTujuan,
                item.nilaiMatW, item.nilaiMatM, item.nilaiFis,
                item.nilaiKim, item.nilaiBio, item.nilaiInd, item.nilaiIng,
                hasil_prediksi))

def get_next_result_id(cursor):
    cursor.execute("SELECT MAX(idHasil) FROM hasil_rasionalisasi_data")
    max_id = cursor.fetchone()[0]
    return 1 if max_id is None else max_id + 1

# Menghapus data user
@app.delete('/user/{user_id}', tags=["Layanan Rasionalisasi Nilai"])
async def delete_user(user_id: int, token: str = Depends(oauth2_scheme)):
    connection = create_connection()
    try:
        with connection.cursor() as cursor:
            user_found = delete_user_from_database(cursor, user_id)
            if user_found:
                connection.commit()
                return "User deleted!"
            else:
                return "User ID not found."
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing database: {str(e)}")
    finally:
        connection.close()

def delete_user_from_database(cursor, user_id):
    cursor.execute("DELETE FROM hasil_rasionalisasi_data WHERE idUser = ?", user_id)
    cursor.execute("SELECT * FROM user_data WHERE idUser = ?", user_id)
    user = cursor.fetchone()

    if user:
        cursor.execute("DELETE FROM user_data WHERE idUser = ?", user_id)
        return True
    else:
        return False
    
@app.get("/integrasi-detail-me", tags=["Integrasi: Layanan Konsultasi Sneakers"])
async def integrasi_detail_me(token: str = Depends(oauth2_scheme)):
    connection = create_connection()
    with connection.cursor() as cursor:
        # Check if the sneaker ID exists
        cursor.execute("SELECT tokenIntegrasi FROM user_data WHERE userName=?", (token))
        integrasiToken = cursor.fetchone()[0]
    url = 'http://sneakersbandung.hzgecqhehxbtanhv.southeastasia.azurecontainer.io/details/me'
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + integrasiToken,
    }

    response = requests.get(url, headers=headers, timeout=10)
    return response.json()

@app.put("/integrasi-update-me", tags=["Integrasi: Layanan Konsultasi Sneakers"])
async def integrasi_update_me(update : updateMe, token: str=Depends(oauth2_scheme)):
    connection = create_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT tokenIntegrasi FROM user_data WHERE userName=?", (token))
        integrasiToken = cursor.fetchone()[0]
    url = 'http://sneakersbandung.hzgecqhehxbtanhv.southeastasia.azurecontainer.io/update/me'
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + integrasiToken,
    }
    data = {
        'age': update.age,
        'footsize': update.footsize,
        'category': update.category,
        'budget': update.budget
    }
    response = requests.put(url, headers=headers, json=data, timeout=100)
    return response.json()

@app.post("/integrasi-doconsult-me", tags=["Integrasi: Layanan Konsultasi Sneakers"])
async def integrasi_doConsult_me(token: str=Depends(oauth2_scheme)):
    connection = create_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT tokenIntegrasi FROM user_data WHERE userName=?", (token))
        integrasiToken = cursor.fetchone()[0]
    url = 'http://sneakersbandung.hzgecqhehxbtanhv.southeastasia.azurecontainer.io/doconsult/me'
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + integrasiToken,
    }
    response = requests.post(url, headers=headers, timeout=10)
    return response.json()

@app.get("/integrasi-consultation-history", tags=["Integrasi: Layanan Konsultasi Sneakers"])
async def integrasi_consultation_history(token: str=Depends(oauth2_scheme)):
    connection = create_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT tokenIntegrasi FROM user_data WHERE userName=?", (token))
        integrasiToken = cursor.fetchone()[0]
    url = 'http://sneakersbandung.hzgecqhehxbtanhv.southeastasia.azurecontainer.io/consult/me'
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + integrasiToken,
    }
    response = requests.get(url, headers=headers, timeout=10)
    return response.json()