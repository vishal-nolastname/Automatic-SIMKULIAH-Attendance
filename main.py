#from cgitb import text
#from selenium import webdriver
#from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
import telebot
from telebot import types
import os
from function import *
import traceback
from classes import *
import asyncio
import datetime as DT
import pytz

bot = telebot.TeleBot("5745671824:AAFZUA2HEiDHvLjWE1NOqNf1Qx1taxzjutQ")

user_dict = {}

# Bot Starter/Helper
@bot.message_handler(commands=['start'])
def start(msg):
    if len(user_dict) > 0 and msg.chat.id in user_dict:
        bot.send_message(msg.chat.id, "Kamu sudah pernah login dengan NIM " + user_dict[msg.chat.id].nim)
        bot.send_message(msg.chat.id, "Jika kamu ingin merubah akun, ketik /daftar")
    else:
        bot.send_message(msg.chat.id, """"\
WELCOME TO AUTOMATIC SIMKULIAH ATTENDANCE! 

In this bot app, you can automatic your attendance on SIMKULIAH for Syiah Kuala University Stundents. 
Before we started, lets input your NIM and Password for SIMKULIAH. Don't worry, we dont have your data! <3""")                          
        bot.send_message(msg.chat.id, "Ketik /daftar untuk mulai mendaftar")

@bot.message_handler(commands=['help'])
def help(msg):
    bot.send_message(msg.chat.id, """\
Berikut beberapa commands yang bisa kamu gunakan:
1. /start -- Untuk memulai bot
2. /help -- Untuk melihat beberapa commands yang ada
3. /daftar -- Untuk mulai mendaftarkan akun SIMKULIAH / daftar ulang
4. /daftarJadwal -- Untuk mulai mendaftarkan jadwal kuliah
5. /jadwal -- Untuk melihat jadwal kuliah yang sudah terdaftar
6. /auto -- Untuk mengaktif/nonaktif-kan fitur automatic absensi
""")
      
# New Account
@bot.message_handler(commands=['daftar'])
def register(msg):
    if msg.chat.id in user_dict and user_dict[msg.chat.id].automatic == True:
        bot.send_message(msg.chat.id, "Fitur Automatic Absensi sedang aktif. Nonaktifkan terlebih dahulu dengan mengetik /auto")
        return
    
    markup = types.ForceReply(selective=False)
    sent_msg = bot.send_message(msg.chat.id, "Masukkan NIM:", reply_markup=markup)
    bot.register_next_step_handler(sent_msg, prosesInputNim)

def prosesInputNim(msg):
    nim = msg.text
    bot.last_message_sent = msg.chat.id, msg.message_id
    markup = types.ForceReply(selective=False)
    sent_msg = bot.send_message(msg.chat.id, "Masukkan Password:", reply_markup=markup)
    bot.delete_message(*bot.last_message_sent)
    bot.register_next_step_handler(sent_msg, prosesInputPassword, nim)
    
def prosesInputPassword(msg, nim):
    pw = msg.text
    chatid=msg.chat.id
    msgid=msg.message_id
    bot.last_message_sent = chatid, msgid
    bot.send_message(chatid, "Logging in...")
    bot.delete_message(*bot.last_message_sent)
    #bot.register_next_step_handler(sent_msg, login, nim, msg.text)
    result = login(nim, pw)
    
    if result[0] == False:
        sent_msg = bot.send_message(chatid, "NIM atau Password Salah! Masukkan Ulang NIM:")
        bot.register_next_step_handler(sent_msg, prosesInputNim)
        return
    elif result[0] == True:
        user = User(result[1], nim, pw)
        user_dict[chatid] = user     
        bot.send_message(chatid, "Berhasil Login. Halo " + user.nama)
        scheduler(msg)

# Functions
def login(nim, pw):
    driver = driver_setup()
    driver.get('https://simkuliah.unsyiah.ac.id/index.php/login')
    
#   LOGIN FORM
    driver.find_element(By.CSS_SELECTOR, 'input[type=nip]').send_keys(nim) # input username
    driver.find_element(By.CSS_SELECTOR, 'input[type=password]').send_keys(pw) # input password
    driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click() # click button submit
    driver.implicitly_wait(30) 
    
    driver.get('https://simkuliah.unsyiah.ac.id/index.php/absensi')
    
    status = False, ' '
    if driver.current_url == 'https://simkuliah.unsyiah.ac.id/index.php/login':
        status = False, ' '
    else:
        driver.find_element(By.CSS_SELECTOR, '.ti-more').click() # click button more
        nama = driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/nav/div/div[2]/div/ul[2]/li[3]/a/span').text
        status = True, nama
    
    driver.quit()
    return status

@bot.message_handler(commands=['daftarJadwal'])
def scheduler(msg):
    if msg.chat.id not in user_dict:
        bot.send_message(msg.chat.id, "Kamu belum terdaftar di sistem. Silahkan daftar terlebih dahulu.")
        return
    
    nim = user_dict[msg.chat.id].nim
    pw = user_dict[msg.chat.id].password
    
    markup = types.ReplyKeyboardRemove(selective=False)
    while True:    # minta request kembali jika servernya erorrr 
        try:
            bot.send_chat_action(msg.chat.id, "typing")
            driver = driver_setup()
            driver.get('https://simkuliah.unsyiah.ac.id/index.php/absensi')
           
        #   LOGIN FORM
            driver.find_element(By.CSS_SELECTOR, 'input[type=nip]').send_keys(nim) # input username
            driver.find_element(By.CSS_SELECTOR, 'input[type=password]').send_keys(pw) # input password
            driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click() # click button submit
            driver.implicitly_wait(30)
            
            driver.get('https://simkuliah.unsyiah.ac.id/index.php/jadwal_kuliah')
            
            bot.send_chat_action(msg.chat.id, "typing")
            table = driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div[2]/div/div/div/div/div/div/div[2]/div/table/tbody')
            rows = table.find_elements(By.TAG_NAME, 'tr')
            if len(rows) <= 1:
                bot.send_message(msg.chat.id, f"Tidak ada jadwal di SIMKULIAH.", reply_markup=markup)
                return
            
            listMatkul = []
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, 'td')
                # kode matkul
                kode = cols[0].text
                # nama matkul dan kelas matkul
                namaMatkul = cols[1].text.split('\n')[0]
                kelas = cols[1].text.split('\n')[1]
                # jadwal matkul
                listJadwal = []
                for i, col in enumerate(cols):
                    if(i >= 2):
                        split = col.text.split('\n')
                        #jadwal = Jadwal(split[0][7:], split[1][6:], split[2][11:], split[3][-18:-12], split[3][-10:], split[4][8:], split[5][6:])
                        jadwal = Jadwal(split[0], split[1], split[2], split[3][16:-12], split[4], split[3][-10:], split[5][6:])
                        listJadwal.append(jadwal)

                matkul = Matakuliah(kode, namaMatkul, kelas, listJadwal)
                listMatkul.append(matkul)
            
            user_dict[msg.chat.id].matakuliah = listMatkul
            driver.quit()
            break
        except:
            traceback.print_exc()
            bot.send_message(msg.chat.id, f"Gagal. Mencoba ulang...", reply_markup=markup)
            continue
        
    bot.send_message(msg.chat.id, "Pendaftaran jadwal kuliah berhasil. Ketik /jadwal untuk melihat jadwal kuliah yang sudah didaftar.")

@bot.message_handler(commands=['jadwal'])
def checkSchedule(msg):
    if msg.chat.id not in user_dict:
        bot.send_message(msg.chat.id, "Kamu belum terdaftar di sistem. Silahkan daftar terlebih dahulu.")
        return
    
    if len(user_dict[msg.chat.id].matakuliah) <= 0:
        bot.send_message(msg.chat.id, "Tidak ada jadwal kuliah yang terdaftar.")
        return
    
    markup = types.ReplyKeyboardRemove(selective=False)
    listMatkul = user_dict[msg.chat.id].matakuliah
    
    semuaMatkul = ''
    for mk in listMatkul:
        #print(len(mk.jadwal[0].jam))
        satuMatkul = f'{mk.kode} {mk.namaMatkul} {mk.kelas}\n{mk.jadwal[0].hari} - Jam : {mk.jadwal[0].jam}\n\n'
        semuaMatkul += satuMatkul
    
    bot.send_message(msg.chat.id, semuaMatkul, reply_markup=markup)

# Auto Absensi
utc = pytz.UTC
UTC_OFFSET = 7

async def main(msg, user):
    nim = user.nim
    pw = user.password
    tasks = []
    for i in range(0, len(user.matakuliah)):
        task = asyncio.create_task(absenPerMatkul(msg, nim, pw, user.matakuliah[i]))
        #print(i)
        tasks.append(task)
        
    #print('sudah selesai mendaftarkan semua tasks')
    user.tasks = tasks
    gather = asyncio.gather(*[tasks[i] for i in range(len(tasks))])
    
    while not gather.done():
        await asyncio.sleep(1)
        #print('Task has not completed, checking again in a second')
        if user.automatic == False:
            #print('Cancelling the task...')
            bot.send_message(msg.chat.id, "Sedang menghentikan fitur auto absensi...")
            gather.cancel()
            break

    try:
        await gather
    except asyncio.CancelledError:
        #print('Task has been cancelled.')
        bot.send_message(msg.chat.id, "Fitur Auto Absensi berakhir.")
        
def akhiriAutoAbsen(msg, user):
    if  msg.text == 'Ya':
        user.automatic = False
        #for task in user.tasks:
            #print('Tes cancel')
            #task.cancel()
        
        return
    elif msg.text == 'Tidak':
        bot.send_message(msg.chat.id, "OK")
        return
    else:
        markup = types.ReplyKeyboardRemove()
        bot.send_message(msg.chat.id, "Woopsiee, jawaban tidak dimengerti.", reply_markup=markup)
        return

@bot.message_handler(commands=['auto'])
def autoAbsen(msg):
    markup = types.ReplyKeyboardRemove(selective=False)
    if msg.chat.id not in user_dict:
        bot.send_message(msg.chat.id, "Kamu belum terdaftar di sistem. Silahkan daftar terlebih dahulu.", reply_markup=markup)
        return
    
    if len(user_dict[msg.chat.id].matakuliah) <= 0:
        bot.send_message(msg.chat.id, "Tidak ada jadwal kuliah yang terdaftar.")
        return
    
    user = user_dict[msg.chat.id]
    if user.automatic == False:
        user.automatic = True
        bot.send_message(msg.chat.id, "Auto Absensi dimulai.")
        asyncio.run(main(msg, user))
    else:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Ya', 'Tidak')
        sent_msg = bot.send_message(msg.chat.id, "Auto Absensi sudah aktif. Apakah kamu mau menonaktifkan fitur automatic absensinya?", reply_markup=markup)
        bot.register_next_step_handler(sent_msg, akhiriAutoAbsen, user)

async def absenPerMatkul(msg, nim, pw, matkul):
    namaMatkul = matkul.namaMatkul
    jadwal = matkul.jadwal
    jumlah_absensi = len(jadwal)
    #print(f'Menjalankan task {namaMatkul}, {jumlah_absensi}')
    try:
        i = 0
        while i < jumlah_absensi:
            waktuAwalAbsen = jadwal[i].tanggal + ' ' + jadwal[i].jam[0:5]
            waktuAkhirAbsen = jadwal[i].tanggal + ' ' + jadwal[i].jam[-6:-1]
            #print(waktuAwalAbsen)
            #print(waktuAkhirAbsen)

            awal = DT.datetime.strptime(waktuAwalAbsen, '%d-%m-%Y %H.%M')
            awal = awal - DT.timedelta(hours=UTC_OFFSET)
            awal = utc.localize(awal)
            #print(awal)

            akhir = DT.datetime.strptime(waktuAkhirAbsen, '%d-%m-%Y %H.%M')
            akhir = akhir - DT.timedelta(hours=UTC_OFFSET)
            akhir = utc.localize(akhir)
            #print(akhir)

            now = DT.datetime.now(utc)
            # Cek apakah sudah lewat waktu absen saat pertama kali fitur diaktifkan
            if now > akhir:
                #print(f'tes 8 {namaMatkul}')
                #bot.send_message(msg.chat.id, f"Matakuliah {namaMatkul} pertemuan ke-{i+1} sudah lewat") 
                i += 1
                continue
            
            # Cek apakah belum masuk waktu absen
            # Jika belum, sleep sampai waktu absen
            #print(f'tes 1 {namaMatkul}')
            if now < awal:
                dif = awal - now
                total_seconds = dif.total_seconds()
                days, remainder1 = divmod(total_seconds, 86400)
                hours, remainder2 = divmod(remainder1, 3600)
                minutes, seconds = divmod(remainder2, 60)
                waktuTunggu = '{:02} hari, {:02} jam, {:02} menit, {:02} detik'.format(int(days), int(hours), int(minutes), int(seconds))
                bot.send_message(msg.chat.id, f"Absensi {namaMatkul} dalam waktu {waktuTunggu}")
                await asyncio.sleep(total_seconds)
            
            # Cek apakah sudah dalam waktu absen dan dalam jangka waktu absen
            #print(f'tes 3 {namaMatkul}')
            while True:
                hasil = False
                if now < akhir:
                    #print(f'tes 4 {namaMatkul}')
                    # Fungsi Absen return true jika berhasil
                    hasil = absensi(nim, pw, msg.chat.id)
                    # Jika berhasil, ubah waktu awal dan akhir absen ke jadwal minggu depan
                    if hasil == True:
                        bot.send_message(msg.chat.id, f"Absensi {namaMatkul} pertemuan ke-{i+1} berhasil.")
                        #print(f'tes 5 {namaMatkul}')
                        i += 1
                        break
                    else:
                        #print(f'tes 6 {namaMatkul}')
                        bot.send_message(msg.chat.id, f"Absensi {namaMatkul} pertemuan ke-{i+1} gagal. Mencoba ulang...")
                        continue
                # Waktu Absen berakhir
                elif now > akhir:
                    #print(f'tes 7 {namaMatkul}')
                    if hasil == False:
                        bot.send_message(msg.chat.id, f"Gagal absensi {namaMatkul} pertemuan ke-{i+1} dan waktunya sudah lewat. I'm Sorry :(")
                    i += 1
                    break
            
    except asyncio.CancelledError:
        #traceback.print_exc()
        #print(f'tes 8 {namaMatkul}')
        bot.send_message(msg.chat.id, f"Auto Absensi {namaMatkul} dihentikan.")
        raise
    finally:
        #print(f'tes 9 {namaMatkul}')
        if i >= jumlah_absensi:
            bot.send_message(msg.chat.id, f"Semua Absensi {namaMatkul} berhasil.")
        
async def absensi(nim, pw, id):
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
        hasil = False
    # JIKA BELUM MASUK WAKTU ABSEN
        if "Belum masuk waktu absen." in cekAbsensi[0]:
            status = 'Belum masuk waktu absen.'
            hasil = False
    # JIKA BELUM ABSEN
        elif "Anda belum absen" in cekAbsensi[1] :
            informasiMK = driver.find_element(By.CLASS_NAME, 'card-header').text # dapatkan informasi MKnya
            driver.find_element(By.CSS_SELECTOR, 'button[id=konfirmasi-kehadiran]').click() # klik button KONFIRMASI KEHADIRAN
            await asyncio.sleep(1)
            driver.find_element(By.CLASS_NAME, 'confirm').click() # klik button ANIMATION KONFIRMASI
            driver.get('https://simkuliah.unsyiah.ac.id/index.php/absensi')
            photoName = f'{id} ss absen.png'
            driver.save_screenshot(photoName)
            try:
                foto = open(photoName, 'rb')
                bot.send_photo(id, foto)
                foto.close()
                os.remove(photoName)
            except Exception as e:
                print("Error: %s : %s" % (photoName, e.strerror))
            status = 'Absensi Matakuliah ' + informasiMK + ' berhasil.'
            hasil = True
    # JIKA SUDAH ABSEN
        elif "Anda sudah absen" in cekAbsensi[1] :
            status = 'Anda sudah absen'
            hasil = True
            
    except:
        hasil = False
        
    driver.quit()
    return hasil
        
print("Bot is running!")
bot.polling()
