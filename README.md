# Lycian Fighters · Antalya HEMA web sitesi

Saf HTML + CSS + biraz vanilla JS. Framework yok, sunucu tarafı yok. `site/` klasörü olduğu gibi
herhangi bir statik barındırmaya yüklenebilir.

## Sayfalar

| URL | İçerik |
| --- | --- |
| `/` | Türkçe ana sayfa: kulüp, HEMA nedir, disiplinler, antrenman + harita, ansiklopedi, basın, SSS, iletişim |
| `/meyer-1570/` | Joachim Meyer 1570 uzun kılıç atlası (64 görsel) |
| `/liechtenauer/` | Liechtenauer atlası (138 çizim) |
| `/en/`, `/en/meyer-1570/`, `/en/liechtenauer/` | İngilizce karşılıkları |

## Klasörler

```
src/pages/home.tr.html, home.en.html   ana sayfa içerikleri (düz HTML, düzenlenebilir)
src/pages/faq.json                      SSS (sayfada ve Google yapılandırılmış verisinde kullanılır)
src/atlas/*.tr.html                     atlas içerikleri (orijinal Çizim Atlası dosyalarından)
src/atlas/*.en.txt                      atlasların İngilizce çevirisi (numara|metin)
src/assets/style.css, app.js            tasarım ve etkileşim
tools/build.py                          siteyi site/ klasörüne üretir
tools/extract.py, brand.py              tek seferlik: görselleri ve logoları üretti
site/                                   YAYINLANACAK KLASÖR
```

## Değişiklik yapınca

```bash
python tools/build.py
```

(Python 3 ve `pip install beautifulsoup4` gerekir.) Yerelde önizleme:

```bash
python -m http.server 8642 --bind 127.0.0.1 --directory site
```

Tarayıcıda http://localhost:8642 adresini açın (`http://[::]:8642` çalışmaz).

## Yayın

1. **Alan adı:** `https://antalyahema.com` (`tools/build.py` içindeki `SITE_URL`). Canonical, hreflang,
   sitemap ve paylaşım görselleri buna bağlı.
2. **Yayın:** GitHub Pages. `main` dalına her push'ta `.github/workflows/pages.yml` siteyi üretip yayınlar.
   DNS (Squarespace): `@` için A kayıtları 185.199.108.153 / .109.153 / .110.153 / .111.153,
   `www` için CNAME `candogan440.github.io`.

## Google'da "Antalya HEMA" için üst sıralar

Sitedeki teknik SEO hazır: başlık/açıklama, h1, iki dilli hreflang, sitemap, robots, Open Graph,
`SportsClub` + `FAQPage` + `Article` + `BreadcrumbList` yapılandırılmış verisi, hızlı statik sayfalar,
WebP görseller, mobil uyum. Sıralamayı asıl belirleyecek adımlar sizin tarafınızda:

1. **Google Search Console:** alan adını doğrulayın, `sitemap.xml` gönderin, ana sayfa için "Dizine eklenmesini iste".
2. **Google İşletme Profili:** "Lycian Fighters – Antalya HEMA" adıyla, 4x4 Sport Center adresi ve
   cumartesi 10:00 saatiyle açın; web sitesi olarak yeni alan adını girin. Yerel aramalarda (harita kutusu) en etkili adım budur.
3. **Geri bağlantılar:** Antalya Gündem'den haberlere site linki eklemelerini rica edin; Instagram biyografisine,
   Free Fighters Guild ve diğer HEMA kulüplerinin sitelerine link verin.
4. **Tutarlılık:** Ad, adres ve telefon (NAP) Instagram, Google İşletme ve sitede aynı yazılsın.
5. **Güncellik:** Turnuva, seminer ve etkinlikleri ana sayfaya ekleyip yeniden derleyin.
