import datetime as DT
import pytz # $ pip install pytz
import time
from classes import *
import asyncio
from function import *

tz = pytz.timezone('Asia/Jakarta') # <- put your local timezone heretz

async def absen(nim, pw, jadwal):
    jumlah_absensi = len(jadwal)
    i = 0
    while i < jumlah_absensi:
        waktuAwalAbsen = jadwal[i].tanggal + ' ' + jadwal[i].jam[0:5]
        waktuAkhirAbsen = jadwal[i].tanggal + ' ' + jadwal[i].jam[-5:]

        awal = DT.datetime.strptime(waktuAwalAbsen, '%d-%m-%Y %H.%M')
        awal = tz.localize(awal, is_dst=None) # make it aware

        akhir = DT.datetime.strptime(waktuAkhirAbsen, '%d-%m-%Y %H.%M')
        akhir = tz.localize(akhir, is_dst=None) # make it aware
        
        now = DT.datetime.now(tz)
        # Cek apakah sudah masuk waktu absen
        if now < awal:
            dif = awal - now
            print(dif)
            asyncio.sleep(dif.total_seconds())
        
        # Cek apakah dalam jangka waktu absen
        if now.time < akhir:
            # Fungsi Absen return true jika berhasil
            hasil = absensi(nim, pw)
            # Jika berhasil, ubah waktu awal dan akhir absen ke jadwal minggu depan
            if hasil[0] == True:
                i += 1
                continue
            
    print('Semua Absensi MK ini sudah selesai.')
        
async def absensi(nim, pw):
    try:
        driver = driver_setup()
        driver.get('https://simkuliah.unsyiah.ac.id/index.php/absensi')
        
    #   LOGIN FORM
        driver.find_element(By.CSS_SELECTOR, 'input[type=nip]').send_keys(nim) # input username
        driver.find_element(By.CSS_SELECTOR, 'input[type=password]').send_keys(pw) # input password
        driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click() # click button submit
        driver.implicitly_wait(30)
        
        status_absen = driver.find_element(By.XPATH, '//*[@id="pcoded"]/div[2]/div/div/div[1]/div/div/div/div[2]/div/div/div/div/div/div/div').text
        cekAbsensi = status_absen.split('\n')

        status = ''
    # JIKA BELUM MASUK WAKTU ABSEN
        if "Belum masuk waktu absen." in cekAbsensi[0]:
            status = 'Belum masuk waktu absen.'
            return False, status
    # JIKA BELUM ABSEN
        elif "Anda belum absen" in cekAbsensi[1] :
            informasiMK = driver.find_element(By.CLASS_NAME, 'card-header').text # dapatkan informasi MKnya
            driver.find_element(By.CSS_SELECTOR, 'button[id=konfirmasi-kehadiran]').click() # klik button KONFIRMASI KEHADIRAN
            asyncio.sleep(1)
            driver.find_element(By.CLASS_NAME, 'confirm').click() # klik button ANIMATION KONFIRMASI
            status = 'Absensi Matakuliah ' + informasiMK + ' berhasil.'
            return True, status
    # JIKA SUDAH ABSEN
        elif "Anda sudah absen" in cekAbsensi[1] :
            status = 'Anda sudah absen'
            return True, status
        
    except:
        return False, 'Gagal absen'
        