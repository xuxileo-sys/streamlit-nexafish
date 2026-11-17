"""Helper grafis NEXAFISH berbasis Pillow: kotak membulat halus, bayangan, ikon vektor, batang gradasi.

Seluruh gambar digambar pada resolusi 4x lalu diperkecil (anti-aliasing) sehingga tepi terlihat halus.
Bila Pillow tidak terpasang, PIL_OK = False dan komponen UI otomatis memakai gambar Canvas biasa.
Modul ini hanya berisi tampilan; tidak menyentuh database maupun logika aplikasi.
"""

import math

try:
    from theme import px
except ImportError:  # struktur paket lama: ui/...
    from ui.theme import px

try:
    from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFilter, ImageTk
    PIL_OK = True
except ImportError:  # pragma: no cover
    PIL_OK = False

SS = 4  # faktor supersampling
_cache = {}


def _lanczos():
    return getattr(Image, "Resampling", Image).LANCZOS


def _rgb(warna):
    return ImageColor.getrgb(warna)


def _simpan(key, foto):
    # Widget selalu menyimpan referensi gambarnya sendiri, jadi cache aman dikosongkan berkala.
    if len(_cache) > 400:
        _cache.clear()
    _cache[key] = foto
    return foto


def _campur(c1, c2, t):
    a, b = _rgb(c1), _rgb(c2)
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ------------------------------------------------------------
#  Kotak membulat
# ------------------------------------------------------------
def kotak_bulat(w, h, r, fill, garis=None, tebal=1):
    """PhotoImage persegi membulat transparan di luar sudut (aman ditaruh di Canvas)."""
    w, h = max(int(w), 2), max(int(h), 2)
    key = ("kb", w, h, r, fill, garis, tebal)
    if key in _cache:
        return _cache[key]
    rr = max(min(r, w // 2, h // 2), 0) * SS
    dasar = _rgb(garis or fill) + (0,)
    besar = Image.new("RGBA", (w * SS, h * SS), dasar)
    d = ImageDraw.Draw(besar)
    if garis:
        d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), rr, fill=_rgb(garis) + (255,))
        t = tebal * SS
        d.rounded_rectangle((t, t, w * SS - 1 - t, h * SS - 1 - t), max(rr - t, 0),
                            fill=_rgb(fill) + (255,))
    else:
        d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), rr, fill=_rgb(fill) + (255,))
    return _simpan(key, ImageTk.PhotoImage(besar.resize((w, h), _lanczos())))


def kartu_bayangan(w, h, r, fill, garis=None, blur=14, dy=8, alpha=70, warna="#06122A"):
    """Kotak membulat dengan bayangan lembut. Mengembalikan (PhotoImage, pad); gambar lebih besar dari kotak."""
    w, h = max(int(w), 8), max(int(h), 8)
    key = ("kbs", w, h, r, fill, garis, blur, dy, alpha, warna)
    if key in _cache:
        return _cache[key]
    pad = blur * 2
    W, H = w + 2 * pad, h + 2 * pad + dy
    sh = Image.new("RGBA", (W, H), _rgb(warna) + (0,))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + dy, pad + w, pad + dy + h), r,
                                         fill=_rgb(warna) + (alpha,))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    besar = Image.new("RGBA", (w * SS, h * SS), _rgb(garis or fill) + (0,))
    d = ImageDraw.Draw(besar)
    rr = r * SS
    if garis:
        d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), rr, fill=_rgb(garis) + (255,))
        d.rounded_rectangle((SS, SS, w * SS - 1 - SS, h * SS - 1 - SS), max(rr - SS, 0),
                            fill=_rgb(fill) + (255,))
    else:
        d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), rr, fill=_rgb(fill) + (255,))
    kartu = besar.resize((w, h), _lanczos())
    sh.alpha_composite(kartu, (pad, pad))
    return _simpan(key, (ImageTk.PhotoImage(sh), pad))


def sudut(r, latar, isi, garis, bar=None, tebal=1, isi_atas=None):
    """Empat gambar sudut (kiri-atas, kanan-atas, kiri-bawah, kanan-bawah) berwarna solid.

    Dipasang di pojok Frame agar tepinya tampak membulat: area luar lengkungan berwarna latar halaman.
    bar=(warna_kiri, warna_kanan, tinggi) mewarnai pita aksen di dasar kartu pada dua sudut bawah."""
    key = ("sd", r, latar, isi, garis, bar, tebal, isi_atas)
    if key in _cache:
        return _cache[key]
    n = 2 * r * SS
    besar = Image.new("RGB", (n, n), _rgb(latar))
    d = ImageDraw.Draw(besar)
    d.rounded_rectangle((0, 0, n - 1, n - 1), r * SS, fill=_rgb(garis or isi))
    t = tebal * SS
    if garis:
        d.rounded_rectangle((t, t, n - 1 - t, n - 1 - t), max(r * SS - t, 0), fill=_rgb(isi))
    if isi_atas:
        atas = Image.new("RGB", (n, n), _rgb(latar))
        da = ImageDraw.Draw(atas)
        da.rounded_rectangle((0, 0, n - 1, n - 1), r * SS, fill=_rgb(garis or isi_atas))
        da.rounded_rectangle((t, t, n - 1 - t, n - 1 - t), max(r * SS - t, 0), fill=_rgb(isi_atas))
        besar.paste(atas.crop((0, 0, n, n // 2)), (0, 0))
    if bar:
        c1, c2, bh = bar
        dalam = Image.new("L", (n, n), 0)
        ImageDraw.Draw(dalam).rounded_rectangle((t, t, n - 1 - t, n - 1 - t), max(r * SS - t, 0), fill=255)
        pita = Image.new("L", (n, n), 0)
        ImageDraw.Draw(pita).rectangle((0, n - (bh + tebal) * SS, n, n - t - 1), fill=255)
        mask = ImageChops.multiply(dalam, pita)
        lapis = Image.new("RGB", (n, n), _rgb(c1))
        lapis.paste(Image.new("RGB", (n // 2, n), _rgb(c2)), (n // 2, 0))
        besar.paste(lapis, (0, 0), mask)
    img = besar.resize((2 * r, 2 * r), _lanczos())
    bagian = [img.crop(b) for b in ((0, 0, r, r), (r, 0, 2 * r, r), (0, r, r, 2 * r), (r, r, 2 * r, 2 * r))]
    return _simpan(key, [ImageTk.PhotoImage(b) for b in bagian])


def batang_gradasi(w, h, atas, bawah, r=5):
    """Batang grafik: gradasi vertikal, sudut atas membulat."""
    w, h = max(int(w), 2), max(int(h), 2)
    key = ("bg", w, h, atas, bawah, r)
    if key in _cache:
        return _cache[key]
    H = h * SS
    kolom = Image.new("RGB", (1, H))
    for y in range(H):
        kolom.putpixel((0, y), _campur(atas, bawah, y / max(H - 1, 1)))
    warna = kolom.resize((w * SS, H))
    rr = min(r, w // 2) * SS
    mask = Image.new("L", (w * SS, H + rr), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w * SS - 1, H + rr - 1), rr, fill=255)
    mask = mask.crop((0, 0, w * SS, H))
    warna = warna.convert("RGBA")
    warna.putalpha(mask)
    return _simpan(key, ImageTk.PhotoImage(warna.resize((w, h), _lanczos())))


# ------------------------------------------------------------
#  Ikon vektor (garis) pada kisi 24 x 24
# ------------------------------------------------------------
def _gambar_ikon(d, nama, s, col, tw):
    def P(x, y):
        return (x * s, y * s)

    def L(*pts):
        xy = [P(*p) for p in pts]
        d.line(xy, fill=col, width=int(tw), joint="curve")
        r = tw / 2
        for x, y in (xy[0], xy[-1]):
            d.ellipse((x - r, y - r, x + r, y + r), fill=col)

    def R(x1, y1, x2, y2, r=2):
        d.rounded_rectangle((x1 * s, y1 * s, x2 * s, y2 * s), r * s, outline=col, width=int(tw))

    def O(cx, cy, r):
        d.ellipse(((cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s), outline=col, width=int(tw))

    def dot(cx, cy, r=1.1):
        d.ellipse(((cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s), fill=col)

    def arc(x1, y1, x2, y2, a0, a1):
        d.arc((x1 * s, y1 * s, x2 * s, y2 * s), a0, a1, fill=col, width=int(tw))

    if nama == "dashboard":
        R(3, 3, 10.5, 10.5); R(13.5, 3, 21, 10.5); R(3, 13.5, 10.5, 21); R(13.5, 13.5, 21, 21)
    elif nama == "stok":
        R(3, 4, 21, 9, 1.5); R(4.5, 9, 19.5, 20.5, 2); L((10, 13.5), (14, 13.5))
    elif nama == "kategori":
        R(2.5, 7.5, 21.5, 16.5, 2); L((7, 7.5), (7, 11.5)); L((11, 7.5), (11, 10.5))
        L((15, 7.5), (15, 11.5)); L((19, 7.5), (19, 10.5))
    elif nama == "kasir":
        R(5, 3, 19, 9, 1.5); R(3, 9, 21, 21, 2.5)
        for cx in (8, 12, 16):
            for cy in (13.2, 17.2):
                dot(cx, cy, 1)
    elif nama == "jurnal":
        L((12, 6.5), (8, 4.5), (3, 4.5), (3, 18.5), (8, 18.5), (12, 20.5), (12, 6.5))
        L((12, 6.5), (16, 4.5), (21, 4.5), (21, 18.5), (16, 18.5), (12, 20.5))
    elif nama == "buku":
        R(4.5, 3, 19.5, 21, 2.5); L((8.5, 8), (15.5, 8)); L((8.5, 12), (15.5, 12)); L((8.5, 16), (12.5, 16))
    elif nama == "laporan":
        R(3, 3, 21, 21, 3.5); L((8, 17), (8, 12.5)); L((12, 17), (12, 8)); L((16, 17), (16, 13.5))
    elif nama == "histori":
        O(12, 12, 9); L((12, 7), (12, 12), (15.5, 14))
    elif nama == "operasional":
        L((4, 8), (19.5, 8)); L((15.5, 4), (19.5, 8), (15.5, 12))
        L((20, 16), (4.5, 16)); L((8.5, 12), (4.5, 16), (8.5, 20))
    elif nama == "pengaturan":
        O(12, 12, 3.2); O(12, 12, 7.6)
        for i in range(8):
            a = math.radians(i * 45)
            L((12 + 7.6 * math.cos(a), 12 + 7.6 * math.sin(a)), (12 + 10 * math.cos(a), 12 + 10 * math.sin(a)))
    elif nama == "dompet":
        R(3, 5.5, 21, 19.5, 3); R(14, 10.5, 21, 14.5, 2); dot(17, 12.5, 0.9)
    elif nama == "tag":
        L((3.5, 3.5), (12, 3.5), (21, 12.5), (12.5, 21), (3.5, 12), (3.5, 3.5)); dot(8, 8, 1.4)
    elif nama == "tas":
        R(4, 8, 20, 21, 2.5); arc(8, 2.5, 16, 12.5, 180, 360)
    elif nama == "grafik":
        L((3, 17), (9, 11), (13, 15), (21, 6.5)); L((15, 6.5), (21, 6.5), (21, 12.5))
    elif nama == "kotak":
        L((12, 3), (20.5, 7.5), (20.5, 16.5), (12, 21), (3.5, 16.5), (3.5, 7.5), (12, 3))
        L((3.5, 7.5), (12, 12), (20.5, 7.5)); L((12, 12), (12, 21))
    elif nama == "struk":
        L((6, 3), (18, 3), (18, 21), (15, 19), (12, 21), (9, 19), (6, 21), (6, 3))
        L((9.5, 8), (14.5, 8)); L((9.5, 12), (14.5, 12))
    elif nama == "nota":
        R(5, 4.5, 19, 21, 2.5); R(9, 2.5, 15, 6.5, 1.5); L((9, 11), (15, 11)); L((9, 15.5), (13, 15.5))
    elif nama == "ikan":
        O(10.5, 12, 6.5); L((16.5, 12), (21.5, 7.5), (21.5, 16.5), (16.5, 12)); dot(7.5, 10.8, 1)
    elif nama == "bohlam":
        arc(5, 3, 19, 17, 140, 40 + 360); L((9.5, 18.5), (14.5, 18.5)); L((10.5, 21.5), (13.5, 21.5))
        L((9.8, 14.5), (9.8, 17.5)); L((14.2, 14.5), (14.2, 17.5))
    elif nama == "kalender":
        R(3, 5, 21, 21, 3); L((3, 10), (21, 10)); L((8, 3), (8, 7)); L((16, 3), (16, 7))
    elif nama == "jam":
        O(12, 12, 9); L((12, 7), (12, 12), (15.5, 14))
    elif nama == "segarkan":
        arc(4.5, 4.5, 19.5, 19.5, 40, 335); L((19.5, 3.5), (19.5, 8.5), (14.5, 8.5))
    elif nama == "keluar":
        L((10, 4), (5, 4), (5, 20), (10, 20)); L((10, 12), (20, 12)); L((16.5, 8), (20.5, 12), (16.5, 16))
    elif nama == "user":
        O(12, 8, 4); arc(4.5, 14, 19.5, 30, 180, 360)
    elif nama == "cek":
        L((5, 12.5), (10, 17.5), (19, 7))
    elif nama == "silang":
        L((6, 6), (18, 18)); L((18, 6), (6, 18))
    elif nama == "seru":
        L((12, 6), (12, 13)); dot(12, 17.5, 1.3)
    elif nama == "peringatan":
        L((12, 3.5), (21.5, 20), (2.5, 20), (12, 3.5)); L((12, 9.5), (12, 14)); dot(12, 17, 0.9)
    elif nama == "unduh":
        L((12, 4), (12, 15)); L((7, 10.5), (12, 15.5), (17, 10.5)); L((4, 20), (20, 20))
    elif nama == "cari":
        O(10.5, 10.5, 6.5); L((15.5, 15.5), (21, 21))
    elif nama == "perisai":
        L((12, 3), (20, 6), (20, 12), (12, 21), (4, 12), (4, 6), (12, 3)); L((8.5, 12), (11, 14.5), (15.5, 9.5))
    elif nama == "chevron":
        L((6, 9), (12, 15), (18, 9))
    elif nama == "analitik":
        L((3, 17), (8, 11.5), (12, 15), (17, 8)); O(18, 7, 2.2)
        L((3, 21), (21, 21))
    else:
        return False
    return True


def ikon(nama, ukuran=20, warna="#FFFFFF", tebal=1.9):
    """PhotoImage ikon garis; `ukuran` adalah ukuran desain (diskalakan otomatis ke piksel fisik)."""
    if not PIL_OK:
        return None
    ukuran = px(ukuran)
    key = ("ik", nama, ukuran, warna, tebal)
    if key in _cache:
        return _cache[key]
    n = ukuran * SS
    img = Image.new("RGBA", (n, n), _rgb(warna) + (0,))
    d = ImageDraw.Draw(img)
    if not _gambar_ikon(d, nama, n / 24.0, _rgb(warna) + (255,), tebal * n / 24.0):
        return None
    return _simpan(key, ImageTk.PhotoImage(img.resize((ukuran, ukuran), _lanczos())))
