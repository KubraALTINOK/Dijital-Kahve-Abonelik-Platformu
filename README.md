# KahveCell

KahveCell, kahve aboneliklerini, Ankara'daki kahve dükkânlarını ve QR kodla
teslim alınan siparişleri yöneten eğitim amaçlı bir web uygulamasıdır. Proje,
FastAPI ve SQLite kullanan bir backend ile React/TypeScript kullanan bağımsız
bir frontend'den oluşur.

> Bu proje bir eğitim/demo çalışmasıdır; gerçek ödeme veya SMS gönderimi
> yapmaz. Gerçek kart numarası veya üretim ortamında kullanılan gizli anahtarları
> girmeyin.

## Özellikler

- GSM numarası ve simüle OTP (`1234`) ile kayıt/giriş
- Müşteri, dükkân sahibi ve admin rolleri
- Abonelik paketleri ve sahte ödeme simülasyonu
- Dükkân arama, konum/mesafe sıralaması ve Leaflet haritası
- Sipariş özelleştirme, abonelik kredisi kontrolü ve imzalı QR kod
- Sipariş durum takibi ve sipariş geçmişi

## Teknolojiler

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite
- **Frontend:** React, TypeScript, Vite, React Router
- **Harita:** Leaflet, React-Leaflet, OpenStreetMap

## Gereksinimler

- Python 3.12 veya üzeri
- Node.js 20.19+ veya 22.12+
- npm

## Kurulum ve çalıştırma

Komutları iki ayrı terminal penceresinde çalıştırın.

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell'de sanal ortamı etkinleştirmek ve örnek ayar dosyasını
kopyalamak için:

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

`backend/.env` içindeki `KAHVECELL_JWT_SECRET` ve `KAHVECELL_QR_SECRET`
değerlerini, en az 32 karakter uzunluğunda birbirinden farklı rastgele
değerlerle doldurun. Güvenli bir değer üretmek için Python ile
`python -c "import secrets; print(secrets.token_urlsafe(48))"` komutunu
çalıştırabilirsiniz. `.env` dosyasını paylaşmayın veya Git'e eklemeyin.

Backend'i `backend` klasöründeyken başlatın:

```bash
python -m uvicorn app.main:app --reload
```

API ana sayfası `http://localhost:8000/`, Swagger arayüzü
`http://localhost:8000/docs` adresindedir. SQLite veritabanı ilk açılışta
`backend/kahvecell.db` dosyasında otomatik oluşturulur.

### 2. Örnek veriler

Backend terminalinde sanal ortam etkin ve geçerli klasör `backend` iken:

```bash
python seed_data.py
python seed_shop_owner.py
```

İlk komut Ankara'daki örnek dükkânları, menüleri, müşteri test hesabını ve
Starter aboneliğini ekler. İkinci komut CoffeeLab için dükkân sahibi test
hesabını hazırlar.

### 3. Frontend

Yeni bir terminal penceresinde:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Windows PowerShell'de `.env.example` kopyalama komutu:

```powershell
Copy-Item .env.example .env
```

Vite'ın gösterdiği adrese gidin; varsayılan adres `http://localhost:5173`.
Frontend API adresi `frontend/.env` içindeki `VITE_API_BASE_URL` ile
değiştirilebilir.

## Demo hesapları ve test kartları

| Rol | Telefon | OTP |
| --- | --- | --- |
| Müşteri (Starter abonelikli) | `+905550000001` | `1234` |
| CoffeeLab dükkân sahibi | `+905550000003` | `1234` |

Ödeme simülasyonundaki başarılı kart `4242424242424242`, başarısız kart
`4000000000000002`'dir. Bunlar yalnızca simülatör girdileridir; gerçek ödeme
bilgisi kullanmayın.

## Kontroller

Backend testleri (`backend` klasöründe ve sanal ortam açıkken):

```bash
python -m unittest discover -s tests -v
```

Frontend kontrolleri (`frontend` klasöründe):

```bash
npm run lint
npm run build
```

## Proje yapısı

```text
backend/
  app/                 FastAPI endpoint'leri, modeller, şemalar ve servisler
  tests/               Backend testleri
  seed_data.py         Ankara demo dükkân ve müşteri verileri
  seed_shop_owner.py   Dükkân sahibi demo hesabı
frontend/
  src/                 React sayfaları, bileşenler ve API istemcisi
  public/              Statik frontend dosyaları
```

## Güvenlik ve demo notları

- Sabit OTP, test hesapları ve test kartları yalnızca yerel geliştirme içindir.
- `.env`, SQLite veritabanı dosyaları, sanal ortamlar ve `node_modules` Git'e
  eklenmemelidir.
- Gizli anahtarları kaynak koda, dokümantasyona veya herkese açık depolara
  koymayın.
- Dükkân konumları demo amaçlıdır. Menü fiyatları ve diğer örnek içerikler
  canlı/veri doğrulaması yapılmış fiyat garantisi vermez.
