from cgitb import text
import enum
import types
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import telebot
from telebot import types
import os
from function import *
import traceback
from classes import *
import asyncio
from auto import absen

bot = telebot.TeleBot("5745671824:AAFZUA2HEiDHvLjWE1NOqNf1Qx1taxzjutQ")

user_dict = {}

@bot.message_handler(commands=['help', 'start'])
def start(msg):
    if len(user_dict) > 0 and msg.chat.id in user_dict:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Ya', 'Tidak')
        bot.send_message(msg.chat.id, "Kamu sudah pernah login dengan NIM " + user_dict[msg.chat.id].nim)
        sent_msg = bot.send_message(msg.chat.id, "Apakah kamu ingin mengganti akun?", reply_markup=markup)
        bot.register_next_step_handler(sent_msg, changeAccount, user_dict[msg.chat.id].nim, user_dict[msg.chat.id].password)
    else:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Ya', 'Tidak')
        bot.send_message(msg.chat.id, """"\
WELCOME TO AUTOMATIC SIMKULIAH ATTENDANCE! 
In this bot app, you can automatic your attendance on 
SIMKULIAH for Syiah Kuala University Stundents. 
Before we started, lets input your NIM and Password for SIMKULIAH. 
Don't worry, we dont have your data! <3""")                          
        sent_msg = bot.send_message(msg.chat.id, "Apakah kamu ingin mendaftar?", reply_markup=markup)
        bot.register_next_step_handler(sent_msg, register)

# New Account
def register(msg):
    if msg.text == "Ya":
        markup = types.ForceReply(selective=False)
        sent_msg = bot.send_message(msg.chat.id, "Masukkan NIM:", reply_markup=markup)
        bot.register_next_step_handler(sent_msg, prosesInputNim)
    elif msg.text == "Tidak":
        markup = types.ReplyKeyboardRemove(selective=False)
        bot.send_message(msg.chat.id, "Okelah kalau begitu. Jika kamu berubah pikiran, tinggal ketik /start atau /help ya :3", reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Ya', 'Tidak')
        sent_msg = bot.send_message(msg.chat.id, "Woopsiee, aku tidak mengerti. Apakah kamu ingin mendaftar?", reply_markup=markup)
        bot.register_next_step_handler(sent_msg, register)

def prosesInputNim(msg):
    markup = types.ForceReply(selective=False)
    sent_msg = bot.send_message(msg.chat.id, "Masukkan Password:", reply_markup=markup)
    bot.register_next_step_handler(sent_msg, prosesInputPassword, msg.text)
    
def prosesInputPassword(msg, nim):
    bot.send_message(msg.chat.id, "Logging in...")
    #bot.register_next_step_handler(sent_msg, login, nim, msg.text)
    result = login(nim, msg.text)
    
    if result[0] == False:
        sent_msg = bot.send_message(msg.chat.id, "NIM atau Password Salah! Masukkan Ulang NIM:")
        bot.register_next_step_handler(sent_msg, prosesInputNim)
        return
    elif result[0] == True:
        user = User(result[1], nim, msg.text)
        user_dict[msg.chat.id] = user     
        bot.send_message(msg.chat.id, "Berhasil Login. Halo " + user.nama)
        markup = types.ReplyKeyboardRemove(selective=False)
        bot.send_message(msg.chat.id, "Aku sedang mendaftarkan jadwal kuliah kamu kedalam sistem...", reply_markup=markup)
        scheduler(msg, user.nim, user.password)

def scheduler(msg, nim, pw):
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
                        jadwal = Jadwal(split[0], split[1], split[2], split[3], split[4], split[3][-10:], split[5][6:])
                        listJadwal.append(jadwal)

                matkul = Matakuliah(kode, namaMatkul, kelas, listJadwal)
                listMatkul.append(matkul)
            
            user_dict[msg.chat.id].matakuliah = listMatkul
            break
        except Exception as e:
            traceback.print_exc()
            bot.send_message(msg.chat.id, f"Gagal. Mencoba ulang...", reply_markup=markup)
            continue
        
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Ya', 'Tidak')
    sent_msg = bot.send_message(msg.chat.id, "Pendaftaran jadwal kuliah berhasil. Apakah anda mau cek jadwal kuliah?", reply_markup=markup)
    bot.register_next_step_handler(sent_msg, checkSchedule)

def checkSchedule(msg):
    markup = types.ReplyKeyboardRemove(selective=False)
    listMatkul = user_dict[msg.chat.id].matakuliah
    
    semuaMatkul = ''
    for mk in listMatkul:
        satuMatkul = f'{mk.kode} {mk.namaMatkul} {mk.kelas}\n{mk.jadwal[0].hariTanggal}\nJam : {mk.jadwal[0].jam}\n\n'
        semuaMatkul += satuMatkul
    
    bot.send_message(msg.chat.id, semuaMatkul, reply_markup=markup)

def absensi(msg, nim, pw):
    markup = types.ReplyKeyboardRemove(selective=False)
    if(msg.text == 'Tidak'):
        bot.send_message(msg.chat.id, 'Ok', reply_markup=markup)
        return

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
            
            bot.send_chat_action(msg.chat.id, "typing")
            status_absen = driver.find_element(By.XPATH, '//*[@id="pcoded"]/div[2]/div/div/div[1]/div/div/div/div[2]/div/div/div/div/div/div/div').text
            cekAbsensi = status_absen.split('\n')

        # JIKA BELUM MASUK WAKTU ABSEN
            if "Belum masuk waktu absen." in cekAbsensi[0]:
                bot.send_chat_action(msg.chat.id, "typing")
                bot.send_message(msg.chat.id, "Belum masuk waktu absen.", reply_markup=markup)

                break
        # JIKA BELUM ABSEN
            elif "Anda belum absen" in cekAbsensi[1] :
                bot.send_chat_action(msg.chat.id, "typing")
                informasiMK = driver.find_element(By.CLASS_NAME, 'card-header').text # dapatkan informasi MKnya
                bot.send_message(msg.chat.id, informasiMK, reply_markup=markup)
                
                driver.find_element(By.CSS_SELECTOR, 'button[id=konfirmasi-kehadiran]').click() # klik button KONFIRMASI KEHADIRAN
                time.sleep(1)
                driver.find_element(By.CLASS_NAME, 'confirm').click() # klik button ANIMATION KONFIRMASI
                break
        # JIKA SUDAH ABSEN
            elif "Anda sudah absen" in cekAbsensi[1] :
                bot.send_chat_action(msg.chat.id, "typing")
                for i in cekAbsensi:
                    bot.send_message(msg.chat.id, i, reply_markup=markup)
                break
            
        except:
            bot.send_message(msg.chat.id, f"Gagal untuk absen.", reply_markup=markup)
            break

# Existing Account
def changeAccount(msg, nim, pw):
    if msg.text == "Ya":
        markup = types.ForceReply(selective=False)
        sent_msg = bot.send_message(msg.chat.id, "Masukkan NIM:", reply_markup=markup)
        bot.register_next_step_handler(sent_msg, prosesInputNim)
    elif msg.text == "Tidak":
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Ya', 'Tidak')
        sent_msg = bot.send_message(msg.chat.id, "Halo " + user_dict[msg.chat.id].nama + ". Apakah anda mau cek jadwal kuliah?", reply_markup=markup)
        bot.register_next_step_handler(sent_msg, checkSchedule)
    else:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Ya', 'Tidak')
        sent_msg = bot.send_message(msg.chat.id, "Woopsiee, aku tidak mengerti. Apakah kamu ingin mengganti akun?", reply_markup=markup)
        bot.register_next_step_handler(sent_msg, changeAccount, user_dict[msg.chat.id].nim, user_dict[msg.chat.id].password)

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
    
    status = False, ''
    if driver.current_url == 'https://simkuliah.unsyiah.ac.id/index.php/login':
        status = False, ''
    else:
        nama = driver.find_element(By.CSS_SELECTOR, '.user-profile > a:nth-child(1) > span:nth-child(2)').text
        status = True, nama
    
    driver.quit()
    return False, ''

async def main(user):
    nim = user.nim
    pw = user.password
    for i in range(0, len(user.matakuliah)):
        asyncio.create_task(absen(nim, pw, user.matakuliah[i].jadwal))

@bot.message_handler(commands=['auto'])
def autoAbsen(msg):
    markup = types.ReplyKeyboardRemove(selective=False)
    if msg.chat.id not in user_dict:
        bot.send_message(msg.chat.id, "Kamu belum terdaftar. Ketik /start atau /help untuk memulai.", reply_markup=markup)
        return
    
    user = user_dict[msg.chat.id]
    bot.send_message(msg.chat.id, "Auto Absensi dimulai.")
    asyncio.run(main(user))

print("runninnnng!")
bot.polling()
