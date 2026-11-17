"""Laporan, jurnal penyesuaian, dan pencatatan penyesuaian operasional."""

import datetime
import tkinter as tk
from tkinter import messagebox

from base import Halaman
from theme import C, f
from utils import rupiah, parse_angka
from widgets import TabModern, Tombol, Isian, buat_combo, buat_tabel, isi_tabel
from pages.jurnal import JurnalManualDialog


class LaporanPage(Halaman):
    def __init__(self, parent, main):
        super().__init__(parent, main)
        nb = TabModern(self)
        nb.pack(fill="both", expand=True)
        self._tab_neraca_saldo(nb, False)
        self._tab_neraca_saldo(nb, True)
        self._tab_penyesuaian(nb)
        self._tab_laba_rugi(nb)
        self._tab_posisi(nb)
        self._tab_modal(nb)
        self._tab_arus_kas(nb)
        self._tab_lajur(nb)

    def _tanggal(self, field):
        value = field.get().strip()
        try:
            datetime.datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Tanggal harus berformat YYYY-MM-DD.")
        return value

    def _tab_neraca_saldo(self, nb, penyesuaian):
        judul = "Neraca Saldo Sesudah Penyesuaian" if penyesuaian else "Neraca Saldo Sebelum Penyesuaian"
        tab = tk.Frame(nb, bg=C["bg"]); nb.add(tab, text=f" {judul} ")
        _fr, tree = buat_tabel(tab, [("kode","No. Akun",85,"center"),("nama","Nama Akun",245,"w"),
            ("tipe","Kelompok",110,"w"),("debit","Debit (Rp)",150,"e"),("kredit","Kredit (Rp)",150,"e")], tinggi=18)
        _fr.pack(fill="both",expand=True,padx=8,pady=12)
        rows, td, tk_ = self.db.neraca_saldo(penyesuaian)
        tipe = {k:t for k,_n,t,_s in self.db.daftar_akun()}
        isi_tabel(tree,[(k,n,tipe.get(k,""),rupiah(d) if d else "",rupiah(kr) if kr else "") for k,n,d,kr in rows])
        tree.insert("","end",values=("","TOTAL","",rupiah(td),rupiah(tk_)),tags=("total",))

    def _tab_penyesuaian(self, nb):
        tab=tk.Frame(nb,bg=C["bg"]); nb.add(tab,text=" Jurnal Penyesuaian ")
        sub=TabModern(tab);sub.pack(fill="both",expand=True,padx=4,pady=4)
        jurnal=tk.Frame(sub,bg=C["bg"]);sub.add(jurnal,text=" Jurnal Penyesuaian ")
        head=tk.Frame(jurnal,bg=C["bg"]); head.pack(fill="x",padx=10,pady=(12,6))
        tk.Label(head,text="Jurnal Penyesuaian",font=f(12,True),bg=C["bg"],fg=C["text"]).pack(side="left")
        Tombol(head,"+ Jurnal Penyesuaian",lambda:JurnalManualDialog(self,self.db,self.user,self._muat_penyesuaian,"JURNAL-PENYESUAIAN"),warna=C["primary"],tinggi=32,ukuran=9).pack(side="right")
        _fr,self.tree_adj=buat_tabel(jurnal,[("no","No. Jurnal",100,"center"),("tgl","Tanggal & Waktu",170,"w"),
            ("ket","Keterangan Penyesuaian",420,"w"),("oleh","Dibuat Oleh",150,"w")],tinggi=17)
        _fr.pack(fill="both",expand=True,padx=8,pady=(0,12)); self._muat_penyesuaian()
        self._tab_pakan(sub)
        self._tab_penyusutan(sub)
        self._tab_opname(sub)

    def _muat_penyesuaian(self):
        isi_tabel(self.tree_adj,[(f"JP-{i:03d}",t,k,o or "-") for i,t,k,o in self.db.daftar_jurnal_penyesuaian()])

    def _form(self, tab, title, labels):
        box=tk.Frame(tab,bg="white",highlightbackground=C["border"],highlightthickness=1)
        box.pack(fill="x",padx=10,pady=(12,8))
        tk.Label(box,text=title,font=f(11,True),bg="white",fg=C["text"]).grid(row=0,column=0,columnspan=len(labels),sticky="w",padx=12,pady=(10,8))
        fields=[]
        for col,(label,kind,values) in enumerate(labels):
            tk.Label(box,text=label,font=f(8,True),bg="white",fg=C["text"]).grid(row=1,column=col,sticky="w",padx=6)
            if kind=="combo":
                field=buat_combo(box,values,lebar=22)
                if values: field.set(values[0])
            else:
                field=Isian(box,numeric=(kind=="number"))
                if kind=="date": field.set(datetime.date.today().isoformat())
            field.grid(row=2,column=col,sticky="ew",padx=6,pady=(2,10))
            fields.append(field); box.columnconfigure(col,weight=1)
        return box,fields

    def _tab_pakan(self, nb):
        tab=tk.Frame(nb,bg=C["bg"]); nb.add(tab,text=" Pemakaian Pakan ")
        products=self.db.daftar_produk_lengkap(jenis_produk="Pakan")
        options=[f"{p[1]} - {p[3]} (Stok {p[8]:g} kg, HPP {rupiah(p[10])}/kg)" for p in products]
        by_option={o:p for o,p in zip(options,products)}
        _,fields=self._form(tab,"Catat Pemakaian Pakan",[("Tanggal","date",None),("Pakan","combo",options),("Pakan Terpakai (kg)","number",None)])
        tanggal,produk,jumlah=fields
        tk.Label(tab,text="Pemakaian dicatat sebagai Beban Pakan dan mengurangi persediaan pakan.",font=f(8),bg=C["bg"],fg=C["muted"]).pack(anchor="w",padx=12)
        _fr,self.tree_pakan=buat_tabel(tab,[("tgl","Tanggal",130,"w"),("kode","Kode",90,"center"),("produk","Produk",220,"w"),("jumlah","Terpakai (kg)",120,"e"),("hpp","Nilai HPP",150,"e"),("oleh","Petugas",130,"w")],tinggi=12)
        _fr.pack(fill="both",expand=True,padx=8,pady=8)
        def save():
            try:
                p=by_option.get(produk.get())
                if not p: raise ValueError("Pilih produk pakan.")
                self.db.catat_pemakaian_pakan(p[0],parse_angka(jumlah.get(),"Jumlah"),self.user,self._tanggal(tanggal))
            except ValueError as e: return messagebox.showwarning("Pemakaian Pakan",str(e),parent=self)
            self._muat_pakan(); jumlah.clear()
        Tombol(fields[0].master,"Catat Pemakaian Pakan",save,warna=C["primary"],tinggi=32,ukuran=9).grid(row=3,column=0,sticky="w",padx=6,pady=(0,10))
        self._muat_pakan()

    def _muat_pakan(self):
        isi_tabel(self.tree_pakan,[(t[:10],k or "-",n,f"{q:g}",rupiah(v),o) for _i,t,k,n,q,v,o in self.db.daftar_pemakaian_pakan()])

    def _tab_penyusutan(self, nb):
        tab=tk.Frame(nb,bg=C["bg"]); nb.add(tab,text=" Penyusutan Peralatan ")
        box,fields=self._form(tab,"Catat Penyusutan Peralatan",[("Tanggal","date",None),("Nilai Penyusutan (Rp)","number",None)])
        tanggal,nilai=fields
        tk.Label(tab,text="Jurnal otomatis: Debit Beban Penyusutan Peralatan, Kredit Akumulasi Penyusutan Peralatan.",font=f(8),bg=C["bg"],fg=C["muted"]).pack(anchor="w",padx=12)
        def save():
            try: self.db.catat_penyusutan(parse_angka(nilai.get(),"Nilai penyusutan"),self.user,self._tanggal(tanggal))
            except ValueError as e: return messagebox.showwarning("Penyusutan",str(e),parent=self)
            messagebox.showinfo("Penyusutan","Jurnal penyusutan berhasil dicatat.",parent=self); nilai.clear()
        Tombol(box,"Catat Penyusutan",save,warna=C["primary"],tinggi=32,ukuran=9).grid(row=3,column=0,sticky="w",padx=6,pady=(0,10))

    def _tab_opname(self, nb):
        tab=tk.Frame(nb,bg=C["bg"]); nb.add(tab,text=" Stock Opname ")
        products=self.db.daftar_produk_lengkap(jenis_produk="Ikan")
        options=[f"{p[1]} - {p[3]} (Stok {p[8]:g} kg / {p[9]} ekor)" for p in products]; by_option={o:p for o,p in zip(options,products)}
        box,fields=self._form(tab,"Catat Ikan Mati / Stock Opname",[("Tanggal","date",None),("Jenis Ikan","combo",options),("Jumlah Mati (kg)","number",None),("Jumlah Mati (ekor)","number",None),("Keterangan","text",None)])
        tanggal,produk,kg,ekor,ket=fields
        _fr,self.tree_opname=buat_tabel(tab,[("tanggal","Tanggal",120,"w"),("kode","Kode",80,"center"),("barang","Barang",190,"w"),("kg","Mati (kg)",95,"e"),("ekor","Mati (ekor)",100,"e"),("jenis","Keterangan",230,"w")],tinggi=10)
        _fr.pack(fill="both",expand=True,padx=8,pady=(4,6))
        actions=tk.Frame(tab,bg=C["bg"]); actions.pack(fill="x",padx=8,pady=(0,8))
        def save():
            try:
                p=by_option.get(produk.get())
                if not p: raise ValueError("Pilih jenis ikan.")
                self.db.catat_stock_opname(p[0],parse_angka(kg.get(),"Jumlah kg"),parse_angka(ekor.get() or "0","Jumlah ekor"),ket.get(),self.user,self._tanggal(tanggal))
            except (ValueError,TypeError) as e: return messagebox.showwarning("Stock Opname",str(e),parent=self)
            self._muat_opname(); kg.clear();ekor.clear();ket.clear()
        Tombol(actions,"Simpan Opname",save,warna=C["primary"],tinggi=32,ukuran=9).pack(side="left")
        Tombol(actions,"Hapus Opname Terpilih",self._hapus_opname,gaya="soft",warna=C["red_text"],tinggi=32,ukuran=9).pack(side="left",padx=8)
        self._muat_opname()

    def _muat_opname(self):
        self.tree_opname.delete(*self.tree_opname.get_children())
        for i,t,k,n,kg,e,ket in self.db.daftar_stock_opname():
            self.tree_opname.insert("","end",iid=str(i),values=(t[:10],k or "-",n,f"{kg:g}",str(e),ket))

    def _hapus_opname(self):
        sel=self.tree_opname.selection()
        if not sel: return messagebox.showinfo("Stock Opname","Pilih opname yang akan dihapus.",parent=self)
        if not messagebox.askyesno("Hapus Opname","Stok dan jurnal akan dikembalikan dengan jurnal pembalik. Lanjutkan?",parent=self): return
        try:
            for ident in sel: self.db.hapus_stock_opname(int(ident),self.user)
        except ValueError as e: return messagebox.showwarning("Stock Opname",str(e),parent=self)
        self._muat_opname()

    def _tab_laba_rugi(self,nb):
        tab=tk.Frame(nb,bg=C["bg"]);nb.add(tab,text=" Laba Rugi ")
        _fr,tree=buat_tabel(tab,[("ket","Komponen Laba Rugi",430,"w"),("nilai","Jumlah (Rp)",190,"e")],tinggi=18);_fr.pack(fill="both",expand=True,padx=8,pady=12)
        lr=self.db.laba_rugi();tree.insert("","end",values=("Pendapatan Usaha",rupiah(lr["pendapatan"])))
        tree.insert("","end",values=("Harga Pokok Penjualan (HPP)",f"({rupiah(lr['hpp'])})"))
        tree.insert("","end",values=("LABA KOTOR",rupiah(lr["laba_kotor"])),tags=("total",))
        tree.insert("","end",values=("Beban", ""),tags=("judul",))
        for n,v in lr["beban"]: tree.insert("","end",values=(f"   {n}",rupiah(v)))
        tree.insert("","end",values=("TOTAL BEBAN",rupiah(sum(v for _,v in lr["beban"]))),tags=("total",))
        tree.insert("","end",values=("LABA BERSIH",rupiah(lr["laba_bersih"])),tags=("total",))

    def _tab_posisi(self,nb):
        tab=tk.Frame(nb,bg=C["bg"]);nb.add(tab,text=" Posisi Keuangan ")
        _fr,tree=buat_tabel(tab,[("ket","Akun",430,"w"),("nilai","Saldo (Rp)",190,"e")],tinggi=18);_fr.pack(fill="both",expand=True,padx=8,pady=12)
        aset,kew,modal,laba=self.db.posisi_keuangan()
        tree.insert("","end",values=("ASET", ""),tags=("judul",))
        for n,s in aset: tree.insert("","end",values=(f"   {n}",rupiah(s)))
        tree.insert("","end",values=("Total Aset",rupiah(sum(s for _,s in aset))),tags=("total",))
        tree.insert("","end",values=("KEWAJIBAN & EKUITAS", ""),tags=("judul",))
        for n,s in kew+modal: tree.insert("","end",values=(f"   {n}",rupiah(s)))
        tree.insert("","end",values=("   Laba Bersih Periode Berjalan",rupiah(laba)))
        tree.insert("","end",values=("Total Kewajiban & Ekuitas",rupiah(sum(s for _,s in kew+modal)+laba)),tags=("total",))

    def _tab_modal(self,nb):
        tab=tk.Frame(nb,bg=C["bg"]);nb.add(tab,text=" Perubahan Modal ")
        _fr,tree=buat_tabel(tab,[("ket","Perubahan Ekuitas",430,"w"),("nilai","Nilai (Rp)",190,"e")],tinggi=12);_fr.pack(fill="both",expand=True,padx=8,pady=12)
        data=self.db.laporan_perubahan_modal()
        rows=(("Modal Awal",data["modal_awal"]),("Setoran Modal Tambahan",data["setoran"]),
              ("Laba Bersih",data["laba"]),("Prive",-data["prive"]),("Modal Akhir",data["akhir"]))
        for label,nilai in rows:
            tree.insert("","end",values=(label,rupiah(nilai)),tags=("total",) if label=="Modal Akhir" else ())

    def _tab_arus_kas(self,nb):
        tab=tk.Frame(nb,bg=C["bg"]);nb.add(tab,text=" Arus Kas Langsung ")
        bar=tk.Frame(tab,bg=C["bg"]);bar.pack(fill="x",padx=10,pady=12)
        tk.Label(bar,text="Periode (YYYY-MM)",font=f(9,True),bg=C["bg"],fg=C["text"]).pack(side="left")
        periode=Isian(bar);periode.set(datetime.date.today().strftime("%Y-%m"));periode.pack(side="left",padx=8)
        _fr,tree=buat_tabel(tab,[("item","Arus Kas",440,"w"),("nilai","Jumlah (Rp)",200,"e")],tinggi=16);_fr.pack(fill="both",expand=True,padx=8,pady=(0,10))
        def load():
            try: data=self.db.laporan_arus_kas_langsung(periode.get().strip())
            except (ValueError,TypeError) as e: return messagebox.showwarning("Arus Kas",str(e),parent=self)
            rows=[("Arus kas dari kegiatan operasi",""),("Penerimaan dari penjualan",data["sales"]),("Pembelian bibit / ikan",-data["bibit"]),("Pembelian pakan",-data["feed"]),("Beban operasional",-data["expense"]),("Arus kas bersih dari operasi",data["operasi"]),("Arus kas dari kegiatan pendanaan",""),("Setoran modal tambahan",data["capital"]),("Prive",-data["prive"]),("Kenaikan kas bersih",data["kenaikan"]),("Saldo kas awal",data["awal"]),("SALDO KAS AKHIR",data["akhir"])]
            tree.delete(*tree.get_children())
            for label,val in rows: tree.insert("","end",values=(label,"" if val=="" else rupiah(val)),tags=("judul",) if val=="" else (("total",) if label in ("Arus kas bersih dari operasi","Kenaikan kas bersih","SALDO KAS AKHIR") else ()))
        Tombol(bar,"Tampilkan",load,warna=C["primary"],tinggi=30,ukuran=9).pack(side="left");load()

    def _tab_lajur(self,nb):
        tab=tk.Frame(nb,bg=C["bg"]);nb.add(tab,text=" Neraca Lajur ")
        cols=[("kode","Kode",70,"center"),("nama","Nama Akun",180,"w"),("sd","NS Awal D",95,"e"),("sk","NS Awal K",95,"e"),("ad","Penyesuaian D",100,"e"),("ak","Penyesuaian K",100,"e"),("fd","NSSP D",95,"e"),("fk","NSSP K",95,"e"),("lrd","LR D",95,"e"),("lrk","LR K",95,"e"),("nsd","Neraca D",95,"e"),("nsk","Neraca K",95,"e")]
        _fr,tree=buat_tabel(tab,cols,tinggi=17);_fr.pack(fill="both",expand=True,padx=6,pady=12)
        rows=self.db.neraca_lajur()
        isi_tabel(tree,[(k,n,*[rupiah(x) if x else "" for x in values]) for k,n,*values in rows])
