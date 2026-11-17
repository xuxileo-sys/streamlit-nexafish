"""Halaman kas operasional dan kas kecil untuk Owner maupun Karyawan."""

import datetime
import tkinter as tk
from tkinter import messagebox

from base import Halaman
from theme import C, f
from utils import rupiah
from widgets import TabModern, Tombol, Isian, buat_combo, buat_tabel, kartu


class KasKecilPage(Halaman):
    def __init__(self, parent, main):
        super().__init__(parent, main)
        self.nb = TabModern(self)
        self.nb.pack(fill="both", expand=True)
        self._tab_kas("Penerimaan", "Kas Masuk")
        self._tab_kas("Pengeluaran", "Kas Keluar")
        self._tab_kecil()

    def _tanggal(self, field):
        teks = field.get().strip()
        try:
            datetime.datetime.strptime(teks, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Tanggal harus berformat YYYY-MM-DD.")
        return teks

    def _tab_kas(self, jenis, judul):
        tab = tk.Frame(self.nb, bg=C["bg"])
        self.nb.add(tab, text=f" {judul} ")
        box = kartu(tab)
        box.pack(fill="x", padx=8, pady=(12, 10))
        isi = tk.Frame(box, bg="white")
        isi.pack(fill="x", padx=18, pady=16)
        tk.Label(isi, text=f"Catat {judul}", font=f(12, True), bg="white", fg=C["text"]).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,10))
        tk.Label(isi,text="Tanggal",font=f(9,True),bg="white",fg=C["text"]).grid(row=1,column=0,sticky="w")
        tgl=Isian(isi); tgl.set(datetime.date.today().isoformat()); tgl.grid(row=2,column=0,sticky="ew",padx=(0,10))
        tk.Label(isi,text="Akun Lawan / Alokasi",font=f(9,True),bg="white",fg=C["text"]).grid(row=1,column=1,sticky="w")
        akunops=[f"{k} - {n}" for k,n,_tipe,_normal in self.db.daftar_akun() if k not in ("1101","1105")]
        cb=buat_combo(isi,akunops,lebar=34); cb.grid(row=2,column=1,sticky="ew")
        tk.Label(isi,text="Keterangan",font=f(9,True),bg="white",fg=C["text"]).grid(row=3,column=0,sticky="w",pady=(8,0))
        ket=Isian(isi,placeholder="Keterangan transaksi"); ket.grid(row=4,column=0,sticky="ew",padx=(0,10))
        tanda="+" if jenis=="Penerimaan" else "−"
        tk.Label(isi,text=f"Jumlah ({tanda} Rp)",font=f(9,True),bg="white",fg=C["text"]).grid(row=3,column=1,sticky="w",pady=(8,0))
        jumlah=Isian(isi,numeric=True,placeholder="Nominal"); jumlah.grid(row=4,column=1,sticky="ew")
        tk.Label(isi,text="Customer / Supplier Terkait (opsional)",font=f(9,True),bg="white",fg=C["text"]).grid(row=5,column=0,sticky="w",pady=(8,0))
        pihak_ops=[""]+[f"Customer - {r[1]}" for r in self.db.daftar_pihak("customer")]+[f"Supplier - {r[1]}" for r in self.db.daftar_pihak("supplier")]
        pihak=buat_combo(isi,pihak_ops,lebar=34); pihak.grid(row=6,column=0,sticky="ew",padx=(0,10))
        isi.columnconfigure(0,weight=1); isi.columnconfigure(1,weight=1)

        def bersihkan():
            tgl.set(datetime.date.today().isoformat()); ket.clear(); jumlah.clear()
            if akunops: cb.set(akunops[0])
            pihak.set("")

        def simpan():
            try:
                kode=cb.get().split(" - ",1)[0]
                nama_pihak=pihak.get().split(" - ",1)[-1] if pihak.get() else ""
                bukti=self.db.catat_kas(jenis,ket.get(),float(jumlah.get()),kode,self.user,
                                        nama_pihak=nama_pihak,tanggal=self._tanggal(tgl))
            except (ValueError,TypeError) as e:
                messagebox.showwarning(judul,str(e),parent=self); return
            self._muat_kas(tree)
            messagebox.showinfo(judul,f"Transaksi tersimpan. Bukti: {bukti}",parent=self)
            bersihkan()

        Tombol(isi,"Simpan Perubahan",simpan,warna=C["primary"],tinggi=34,ukuran=9).grid(row=7,column=0,sticky="w",pady=(12,0))
        Tombol(isi,"Bersihkan",bersihkan,gaya="outline",tinggi=34,ukuran=9).grid(row=7,column=1,sticky="w",pady=(12,0))

        tk.Label(tab,text="Riwayat Kas",font=f(11,True),bg=C["bg"],fg=C["text"]).pack(anchor="w",padx=10,pady=(4,6))
        _fr,tree=buat_tabel(tab,[("bukti","Bukti",95,"center"),("waktu","Tanggal",130,"w"),
            ("jenis","Jenis",110,"w"),("ket","Keterangan",240,"w"),("pihak","Customer/Supplier",160,"w"),("jumlah","Jumlah",140,"e")],tinggi=10)
        _fr.pack(fill="both",expand=True,padx=8,pady=(0,12))
        self._muat_kas(tree)

    def _muat_kas(self, tree):
        tree.delete(*tree.get_children())
        for ident,waktu,jenis,ket,jumlah,_akun,_oleh,pihak in self.db.daftar_kas():
            nomor=f"{'KM' if jenis=='Penerimaan' else 'KK'}-{ident:03d}"
            tanda="+" if jenis=="Penerimaan" else "−"
            tree.insert("","end",values=(nomor,str(waktu)[:10],jenis,ket,pihak or "-",f"{tanda}{rupiah(jumlah)}"))

    def _tab_kecil(self):
        tab=tk.Frame(self.nb,bg=C["bg"])
        self.nb.add(tab,text=" Kas Kecil ")
        self.lbl_saldo=tk.Label(tab,text="",font=f(14,True),bg=C["bg"],fg=C["primary"])
        self.lbl_saldo.pack(anchor="w",padx=10,pady=(12,4))
        kolom=tk.Frame(tab,bg=C["bg"]); kolom.pack(fill="x")
        box1=kartu(kolom); box1.pack(side="left",fill="both",expand=True,padx=(8,5),pady=8)
        box2=kartu(kolom); box2.pack(side="left",fill="both",expand=True,padx=(5,8),pady=8)
        self.tgl_masuk,self.nom_masuk=self._form_kecil(box1,"Isi Dana Kas Kecil",True)
        self.tgl_keluar,self.nom_keluar=self._form_kecil(box2,"Belanja Kas Kecil",False)
        tk.Label(tab,text="Riwayat Kas Kecil",font=f(11,True),bg=C["bg"],fg=C["text"]).pack(anchor="w",padx=10,pady=(6,4))
        _fr,self.tree_kecil=buat_tabel(tab,[("bukti","Bukti",100,"center"),("tanggal","Tanggal",120,"w"),
            ("ket","Keterangan",320,"w"),("masuk","Masuk",130,"e"),("keluar","Keluar",130,"e")],tinggi=9)
        _fr.pack(fill="both",expand=True,padx=8)
        Tombol(tab,"Hapus Transaksi Terpilih",self._hapus_kecil,gaya="soft",warna=C["red_text"],tinggi=34,ukuran=9).pack(anchor="e",padx=8,pady=8)
        self._muat_kecil()

    def _form_kecil(self,parent,judul,masuk):
        dalam=tk.Frame(parent,bg="white"); dalam.pack(fill="x",padx=16,pady=14)
        tk.Label(dalam,text=judul,font=f(11,True),bg="white",fg=C["text"]).pack(anchor="w",pady=(0,8))
        tk.Label(dalam,text="Tanggal",font=f(8,True),bg="white",fg=C["text"]).pack(anchor="w")
        tgl=Isian(dalam); tgl.set(datetime.date.today().isoformat()); tgl.pack(fill="x")
        combo=None
        if masuk:
            tk.Label(dalam,text="Sumber Dana",font=f(8,True),bg="white",fg=C["text"]).pack(anchor="w",pady=(6,0))
            tk.Label(dalam,text="Kas (1101)",font=f(9),bg="white",fg=C["muted"]).pack(anchor="w")
        else:
            tk.Label(dalam,text="Akun Beban",font=f(8,True),bg="white",fg=C["text"]).pack(anchor="w",pady=(6,0))
            daftar=[f"{k} - {n}" for k,n,tipe,_normal in self.db.daftar_akun() if tipe=="Beban"]
            combo=buat_combo(dalam,daftar); combo.pack(fill="x")
        tk.Label(dalam,text="Keterangan",font=f(8,True),bg="white",fg=C["text"]).pack(anchor="w",pady=(6,0))
        ket=Isian(dalam,placeholder="Pengisian Kas Kecil" if masuk else "Keterangan belanja"); ket.pack(fill="x")
        tk.Label(dalam,text=f"Jumlah ({'+' if masuk else '−'} Rp)",font=f(8,True),bg="white",fg=C["text"]).pack(anchor="w",pady=(6,0))
        jumlah=Isian(dalam,numeric=True,placeholder="Nominal"); jumlah.pack(fill="x")
        def bersihkan():
            tgl.set(datetime.date.today().isoformat()); ket.clear(); jumlah.clear()
        def simpan():
            try:
                tanggal=self._tanggal(tgl); nilai=float(jumlah.get())
                nomor=(self.db.isi_dana_kas_kecil(nilai,self.user,tanggal,ket.get() or "Pengisian Kas Kecil")
                       if masuk else self.db.catat_belanja_kas_kecil(combo.get().split(" - ",1)[0],nilai,ket.get(),self.user,tanggal))
            except (ValueError,TypeError) as e:
                messagebox.showwarning(judul,str(e),parent=self); return
            self._muat_kecil(); bersihkan()
            messagebox.showinfo(judul,f"Transaksi tersimpan. Bukti: {nomor}",parent=self)
        Tombol(dalam,"Isi Dana" if masuk else "Catat Belanja",simpan,warna=C["primary"],tinggi=32,ukuran=9).pack(anchor="w",pady=(10,0))
        return tgl,jumlah

    def _muat_kecil(self):
        self.lbl_saldo.config(text=f"Saldo Kas Kecil: {rupiah(self.db.saldo_kas_kecil())}")
        self.tree_kecil.delete(*self.tree_kecil.get_children())
        for ident,waktu,nomor,ket,masuk,keluar,_jenis in self.db.daftar_kas_kecil():
            self.tree_kecil.insert("","end",iid=str(ident),values=(nomor or f"BKK-{ident:03d}",str(waktu)[:10],ket,f"+{rupiah(masuk)}" if masuk else "-",f"−{rupiah(keluar)}" if keluar else "-"))

    def _hapus_kecil(self):
        sel=self.tree_kecil.selection()
        if not sel:
            return messagebox.showinfo("Kas Kecil","Pilih transaksi yang akan dihapus.",parent=self)
        if not messagebox.askyesno("Hapus Transaksi","Transaksi akan dihapus dan jurnalnya dibalikkan. Lanjutkan?",parent=self):
            return
        try:
            for ident in sel: self.db.hapus_kas_kecil(int(ident),self.user)
        except ValueError as e:
            return messagebox.showwarning("Kas Kecil",str(e),parent=self)
        self._muat_kecil()
