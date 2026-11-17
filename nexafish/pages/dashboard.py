"""Halaman Dashboard NEXAFISH: banner ringkasan, kartu KPI, grafik arus kas, dan rekomendasi sistem.

Redesain tampilan saja. Pengambilan data (ringkasan, rekomendasi, query arus kas) sama seperti sebelumnya.
"""

import datetime
import tkinter as tk

import gfx
from base import Halaman
from theme import C, f, fisik, lembut, mix, px
from utils import rupiah, angka
from widgets import Chip, IkonKotak, Kartu, Segmen, Tombol, _ukur, kartu_stat


def format_ringkas(nilai):
    """Format angka rupiah ringkas untuk sumbu dan label grafik (misal: 5 jt, 500 rb)."""
    if abs(nilai) >= 1_000_000_000:
        return f"Rp {nilai / 1_000_000_000:.1f} M"
    elif abs(nilai) >= 1_000_000:
        return f"Rp {nilai / 1_000_000:.1f} jt"
    elif abs(nilai) >= 1_000:
        return f"Rp {nilai / 1_000:.0f} rb"
    else:
        return f"Rp {int(nilai)}"


class GrafikKeuanganCanvas(Kartu):
    """Grafik batang Kas Masuk vs Kas Keluar (Canvas). Data dibaca read-only dari SQLite."""

    def __init__(self, parent, db):
        super().__init__(parent, radius=14)
        self.db = db
        self.periode_bulan = 6
        self._data = []
        self._imgs = []
        self._tip_img = None
        self._pad_kiri, self._pad_atas, self._lebar_slot = px(78), px(30), 1

        header = tk.Frame(self, bg="white")
        header.pack(fill="x", padx=24, pady=(20, 0))
        tk.Label(header, text="Tren Arus Keuangan", font=f(13, True), bg="white", fg=C["text"]).pack(side="left")
        Chip(header, "Bulanan", fg=C["muted"], bg="#F1F4F9", ukuran=8, tinggi=22, padx=10).pack(side="left", padx=(10, 0))
        self.seg = Segmen(header, [(6, "6 Bulan"), (12, "12 Bulan")], 6, self.set_periode)
        self.seg.pack(side="right")

        sub = tk.Frame(self, bg="white")
        sub.pack(fill="x", padx=24, pady=(6, 0))
        tk.Label(sub, text="Kas masuk vs kas keluar per periode", font=f(9), bg="white",
                 fg=C["muted"]).pack(side="left")
        legenda = tk.Frame(sub, bg="white")
        legenda.pack(side="right")
        for warna, teks in ((C["income"], "Kas Masuk"), (C["expense"], "Kas Keluar")):
            kotak = tk.Canvas(legenda, width=12, height=12, bg="white", highlightthickness=0)
            kotak.pack(side="left", padx=(10, 6))
            kotak.create_rectangle(1, 1, 11, 11, fill=warna, outline=warna)
            tk.Label(legenda, text=teks, font=f(9, True), fg=C["text"], bg="white").pack(side="left")

        self.canvas = tk.Canvas(self, bg="white", height=270, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True, padx=14, pady=(4, 8))
        self.canvas.bind("<Configure>", lambda e: self.gambar())
        self.canvas.bind("<Motion>", self._tooltip)
        self.canvas.bind("<Leave>", lambda e: self.canvas.delete("tip"))

        # Ringkasan bawah grafik
        self.foot = tk.Frame(self, bg="#F5F8FC")
        self.foot.pack(fill="x", padx=20, pady=(0, 20))
        isi = tk.Frame(self.foot, bg="#F5F8FC")
        isi.pack(fill="x", padx=16, pady=10)
        tk.Label(isi, text="Surplus arus kas rata-rata:", font=f(9), bg="#F5F8FC", fg=C["muted"]).pack(side="left")
        self.lbl_surplus = tk.Label(isi, text="", font=f(9, True), bg="#F5F8FC", fg=C["text"])
        self.lbl_surplus.pack(side="left", padx=(6, 0))
        self.lbl_rasio = tk.Label(isi, text="", font=f(9, True), bg="#F5F8FC", fg=C["text"])
        self.lbl_rasio.pack(side="right")
        tk.Label(isi, text="Rasio kas masuk / keluar:", font=f(9), bg="#F5F8FC", fg=C["muted"]).pack(side="right", padx=(0, 6))
        self.angkat_sudut()

    def set_periode(self, jml_bulan):
        self.periode_bulan = jml_bulan
        if self.seg.nilai != jml_bulan:
            self.seg.pilih(jml_bulan)
        self.gambar()

    def ambil_data(self):
        """Query SELECT read-only untuk mengambil arus kas per bulan."""
        sekarang = datetime.date.today()
        bulan_list = []
        y, m = sekarang.year, sekarang.month
        for _ in range(self.periode_bulan):
            bulan_list.append(f"{y:04d}-{m:02d}")
            m -= 1
            if m == 0:
                m = 12
                y -= 1
        bulan_list.reverse()

        seq = ",".join(f"'{b}'" for b in bulan_list)
        query = f"""
            SELECT substr(j.tanggal, 1, 7) as bln,
                   SUM(CASE WHEN d.kode_akun IN ('1101','1105') THEN d.debit ELSE 0 END) as masuk,
                   SUM(CASE WHEN d.kode_akun IN ('1101','1105') THEN d.kredit ELSE 0 END) as keluar
            FROM jurnal j
            JOIN jurnal_detail d ON j.id_jurnal = d.id_jurnal
            WHERE substr(j.tanggal, 1, 7) IN ({seq}) AND d.kode_akun IN ('1101','1105')
            GROUP BY bln
        """

        data_map = {}
        try:
            rows = self.db.conn.execute(query).fetchall()
            for bln, masuk, keluar in rows:
                data_map[bln] = (float(masuk or 0), float(keluar or 0))
        except Exception:
            pass

        nama_bln = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
        hasil = []
        for b in bulan_list:
            thn, bln_num = b.split("-")
            label = f"{nama_bln[int(bln_num)]} '{thn[2:]}"
            masuk, keluar = data_map.get(b, (0.0, 0.0))
            hasil.append({"label": label, "masuk": masuk, "keluar": keluar})
        return hasil

    def _ringkasan_bawah(self, data):
        n = max(len(data), 1)
        total_masuk = sum(d["masuk"] for d in data)
        total_keluar = sum(d["keluar"] for d in data)
        surplus = (total_masuk - total_keluar) / n
        self.lbl_surplus.config(text=f"{rupiah(surplus)} / bln",
                                fg=C["green_text"] if surplus >= 0 else C["red_text"])
        if total_keluar > 0:
            self.lbl_rasio.config(text=f"{total_masuk / total_keluar:.2f}x")
        else:
            self.lbl_rasio.config(text="-")

    def gambar(self):
        c = self.canvas
        w, h = c.winfo_width(), c.winfo_height()
        if w < 50 or h < 50:
            return

        c.delete("all")
        self._imgs = []
        data = self.ambil_data()
        self._data = data
        if not data:
            return
        self._ringkasan_bawah(data)

        pad_kiri, pad_kanan, pad_atas, pad_bawah = px(78), px(24), px(30), px(40)
        self._pad_kiri, self._pad_atas = pad_kiri, pad_atas
        lebar_grafik = w - pad_kiri - pad_kanan
        tinggi_grafik = h - pad_atas - pad_bawah

        maks_nilai = max(max(d["masuk"], d["keluar"]) for d in data)
        if maks_nilai <= 0:
            maks_nilai = 1_000_000
        skala_atas = maks_nilai * 1.15

        # Garis kisi dan label sumbu Y
        jumlah_grid = 4
        y_dasar = pad_atas + tinggi_grafik
        for i in range(jumlah_grid + 1):
            y_val = skala_atas * (i / jumlah_grid)
            y_pos = y_dasar - (tinggi_grafik * (i / jumlah_grid))
            if i == 0:
                c.create_line(pad_kiri, y_pos, w - pad_kanan, y_pos, fill=C["border"], width=1)
            else:
                c.create_line(pad_kiri, y_pos, w - pad_kanan, y_pos, fill="#E9EEF5", width=1, dash=(px(3), px(5)))
            c.create_text(pad_kiri - px(12), y_pos, text=format_ringkas(y_val), font=f(8), fill=C["muted"], anchor="e")

        # Batang
        n = len(data)
        lebar_slot = lebar_grafik / n
        self._lebar_slot = lebar_slot
        lebar_bar = max(px(10), min(px(30), int(lebar_slot * 0.26)))
        warna_batang = (
            ("masuk", "#38D9A0", "#0E9F6E", C["income"], -1),
            ("keluar", "#FF7A8A", "#E8374F", C["expense"], 1),
        )

        for i, item in enumerate(data):
            cx = pad_kiri + (i * lebar_slot) + (lebar_slot / 2)
            terakhir = i == n - 1

            # Label bulan (bulan berjalan diberi penanda)
            if terakhir:
                lb = _ukur(item["label"], f(8, True)) + px(20)
                if gfx.PIL_OK:
                    pil = gfx.kotak_bulat(lb, px(24), px(12), "#E8EEF8")
                    self._imgs.append(pil)
                    c.create_image(cx, y_dasar + px(20), image=pil)
                c.create_text(cx, y_dasar + px(20), text=item["label"], font=f(8, True), fill=C["primary"])
            else:
                c.create_text(cx, y_dasar + px(20), text=item["label"], font=f(8), fill=C["muted"])

            for kunci, atas, bawah, warna_teks, arah in warna_batang:
                nilai = item[kunci]
                tinggi_bar = (nilai / skala_atas) * tinggi_grafik if skala_atas > 0 else 0
                x1 = cx - lebar_bar - px(3) if arah < 0 else cx + px(3)
                x2 = x1 + lebar_bar
                if tinggi_bar >= px(2):
                    if gfx.PIL_OK:
                        im = gfx.batang_gradasi(lebar_bar, int(tinggi_bar), atas, bawah, r=min(px(7), lebar_bar // 2))
                        self._imgs.append(im)
                        c.create_image(x1, y_dasar - int(tinggi_bar), anchor="nw", image=im)
                    else:
                        c.create_rectangle(x1, y_dasar - tinggi_bar, x2, y_dasar, fill=warna_teks, outline=warna_teks)
                    lbl_val = format_ringkas(nilai).replace("Rp ", "")
                    c.create_text((x1 + x2) / 2, y_dasar - tinggi_bar - px(9), text=lbl_val,
                                  font=f(7, True), fill=warna_teks, anchor="center")
                else:
                    c.create_line(x1, y_dasar - 1, x2, y_dasar - 1, fill=warna_teks, width=px(2))

    def _tooltip(self, e):
        c = self.canvas
        c.delete("tip")
        if not self._data:
            return
        h = c.winfo_height()
        i = int((e.x - self._pad_kiri) // self._lebar_slot)
        if i < 0 or i >= len(self._data) or e.y < self._pad_atas - px(10) or e.y > h - px(30):
            return
        d = self._data[i]
        baris = [d["label"], f"Masuk   {rupiah(d['masuk'])}", f"Keluar   {rupiah(d['keluar'])}"]
        lebar = max(_ukur(t, f(8, True)) for t in baris) + px(28)
        tinggi = px(74)
        x = min(max(e.x + px(14), px(4)), c.winfo_width() - lebar - px(6))
        y = max(e.y - tinggi - px(8), px(4))
        if gfx.PIL_OK:
            self._tip_img = gfx.kotak_bulat(lebar, tinggi, px(10), "#14253D")
            c.create_image(x, y, anchor="nw", image=self._tip_img, tags="tip")
        else:
            c.create_rectangle(x, y, x + lebar, y + tinggi, fill="#14253D", outline="#14253D", tags="tip")
        warna = ("#FFFFFF", "#7CE3BE", "#FF9AA6")
        for k, teks in enumerate(baris):
            c.create_text(x + px(14), y + px(16) + k * px(20), text=teks, anchor="w", font=f(8, True),
                          fill=warna[k], tags="tip")



class DashboardPage(Halaman):
    """Dashboard perdagangan dengan metrik, tren penjualan, dan aktivitas terbaru."""

    def __init__(self, parent, main):
        super().__init__(parent, main)
        self._owner = self.is_owner
        self._cols = 3 if self._owner else 2
        self._sempit = None
        self._kartu = []
        self._buat_data()
        self._bangun()
        self.bind("<Configure>", self._ubah_lebar)

    def _buat_data(self):
        db = self.db
        sekarang = datetime.date.today()
        if self._owner:
            self.ringkas = db.ringkasan()
            self.judul_kartu = [
                ("Saldo Kas", rupiah(self.ringkas["kas"]), C["income"], "Saldo akun kas"),
                ("Penjualan Bulan Ini", rupiah(self.ringkas["penjualan_periode"]), C["primary"], "Bulan berjalan"),
                ("Pembelian Bulan Ini", rupiah(self.ringkas["pembelian_periode"]), C["warning"], "Bulan berjalan"),
                ("Laba Bersih", rupiah(self.ringkas["laba"]), C["income"] if self.ringkas["laba"] >= 0 else C["danger"], "Akumulasi pembukuan"),
                ("Stok Ikan", f'{self.ringkas["stok_kg"]:g} kg', "#2F80ED", "Jumlah ikan tersedia"),
                ("Piutang Usaha", rupiah(self.ringkas["piutang"]), C["purple"], "Belum tertagih"),
                ("Utang Usaha", rupiah(self.ringkas["utang"]), C["danger"], "Belum dibayar"),
                ("Nilai Persediaan", rupiah(self.ringkas["persediaan"]), C["indigo"], "Nilai stok ikan"),
            ]
        else:
            self.ringkas = db.ringkasan_karyawan(self.user["nama"])
            self.judul_kartu = [
                ("Transaksi Hari Ini", angka(self.ringkas["transaksi"]), C["primary"], "Transaksi saya"),
                ("Penjualan Hari Ini", rupiah(self.ringkas["total"]), C["income"], "Total penjualan saya"),
                ("Volume Terjual", f'{self.ringkas["kg"]:g} kg', "#2F80ED", "Hari ini"),
                ("Stok Menipis", f'{self.ringkas["menipis"]} dari {self.ringkas["produk"]}', C["danger"] if self.ringkas["menipis"] else C["warning"], "Perlu diperiksa"),
            ]
        self._tanggal = sekarang

    def _bangun(self):
        self.konten = tk.Frame(self, bg=C["bg"])
        self.konten.pack(fill="both", expand=True)

        kepala = tk.Frame(self.konten, bg=C["bg"])
        kepala.pack(fill="x", pady=(0, 18))
        kiri = tk.Frame(kepala, bg=C["bg"])
        kiri.pack(side="left", fill="x", expand=True)
        tk.Label(kiri, text="Dashboard Perdagangan" if self._owner else "Ringkasan Aktivitas Saya",
                 font=f(21, True), bg=C["bg"], fg=C["text"]).pack(anchor="w")
        keterangan = ("Pantau penjualan, arus kas, persediaan, dan kewajiban usaha."
                      if self._owner else "Pantau transaksi, penjualan, dan stok yang Anda kelola.")
        tk.Label(kiri, text=keterangan, font=f(10), bg=C["bg"], fg=C["muted"]).pack(anchor="w", pady=(5, 0))

        aksi = tk.Frame(kepala, bg=C["bg"])
        aksi.pack(side="right", anchor="e")
        Chip(aksi, self._tanggal.strftime("%d %b %Y"), fg=C["muted"], bg="white",
             garis=C["border"], ukuran=9, tinggi=34, padx=12).pack(side="left", padx=(0, 8))
        Tombol(aksi, "Jual", lambda: self.main.buka("Kasir"), tinggi=36,
               ukuran=9, ikon="+").pack(side="left")
        if self._owner:
            Tombol(aksi, "Beli", lambda: self._buka_operasional(1),
                   gaya="outline", tinggi=36, ukuran=9).pack(side="left", padx=(8, 0))
            Tombol(aksi, "Biaya", lambda: self._buka_operasional(2),
                   gaya="outline", tinggi=36, ukuran=9).pack(side="left", padx=(8, 0))

        self.grid_kpi = tk.Frame(self.konten, bg=C["bg"])
        self.grid_kpi.pack(fill="x", pady=(0, 4))
        self._bangun_kpi()

        self.baris_bawah = tk.Frame(self.konten, bg=C["bg"])
        self.baris_bawah.pack(fill="x", pady=(0, 16))
        self.kolom_grafik = tk.Frame(self.baris_bawah, bg=C["bg"])
        self.kolom_samping = tk.Frame(self.baris_bawah, bg=C["bg"])
        self._bangun_grafik()
        if self._owner:
            self.grafik_kas = GrafikKeuanganCanvas(self.kolom_grafik, self.db)
            self.grafik_kas.pack(fill="x", pady=(14, 0))
        self._bangun_samping()

        self._bangun_transaksi()

    def _buka_operasional(self, indeks_tab):
        if indeks_tab == 1:
            self.main.buka("Kasir")
            halaman=self.main.halaman
            if hasattr(halaman,"nb") and len(halaman.nb._tab)>1:
                halaman.nb.select(halaman.nb._tab[1][0])
        else:
            self.main.buka("Kas & Kas Kecil")
            halaman=self.main.halaman
            if hasattr(halaman,"nb") and len(halaman.nb._tab)>1:
                halaman.nb.select(halaman.nb._tab[1][0])

    def _bangun_kpi(self):
        self._kartu.clear()
        for i, (judul, nilai, warna, sub) in enumerate(self.judul_kartu):
            kartu = kartu_stat(self.grid_kpi, judul, nilai, warna, sub=sub)
            self._kartu.append(kartu)
        self._atur_kpi(self.winfo_width() or 1100)

    def _atur_kpi(self, lebar):
        batas = px(900) if self._owner else px(720)
        kolom = 1 if lebar < px(560) else (2 if lebar < batas else (3 if self._owner else 4))
        if kolom == self._cols and all(w.winfo_manager() == "grid" for w in self._kartu):
            return
        self._cols = kolom
        for i, kartu in enumerate(self._kartu):
            kartu.grid_forget()
            kartu.grid(row=i // kolom, column=i % kolom, sticky="nsew",
                       padx=(0 if i % kolom == 0 else 7, 0 if i % kolom == kolom - 1 else 7),
                       pady=(0, 14))
        for kol in range(6):
            self.grid_kpi.columnconfigure(kol, weight=1 if kol < kolom else 0)

    def _bangun_grafik(self):
        box = Kartu(self.kolom_grafik, radius=14)
        box.pack(fill="both", expand=True)
        kepala = tk.Frame(box, bg="white")
        kepala.pack(fill="x", padx=20, pady=(18, 2))
        tk.Label(kepala, text="Volume Penjualan Harian", font=f(12, True),
                 bg="white", fg=C["text"]).pack(anchor="w")
        tk.Label(kepala, text="Jumlah ikan terjual dalam 7 hari terakhir",
                 font=f(9), bg="white", fg=C["muted"]).pack(anchor="w", pady=(3, 0))
        self.canvas_jual = tk.Canvas(box, height=230, bg="white", highlightthickness=0, bd=0)
        self.canvas_jual.pack(fill="both", expand=True, padx=12, pady=(3, 14))
        self.canvas_jual.bind("<Configure>", lambda e: self._gambar_jual())
        self._gambar_jual()

    def _data_jual_harian(self):
        mulai = self._tanggal - datetime.timedelta(days=6)
        tanggal = [mulai + datetime.timedelta(days=i) for i in range(7)]
        akhir = (self._tanggal + datetime.timedelta(days=1)).isoformat()
        sql = ("SELECT substr(waktu,1,10), COALESCE(SUM(jumlah),0), "
               "COALESCE(SUM(total_harga),0) FROM penjualan WHERE waktu >= ? AND waktu < ?")
        params = [mulai.isoformat(), akhir]
        if not self._owner:
            sql += " AND kasir=?"
            params.append(self.user["nama"])
        sql += " GROUP BY substr(waktu,1,10)"
        try:
            rows = self.db.conn.execute(sql, params).fetchall()
            return {hari: (float(kg or 0), float(total or 0)) for hari, kg, total in rows}, tanggal
        except Exception:
            return {}, tanggal

    def _gambar_jual(self):
        if not hasattr(self, "canvas_jual"):
            return
        c = self.canvas_jual
        w, h = c.winfo_width(), c.winfo_height()
        if w < 120 or h < 100:
            return
        c.delete("all")
        data, tanggal = self._data_jual_harian()
        nilai = [data.get(d.isoformat(), (0, 0))[0] for d in tanggal]
        maks = max(max(nilai, default=0), 1)
        kiri, kanan, atas, bawah = px(44), px(18), px(18), px(35)
        gh = h - atas - bawah
        gw = w - kiri - kanan
        nama_hari = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
        for i in range(4):
            y = atas + gh * i / 3
            label = maks * (1 - i / 3)
            c.create_line(kiri, y, w - kanan, y, fill="#E9EEF5", dash=(3, 4))
            c.create_text(kiri - 7, y, text=f"{label:.0f}", font=f(8), fill=C["muted"], anchor="e")
        slot = gw / 7
        bw = min(px(34), slot * 0.48)
        for i, d in enumerate(tanggal):
            kg = nilai[i]
            x = kiri + slot * (i + 0.5)
            bh = max(2, gh * kg / maks) if kg else 2
            c.create_rectangle(x - bw / 2, atas + gh - bh, x + bw / 2, atas + gh,
                               fill=C["primary"] if i < 6 else C["income"], outline="")
            c.create_text(x, h - px(16), text=nama_hari[d.weekday()], font=f(8, d == self._tanggal),
                          fill=C["primary"] if d == self._tanggal else C["muted"])
            if kg:
                c.create_text(x, atas + gh - bh - 9, text=f"{kg:g}", font=f(8, True), fill=C["text"])

    def _bangun_samping(self):
        if self._owner:
            self._bangun_posisi()
            self._bangun_perhatian()
        else:
            box = Kartu(self.kolom_samping, radius=14)
            box.pack(fill="both", expand=True)
            tk.Label(box, text="Status Stok", font=f(12, True), bg="white",
                     fg=C["text"]).pack(anchor="w", padx=18, pady=(18, 8))
            produk = self.db.daftar_produk_lengkap()
            menipis = [p for p in produk if (p[2] == "Pakan" and p[8] <= self.db.BATAS_STOK_PAKAN)
                       or (p[2] == "Ikan" and p[9] <= self.db.BATAS_STOK_IKAN)]
            for p in menipis:
                stok = f"Sisa {p[8]:g} kg" if p[2] == "Pakan" else f"Sisa {p[9]} ekor"
                self._baris_ringkas(box, p[3], stok, C["danger"])
            if not menipis:
                tk.Label(box, text="Stok produk dalam batas aman.", font=f(9),
                         bg="white", fg=C["muted"]).pack(anchor="w", padx=18, pady=(4, 18))

    def _bangun_posisi(self):
        box = Kartu(self.kolom_samping, radius=14)
        box.pack(fill="x", pady=(0, 14))
        tk.Label(box, text="Posisi Keuangan", font=f(12, True), bg="white",
                 fg=C["text"]).pack(anchor="w", padx=18, pady=(17, 9))
        for nama, nilai, warna in (
            ("Kas & bank", self.ringkas["kas"], C["income"]),
            ("Piutang usaha", self.ringkas["piutang"], C["purple"]),
            ("Utang dagang", self.ringkas["utang"], C["danger"]),
            ("Persediaan", self.ringkas["persediaan"], C["primary"]),
        ):
            self._baris_ringkas(box, nama, rupiah(nilai), warna)
        aset_lancar = max(0, self.ringkas["kas"] + self.ringkas["piutang"] + self.ringkas["persediaan"])
        rasio = (self.ringkas["utang"] / aset_lancar) if aset_lancar else 0
        tk.Label(box, text="Utang dibanding aset lancar", font=f(9), bg="white",
                 fg=C["muted"]).pack(anchor="w", padx=18, pady=(10, 4))
        tk.Label(box, text=f"{rasio:.0%}" if aset_lancar else "Belum ada data aset",
                 font=f(16, True), bg="white", fg=C["danger"] if rasio >= 0.5 else C["text"]).pack(
                     anchor="w", padx=18, pady=(0, 15))

    def _bangun_perhatian(self):
        daftar=self.db.rekomendasi(True)
        peringatan=[teks for level,teks in daftar if level=="warn"][:4]
        informasi=[teks for level,teks in daftar if level in ("info","good")]
        box=Kartu(self.kolom_samping,radius=14); box.pack(fill="x")
        tk.Label(box,text="Morning Brief · Perlu Perhatian",font=f(12,True),bg="white",fg=C["text"]).pack(anchor="w",padx=18,pady=(17,8))
        if not peringatan:
            peringatan=["Tidak ada peringatan stok atau keuangan."]
        for teks in peringatan:
            tk.Label(box,text="• "+teks,font=f(9),bg="white",fg=C["text"],justify="left",
                     anchor="w",wraplength=300).pack(fill="x",padx=18,pady=5)
        tk.Frame(box,bg="white",height=8).pack()
        info=Kartu(self.kolom_samping,radius=14); info.pack(fill="x",pady=(14,0))
        tk.Label(info,text="Informasi Usaha",font=f(12,True),bg="white",fg=C["text"]).pack(anchor="w",padx=18,pady=(16,7))
        if not informasi:
            informasi=["Belum ada informasi penjualan tambahan."]
        for teks in informasi[:3]:
            tk.Label(info,text="• "+teks,font=f(9),bg="white",fg=C["text"],justify="left",
                     anchor="w",wraplength=300).pack(fill="x",padx=18,pady=5)
        tk.Frame(info,bg="white",height=8).pack()

    def _baris_ringkas(self, parent, nama, nilai, warna):
        baris = tk.Frame(parent, bg="white")
        baris.pack(fill="x", padx=18, pady=5)
        tk.Frame(baris, bg=warna, width=4, height=24).pack(side="left", fill="y", padx=(0, 9))
        tk.Label(baris, text=nama, font=f(9), bg="white", fg=C["muted"]).pack(side="left")
        tk.Label(baris, text=nilai, font=f(9, True), bg="white", fg=C["text"]).pack(side="right")

    def _bangun_transaksi(self):
        box = Kartu(self.konten, radius=14)
        box.pack(fill="x", pady=(0, 20))
        kepala = tk.Frame(box, bg="white")
        kepala.pack(fill="x", padx=20, pady=(17, 10))
        tk.Label(kepala, text="Transaksi Terbaru", font=f(12, True),
                 bg="white", fg=C["text"]).pack(side="left")
        tk.Label(kepala, text="5 transaksi terakhir", font=f(9),
                 bg="white", fg=C["muted"]).pack(side="right")
        tabel = tk.Frame(box, bg="white")
        tabel.pack(fill="x", padx=18, pady=(0, 14))
        for i, judul in enumerate(("WAKTU", "PELANGGAN", "PRODUK", "VOLUME", "TOTAL")):
            tk.Label(tabel, text=judul, font=f(8, True), bg="#F4F7FB",
                     fg=C["muted"], anchor="w").grid(row=0, column=i, sticky="ew", padx=4, pady=5)
            tabel.columnconfigure(i, weight=(2 if i == 0 else 3 if i in (1, 2) else 1))
        sql = ("SELECT waktu,nama_pembeli,nama_produk,jumlah,total_harga,kasir "
               "FROM penjualan")
        params = []
        if not self._owner:
            sql += " WHERE kasir=?"
            params.append(self.user["nama"])
        sql += " ORDER BY id_penjualan DESC LIMIT 5"
        rows = self.db.conn.execute(sql, params).fetchall()
        if not rows:
            tk.Label(tabel, text="Belum ada transaksi penjualan.", font=f(9),
                     bg="white", fg=C["muted"]).grid(row=1, column=0, columnspan=5,
                                                     sticky="w", padx=5, pady=12)
            return
        for r, row in enumerate(rows, 1):
            waktu, pelanggan, produk, kg, total, _kasir = row
            waktu_pendek = str(waktu)[5:16]
            isi = (waktu_pendek, pelanggan or "Pelanggan umum", produk or "-",
                   f"{kg:g} kg", rupiah(total))
            for col, teks in enumerate(isi):
                tk.Label(tabel, text=teks, font=f(9, col == 4), bg="white",
                         fg=C["text"], anchor="w").grid(row=r, column=col, sticky="ew",
                                                        padx=4, pady=8)


    def _ubah_lebar(self, e):
        if e.widget is not self:
            return
        self._atur_kpi(e.width)
        if not hasattr(self, "kolom_grafik"):
            return
        sempit = e.width < px(900)
        if sempit == self._sempit:
            return
        self._sempit = sempit
        self.kolom_grafik.grid_forget()
        self.kolom_samping.grid_forget()
        if sempit:
            self.kolom_grafik.pack(fill="x", pady=(0, 14))
            self.kolom_samping.pack(fill="x")
        else:
            self.kolom_grafik.pack_forget()
            self.kolom_samping.pack_forget()
            self.baris_bawah.columnconfigure(0, weight=7)
            self.baris_bawah.columnconfigure(1, weight=4)
            self.kolom_grafik.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
            self.kolom_samping.grid(row=0, column=1, sticky="new")
