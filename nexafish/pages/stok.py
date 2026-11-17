"""Halaman Manajemen Stok & Katalog Produk Ikan Bawal NEXAFISH ERP."""

import tkinter as tk
from tkinter import messagebox

from base import Halaman
from theme import C, f
from utils import rupiah, parse_angka
from widgets import Tombol, Dialog, buat_combo, buat_tabel, isi_tabel, kartu


class StokPage(Halaman):
    def __init__(self, parent, main):
        super().__init__(parent, main)

        # Toolbar Atas
        toolbar = kartu(self)
        toolbar.pack(fill="x", pady=(0, 12))

        tb_inner = tk.Frame(toolbar, bg="white")
        tb_inner.pack(fill="x", padx=16, pady=12)

        # Filter Kategori Sisi Kiri
        kiri = tk.Frame(tb_inner, bg="white")
        kiri.pack(side="left")

        tk.Label(kiri, text="Kategori Ukuran:", font=f(9, True), bg="white", fg=C["text"]).pack(side="left", padx=(0, 8))
        self.filter = buat_combo(kiri, [], lebar=18)
        self.filter.pack(side="left", ipady=2)
        self.filter.bind("<<ComboboxSelected>>", lambda e: self.muat())

        if self.is_owner:
            kanan=tk.Frame(tb_inner,bg="white"); kanan.pack(side="right")
            Tombol(kanan,"Hapus",self.hapus,gaya="soft",warna=C["red_text"],tinggi=34,ukuran=9).pack(side="right",padx=(6,0))
            Tombol(kanan,"Ubah Harga",self.ubah_harga,gaya="soft",warna=C["primary"],tinggi=34,ukuran=9).pack(side="right",padx=(6,0))
            Tombol(kanan,"Koreksi Ekor",self.koreksi_ekor,gaya="soft",warna=C["primary"],tinggi=34,ukuran=9).pack(side="right",padx=(6,0))
            Tombol(kanan,"Kurangi Stok",self.kurangi,gaya="soft",warna=C["amber_text"],tinggi=34,ukuran=9).pack(side="right",padx=(6,0))
            Tombol(kanan,"Restock",self.restock,gaya="soft",warna=C["green_text"],tinggi=34,ukuran=9).pack(side="right",padx=(6,0))
            Tombol(kanan,"+ Pakan",lambda:self.tambah("Pakan"),gaya="soft",warna=C["primary"],tinggi=34,ukuran=9).pack(side="right",padx=(6,0))
            Tombol(kanan,"+ Produk Ikan",lambda:self.tambah("Ikan"),warna=C["primary"],tinggi=34,ukuran=9).pack(side="right")
        if self.is_owner:
            kolom=[
                ("kode","Kode",90,"center"),("jenis","Jenis Produk",190,"w"),
                ("kat","Kategori Ukuran",130,"w"),("stok","Stok (kg)",85,"e"),
                ("ekor","Ekor",70,"e"),("beli","HPP / kg",115,"e"),
                ("jual","Harga Jual / kg",115,"e"),("margin","Margin Laba",90,"e"),
            ]
        else:
            kolom=[("kode","Kode",90,"center"),("jenis","Jenis Produk",220,"w"),
                   ("kat","Kategori Ukuran",140,"w"),("stok","Stok (kg)",100,"e"),
                   ("jual","Harga Jual / kg",140,"e")]
        frame_tabel,self.tree=buat_tabel(self,kolom,tinggi=14)
        frame_tabel.pack(fill="both",expand=True)

        # Baris Ringkasan & Legenda di Bawah Tabel
        bawah = tk.Frame(self, bg=C["bg"])
        bawah.pack(fill="x", pady=(10, 0))

        self.ringkas = tk.Label(bawah, text="", font=f(9, True), bg=C["bg"], fg=C["text"])
        self.ringkas.pack(side="left")

        # Indikator stok tipis
        legenda = tk.Frame(bawah, bg=C["bg"])
        legenda.pack(side="right")
        tk.Label(legenda, text="●", font=f(8), fg=C["danger"], bg=C["bg"]).pack(side="left", padx=(0, 4))
        tk.Label(legenda, text="Peringatan: ikan ≤ 50 ekor, pakan ≤ 50 kg", font=f(8),
                 fg=C["muted"], bg=C["bg"]).pack(side="left")

        self.muat_filter()
        self.muat()

    def muat_filter(self):
        self.kategori={nama:idk for idk,nama,_k,_j in self.db.daftar_kategori()}
        self.filter.config(values=["Semua Kategori"]+list(self.kategori))
        if self.filter.get() not in self.filter.cget("values"):
            self.filter.set("Semua Kategori")

    def muat(self):
        idk=self.kategori.get(self.filter.get())
        produk=self.db.daftar_produk_lengkap(id_kategori=idk)
        baris=[]; total_kg=0.0; nilai=0.0
        for pid,kode,kind,jenis,_idkat,_kodekat,kat,_ket,stok,ekor,beli,jual in produk:
            total_kg+=stok; nilai+=stok*beli
            if self.is_owner:
                margin=f"{(jual-beli)/jual*100:.0f}%" if jual>0 else "-"
                vals=(kode,f"{jenis} ({kind})",kat,f"{stok:g}",f"{ekor}",rupiah(beli),rupiah(jual) if jual else "-",margin)
            else:
                vals=(kode,f"{jenis} ({kind})",kat,f"{stok:g}",rupiah(jual) if jual else "-")
            baris.append((pid,vals))
        isi_tabel(self.tree,baris)
        self.ringkas.config(text=f"{len(produk)} produk  •  Total kuantitas: {total_kg:g} kg  •  Nilai persediaan: {rupiah(nilai)}")

    def terpilih(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Pilih Produk", "Silakan klik salah satu produk pada tabel terlebih dahulu.", parent=self)
            return None
        return int(sel[0])

    def tambah(self, kind="Ikan"):
        kategori=list(self.kategori)
        if kind=="Pakan":
            kategori=[nama for nama in kategori if "pakan" in nama.casefold()] or kategori
        else:
            kategori=[nama for nama in kategori if "pakan" not in nama.casefold()]
        if not kategori:
            return messagebox.showwarning("Kategori Belum Ada","Tambahkan kategori terlebih dahulu.",parent=self)
        def simpan(v):
            self.db.tambah_produk(v["jenis"],self.kategori[v["kat"]],
                parse_angka(v["stok"],"Stok"),parse_angka(v["beli"],"HPP"),
                parse_angka(v.get("jual") or "0","Harga jual"),"Kas",self.user,
                kode=v["kode"],jenis_produk=kind,
                stok_ekor=parse_angka(v.get("ekor") or "0","Jumlah ekor"))
            self.muat_filter(); self.muat()
        fields=[("kode","Kode Produk (BWL01 / PKN01)","text",None,""),
            ("jenis","Nama Produk","text",None,""),("kat","Kategori Ukuran","combo",kategori,""),
            ("stok","Stok Awal (kg)","number",None,"0")]
        if kind=="Ikan": fields.append(("ekor","Jumlah Awal (ekor ikan)","number",None,"0"))
        fields.append(("beli","HPP / kg","number",None,""))
        if kind=="Ikan": fields.append(("jual","Harga Jual / kg","number",None,""))
        Dialog(self,"Tambah Produk Pakan" if kind=="Pakan" else "Tambah Produk Ikan",fields,
            simpan,info=f"Form khusus untuk {kind.lower()}. Kode produk diisi manual dan harus unik.")

    def restock(self):
        pid=self.terpilih()
        if pid is None:return
        p=self.db.ambil_produk(pid)
        def simpan(v):
            self.db.restock(pid,parse_angka(v["qty"],"Jumlah"),parse_angka(v["beli"],"HPP"),
                            "Kas",self.user,parse_angka(v["ekor"] or "0","Jumlah ekor"))
            self.muat()
        Dialog(self,"Restock Produk",[("qty","Kuantitas Tambahan (kg)","number",None,""),
            ("ekor","Jumlah Ekor Tambahan (isi 0 untuk pakan)","number",None,"0"),
            ("beli","HPP / kg","number",None,f"{p['harga_beli']:.0f}")],simpan,
            info=f"{p['kode']} — {p['jenis']} — stok saat ini {p['stok']:g} kg.")
    def kurangi(self):
        pid=self.terpilih()
        if pid is None:return
        p=self.db.ambil_produk(pid)
        def simpan(v):
            self.db.kurangi_stok(pid,parse_angka(v["qty"],"Jumlah"),v["alasan"],self.user,
                                 parse_angka(v["ekor"] or "0","Jumlah ekor"))
            self.muat()
        Dialog(self,"Kurangi Stok",[("qty","Kuantitas Dikurangi (kg)","number",None,""),
            ("ekor","Ekor Ikan Mati (isi 0 untuk pakan)","number",None,"0"),
            ("alasan","Alasan","combo",["Ikan mati / susut","Rusak / tidak layak","Koreksi stok"],"Ikan mati / susut")],
            simpan,info=f"{p['kode']} — stok {p['stok']:g} kg; jumlah ikan tercatat {p['stok_ekor']} ekor.")

    def ubah_harga(self):
        pid = self.terpilih()
        if pid is None:
            return
        p = self.db.ambil_produk(pid)

        def simpan(v):
            self.db.ubah_harga_jual(pid, parse_angka(v["jual"], "Harga jual"), self.user)
            self.muat()

        Dialog(self, "Perbarui Harga Jual", [
            ("jual", "Harga Jual Baru per kg", "number", None, f"{p['harga_jual']:.0f}"),
        ], simpan, info=f"{p['jenis']} ({p['kategori']}). Perubahan harga jual berlaku untuk transaksi kasir berikutnya.")

    def koreksi_ekor(self):
        pid=self.terpilih()
        if pid is None:return
        p=self.db.ambil_produk(pid)
        if p["jenis_produk"]!="Ikan":
            return messagebox.showinfo("Koreksi Jumlah Ekor","Fitur ini hanya berlaku untuk produk ikan.",parent=self)
        def simpan(v):
            self.db.ubah_jumlah_ekor(pid,parse_angka(v["jumlah"],"Jumlah ekor"),self.user)
            self.muat()
        Dialog(self,"Koreksi Jumlah Ekor",[("jumlah","Jumlah Ekor Saat Ini","number",None,str(p["stok_ekor"]))],
               simpan,info="Masukkan jumlah ikan yang benar setelah penghitungan fisik.")

    def hapus(self):
        pid = self.terpilih()
        if pid is None:
            return
        p = self.db.ambil_produk(pid)
        if messagebox.askyesno("Hapus Produk", f"Apakah Anda yakin ingin menghapus produk '{p['jenis']}'?", parent=self):
            if self.coba(self.db.hapus_produk, pid, self.user):
                self.muat_filter()
                self.muat()


