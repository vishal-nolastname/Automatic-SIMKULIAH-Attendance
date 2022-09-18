import datetime as DT
import pytz # $ pip install pytz
import time
from classes import *
import asyncio
from function import *

tz = pytz.timezone('Asia/Jakarta') # <- put your local timezone heretz


async def absen(nim, pw, jadwal):
    waktuAwalAbsen = jadwal[0].tanggal + ' ' + jadwal[0].jam[0:5]
    waktuAkhirAbsen = jadwal[0].tanggal + ' ' + jadwal[0].jam[-5:]

    awal = DT.datetime.strptime(waktuAwalAbsen, '%d-%m-%Y %H.%M')
    awal = tz.localize(awal, is_dst=None) # make it aware
    print(awal)

    akhir = DT.datetime.strptime(waktuAkhirAbsen, '%d-%m-%Y %H.%M')
    akhir = tz.localize(akhir, is_dst=None) # make it aware
    print(akhir)

    while True:
        now = DT.datetime.now(tz)
        print(now)
        if now < awal:
            dif = awal - now
            print(dif)
            time.sleep(dif.total_seconds())
        
        # Cek apakah dalam waktu absen
        if now.time < akhir:
            # Fungsi Absen return true jika berhasil
            # Jika berhasil, ubah waktu awal dan akhir absen ke jadwal minggu depan
            print("Absen")
            
        break