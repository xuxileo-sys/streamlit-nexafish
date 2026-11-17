## DATABASE & LOGIKA AKUNTANSI (tanpa tampilan)

import datetime
import math
import os
import sqlite3
from contextlib import contextmanager

try:
    from ui.utils import DB_FILE, hash_password, rupiah, sekarang
except ImportError:
    from utils import DB_FILE, hash_password, rupiah, sekarang


class Database:
    BATAS_STOK = 10  # kompatibilitas untuk kode lama
    BATAS_STOK_IKAN = 50  # ekor
    BATAS_STOK_PAKAN = 50  # kg

    KATEGORI_AWAL = [
        ("Benih", "Ukuran 3-5 cm (siap tebar)"),
        ("Kecil", "8-10 ekor per kg"),
        ("Sedang", "4-6 ekor per kg"),
        ("Besar", "2-3 ekor per kg"),
        ("Jumbo", "1 ekor per kg atau lebih besar"),
    ]

    AKUN_AWAL = [
        ("1101", "Kas", "Aset", "Debit"),
        ("1102", "Piutang Usaha", "Aset", "Debit"),
        ("1103", "Persediaan Pakan", "Aset", "Debit"),
        ("1104", "Persediaan Ikan Bawal", "Aset", "Debit"),
        ("1105", "Kas Kecil", "Aset", "Debit"),
        ("1201", "Indukan Bawal", "Aset", "Debit"),
        ("1301", "Peralatan", "Aset", "Debit"),
        ("1302", "Akumulasi Penyusutan Peralatan", "Aset", "Kredit"),
        ("2101", "Utang Usaha", "Kewajiban", "Kredit"),
        ("3101", "Modal Pemilik", "Modal", "Kredit"),
        ("3201", "Prive", "Modal", "Debit"),
        ("3202", "Laba Ditahan", "Modal", "Kredit"),
        ("4101", "Penjualan Ikan Bawal", "Pendapatan", "Kredit"),
        ("5101", "Harga Pokok Penjualan", "Beban", "Debit"),
        ("5102", "Beban Operasional", "Beban", "Debit"),
        ("5103", "Beban Kerugian Stok", "Beban", "Debit"),
        ("4102", "Pendapatan Ongkir", "Pendapatan", "Kredit"),
        ("5104", "Beban Ongkir", "Beban", "Debit"),
        ("6101", "Beban Pakan", "Beban", "Debit"),
        ("6102", "Beban Retribusi", "Beban", "Debit"),
        ("6103", "Beban Perlengkapan", "Beban", "Debit"),
        ("6104", "Beban Ongkos Kirim", "Beban", "Debit"),
        ("6105", "Beban Penyusutan Peralatan", "Beban", "Debit"),
        ("6106", "Beban Kerugian Ikan", "Beban", "Debit"),
    ]

    PRODUK_AWAL = [
        # jenis, kategori, stok kg, harga beli, harga jual
        ("Bawal Konsumsi", "Sedang", 50, 38000, 45000),
        ("Bawal Hitam", "Kecil", 60, 22000, 30000),
        ("Bibit Bawal", "Benih", 15, 70000, 90000),
    ]

    def __init__(self, path=DB_FILE):
        self.path = ":memory:" if str(path) == ":memory:" else os.path.abspath(path)
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.buat_tabel()
        self.isi_data_awal()

    @contextmanager
    def transaksi(self):
        try:
            yield
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def tutup(self):
        self.conn.close()

    # ---------- struktur tabel ----------
    def buat_tabel(self):
        c = self.conn
        c.execute("""CREATE TABLE IF NOT EXISTS akun_jabatan (
            jabatan TEXT PRIMARY KEY CHECK (jabatan IN ('Owner', 'Karyawan')),
            password TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS profil_owner (
            id INTEGER PRIMARY KEY CHECK (id = 1), nama TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS histori_aktivitas (
            id_histori INTEGER PRIMARY KEY AUTOINCREMENT,
            waktu TEXT NOT NULL, nama_pengguna TEXT NOT NULL,
            jabatan TEXT NOT NULL, aktivitas TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS kategori_ukuran (
            id_kategori INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL UNIQUE, keterangan TEXT, kode TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS produk_bawal (
            id_produk INTEGER PRIMARY KEY AUTOINCREMENT,
            jenis_bawal TEXT NOT NULL, kode TEXT, jenis_produk TEXT NOT NULL DEFAULT 'Ikan', stok_ekor INTEGER NOT NULL DEFAULT 0,
            id_kategori INTEGER NOT NULL,
            stok REAL NOT NULL CHECK (stok >= 0),
            harga_beli REAL NOT NULL CHECK (harga_beli >= 0),
            harga_jual REAL NOT NULL CHECK (harga_jual >= 0),
            FOREIGN KEY (id_kategori) REFERENCES kategori_ukuran (id_kategori))""")
        c.execute("""CREATE TABLE IF NOT EXISTS akun (
            kode TEXT PRIMARY KEY, nama TEXT NOT NULL,
            tipe TEXT NOT NULL, saldo_normal TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS jurnal (
            id_jurnal INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT NOT NULL, keterangan TEXT NOT NULL,
            referensi TEXT, dibuat_oleh TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS jurnal_detail (
            id_detail INTEGER PRIMARY KEY AUTOINCREMENT,
            id_jurnal INTEGER NOT NULL, kode_akun TEXT NOT NULL,
            debit REAL NOT NULL DEFAULT 0, kredit REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (id_jurnal) REFERENCES jurnal (id_jurnal),
            FOREIGN KEY (kode_akun) REFERENCES akun (kode))""")
        c.execute("""CREATE TABLE IF NOT EXISTS penjualan (
            id_penjualan INTEGER PRIMARY KEY AUTOINCREMENT,
            waktu TEXT NOT NULL, nama_pembeli TEXT, id_produk INTEGER,
            nama_produk TEXT, jumlah REAL NOT NULL, harga_satuan REAL NOT NULL,
            total_harga REAL NOT NULL, metode TEXT NOT NULL,
            kasir TEXT NOT NULL, id_jurnal INTEGER)""")
        c.execute("""CREATE TABLE IF NOT EXISTS customer (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT NOT NULL UNIQUE,
            telepon TEXT DEFAULT '', alamat TEXT DEFAULT '', saldo_awal REAL NOT NULL DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS supplier (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT NOT NULL UNIQUE,
            telepon TEXT DEFAULT '', alamat TEXT DEFAULT '', saldo_awal REAL NOT NULL DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS pembelian (
            id INTEGER PRIMARY KEY AUTOINCREMENT, waktu TEXT NOT NULL,
            supplier TEXT NOT NULL, produk TEXT NOT NULL, jumlah REAL NOT NULL,
            harga_satuan REAL NOT NULL, ongkir REAL NOT NULL DEFAULT 0,
            total REAL NOT NULL, metode TEXT NOT NULL, dibuat_oleh TEXT NOT NULL,
            id_jurnal INTEGER)""")
        c.execute("""CREATE TABLE IF NOT EXISTS kebijakan (
            nama TEXT PRIMARY KEY, nilai TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS kas_kecil (
            id INTEGER PRIMARY KEY AUTOINCREMENT, waktu TEXT NOT NULL,
            keterangan TEXT NOT NULL, jumlah REAL NOT NULL, akun TEXT NOT NULL,
            dibuat_oleh TEXT NOT NULL, id_jurnal INTEGER,
            jenis TEXT NOT NULL DEFAULT 'Keluar', nomor_bukti TEXT,
            jumlah_masuk REAL NOT NULL DEFAULT 0, jumlah_keluar REAL NOT NULL DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS pelunasan_pihak (
            id INTEGER PRIMARY KEY AUTOINCREMENT, waktu TEXT NOT NULL,
            jenis TEXT NOT NULL, nama TEXT NOT NULL, jumlah REAL NOT NULL,
            id_jurnal INTEGER)""")
        c.execute("""CREATE TABLE IF NOT EXISTS kas_transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT, waktu TEXT NOT NULL,
            jenis TEXT NOT NULL, keterangan TEXT NOT NULL, jumlah REAL NOT NULL,
            akun_lawan TEXT NOT NULL, dibuat_oleh TEXT NOT NULL, id_jurnal INTEGER,
            nama_pihak TEXT NOT NULL DEFAULT '')""")
        c.execute("""CREATE TABLE IF NOT EXISTS stock_opname (
            id INTEGER PRIMARY KEY AUTOINCREMENT, waktu TEXT NOT NULL, id_produk INTEGER NOT NULL,
            jumlah_mati REAL NOT NULL, keterangan TEXT NOT NULL, dibuat_oleh TEXT NOT NULL,
            id_jurnal INTEGER, jumlah_mati_ekor INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(id_produk) REFERENCES produk_bawal(id_produk))""")
        c.execute("""CREATE TABLE IF NOT EXISTS penggunaan_pakan (
            id INTEGER PRIMARY KEY AUTOINCREMENT, waktu TEXT NOT NULL, id_produk INTEGER NOT NULL,
            jumlah REAL NOT NULL, hpp REAL NOT NULL, dibuat_oleh TEXT NOT NULL, id_jurnal INTEGER,
            FOREIGN KEY(id_produk) REFERENCES produk_bawal(id_produk))""")
        c.execute("""CREATE TABLE IF NOT EXISTS pembelian_indukan (
            id INTEGER PRIMARY KEY AUTOINCREMENT, waktu TEXT NOT NULL, jumlah REAL NOT NULL,
            keterangan TEXT NOT NULL, dibuat_oleh TEXT NOT NULL, id_jurnal INTEGER)""")
        c.execute("CREATE TABLE IF NOT EXISTS schema_migrations (nama TEXT PRIMARY KEY)")
        c.execute("CREATE TABLE IF NOT EXISTS pengaturan_sistem (nama TEXT PRIMARY KEY, nilai TEXT NOT NULL)")
        c.execute("INSERT OR IGNORE INTO pengaturan_sistem VALUES ('tanggal_mulai_histori_tunai',?)",
                  (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
        for tabel, kolom, definisi in (("kategori_ukuran", "kode", "TEXT"),
                                        ("produk_bawal", "kode", "TEXT"),
                                        ("produk_bawal", "jenis_produk", "TEXT NOT NULL DEFAULT 'Ikan'"),
                                        ("produk_bawal", "stok_ekor", "INTEGER NOT NULL DEFAULT 0")):
            kolom_ada = {r[1] for r in c.execute(f"PRAGMA table_info({tabel})")}
            if kolom not in kolom_ada:
                c.execute(f"ALTER TABLE {tabel} ADD COLUMN {kolom} {definisi}")
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_produk_kode ON produk_bawal(kode) WHERE kode IS NOT NULL")
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_kategori_kode ON kategori_ukuran(kode) WHERE kode IS NOT NULL")
        for tabel, kolom, definisi in (
            ("kas_kecil", "jenis", "TEXT NOT NULL DEFAULT 'Keluar'"),
            ("kas_kecil", "nomor_bukti", "TEXT"),
            ("kas_kecil", "jumlah_masuk", "REAL NOT NULL DEFAULT 0"),
            ("kas_kecil", "jumlah_keluar", "REAL NOT NULL DEFAULT 0"),
            ("penjualan", "subtotal", "REAL NOT NULL DEFAULT 0"),
            ("stock_opname", "jumlah_mati_ekor", "INTEGER NOT NULL DEFAULT 0"),
            ("kas_transaksi", "nama_pihak", "TEXT NOT NULL DEFAULT ''"),
        ):
            kolom_ada = {r[1] for r in c.execute(f"PRAGMA table_info({tabel})")}
            if kolom not in kolom_ada:
                c.execute(f"ALTER TABLE {tabel} ADD COLUMN {kolom} {definisi}")
        c.execute("UPDATE kas_kecil SET jumlah_keluar=jumlah WHERE jumlah_keluar=0")
        kolom_jual = {r[1] for r in c.execute("PRAGMA table_info(penjualan)")}
        if "ongkir" not in kolom_jual:
            c.execute("ALTER TABLE penjualan ADD COLUMN ongkir REAL NOT NULL DEFAULT 0")
        c.execute("UPDATE penjualan SET subtotal=total_harga-ongkir WHERE subtotal=0")
        if "jatuh_tempo" not in kolom_jual:
            c.execute("ALTER TABLE penjualan ADD COLUMN jatuh_tempo TEXT")
        kolom_beli = {r[1] for r in c.execute("PRAGMA table_info(pembelian)")}
        if "jatuh_tempo" not in kolom_beli:
            c.execute("ALTER TABLE pembelian ADD COLUMN jatuh_tempo TEXT")
        c.execute("INSERT OR IGNORE INTO kebijakan VALUES ('ongkir_per_kg', '15000')")
        c.execute("INSERT OR IGNORE INTO kebijakan VALUES ('denda_persen', '0')")
        c.execute("INSERT OR IGNORE INTO kebijakan VALUES ('termin_hari', '30')")
        c.commit()

    def isi_data_awal(self):
        c = self.conn
        # Nama akun Owner selalu tunggal dan tetap, termasuk pada database lama.
        c.execute("INSERT OR REPLACE INTO profil_owner (id,nama) VALUES (1,'Owner')")
        c.execute("INSERT OR IGNORE INTO akun_jabatan VALUES (?, ?)", ("Owner", hash_password("owner999")))
        c.execute("INSERT OR IGNORE INTO akun_jabatan VALUES (?, ?)", ("Karyawan", hash_password("kerja111")))
        c.executemany("INSERT OR IGNORE INTO akun VALUES (?, ?, ?, ?)", self.AKUN_AWAL)
        if not c.execute("SELECT 1 FROM schema_migrations WHERE nama='inventory_split_v1'").fetchone():
            c.execute("UPDATE jurnal_detail SET kode_akun='1104' WHERE kode_akun='1103'")
            c.execute("UPDATE akun SET nama='Persediaan Pakan' WHERE kode='1103'")
            c.execute("UPDATE akun SET nama='Persediaan Ikan Bawal' WHERE kode='1104'")
            c.execute("INSERT INTO schema_migrations(nama) VALUES ('inventory_split_v1')")
        for ident in [r[0] for r in c.execute("SELECT id_kategori FROM kategori_ukuran WHERE kode IS NULL")]:
            c.execute("UPDATE kategori_ukuran SET kode=? WHERE id_kategori=?", (f"KAT{ident:02d}", ident))
        for ident, kind in c.execute("SELECT id_produk,jenis_produk FROM produk_bawal WHERE kode IS NULL").fetchall():
            prefix = "PKN" if kind == "Pakan" else "BWL"
            c.execute("UPDATE produk_bawal SET kode=? WHERE id_produk=?", (f"{prefix}{ident:02d}", ident))
        if not c.execute("SELECT 1 FROM schema_migrations WHERE nama='fish_count_estimate_v1'").fetchone():
            c.execute("""UPDATE produk_bawal SET stok_ekor=CAST(ROUND(stok *
                        CASE (SELECT nama FROM kategori_ukuran k WHERE k.id_kategori=produk_bawal.id_kategori)
                        WHEN 'Kecil' THEN 9 WHEN 'Sedang' THEN 5 WHEN 'Besar' THEN 2
                        WHEN 'Jumbo' THEN 1 ELSE 1 END) AS INTEGER)
                        WHERE jenis_produk='Ikan' AND stok_ekor=0 AND stok>0""")
            c.execute("INSERT INTO schema_migrations(nama) VALUES ('fish_count_estimate_v1')")
        c.execute("UPDATE akun SET nama=REPLACE(nama, 'Nila', 'Bawal') WHERE nama LIKE '%Nila%'")
        c.execute("UPDATE produk_bawal SET jenis_bawal=REPLACE(jenis_bawal, 'Nila', 'Bawal') WHERE jenis_bawal LIKE '%Nila%'")
        c.execute("UPDATE produk_bawal SET jenis_bawal='Bibit Bawal' WHERE jenis_bawal IN ('Bawal Nila', 'Bibit Nila', 'Bawal Bawal')")
        c.execute("UPDATE jurnal SET keterangan=REPLACE(keterangan, 'Nila', 'Bawal') WHERE keterangan LIKE '%Nila%'")
        c.execute("UPDATE histori_aktivitas SET aktivitas=REPLACE(aktivitas, 'Nila', 'Bawal') WHERE aktivitas LIKE '%Nila%'")
        if c.execute("SELECT COUNT(*) FROM kategori_ukuran").fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO kategori_ukuran (nama, keterangan) VALUES (?, ?)",
                self.KATEGORI_AWAL)
        if c.execute("SELECT COUNT(*) FROM produk_bawal").fetchone()[0] == 0:
            nilai = 0.0
            for jenis, kat, stok, beli, jual in self.PRODUK_AWAL:
                idk = c.execute("SELECT id_kategori FROM kategori_ukuran WHERE nama=?",
                                (kat,)).fetchone()[0]
                c.execute("INSERT INTO produk_bawal (jenis_bawal, id_kategori, stok, "
                          "harga_beli, harga_jual) VALUES (?, ?, ?, ?, ?)",
                          (jenis, idk, stok, beli, jual))
                nilai += stok * beli
            kas_awal = 5_000_000
            with self.transaksi():
                self._simpan_jurnal(
                    "Saldo awal usaha",
                    [("1101", kas_awal, 0), ("1104", nilai, 0),
                     ("3101", 0, kas_awal + nilai)],
                    {"nama": "Sistem", "jabatan": "Sistem"}, ref="SALDO-AWAL")
        if not c.execute("SELECT 1 FROM produk_bawal WHERE jenis_produk='Pakan' LIMIT 1").fetchone():
            baris_kat = c.execute("SELECT id_kategori FROM kategori_ukuran WHERE nama='Pakan Bawal'").fetchone()
            if not baris_kat:
                kode_kat = f"PKN{c.execute('SELECT COALESCE(MAX(id_kategori),0)+1 FROM kategori_ukuran').fetchone()[0]:02d}"
                cur_kat = c.execute("INSERT INTO kategori_ukuran(nama,keterangan,kode) VALUES(?,?,?)",
                                    ("Pakan Bawal", "Persediaan pakan ikan", kode_kat))
                baris_kat = (cur_kat.lastrowid,)
            kode_produk = "PKN01"
            if c.execute("SELECT 1 FROM produk_bawal WHERE kode=?", (kode_produk,)).fetchone():
                kode_produk = f"PKN{c.execute('SELECT COALESCE(MAX(id_produk),0)+1 FROM produk_bawal').fetchone()[0]:02d}"
            c.execute("INSERT INTO produk_bawal(jenis_bawal,kode,jenis_produk,stok_ekor,id_kategori,stok,harga_beli,harga_jual) VALUES(?,?,?,?,?,?,?,?)",
                      ("Pakan Ikan", kode_produk, "Pakan", 0, baris_kat[0], 0, 12000, 0))
        for ident in [r[0] for r in c.execute("SELECT id_kategori FROM kategori_ukuran WHERE kode IS NULL")]:
            c.execute("UPDATE kategori_ukuran SET kode=? WHERE id_kategori=?", (f"KAT{ident:02d}", ident))
        for ident, kind in c.execute("SELECT id_produk,jenis_produk FROM produk_bawal WHERE kode IS NULL").fetchall():
            prefix = "PKN" if kind == "Pakan" else "BWL"
            c.execute("UPDATE produk_bawal SET kode=? WHERE id_produk=?", (f"{prefix}{ident:02d}", ident))
        c.commit()

    # ---------- login & histori ----------
    def verifikasi_login(self, jabatan, password):
        r = self.conn.execute(
            "SELECT 1 FROM akun_jabatan WHERE jabatan=? AND password=?",
            (jabatan, hash_password(password))).fetchone()
        return r is not None

    def ganti_password(self, jabatan, password_lama, password_baru, user):
        if jabatan not in ("Owner", "Karyawan"):
            raise ValueError("Jabatan tidak valid.")
        if not self.verifikasi_login(jabatan, password_lama):
            raise ValueError("Password saat ini tidak cocok.")
        if len(password_baru) < 4:
            raise ValueError("Password baru minimal 4 karakter.")
        with self.transaksi():
            self.conn.execute("UPDATE akun_jabatan SET password=? WHERE jabatan=?",
                              (hash_password(password_baru), jabatan))
            self._histori(user, f"Mengubah password akun {jabatan}")

    def backup_database(self, tujuan):
        if self.path == ":memory:":
            raise ValueError("Database sementara tidak dapat dibackup ke file aplikasi.")
        tujuan = os.path.abspath(tujuan)
        if tujuan == self.path:
            raise ValueError("Pilih lokasi backup yang berbeda dari database aktif.")
        target = sqlite3.connect(tujuan)
        try:
            self.conn.commit()
            self.conn.backup(target)
        finally:
            target.close()
        return tujuan

    def pulihkan_database(self, sumber):
        if self.path == ":memory:":
            raise ValueError("Database sementara tidak dapat dipulihkan dari file aplikasi.")
        sumber = os.path.abspath(sumber)
        if sumber == self.path:
            raise ValueError("Pilih file backup, bukan database yang sedang digunakan.")
        if not os.path.isfile(sumber):
            raise ValueError("File backup tidak ditemukan.")
        src = sqlite3.connect(sumber)
        try:
            if src.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("File backup rusak dan tidak dapat dipulihkan.")
            tabel = {r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            wajib = {"akun_jabatan", "histori_aktivitas", "akun", "jurnal", "jurnal_detail", "produk_bawal"}
            if not wajib.issubset(tabel):
                raise ValueError("File yang dipilih bukan backup Nexafish yang lengkap.")
            cap = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            aman = f"{self.path}.sebelum_pemulihan_{cap}.bak"
            cadangan = sqlite3.connect(aman)
            try:
                self.conn.commit()
                self.conn.backup(cadangan)
            finally:
                cadangan.close()
            try:
                src.backup(self.conn)
                self.buat_tabel()
                self.isi_data_awal()
            except Exception:
                rollback = sqlite3.connect(aman)
                try:
                    rollback.backup(self.conn)
                finally:
                    rollback.close()
                raise
            return aman
        finally:
            src.close()

    def nama_owner(self):
        row = self.conn.execute("SELECT nama FROM profil_owner WHERE id=1").fetchone()
        return row[0] if row else ""

    def validasi_nama_owner(self, nama):
        """Terima hanya nama akun tetap Owner, tanpa pendaftaran nama bebas."""
        return "Owner" if nama.strip().casefold() == "owner" else None

    def catat_histori(self, nama, jabatan, aktivitas):
        self.conn.execute(
            "INSERT INTO histori_aktivitas (waktu, nama_pengguna, jabatan, aktivitas) "
            "VALUES (?, ?, ?, ?)", (sekarang(), nama, jabatan, aktivitas))
        self.conn.commit()

    def _histori(self, user, aktivitas):
        """Catat histori tanpa commit (dipakai di dalam transaksi)."""
        self.conn.execute(
            "INSERT INTO histori_aktivitas (waktu, nama_pengguna, jabatan, aktivitas) "
            "VALUES (?, ?, ?, ?)", (sekarang(), user["nama"], user["jabatan"], aktivitas))

    def daftar_histori(self, limit=300):
        return self.conn.execute(
            "SELECT waktu, nama_pengguna, jabatan, aktivitas FROM histori_aktivitas "
            "ORDER BY id_histori DESC LIMIT ?", (limit,)).fetchall()

    # ---------- jurnal (double entry) ----------
    def _simpan_jurnal(self, keterangan, lines, user, ref=None, tanggal=None):
        """lines = [(kode_akun, debit, kredit), ...]. Total debit harus = total kredit."""
        bersih = []
        for kode, d, k in lines:
            d, k = round(float(d), 2), round(float(k), 2)
            if d < 0 or k < 0:
                raise ValueError("Nilai debit/kredit tidak boleh negatif.")
            if d > 0 and k > 0:
                raise ValueError("Satu baris tidak boleh berisi debit dan kredit sekaligus.")
            if d > 0 or k > 0:
                bersih.append((kode, d, k))
        if len(bersih) < 2:
            raise ValueError("Jurnal minimal terdiri dari 2 baris (debit dan kredit).")
        td = round(sum(x[1] for x in bersih), 2)
        tk_ = round(sum(x[2] for x in bersih), 2)
        if abs(td - tk_) > 0.005:
            raise ValueError(
                f"Jurnal tidak seimbang: debit {rupiah(td)} tidak sama dengan kredit {rupiah(tk_)}.")
        cur = self.conn.execute(
            "INSERT INTO jurnal (tanggal, keterangan, referensi, dibuat_oleh) VALUES (?, ?, ?, ?)",
            (tanggal or sekarang(), keterangan, ref, user["nama"]))
        id_j = cur.lastrowid
        self.conn.executemany(
            "INSERT INTO jurnal_detail (id_jurnal, kode_akun, debit, kredit) VALUES (?, ?, ?, ?)",
            [(id_j, kode, d, k) for kode, d, k in bersih])
        return id_j

    def jurnal_manual(self, keterangan, lines, user):
        keterangan = keterangan.strip()
        if not keterangan:
            raise ValueError("Keterangan jurnal tidak boleh kosong.")
        with self.transaksi():
            id_j = self._simpan_jurnal(keterangan, lines, user, ref="MANUAL")
            self._histori(user, f"Membuat jurnal manual #{id_j}: {keterangan}")
        return id_j

    def jurnal_penyesuaian(self, keterangan, lines, user, tanggal=None):
        keterangan = keterangan.strip()
        if not keterangan:
            raise ValueError("Keterangan penyesuaian tidak boleh kosong.")
        with self.transaksi():
            id_j = self._simpan_jurnal(keterangan, lines, user, ref="JURNAL-PENYESUAIAN", tanggal=tanggal)
            self._histori(user, f"Membuat jurnal penyesuaian #{id_j}: {keterangan}")
        return id_j

    def kelola_akun(self, kode, nama, tipe, normal, saldo_awal=0, user=None):
        kode, nama = kode.strip(), nama.strip()
        if not kode or not nama:
            raise ValueError("Kode dan nama akun wajib diisi.")
        if tipe not in ("Aset", "Kewajiban", "Modal", "Pendapatan", "Beban"):
            raise ValueError("Tipe akun tidak valid.")
        if normal not in ("Debit", "Kredit"):
            raise ValueError("Saldo normal harus Debit atau Kredit.")
        saldo_awal = float(saldo_awal)
        if saldo_awal < 0:
            raise ValueError("Saldo awal tidak boleh negatif.")
        with self.transaksi():
            ada = self.conn.execute("SELECT 1 FROM akun WHERE kode=?", (kode,)).fetchone()
            if ada:
                self.conn.execute("UPDATE akun SET nama=?, tipe=?, saldo_normal=? WHERE kode=?",
                                  (nama, tipe, normal, kode))
            else:
                self.conn.execute("INSERT INTO akun VALUES (?, ?, ?, ?)", (kode, nama, tipe, normal))
            if saldo_awal:
                ket_awal=f"Saldo awal akun {kode} - {nama}"
                sudah=self.conn.execute("SELECT 1 FROM jurnal WHERE referensi='SALDO-AWAL-AKUN' AND keterangan LIKE ? LIMIT 1",(f"Saldo awal akun {kode} -%",)).fetchone()
                if sudah:
                    raise ValueError("Saldo awal akun ini sudah pernah dicatat. Koreksi melalui Jurnal Umum.")
                lawan = "1101" if kode == "3101" else "3101"
                lines = [(kode, saldo_awal, 0)] if normal == "Debit" else [(kode, 0, saldo_awal)]
                lines += [(lawan, 0, saldo_awal)] if normal == "Debit" else [(lawan, saldo_awal, 0)]
                self._simpan_jurnal(ket_awal, lines,
                                    user or {"nama": "Owner", "jabatan": "Owner"}, ref="SALDO-AWAL-AKUN")
            if user:
                self._histori(user, f"Menyimpan akun {kode} - {nama}")

    def hapus_akun(self, kode, user=None):
        if kode in {a[0] for a in self.AKUN_AWAL}:
            raise ValueError("Akun inti sistem tidak dapat dihapus.")
        dipakai = self.conn.execute("SELECT COUNT(*) FROM jurnal_detail WHERE kode_akun=?", (kode,)).fetchone()[0]
        if dipakai:
            raise ValueError("Akun sudah dipakai dalam jurnal dan tidak dapat dihapus.")
        with self.transaksi():
            self.conn.execute("DELETE FROM akun WHERE kode=?", (kode,))
            if user: self._histori(user, f"Menghapus akun {kode}")

    def daftar_pihak(self, jenis):
        tabel = "customer" if jenis == "customer" else "supplier"
        return self.conn.execute(f"SELECT id,nama,telepon,alamat,saldo_awal FROM {tabel} ORDER BY nama").fetchall()

    def tambah_pihak(self, jenis, nama, telepon, alamat, saldo_awal=0, user=None):
        tabel, akun = ("customer", "1102") if jenis == "customer" else ("supplier", "2101")
        nama = nama.strip()
        saldo_awal = float(saldo_awal)
        if not nama:
            raise ValueError("Nama wajib diisi.")
        if saldo_awal < 0:
            raise ValueError("Saldo awal tidak boleh negatif.")
        try:
            with self.transaksi():
                self.conn.execute(f"INSERT INTO {tabel} (nama,telepon,alamat,saldo_awal) VALUES (?,?,?,?)",
                                  (nama, telepon.strip(), alamat.strip(), saldo_awal))
                if saldo_awal:
                    lines = [(akun, saldo_awal, 0), ("3101", 0, saldo_awal)] if jenis == "customer" else [("3101", saldo_awal, 0), (akun, 0, saldo_awal)]
                    self._simpan_jurnal(f"Saldo awal {'piutang' if jenis == 'customer' else 'utang'} {nama}",
                                        lines, user or {"nama": "Owner", "jabatan": "Owner"}, ref="SALDO-AWAL-PIHAK")
                if user: self._histori(user, f"Menambah {jenis}: {nama}")
        except sqlite3.IntegrityError:
            raise ValueError(f"Nama {jenis} tersebut sudah terdaftar.")

    def ongkir_otomatis(self, jumlah):
        jumlah = float(jumlah)
        if jumlah <= 0:
            return 0.0
        return float(math.ceil(jumlah / 10) * 15000)

    def set_kebijakan(self, denda_persen, termin_hari, user=None):
        if min(denda_persen, termin_hari) < 0:
            raise ValueError("Kebijakan tidak boleh bernilai negatif.")
        with self.transaksi():
            for k,v in (("denda_persen",denda_persen),("termin_hari",termin_hari)):
                self.conn.execute("INSERT OR REPLACE INTO kebijakan VALUES (?,?)",(k,str(v)))
            if user: self._histori(user,"Mengubah kebijakan denda dan termin")

    def jatuh_tempo_kredit(self):
        hari = int(float(self.conn.execute("SELECT nilai FROM kebijakan WHERE nama='termin_hari'").fetchone()[0]))
        return (datetime.date.today() + datetime.timedelta(days=hari)).isoformat()

    def pembelian_produk(self, id_produk, supplier, jumlah, harga, metode, user, jumlah_ekor=0):
        p = self.ambil_produk(id_produk)
        jumlah, harga = float(jumlah), float(harga)
        jumlah_ekor = float(jumlah_ekor or 0)
        if jumlah <= 0 or harga < 0 or jumlah_ekor < 0 or not jumlah_ekor.is_integer():
            raise ValueError("Jumlah harus lebih dari nol dan harga tidak boleh negatif.")
        jumlah_ekor = int(jumlah_ekor)
        if p["jenis_produk"] == "Pakan" and jumlah_ekor:
            raise ValueError("Jumlah ekor hanya berlaku untuk produk ikan.")
        if metode != "Tunai":
            raise ValueError("Pembelian pada revisi ini hanya menggunakan metode tunai.")
        supplier = supplier.strip() or "Supplier Umum"
        total = round(jumlah * harga, 2)
        if self._saldo_kas() + 0.005 < total:
            raise ValueError("Saldo kas tidak cukup untuk pembelian ini.")
        akun_stok = "1103" if p["jenis_produk"] == "Pakan" else "1104"
        stok_baru = round(p["stok"] + jumlah, 3)
        hpp_baru = round((p["stok"] * p["harga_beli"] + total) / stok_baru, 4)
        with self.transaksi():
            self.conn.execute("INSERT OR IGNORE INTO supplier (nama) VALUES (?)", (supplier,))
            self.conn.execute("UPDATE produk_bawal SET stok=?,harga_beli=?,stok_ekor=stok_ekor+? WHERE id_produk=?",
                              (stok_baru, hpp_baru, jumlah_ekor, id_produk))
            idj = self._simpan_jurnal(f"Pembelian {jumlah:g} kg {p['jenis']} dari {supplier}",
                                     [(akun_stok, total, 0), ("1101", 0, total)], user, ref="PEMBELIAN")
            cur = self.conn.execute(
                "INSERT INTO pembelian (waktu,supplier,produk,jumlah,harga_satuan,ongkir,total,metode,dibuat_oleh,id_jurnal) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (sekarang(), supplier, p["jenis"], jumlah, harga, 0, total, "Tunai", user["nama"], idj))
            return_id = cur.lastrowid
            self._histori(user, f"Pembelian {jumlah:g} kg {p['jenis']} dari {supplier} senilai {rupiah(total)}")
        return return_id, total, 0.0

    def catat_kas(self, jenis, keterangan, jumlah, akun_lawan, user, kas_kecil=False, nama_pihak="", tanggal=None):
        jumlah = float(jumlah)
        keterangan = keterangan.strip()
        if jenis not in ("Penerimaan", "Pengeluaran") or jumlah <= 0 or not keterangan:
            raise ValueError("Jenis, keterangan, dan jumlah kas wajib diisi dengan benar.")
        akun = self.conn.execute("SELECT tipe FROM akun WHERE kode=?", (akun_lawan,)).fetchone()
        if not akun or akun_lawan in ("1101", "1105"):
            raise ValueError("Pilih akun lawan yang valid.")
        if jenis == "Pengeluaran" and self._saldo_kas() + 0.005 < jumlah:
            raise ValueError("Saldo kas tidak cukup.")
        lines = [("1101", jumlah, 0), (akun_lawan, 0, jumlah)] if jenis == "Penerimaan" else [(akun_lawan, jumlah, 0), ("1101", 0, jumlah)]
        with self.transaksi():
            idj = self._simpan_jurnal(keterangan, lines, user, ref="KAS", tanggal=tanggal)
            cur = self.conn.execute(
                "INSERT INTO kas_transaksi(waktu,jenis,keterangan,jumlah,akun_lawan,dibuat_oleh,id_jurnal,nama_pihak) VALUES(?,?,?,?,?,?,?,?)",
                (tanggal or sekarang(), jenis, keterangan, jumlah, akun_lawan, user["nama"], idj, nama_pihak.strip()))
            ident = cur.lastrowid
            self._histori(user, f"{jenis} kas {rupiah(jumlah)}: {keterangan}")
        return f"{'KM' if jenis == 'Penerimaan' else 'KK'}-{ident:03d}"

    def daftar_kas(self, limit=300):
        return self.conn.execute(
            "SELECT id,waktu,jenis,keterangan,jumlah,akun_lawan,dibuat_oleh,nama_pihak FROM kas_transaksi ORDER BY id DESC LIMIT ?",
            (limit,)).fetchall()

    def saldo_kas_kecil(self):
        row = next((a for a in self._saldo_semua() if a["kode"] == "1105"), None)
        return row["saldo"] if row else 0.0

    def isi_dana_kas_kecil(self, jumlah, user, tanggal=None, keterangan="Pengisian Kas Kecil"):
        jumlah = float(jumlah)
        if jumlah <= 0 or self._saldo_kas() + 0.005 < jumlah:
            raise ValueError("Jumlah harus positif dan saldo kas utama harus mencukupi.")
        with self.transaksi():
            idj = self._simpan_jurnal(keterangan, [("1105", jumlah, 0), ("1101", 0, jumlah)],
                                      user, ref="KAS-KECIL", tanggal=tanggal)
            cur = self.conn.execute(
                "INSERT INTO kas_kecil(waktu,keterangan,jumlah,akun,dibuat_oleh,id_jurnal,jenis,jumlah_masuk) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (tanggal or sekarang(), keterangan, jumlah, "1101", user["nama"], idj, "Masuk", jumlah))
            ident = cur.lastrowid
            nomor = f"KMK-{ident:03d}"
            self.conn.execute("UPDATE kas_kecil SET nomor_bukti=? WHERE id=?", (nomor, ident))
            self._histori(user, f"Isi kas kecil {rupiah(jumlah)}")
        return nomor

    def catat_belanja_kas_kecil(self, akun_beban, jumlah, keterangan, user, tanggal=None):
        jumlah = float(jumlah)
        keterangan = keterangan.strip()
        tipe = self.conn.execute("SELECT tipe FROM akun WHERE kode=?", (akun_beban,)).fetchone()
        if jumlah <= 0 or not keterangan or not tipe or tipe[0] != "Beban":
            raise ValueError("Pilih akun beban, isi keterangan, dan masukkan jumlah yang valid.")
        if self.saldo_kas_kecil() + 0.005 < jumlah:
            raise ValueError("Saldo kas kecil tidak cukup.")
        with self.transaksi():
            idj = self._simpan_jurnal(keterangan, [(akun_beban, jumlah, 0), ("1105", 0, jumlah)],
                                      user, ref="KAS-KECIL", tanggal=tanggal)
            cur = self.conn.execute(
                "INSERT INTO kas_kecil(waktu,keterangan,jumlah,akun,dibuat_oleh,id_jurnal,jenis,jumlah_keluar) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (tanggal or sekarang(), keterangan, jumlah, akun_beban, user["nama"], idj, "Keluar", jumlah))
            ident = cur.lastrowid
            nomor = f"BKK-{ident:03d}"
            self.conn.execute("UPDATE kas_kecil SET nomor_bukti=? WHERE id=?", (nomor, ident))
            self._histori(user, f"Belanja kas kecil {rupiah(jumlah)}: {keterangan}")
        return nomor

    def daftar_kas_kecil(self, limit=300):
        return self.conn.execute(
            "SELECT id,waktu,nomor_bukti,keterangan,jumlah_masuk,jumlah_keluar,jenis "
            "FROM kas_kecil ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

    def hapus_kas_kecil(self, ident, user):
        row = self.conn.execute("SELECT id_jurnal,keterangan FROM kas_kecil WHERE id=?", (ident,)).fetchone()
        if not row:
            raise ValueError("Transaksi kas kecil tidak ditemukan.")
        idj, ket = row
        with self.transaksi():
            lines = self.conn.execute(
                "SELECT kode_akun,debit,kredit FROM jurnal_detail WHERE id_jurnal=?", (idj,)).fetchall()
            if lines:
                self._simpan_jurnal(f"Pembatalan kas kecil #{ident}: {ket}",
                                    [(k,kr,d) for k,d,kr in lines], user, ref="VOID-KAS-KECIL")
            self.conn.execute("DELETE FROM kas_kecil WHERE id=?", (ident,))
            self._histori(user, f"Menghapus transaksi kas kecil #{ident} (dibalikkan di jurnal)")

    def daftar_pembelian(self, limit=100):
        return self.conn.execute("SELECT waktu,supplier,produk,jumlah,total,metode,dibuat_oleh FROM pembelian ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

    def daftar_akun(self):
        return self.conn.execute(
            "SELECT kode, nama, tipe, saldo_normal FROM akun ORDER BY kode").fetchall()

    def _saldo_semua(self, include_adjustments=True):
        rows = self.conn.execute(
            "SELECT a.kode, a.nama, a.tipe, a.saldo_normal, "
            "COALESCE(SUM(CASE WHEN (?=1 OR j.referensi IS NULL OR j.referensi NOT IN "
            "('JURNAL-PENYESUAIAN','PEMAKAIAN-PAKAN','STOCK-OPNAME','VOID-STOCK-OPNAME')) THEN d.debit ELSE 0 END), 0), "
            "COALESCE(SUM(CASE WHEN (?=1 OR j.referensi IS NULL OR j.referensi NOT IN "
            "('JURNAL-PENYESUAIAN','PEMAKAIAN-PAKAN','STOCK-OPNAME','VOID-STOCK-OPNAME')) THEN d.kredit ELSE 0 END), 0) "
            "FROM akun a LEFT JOIN jurnal_detail d ON d.kode_akun = a.kode "
            "LEFT JOIN jurnal j ON j.id_jurnal=d.id_jurnal "
            "GROUP BY a.kode ORDER BY a.kode",
            (1 if include_adjustments else 0,1 if include_adjustments else 0)).fetchall()
        hasil = []
        for kode, nama, tipe, normal, deb, kre in rows:
            saldo = (deb - kre) if normal == "Debit" else (kre - deb)
            hasil.append({"kode": kode, "nama": nama, "tipe": tipe, "normal": normal,
                          "debit": deb, "kredit": kre, "saldo": round(saldo, 2)})
        return hasil

    def _saldo_kas(self):
        return self.conn.execute(
            "SELECT COALESCE(SUM(debit - kredit), 0) FROM jurnal_detail WHERE kode_akun='1101'"
        ).fetchone()[0]

    def daftar_jurnal(self, limit=150):
        hasil = []
        heads = self.conn.execute(
            "SELECT id_jurnal, tanggal, keterangan, dibuat_oleh FROM jurnal "
            "ORDER BY id_jurnal DESC LIMIT ?", (limit,)).fetchall()
        for h in heads:
            lines = self.conn.execute(
                "SELECT a.kode, a.nama, d.debit, d.kredit FROM jurnal_detail d "
                "JOIN akun a ON a.kode = d.kode_akun WHERE d.id_jurnal=? "
                "ORDER BY d.id_detail", (h[0],)).fetchall()
            hasil.append((h, lines))
        return hasil

    def buku_besar(self, kode):
        akun = self.conn.execute("SELECT nama, saldo_normal FROM akun WHERE kode=?",
                                 (kode,)).fetchone()
        if not akun:
            raise ValueError("Akun tidak ditemukan.")
        rows = self.conn.execute(
            "SELECT j.tanggal, j.keterangan, d.debit, d.kredit FROM jurnal_detail d "
            "JOIN jurnal j ON j.id_jurnal = d.id_jurnal WHERE d.kode_akun=? "
            "ORDER BY j.id_jurnal, d.id_detail", (kode,)).fetchall()
        saldo, hasil = 0.0, []
        for tgl, ket, deb, kre in rows:
            saldo += (deb - kre) if akun[1] == "Debit" else (kre - deb)
            hasil.append((tgl, ket, deb, kre, saldo))
        return akun, hasil

    # ---------- laporan ----------
    def neraca_saldo(self, penyesuaian=True):
        rows, td, tk_ = [], 0.0, 0.0
        for a in self._saldo_semua(include_adjustments=penyesuaian):
            net = a["debit"] - a["kredit"]
            d, k = (net, 0.0) if net >= 0 else (0.0, -net)
            td += d
            tk_ += k
            rows.append((a["kode"], a["nama"], d, k))
        return rows, round(td, 2), round(tk_, 2)

    def laba_rugi(self):
        s = {a["kode"]: a for a in self._saldo_semua()}
        pendapatan = sum(a["saldo"] for a in s.values() if a["tipe"] == "Pendapatan")
        hpp = s["5101"]["saldo"]
        beban = [(a["nama"], a["saldo"]) for a in s.values()
                 if a["tipe"] == "Beban" and a["kode"] != "5101"]
        laba_kotor = pendapatan - hpp
        laba_bersih = laba_kotor - sum(b[1] for b in beban)
        return {"pendapatan": pendapatan, "hpp": hpp, "laba_kotor": laba_kotor,
                "beban": beban, "laba_bersih": laba_bersih}

    def laporan_perubahan_modal(self):
        saldo_modal = self.conn.execute(
            "SELECT COALESCE(SUM(d.kredit-d.debit),0) FROM jurnal_detail d "
            "JOIN jurnal j ON j.id_jurnal=d.id_jurnal WHERE d.kode_akun='3101'").fetchone()[0]
        modal_awal = self.conn.execute(
            "SELECT COALESCE(SUM(d.kredit-d.debit),0) FROM jurnal_detail d "
            "JOIN jurnal j ON j.id_jurnal=d.id_jurnal WHERE d.kode_akun='3101' "
            "AND j.referensi LIKE 'SALDO-AWAL%'").fetchone()[0]
        prive = self.conn.execute(
            "SELECT COALESCE(SUM(d.debit-d.kredit),0) FROM jurnal_detail d "
            "WHERE d.kode_akun='3201'").fetchone()[0]
        setoran = saldo_modal - modal_awal
        laba = self.laba_rugi()["laba_bersih"]
        return {"modal_awal":modal_awal,"setoran":setoran,"laba":laba,
                "prive":prive,"akhir":modal_awal+setoran+laba-prive}

    def laporan_arus_kas(self):
        rows = self.conn.execute(
            "SELECT j.tanggal,j.keterangan,d.debit,d.kredit FROM jurnal_detail d "
            "JOIN jurnal j ON j.id_jurnal=d.id_jurnal WHERE d.kode_akun='1101' ORDER BY j.id_jurnal,d.id_detail"
        ).fetchall()
        hasil, saldo = [], 0.0
        for tgl, ket, debit, kredit in rows:
            saldo += debit-kredit
            hasil.append((tgl, ket, debit, kredit, saldo))
        return hasil

    def laporan_arus_kas_langsung(self, periode=None):
        periode=periode or datetime.date.today().strftime("%Y-%m")
        awal=periode+"-01"
        akhir=(datetime.date.fromisoformat(awal).replace(day=28)+datetime.timedelta(days=4)).replace(day=1).isoformat()
        tahun_awal=periode[:4]+"-01-01"
        ada_saldo_tahun_lalu=self.conn.execute(
            "SELECT 1 FROM jurnal_detail d JOIN jurnal j ON j.id_jurnal=d.id_jurnal "
            "WHERE d.kode_akun IN ('1101','1105') AND j.tanggal<? LIMIT 1",(tahun_awal,)).fetchone()
        saldo_tahun_lalu=self.conn.execute(
            "SELECT COALESCE(SUM(d.debit-d.kredit),0) FROM jurnal_detail d JOIN jurnal j ON j.id_jurnal=d.id_jurnal "
            "WHERE d.kode_akun IN ('1101','1105') AND j.tanggal<?",(tahun_awal,)).fetchone()[0]
        saldo_awal=(saldo_tahun_lalu if ada_saldo_tahun_lalu else 65_000_000)+self.conn.execute(
            "SELECT COALESCE(SUM(d.debit-d.kredit),0) FROM jurnal_detail d JOIN jurnal j ON j.id_jurnal=d.id_jurnal "
            "WHERE d.kode_akun IN ('1101','1105') AND j.tanggal>=? AND j.tanggal<? "
            "AND COALESCE(j.referensi,'') NOT LIKE 'SALDO-AWAL%'",(tahun_awal,awal)).fetchone()[0]
        rows=self.conn.execute(
            "SELECT j.id_jurnal,SUM(d.debit),SUM(d.kredit) FROM jurnal_detail d JOIN jurnal j ON j.id_jurnal=d.id_jurnal "
            "WHERE d.kode_akun IN ('1101','1105') AND j.tanggal>=? AND j.tanggal<? "
            "AND COALESCE(j.referensi,'') NOT LIKE 'SALDO-AWAL%' GROUP BY j.id_jurnal",(awal,akhir)).fetchall()
        totals={"sales":0.0,"bibit":0.0,"feed":0.0,"expense":0.0,"capital":0.0,"prive":0.0}
        for jid,debit,credit in rows:
            masuk=max(0.0,(debit or 0)-(credit or 0))
            keluar=max(0.0,(credit or 0)-(debit or 0))
            if not masuk and not keluar:
                continue
            lawan=self.conn.execute(
                "SELECT d.kode_akun,d.debit,d.kredit,a.tipe FROM jurnal_detail d JOIN akun a ON a.kode=d.kode_akun "
                "WHERE d.id_jurnal=? AND d.kode_akun NOT IN ('1101','1105')",(jid,)).fetchall()
            for kode,deb,kre,tipe in lawan:
                if masuk>0:
                    if kode in ("4101","4102","1102"): totals["sales"]+=masuk
                    elif kode=="3101": totals["capital"]+=masuk
                if keluar>0:
                    if kode=="1103": totals["feed"]+=keluar
                    elif kode in ("1104","1201","2101"): totals["bibit"]+=keluar
                    elif kode=="3201": totals["prive"]+=keluar
                    elif tipe=="Beban": totals["expense"]+=keluar
        operasi=totals["sales"]-totals["bibit"]-totals["feed"]-totals["expense"]
        net=operasi+totals["capital"]-totals["prive"]
        return {**totals,"operasi":operasi,"kenaikan":net,"awal":saldo_awal,"akhir":saldo_awal+net}

    def daftar_jurnal_penyesuaian(self, limit=300):
        return self.conn.execute(
            "SELECT id_jurnal,tanggal,keterangan,dibuat_oleh FROM jurnal "
            "WHERE referensi IN ('JURNAL-PENYESUAIAN','PEMAKAIAN-PAKAN','STOCK-OPNAME','VOID-STOCK-OPNAME') "
            "ORDER BY id_jurnal DESC LIMIT ?", (limit,)
        ).fetchall()

    def neraca_lajur(self):
        sebelum, _td, _tk = self.neraca_saldo(False)
        semua = {a["kode"]:a for a in self._saldo_semua(include_adjustments=False)}
        adj = {k:(d or 0,kr or 0) for k,d,kr in self.conn.execute(
            "SELECT kode_akun,SUM(debit),SUM(kredit) FROM jurnal_detail d "
            "JOIN jurnal j ON j.id_jurnal=d.id_jurnal WHERE j.referensi IN "
            "('JURNAL-PENYESUAIAN','PEMAKAIAN-PAKAN','STOCK-OPNAME','VOID-STOCK-OPNAME') "
            "GROUP BY kode_akun").fetchall()}
        hasil=[]
        total_lr_d=total_lr_k=total_ns_d=total_ns_k=0.0
        for kode,nama,sd,sk in sebelum:
            ad,ak=adj.get(kode,(0,0))
            net=sd-sk+ad-ak
            fd,fk=(net,0) if net>=0 else (0,-net)
            tipe=semua.get(kode,{}).get("tipe","")
            lrd,lrk,nsd,nsk=0.0,0.0,0.0,0.0
            if tipe=="Beban":
                lrd=fd-fk
                if lrd<0: lrk=-lrd; lrd=0
            elif tipe=="Pendapatan":
                lrk=fk-fd
                if lrk<0: lrd=-lrk; lrk=0
            elif tipe=="Aset":
                nsd=fd-fk
                if nsd<0: nsk=-nsd; nsd=0
            else:
                nsk=fk-fd
                if nsk<0: nsd=-nsk; nsk=0
            total_lr_d+=lrd; total_lr_k+=lrk
            total_ns_d+=nsd; total_ns_k+=nsk
            hasil.append((kode,nama,sd,sk,ad,ak,fd,fk,lrd,lrk,nsd,nsk))
        laba=total_lr_k-total_lr_d
        if laba>=0:
            total_lr_d+=laba
            total_ns_k+=laba
        else:
            total_lr_k+=-laba
            total_ns_d+=-laba
        hasil.append(("", "Laba Bersih", 0,0,0,0,0,0,max(laba,0),max(-laba,0),max(-laba,0),max(laba,0)))
        hasil.append(("", "TOTAL", 0,0,0,0,0,0,total_lr_d,total_lr_k,total_ns_d,total_ns_k))
        return hasil

    def posisi_keuangan(self):
        semua = self._saldo_semua()
        aset = [(a["nama"], -a["saldo"] if a["kode"] == "1302" else a["saldo"])
                for a in semua if a["tipe"] == "Aset"]
        kew = [(a["nama"], a["saldo"]) for a in semua if a["tipe"] == "Kewajiban"]
        modal = [(a["nama"], -a["saldo"] if a["kode"] == "3201" else a["saldo"])
                 for a in semua if a["tipe"] == "Modal"]
        return aset, kew, modal, self.laba_rugi()["laba_bersih"]

    # ---------- kategori ukuran ----------
    def daftar_kategori(self):
        return self.conn.execute(
            "SELECT k.id_kategori, k.nama, k.keterangan, COUNT(p.id_produk) "
            "FROM kategori_ukuran k LEFT JOIN produk_bawal p ON p.id_kategori = k.id_kategori "
            "GROUP BY k.id_kategori ORDER BY k.id_kategori").fetchall()

    def daftar_kategori_lengkap(self):
        return self.conn.execute(
            "SELECT k.id_kategori,k.kode,k.nama,k.keterangan,COUNT(p.id_produk) "
            "FROM kategori_ukuran k LEFT JOIN produk_bawal p ON p.id_kategori=k.id_kategori "
            "GROUP BY k.id_kategori ORDER BY k.id_kategori").fetchall()

    def tambah_kategori(self, nama, keterangan, user, kode=None):
        nama = nama.strip()
        kode = (kode or f"KAT{self.conn.execute('SELECT COALESCE(MAX(id_kategori),0)+1 FROM kategori_ukuran').fetchone()[0]:02d}").strip().upper()
        if not nama or not kode:
            raise ValueError("Kode dan nama kategori wajib diisi.")
        try:
            with self.transaksi():
                self.conn.execute("INSERT INTO kategori_ukuran (nama,keterangan,kode) VALUES (?,?,?)",
                                  (nama, keterangan.strip(), kode))
                self._histori(user, f"Menambah kategori ukuran {kode}: {nama}")
        except sqlite3.IntegrityError:
            raise ValueError("Kode atau nama kategori sudah digunakan.")

    def ubah_kategori(self, id_kat, nama, keterangan, user, kode=None):
        nama = nama.strip()
        if not nama:
            raise ValueError("Nama kategori tidak boleh kosong.")
        try:
            with self.transaksi():
                if kode:
                    self.conn.execute("UPDATE kategori_ukuran SET nama=?,keterangan=?,kode=? WHERE id_kategori=?",
                                      (nama, keterangan.strip(), kode.strip().upper(), id_kat))
                else:
                    self.conn.execute("UPDATE kategori_ukuran SET nama=?,keterangan=? WHERE id_kategori=?",
                                      (nama, keterangan.strip(), id_kat))
                self._histori(user, f"Mengubah kategori ukuran ID {id_kat} menjadi: {nama}")
        except sqlite3.IntegrityError:
            raise ValueError("Kode atau nama kategori sudah digunakan.")

    def hapus_kategori(self, id_kat, user):
        pakai = self.conn.execute(
            "SELECT COUNT(*) FROM produk_bawal WHERE id_kategori=?", (id_kat,)).fetchone()[0]
        if pakai > 0:
            raise ValueError(
                f"Kategori ini masih dipakai {pakai} produk. Pindahkan atau hapus produknya dulu.")
        nama = self.conn.execute("SELECT nama FROM kategori_ukuran WHERE id_kategori=?",
                                 (id_kat,)).fetchone()
        if not nama:
            raise ValueError("Kategori tidak ditemukan.")
        with self.transaksi():
            self.conn.execute("DELETE FROM kategori_ukuran WHERE id_kategori=?", (id_kat,))
            self._histori(user, f"Menghapus kategori ukuran: {nama[0]}")

    # ---------- produk ----------
    def daftar_produk(self, id_kategori=None):
        sql = ("SELECT p.id_produk,p.jenis_bawal,k.nama,p.stok,p.harga_beli,p.harga_jual "
               "FROM produk_bawal p JOIN kategori_ukuran k ON k.id_kategori=p.id_kategori ")
        if id_kategori:
            return self.conn.execute(sql + "WHERE p.id_kategori=? ORDER BY p.id_produk", (id_kategori,)).fetchall()
        return self.conn.execute(sql + "ORDER BY p.id_produk").fetchall()

    def daftar_produk_lengkap(self, id_kategori=None, jenis_produk=None):
        sql = ("SELECT p.id_produk,p.kode,p.jenis_produk,p.jenis_bawal,k.id_kategori,k.kode,k.nama,"
               "k.keterangan,p.stok,p.stok_ekor,p.harga_beli,p.harga_jual "
               "FROM produk_bawal p JOIN kategori_ukuran k ON k.id_kategori=p.id_kategori WHERE 1=1")
        params = []
        if id_kategori:
            sql += " AND p.id_kategori=?"
            params.append(id_kategori)
        if jenis_produk:
            sql += " AND p.jenis_produk=?"
            params.append(jenis_produk)
        return self.conn.execute(sql + " ORDER BY p.id_produk", params).fetchall()

    def ambil_produk(self, id_produk):
        r = self.conn.execute(
            "SELECT p.id_produk, p.jenis_bawal, p.id_kategori, k.nama, p.stok, "
            "p.harga_beli, p.harga_jual, p.kode, p.jenis_produk, p.stok_ekor FROM produk_bawal p "
            "JOIN kategori_ukuran k ON k.id_kategori = p.id_kategori "
            "WHERE p.id_produk=?", (id_produk,)).fetchone()
        if not r:
            raise ValueError("Produk tidak ditemukan.")
        return dict(zip(("id", "jenis", "id_kategori", "kategori", "stok",
                         "harga_beli", "harga_jual", "kode", "jenis_produk", "stok_ekor"), r))

    def _bayar_persediaan(self, nilai, sumber, keterangan, user, akun_stok="1104"):
        """Jurnal pembelian persediaan: Dr Persediaan, Cr Kas / Utang Usaha."""
        if nilai <= 0:
            return
        if sumber == "Kas":
            if self._saldo_kas() + 0.005 < nilai:
                raise ValueError(
                    f"Saldo kas tidak cukup ({rupiah(self._saldo_kas())}). "
                    "Pilih 'Utang Usaha' atau setor modal dulu lewat Jurnal Manual.")
            kredit = "1101"
        else:
            kredit = "2101"
        self._simpan_jurnal(keterangan, [(akun_stok, nilai, 0), (kredit, 0, nilai)],
                            user, ref="PEMBELIAN")

    def tambah_produk(self, jenis, id_kategori, stok, harga_beli, harga_jual, sumber, user,
                      kode=None, jenis_produk="Ikan", stok_ekor=0):
        jenis = jenis.strip()
        jenis_produk = jenis_produk.strip().title()
        kode = (kode or "").strip().upper()
        stok_ekor = float(stok_ekor or 0)
        if not jenis or jenis_produk not in ("Ikan", "Pakan"):
            raise ValueError("Jenis produk wajib dipilih.")
        if min(stok, harga_beli, harga_jual, stok_ekor) < 0 or not stok_ekor.is_integer():
            raise ValueError("Stok dan harga tidak boleh negatif.")
        if jenis_produk == "Pakan" and stok_ekor:
            raise ValueError("Pakan tidak menggunakan satuan ekor.")
        with self.transaksi():
            if not kode:
                prefix = "PKN" if jenis_produk == "Pakan" else "BWL"
                next_id = self.conn.execute("SELECT COALESCE(MAX(id_produk),0)+1 FROM produk_bawal").fetchone()[0]
                kode = f"{prefix}{next_id:02d}"
            try:
                self.conn.execute(
                    "INSERT INTO produk_bawal (jenis_bawal,kode,jenis_produk,stok_ekor,id_kategori,stok,harga_beli,harga_jual) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (jenis,kode,jenis_produk,int(stok_ekor),id_kategori,stok,harga_beli,harga_jual))
            except sqlite3.IntegrityError:
                raise ValueError("Kode produk sudah digunakan atau kategori tidak valid.")
            akun_stok = "1103" if jenis_produk == "Pakan" else "1104"
            self._bayar_persediaan(round(stok*harga_beli,2),sumber,
                                   f"Stok awal {jenis} {stok:g} kg",user,akun_stok)
            self._histori(user,f"Menambah produk {kode}: {jenis}")

    def restock(self, id_produk, qty, harga_beli, sumber, user, jumlah_ekor=0):
        p = self.ambil_produk(id_produk)
        qty, harga_beli, jumlah_ekor = float(qty), float(harga_beli), float(jumlah_ekor or 0)
        if qty <= 0 or harga_beli < 0 or jumlah_ekor < 0 or not jumlah_ekor.is_integer():
            raise ValueError("Jumlah restock harus lebih dari nol; harga dan jumlah ekor tidak boleh negatif.")
        jumlah_ekor = int(jumlah_ekor)
        if p["jenis_produk"] == "Pakan" and jumlah_ekor:
            raise ValueError("Jumlah ekor hanya berlaku untuk produk ikan.")
        stok_baru = round(p["stok"]+qty,3)
        hpp_baru = round((p["stok"]*p["harga_beli"]+qty*harga_beli)/stok_baru,4)
        with self.transaksi():
            self.conn.execute("UPDATE produk_bawal SET stok=?,harga_beli=?,stok_ekor=stok_ekor+? WHERE id_produk=?",
                              (stok_baru,hpp_baru,jumlah_ekor,id_produk))
            akun_stok = "1103" if p["jenis_produk"] == "Pakan" else "1104"
            self._bayar_persediaan(round(qty*harga_beli,2),sumber,
                                   f"Restock {p['jenis']} {qty:g} kg",user,akun_stok)
            self._histori(user,f"Restock {qty:g} kg {p['jenis']}")

    def kurangi_stok(self, id_produk, qty, alasan, user, jumlah_ekor=None, tanggal=None):
        p = self.ambil_produk(id_produk)
        qty = float(qty)
        if qty <= 0 or qty > p["stok"]:
            raise ValueError(f"Jumlah pengurangan harus di atas nol dan maksimal {p['stok']:g} kg.")
        if jumlah_ekor is None:
            ekor = min(p["stok_ekor"], int(round(p["stok_ekor"]*qty/p["stok"]))) if p["stok"] else 0
        else:
            ekor = float(jumlah_ekor)
        if ekor < 0 or ekor > p["stok_ekor"] or not float(ekor).is_integer():
            raise ValueError("Jumlah ikan mati tidak boleh melebihi jumlah ekor yang tercatat.")
        ekor = int(ekor)
        nilai = round(qty*p["harga_beli"],2)
        akun_stok = "1103" if p["jenis_produk"] == "Pakan" else "1104"
        akun_beban = "6101" if p["jenis_produk"] == "Pakan" else "6106"
        with self.transaksi():
            self.conn.execute("UPDATE produk_bawal SET stok=?,stok_ekor=MAX(0,stok_ekor-?) WHERE id_produk=?",
                              (round(p["stok"]-qty,3),ekor,id_produk))
            idj = None
            if nilai > 0:
                idj = self._simpan_jurnal(f"{alasan}: {p['jenis']} {qty:g} kg",
                                          [(akun_beban,nilai,0),(akun_stok,0,nilai)],
                                          user,ref="PENYESUAIAN",tanggal=tanggal)
            self._histori(user,f"{alasan}: {qty:g} kg {p['jenis']}")
        return idj

    def ubah_harga_jual(self, id_produk, harga_jual, user):
        p = self.ambil_produk(id_produk)
        if harga_jual < 0:
            raise ValueError("Harga jual tidak boleh negatif.")
        with self.transaksi():
            self.conn.execute("UPDATE produk_bawal SET harga_jual=? WHERE id_produk=?",
                              (harga_jual, id_produk))
            self._histori(user, f"Ubah harga jual {p['jenis']}: {rupiah(p['harga_jual'])} -> "
                                f"{rupiah(harga_jual)}")

    def ubah_jumlah_ekor(self, id_produk, jumlah, user):
        p = self.ambil_produk(id_produk)
        jumlah = float(jumlah)
        if p["jenis_produk"] != "Ikan" or jumlah < 0 or not jumlah.is_integer():
            raise ValueError("Jumlah ekor ikan harus berupa angka nol atau lebih.")
        jumlah = int(jumlah)
        with self.transaksi():
            self.conn.execute("UPDATE produk_bawal SET stok_ekor=? WHERE id_produk=?", (jumlah,id_produk))
            self._histori(user,f"Koreksi jumlah {p['jenis']} menjadi {jumlah} ekor")

    def hapus_produk(self, id_produk, user):
        p = self.ambil_produk(id_produk)
        if p["stok"] > 0:
            raise ValueError(
                f"Stok {p['jenis']} masih {p['stok']:g} kg. Kurangi stok sampai 0 dulu "
                "agar pembukuan tetap seimbang.")
        with self.transaksi():
            self.conn.execute("DELETE FROM produk_bawal WHERE id_produk=?", (id_produk,))
            self._histori(user, f"Menghapus produk: {p['jenis']}")

    # ---------- penjualan ----------
    def jual(self, id_produk, jumlah, pembeli, metode, user, akun_pendapatan="4101"):
        p = self.ambil_produk(id_produk)
        jumlah = float(jumlah)
        if p["jenis_produk"] != "Ikan":
            raise ValueError("Kasir penjualan hanya menerima produk ikan.")
        if jumlah <= 0:
            raise ValueError("Jumlah harus lebih dari 0.")
        if jumlah > p["stok"]:
            raise ValueError(f"Stok tidak cukup. Sisa stok {p['jenis']}: {p['stok']:g} kg.")
        if metode != "Tunai":
            raise ValueError("Penjualan pada revisi ini hanya menggunakan metode tunai.")
        pembeli = pembeli.strip() or "Umum"
        akun_info = self.conn.execute("SELECT tipe FROM akun WHERE kode=?", (akun_pendapatan,)).fetchone()
        if not akun_info or akun_info[0] != "Pendapatan":
            raise ValueError("Pilih akun bertipe Pendapatan untuk transaksi penjualan.")
        subtotal = round(jumlah * p["harga_jual"], 2)
        ongkir = self.ongkir_otomatis(jumlah)
        total = subtotal + ongkir
        hpp = round(jumlah * p["harga_beli"], 2)
        jumlah_ekor = min(p["stok_ekor"], int(round(p["stok_ekor"] * jumlah / p["stok"]))) if p["stok"] else 0
        lines = [("1101", total, 0), (akun_pendapatan, 0, subtotal)]
        if ongkir:
            lines.append(("4102", 0, ongkir))
        if hpp > 0:
            lines += [("5101", hpp, 0), ("1104", 0, hpp)]
        with self.transaksi():
            self.conn.execute("UPDATE produk_bawal SET stok=?,stok_ekor=MAX(0,stok_ekor-?) WHERE id_produk=?",
                              (round(p["stok"] - jumlah, 3), jumlah_ekor, id_produk))
            id_j = self._simpan_jurnal(
                f"Penjualan {jumlah:g} kg {p['jenis']} ke {pembeli} (Tunai)",
                lines, user, ref="PENJUALAN")
            cur = self.conn.execute(
                "INSERT INTO penjualan (waktu,nama_pembeli,id_produk,nama_produk,jumlah,harga_satuan,total_harga,metode,kasir,id_jurnal,ongkir,subtotal) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (sekarang(), pembeli, id_produk, p["jenis"], jumlah, p["harga_jual"],
                 total, "Tunai", user["nama"], id_j, ongkir, subtotal))
            id_jual = cur.lastrowid
            self._histori(user, f"Penjualan {jumlah:g} kg {p['jenis']} ke {pembeli} senilai {rupiah(total)} (Tunai)")
        return id_jual, total, subtotal, ongkir

    def riwayat_penjualan(self, limit=30):
        return self.conn.execute(
            "SELECT waktu, nama_pembeli, nama_produk, jumlah, total_harga, metode, kasir "
            "FROM penjualan ORDER BY id_penjualan DESC LIMIT ?", (limit,)).fetchall()

    def catat_pemakaian_pakan(self, id_produk, jumlah, user, tanggal=None):
        p = self.ambil_produk(id_produk)
        jumlah = float(jumlah)
        if p["jenis_produk"] != "Pakan" or jumlah <= 0 or jumlah > p["stok"]:
            raise ValueError("Pilih pakan dengan jumlah pemakaian yang tersedia.")
        nilai = round(jumlah * p["harga_beli"], 2)
        with self.transaksi():
            self.conn.execute("UPDATE produk_bawal SET stok=? WHERE id_produk=?",
                              (round(p["stok"]-jumlah,3), id_produk))
            idj = self._simpan_jurnal(f"Pemakaian pakan {p['jenis']} {jumlah:g} kg",
                                      [("6101",nilai,0),("1103",0,nilai)],
                                      user,ref="JURNAL-PENYESUAIAN",tanggal=tanggal) if nilai else None
            self.conn.execute("INSERT INTO penggunaan_pakan(waktu,id_produk,jumlah,hpp,dibuat_oleh,id_jurnal) VALUES(?,?,?,?,?,?)",
                              (tanggal or sekarang(),id_produk,jumlah,nilai,user["nama"],idj))
            self._histori(user,f"Pemakaian pakan {p['jenis']} {jumlah:g} kg")
        return nilai

    def daftar_pemakaian_pakan(self, limit=300):
        return self.conn.execute(
            "SELECT x.id,x.waktu,p.kode,p.jenis_bawal,x.jumlah,x.hpp,x.dibuat_oleh "
            "FROM penggunaan_pakan x JOIN produk_bawal p ON p.id_produk=x.id_produk "
            "ORDER BY x.id DESC LIMIT ?",(limit,)).fetchall()

    def catat_penyusutan(self, jumlah, user, tanggal=None):
        jumlah=float(jumlah)
        if jumlah <= 0:
            raise ValueError("Nilai penyusutan harus lebih dari nol.")
        return self.jurnal_penyesuaian("Penyusutan peralatan",
                                       [("6105",jumlah,0),("1302",0,jumlah)],user,tanggal)

    def beli_indukan(self, jumlah, keterangan, user, tanggal=None):
        jumlah=float(jumlah)
        keterangan=keterangan.strip() or "Beli Indukan Bawal"
        if jumlah <= 0 or self._saldo_kas()+0.005 < jumlah:
            raise ValueError("Jumlah harus positif dan saldo kas harus mencukupi.")
        with self.transaksi():
            idj=self._simpan_jurnal(keterangan,[("1201",jumlah,0),("1101",0,jumlah)],
                                    user,ref="PEMBELIAN-INDUKAN",tanggal=tanggal)
            cur=self.conn.execute("INSERT INTO pembelian_indukan(waktu,jumlah,keterangan,dibuat_oleh,id_jurnal) VALUES(?,?,?,?,?)",
                                  (tanggal or sekarang(),jumlah,keterangan,user["nama"],idj))
            ident=cur.lastrowid
            self._histori(user,f"Pembelian indukan bawal {rupiah(jumlah)}")
        return f"PI-{ident:03d}"

    def daftar_indukan(self,limit=300):
        return self.conn.execute("SELECT id,waktu,jumlah,keterangan,dibuat_oleh FROM pembelian_indukan ORDER BY id DESC LIMIT ?",
                                 (limit,)).fetchall()

    def catat_stock_opname(self,id_produk,jumlah_mati,jumlah_mati_ekor,keterangan,user,tanggal=None):
        p=self.ambil_produk(id_produk)
        jumlah_mati=float(jumlah_mati)
        jumlah_mati_ekor=float(jumlah_mati_ekor or 0)
        if p["jenis_produk"]!="Ikan" or jumlah_mati<=0 or jumlah_mati>p["stok"]:
            raise ValueError("Pilih ikan dan jumlah mati dalam batas stok.")
        if jumlah_mati_ekor<0 or jumlah_mati_ekor>p["stok_ekor"] or not jumlah_mati_ekor.is_integer():
            raise ValueError("Jumlah ekor mati melebihi jumlah ikan tercatat.")
        jumlah_mati_ekor=int(jumlah_mati_ekor)
        nilai=round(jumlah_mati*p["harga_beli"],2)
        with self.transaksi():
            self.conn.execute("UPDATE produk_bawal SET stok=?,stok_ekor=stok_ekor-? WHERE id_produk=?",
                              (round(p["stok"]-jumlah_mati,3),jumlah_mati_ekor,id_produk))
            idj=self._simpan_jurnal(f"Stock opname: {keterangan or 'ikan mati'} - {p['jenis']}",
                                    [("6106",nilai,0),("1104",0,nilai)],user,
                                    ref="JURNAL-PENYESUAIAN",tanggal=tanggal) if nilai else None
            cur=self.conn.execute("INSERT INTO stock_opname(waktu,id_produk,jumlah_mati,keterangan,dibuat_oleh,id_jurnal,jumlah_mati_ekor) VALUES(?,?,?,?,?,?,?)",
                                  (tanggal or sekarang(),id_produk,jumlah_mati,keterangan.strip(),user["nama"],idj,jumlah_mati_ekor))
            ident=cur.lastrowid
            self._histori(user,f"Stock opname {p['jenis']}: mati {jumlah_mati:g} kg / {jumlah_mati_ekor} ekor")
        return ident

    def daftar_stock_opname(self,limit=300):
        return self.conn.execute("SELECT o.id,o.waktu,p.kode,p.jenis_bawal,o.jumlah_mati,o.jumlah_mati_ekor,o.keterangan FROM stock_opname o JOIN produk_bawal p ON p.id_produk=o.id_produk ORDER BY o.id DESC LIMIT ?",
                                 (limit,)).fetchall()

    def hapus_stock_opname(self,ident,user):
        row=self.conn.execute("SELECT id_produk,jumlah_mati,jumlah_mati_ekor,id_jurnal,keterangan FROM stock_opname WHERE id=?",(ident,)).fetchone()
        if not row:
            raise ValueError("Data stock opname tidak ditemukan.")
        pid,kg,ekor,idj,ket=row
        with self.transaksi():
            p=self.ambil_produk(pid)
            self.conn.execute("UPDATE produk_bawal SET stok=stok+?,stok_ekor=stok_ekor+? WHERE id_produk=?",(kg,ekor,pid))
            lines=self.conn.execute("SELECT kode_akun,debit,kredit FROM jurnal_detail WHERE id_jurnal=?",(idj,)).fetchall()
            if lines:
                self._simpan_jurnal(f"Pembatalan stock opname #{ident}: {ket}",[(k,kr,d) for k,d,kr in lines],user,ref="VOID-STOCK-OPNAME")
            self.conn.execute("DELETE FROM stock_opname WHERE id=?",(ident,))
            self._histori(user,f"Menghapus stock opname #{ident}; jurnal dibalikkan")

    def daftar_penjualan_rinci(self, limit=100):
        mulai=self.conn.execute("SELECT nilai FROM pengaturan_sistem WHERE nama='tanggal_mulai_histori_tunai'").fetchone()[0]
        return self.conn.execute(
            "SELECT id_penjualan,waktu,nama_pembeli,nama_produk,jumlah,subtotal,ongkir,total_harga,metode,kasir "
            "FROM penjualan WHERE metode='Tunai' AND waktu>=? ORDER BY id_penjualan DESC LIMIT ?",(mulai,limit)).fetchall()

    def daftar_pembelian_rinci(self, limit=100):
        mulai=self.conn.execute("SELECT nilai FROM pengaturan_sistem WHERE nama='tanggal_mulai_histori_tunai'").fetchone()[0]
        return self.conn.execute(
            "SELECT id,waktu,supplier,produk,jumlah,harga_satuan,total,metode,dibuat_oleh "
            "FROM pembelian WHERE metode='Tunai' AND waktu>=? ORDER BY id DESC LIMIT ?",(mulai,limit)).fetchall()

    # ---------- ringkasan & rekomendasi ----------
    def ringkasan(self):
        s={a["kode"]:a["saldo"] for a in self._saldo_semua()}
        lr=self.laba_rugi()
        cnt,kg=self.conn.execute("SELECT COUNT(*),COALESCE(SUM(jumlah),0) FROM penjualan").fetchone()
        awal=datetime.date.today().replace(day=1).strftime("%Y-%m-%d")
        beli=self.conn.execute("SELECT COALESCE(SUM(total),0) FROM pembelian WHERE waktu>=?",(awal,)).fetchone()[0]
        jual=self.conn.execute("SELECT COALESCE(SUM(total_harga),0) FROM penjualan WHERE waktu>=?",(awal,)).fetchone()[0]
        stok_kg=self.conn.execute("SELECT COALESCE(SUM(stok),0) FROM produk_bawal WHERE jenis_produk='Ikan'").fetchone()[0]
        stok_pakan=self.conn.execute("SELECT COALESCE(SUM(stok),0) FROM produk_bawal WHERE jenis_produk='Pakan'").fetchone()[0]
        return {"kas":s.get("1101",0),"piutang":s.get("1102",0),"persediaan":s.get("1104",0),
                "persediaan_pakan":s.get("1103",0),"utang":s.get("2101",0),
                "pendapatan":lr["pendapatan"],"laba":lr["laba_bersih"],"transaksi":cnt,
                "kg":kg,"stok_kg":stok_kg,"stok_pakan":stok_pakan,
                "pembelian_periode":beli,"penjualan_periode":jual}

    def ringkasan_karyawan(self,nama):
        hari_ini=datetime.date.today().strftime("%Y-%m-%d")+"%"
        cnt,total,kg=self.conn.execute(
            "SELECT COUNT(*),COALESCE(SUM(total_harga),0),COALESCE(SUM(jumlah),0) "
            "FROM penjualan WHERE kasir=? AND waktu LIKE ?",(nama,hari_ini)).fetchone()
        produk=self.daftar_produk_lengkap()
        menipis=sum(1 for p in produk if (p[2]=="Pakan" and p[8]<=self.BATAS_STOK_PAKAN)
                    or (p[2]=="Ikan" and p[9]<=self.BATAS_STOK_IKAN))
        return {"transaksi":cnt,"total":total,"kg":kg,"produk":len(produk),"menipis":menipis}

    def rekomendasi(self, owner=True):
        hasil=[]
        batas=(datetime.datetime.now()-datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        terjual=dict(self.conn.execute(
            "SELECT id_produk,SUM(jumlah) FROM penjualan WHERE waktu>=? GROUP BY id_produk",(batas,)).fetchall())
        produk=self.daftar_produk_lengkap()
        for p in produk:
            pid,kode,kind,nama,_idkat,_kodekat,kategori,_ket,kg,ekor,hpp,jual=p
            if kind=="Pakan" and kg<=self.BATAS_STOK_PAKAN:
                hasil.append(("warn",f"Stok pakan {nama} tersisa {kg:g} kg; batas minimum 50 kg."))
            elif kind=="Ikan" and ekor<=self.BATAS_STOK_IKAN:
                hasil.append(("warn",f"Stok {nama} tersisa {ekor} ekor; batas minimum 50 ekor."))
        if owner:
            ringkas=self.ringkasan()
            if ringkas["kas"]<1_000_000:
                hasil.append(("warn",f"Saldo kas menipis ({rupiah(ringkas['kas'])})."))
            if ringkas["piutang"]>0:
                hasil.append(("warn",f"Masih ada piutang usaha {rupiah(ringkas['piutang'])}."))
            if ringkas["utang"]>0:
                hasil.append(("warn",f"Masih ada utang usaha {rupiah(ringkas['utang'])}."))
            if terjual:
                top=max(terjual,key=terjual.get)
                nama=next((p[3] for p in produk if p[0]==top),None)
                if nama:
                    hasil.append(("good",f"Ikan terlaris 30 hari terakhir: {nama} ({terjual[top]:g} kg)."))
        if not hasil:
            hasil.append(("good","Stok dan kondisi operasional dalam batas aman."))
        urutan={"warn":0,"info":1,"good":2}
        return sorted(hasil,key=lambda x:urutan[x[0]])

