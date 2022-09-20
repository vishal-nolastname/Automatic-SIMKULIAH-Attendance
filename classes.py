class User:
    def __init__(self, nama, nim, pw):
        self.nama = nama
        self.nim = nim
        self.password = pw
        self.automatic = False
        self.matakuliah = None
        self.tasks = []
        
class Matakuliah:
    def __init__(self, kode, namaMatkul, kelas, jadwal):
        self.kode = kode
        self.namaMatkul = namaMatkul
        self.kelas = kelas
        self.jadwal = jadwal
        
class Jadwal:
    def __init__(self, namaDosen, nipDosen, hpDosen, hari, ruang, tanggal, jam):
        self.namaDosen = namaDosen
        self.nipDosen = nipDosen
        self.hpDosen = hpDosen
        self.ruang = ruang
        self.hari = hari
        self.tanggal = tanggal
        self.jam = jam