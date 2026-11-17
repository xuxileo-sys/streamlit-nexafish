# 🐟 NEXAFISH — Enterprise Fish Tech & Accounting

Aplikasi desktop profesional berskala Enterprise ERP untuk sistem informasi akuntansi, manajemen persediaan, dan penjualan kasir usaha budidaya & distribusi **Ikan Bawal**. Dikembangkan menggunakan **Python**, **Tkinter**, dan **SQLite** dengan prinsip pembukuan berpasangan (*double-entry bookkeeping*) yang terhubung penuh secara real-time.

---

## 🚀 Cara Menjalankan Aplikasi

Aplikasi dapat dijalankan melalui berkas utama **`app.py`**.

### 1. Prasyarat Lingkungan
Pastikan Python 3.10+ telah terpasang di komputer Anda. Disarankan memasang library **Pillow** untuk rendering grafis, sudut membulat, dan ikon yang halus:
```powershell
pip install pillow
```
*(Catatan: Tanpa Pillow aplikasi tetap dapat berjalan normal menggunakan fallback grafis native Tkinter Canvas).*

### 2. Menjalankan Aplikasi
Buka terminal (PowerShell / Command Prompt) di direktori proyek ini:

* **Opsi A — Menjalankan dari folder `nexafish/`:**
  ```powershell
  cd nexafish
  python app.py
  ```

* **Opsi B — Menjalankan langsung dari root direktori proyek:**
  ```powershell
  python nexafish/app.py
  ```

Jendela antarmuka NEXAFISH Enterprise ERP akan terbuka di layar Anda.

---

## 🔐 Kredensial Akun untuk Login

Sistem menyediakan 2 tingkatan hak akses berbasis otentikasi SHA-256 tersimpan di database:

| Hak Akses | Username / Nama Akun | Kata Sandi (Password) | Cakupan Fitur & Hak Akses |
| :--- | :--- | :--- | :--- |
| **Owner** | `Owner` | **`owner999`** | **Akses Penuh:** Dashboard eksekutif, analisis tren arus kas keuangan Canvas, katalog stok & manajemen harga, kategori ukuran, kasir POS, jurnal umum kronologis, buku besar akun, 7 laporan keuangan komprehensif, master rekan bisnis (Customer/Supplier), pembelian stok, kas & kas kecil, bagan akun (COA), kebijakan usaha, audit trail, serta backup & restore database. |
| **Karyawan** | Bebas *(Contoh: Budi, Siti)* | **`kerja111`** | **Akses Operasional Kasir & Transaksi:** Point of sales (POS) penjualan ikan bawal, pencatatan pembelian stok harian, pencatatan kas operasional/kas kecil harian, riwayat penjualan pribadi, dan penggantian password staf kasir. |

*(Kata sandi dapat diperbarui sewaktu-waktu secara aman melalui menu **Pengaturan**).*

---

## 🎨 Karakteristik Tampilan & Design System ERP

Antarmuka didesain modern, elegan, dan profesional bergaya macOS/iOS enterprise software:
* **Sidebar Navy (`#0F2547`)**: Navigasi berkelompok (*Navigasi Utama*, *Keuangan & Akuntansi*, *Sistem & Kontrol*), status aktif beraksen garis biru cerah, badge peran pengguna, dan tombol logout dengan konfirmasi.
* **Topbar Bersih**: Judul halaman dinamis, deskripsi fungsi modul, penanggalan format Indonesia (`tanggal_indonesia`), serta chip status peran.
* **Kartu Membulat (Modern Card UI)**: Kontainer kartu putih bersudut membulat (`radius=14-18`) di atas latar abu kebiruan lembut (`#EEF2F8`), focus ring biru pada input teks, serta tombol solid/soft/outline.
* **Sadar-DPI (DPI-Aware)**: Teks dan elemen antarmuka tajam di berbagai resolusi layar (100%, 125%, 150%, 200%) melalui auto-scale Tkinter modern.
* **Tipografi Dinamis**: Pemilihan otomatis font keluarga modern: SF Pro Text → Segoe UI Variable → Segoe UI → Helvetica Neue.
* **Visualisasi Arus Kas**: Grafik batang interaktif Canvas (Kas Masuk vs Kas Keluar bulanan) dengan tooltip kustom saat di-hover dan perhitungan surplus arus kas rata-rata.
* **Tabel Modern**: Treeview bernuansa zebra halus, perataan angka kanan otomatis, auto-fit kolom, serta indikator teks merah untuk stok kritis di bawah batas aman.

---

## 📁 Struktur dan Fungsi Berkas Lengkap

```text
nexafish_ui_redesign_FIX/
├── nexafish.db                    # Database SQLite lokal (tersinkronisasi)
├── README.md                      # Dokumentasi teknis proyek
└── nexafish/
    ├── app.py                     # Entry point aplikasi (LoginScreen, MainFrame, App lifecycle)
    ├── database.py                # Backend engine akuntansi, transaksi atomik SQLite, skema tabel
    ├── base.py                    # Kelas dasar halaman (Halaman) penyedia self.db, self.user, self.coba()
    ├── widgets.py                 # Pustaka komponen UI ERP (Tombol, Isian, Kartu, Dialog, buat_tabel, dll)
    ├── theme.py                   # Design System, palet warna C, penskalaan DPI & tipografi
    ├── gfx.py                     # Helper grafis berbasis Pillow & Canvas (rounded corners, shadow, gradient)
    ├── sidebar.py                 # Komponen navigasi sidebar Dark Navy
    ├── utils.py                   # Utilitas format angka, rupiah(), penanggalan, hash SHA-256, path database
    ├── logo.png                   # Aset visual logo resmi NEXAFISH
    ├── nexafish.db                # Database SQLite lokal aktif
    ├── README.md                  # Dokumentasi teknis modul aplikasi
    └── pages/                     # Modul halaman UI antarmuka
        ├── __init__.py            # Export package seluruh modul halaman
        ├── dashboard.py           # Dashboard eksekutif, 9 KPI card, grafik arus kas, rekomendasi cerdas
        ├── stok.py                # Manajemen katalog produk, restock, penyesuaian susut, ubah harga
        ├── kategori.py            # Klasifikasi ukuran & standar bobot ikan bawal
        ├── kasir.py               # Point of Sales (POS), perhitungan ongkir, live double-entry preview
        ├── jurnal.py              # Buku jurnal umum kronologis & dialog jurnal manual seimbang
        ├── buku_besar.py          # Buku besar per akun (mutasi debit/kredit dan saldo berjalan)
        ├── laporan.py             # 7 tab laporan keuangan (Laba Rugi, Neraca, Arus Kas, Neraca Lajur, dll)
        ├── histori.py             # Audit trail aktivitas pengguna (siapa, apa, kapan)
        ├── operasional.py         # Master customer/supplier, pembelian, mutasi kas, COA, kebijakan bisnis
        └── pengaturan.py          # Keamanan kata sandi dan manajemen backup/restore database
```

---

## 🔗 Integrasi UI dengan Database (Database Information Flow)

Seluruh 10 modul halaman antarmuka (UI) terhubung secara langsung (*live connection*) ke database SQLite `nexafish.db` melalui objek `self.db` yang disediakan oleh `base.py (Halaman)`. Setiap halaman memanggil informasi dari database dan menampilkan datanya secara real-time:

| Halaman UI | Kelas Komponen | Tabel Database yang Diakses | Metode & Informasi yang Dipanggil dari Database |
| :--- | :--- | :--- | :--- |
| **Login** | `LoginScreen` | `akun_jabatan`, `profil_owner`, `histori_aktivitas` | Memvalidasi kata sandi (`verifikasi_login`), memeriksa profil Owner (`validasi_nama_owner`), dan mencatat histori percobaan login (`catat_histori`). |
| **Dashboard** | `DashboardPage` | `penjualan`, `pembelian`, `produk_bawal`, `jurnal`, `jurnal_detail`, `kebijakan`, `customer`, `supplier` | Memuat metrik ringkasan keuangan (`ringkasan`), ringkasan kasir staf (`ringkasan_karyawan`), grafik agregasi arus kas bulanan (`jurnal_detail`), serta analisis cerdas peringatan stok/piutang (`rekomendasi`). |
| **Stok & Produk** | `StokPage` | `produk_bawal`, `kategori_ukuran`, `jurnal`, `jurnal_detail` | Mengambil katalog produk berelasi (`daftar_produk`), daftar kategori filter (`daftar_kategori`), menambah produk (`tambah_produk`), restock kuantitas (`restock`), kurangi susut/mati (`kurangi_stok`), dan ubah harga (`ubah_harga_jual`). |
| **Kategori Ukuran** | `KategoriPage` | `kategori_ukuran`, `produk_bawal` | Menampilkan seluruh kategori beserta jumlah produk terkait (`daftar_kategori`), menambah (`tambah_kategori`), mengubah (`ubah_kategori`), dan menghapus dengan proteksi relasi (`hapus_kategori`). |
| **Kasir (POS)** | `KasirPage` | `produk_bawal`, `customer`, `akun`, `penjualan`, `jurnal`, `jurnal_detail`, `kebijakan` | Mengambil data stok produk real-time (`ambil_produk`), daftar pelanggan terdaftar (`daftar_pihak`), akun pendapatan (`daftar_akun`), menghitung ongkir otomatis (`ongkir_otomatis`), membukukan penjualan & jurnal double-entry otomatis (`jual`), serta riwayat transaksi (`riwayat_penjualan`). |
| **Jurnal Umum** | `JurnalPage` | `jurnal`, `jurnal_detail`, `akun` | Menampilkan buku jurnal kronologis (`daftar_jurnal`) dengan debit & kredit per baris, dialog input jurnal manual seimbang (`jurnal_manual`), serta jurnal penyesuaian (`jurnal_penyesuaian`). |
| **Buku Besar** | `BukuBesarPage` | `akun`, `jurnal`, `jurnal_detail` | Memuat daftar seluruh akun (`daftar_akun`), mutasi debit/kredit per rekening akun kronologis, serta kalkulasi saldo berjalan (`buku_besar`). |
| **Laporan Keuangan** | `LaporanPage` | `jurnal`, `jurnal_detail`, `akun` | Menyajikan 7 laporan akuntansi resmi terverifikasi: Neraca Saldo Sebelum Penyesuaian (`neraca_saldo(False)`), Neraca Saldo Sesudah Penyesuaian (`neraca_saldo(True)`), Laba Rugi (`laba_rugi`), Posisi Keuangan Aktiva-Pasiva (`posisi_keuangan`), Perubahan Modal (`laporan_perubahan_modal`), Arus Kas (`laporan_arus_kas`), dan Neraca Lajur 8 Kolom (`neraca_lajur`). |
| **Histori Aktivitas** | `HistoriPage` | `histori_aktivitas` | Menampilkan audit trail jejak aktivitas pengguna sistem secara terurut waktu terbaru (`daftar_histori`). |
| **Operasional** | `OperasionalPage` | `customer`, `supplier`, `pembelian`, `kas_kecil`, `pelunasan_pihak`, `akun`, `kebijakan`, `jurnal`, `jurnal_detail` | Manajemen rekan bisnis (`daftar_pihak`, `tambah_pihak`), pencatatan pembelian stok dengan ongkir (`pembelian_produk`), transaksi kas operasional & kas kecil (`catat_kas`), bagan akun COA (`daftar_akun`, `kelola_akun`, `hapus_akun`), konfigurasi tarif ongkir/denda/termin (`set_kebijakan`), dan riwayat jurnal penyesuaian. |
| **Pengaturan** | `PengaturanPage` | `akun_jabatan`, `histori_aktivitas`, seluruh tabel untuk backup | Penggantian kata sandi per jabatan (`ganti_password`), pembuatan salinan cadangan database SQLite (`backup_database`), serta pemulihan aman dengan backup snapshot otomatis (`pulihkan_database`). |

---

## 🗄️ Skema Database SQLite (`nexafish.db`)

Sistem menggunakan 16 tabel yang saling berelasi dengan integritas foreign key aktif (`PRAGMA foreign_keys = ON`):
1. **`akun_jabatan`**: Otorisasi kredensial kata sandi SHA-256 untuk jabatan Owner dan Karyawan.
2. **`profil_owner`**: Data profil identitas akun tunggal Owner.
3. **`histori_aktivitas`**: Catatan audit trail kronologis aktivitas seluruh pengguna.
4. **`kategori_ukuran`**: Master klasifikasi bobot dan ukuran ikan bawal (Benih, Kecil, Sedang, Besar, Jumbo).
5. **`produk_bawal`**: Katalog varian ikan bawal, id kategori, kuantitas stok (kg), harga pokok beli rata-rata, dan harga jual.
6. **`akun`**: Bagan Akun Standar (COA) dengan kode, nama akun, klasifikasi tipe (Aset, Kewajiban, Modal, Pendapatan, Beban), dan saldo normal.
7. **`jurnal`**: Header jurnal akuntansi berpasangan (tanggal, nomor transaksi, keterangan, referensi, user pembuat).
8. **`jurnal_detail`**: Rincian baris jurnal (id jurnal, kode akun, nilai debit, nilai kredit). Total debit selalu sama dengan total kredit.
9. **`penjualan`**: Rekam transaksi kasir POS (waktu, pembeli, produk, kuantitas kg, harga satuan, ongkir, total, metode tunai/piutang, kasir, jatuh tempo, id jurnal).
10. **`customer`**: Master data pelanggan/pembeli dengan nomor telepon, alamat, dan saldo awal piutang.
11. **`supplier`**: Master data pemasok/pembudidaya ikan dengan nomor telepon, alamat, dan saldo awal utang.
12. **`pembelian`**: Transaksi pengadaan stok ikan bawal dari supplier (kuantitas, harga beli, ongkir, total, tunai/kredit, jatuh tempo, id jurnal).
13. **`kebijakan`**: Parameter bisnis operasional (`ongkir_per_kg`, `denda_persen`, `termin_hari`).
14. **`kas_kecil`**: Rekam mutasi pengeluaran kas kecil (*petty cash*) untuk belanja operasional harian tambak/toko.
15. **`pelunasan_pihak`**: Rekam transaksi pelunasan piutang customer atau pembayaran utang supplier.
16. **`sqlite_sequence`**: Pengelola internal auto-increment primary key SQLite.

---

## 🛡️ Jaminan Integritas Akuntansi (Double-Entry Bookkeeping)

Aplikasi menerapkan aturan akuntansi ketat pada setiap mutasi data:
* **Keseimbangan Jurnal Mutlak**: Setiap transaksi penjualan, pembelian stok, biaya kas, setor modal, maupun penyesuaian selalu mencatat minimal 2 baris rekening dengan debit dan kredit yang sama persis.
* **Transaksi Atomik**: Seluruh proses multi-tabel dibungkus dalam blok transaksi database context-manager (`with self.transaksi():`). Jika terjadi kegagalan sistem di tengah proses, seluruh perubahan akan di-*rollback* secara otomatis.
* **Audit Trail Otomatis**: Setiap aksi penting (perubahan harga, restock, hapus data, penjualan kasir, ganti password) dicatat otomatis di tabel riwayat aktivitas.
* **Keseimbangan Laporan Neraca**: Total Aktiva (Aset) selalu terbukti seimbang dengan Total Pasiva (Kewajiban + Modal + Laba Periode Berjalan) hingga desimal terakhir (selisih `Rp 0`).

---

## 💡 Tips & Panduan Operasional

* **Pencarian Database Otomatis**: Berkas `utils.py` secara cerdas mendeteksi letak file database `nexafish.db`, baik saat aplikasi dijalankan dari folder `nexafish/` maupun dari direktori root proyek.
* **Menambah Stok**: Gunakan tombol **Restock** di menu *Stok & Produk* atau catat faktur pengadaan di menu *Operasional > Pembelian Stok*. Harga pokok pembelian akan dihitung otomatis menggunakan metode rata-rata tertimbang (*weighted average cost*).
* **Penjualan Kasir Cepat**: Di menu *Kasir*, masukkan kuantitas (kg), pilih pelanggan, dan pilih metode bayar. Pratinjau jurnal debit-kredit akan ditampilkan secara langsung sebelum Anda menekan tombol *Proses Transaksi*.
* **Backup Berkala**: Sebelum melakukan tutup buku atau pemulihan data, simpan cadangan database melalui menu *Pengaturan > Backup & Pemulihan Database*.
