# Refactor Kuralları ve Planı — Code Wiki Uyumu

**Rol:** Kıdemli Python Yazılım Mimarı  
**Amaç:** Projeyi Code Wiki ve GitHub dokümantasyonuna uygun hale getirmek (mimari, sözleşmeler, dokümantasyon).  
**Kritik kısıt:** Simülasyon mantığı, veri yapıları (data_* dict’leri, MagneticFieldData alanları), GUI davranışı ve kullanıcıya görünen çıktılar **değişmeyecek**; refactor sonrası uygulama davranışı birebir aynı kalacak.

---

## 1. Proje Yapısı Özeti

```
satmagsim/
├── main.py                      # Tek giriş noktası
├── SatMagSim_Extended.py        # Alternatif giriş
├── load_gmat.py                 # GMAT API yükleme (GmatInstall, get_gmat_data_path)
│
├── config/
│   ├── constants.py             # Constants: orbit, inertia, time, noise
│   └── theme.py                 # setup_theme, script_dir, roboto_prop
│
├── core/
│   ├── gmat_sim.py              # GMAT spacecraft, force model, propagator, data yapıları
│   └── satellite_simulator.py   # SatelliteSimulator, MagneticFieldData
│
├── gui/
│   ├── __init__.py              # SpacecraftGUI, MagneticFieldGUI, ImpulsiveBurnGUI
│   ├── common.py                # Fontlar, renkler, pencere boyutları
│   ├── ui_system.py             # Layout sözleşmesi (spacing, panel, form)
│   ├── spacecraft_gui/          # Uzay aracı parametre penceresi
│   │   ├── window.py            # SpacecraftGUI
│   │   ├── _frames.py           # Paneller, section, bottom bar
│   │   ├── _figures.py          # Grafikler
│   │   ├── _attitude.py         # Attitude hesapları
│   │   └── _simulation.py       # run_simulation, start_gui, Apply
│   ├── magnetic_field_gui/      # Manyetik alan görselleştirme
│   │   ├── window.py            # MagneticFieldGUI
│   │   ├── _figures.py, _layout.py, _animations.py, _serial_esp32.py
│   └── impulsive_burn_gui.py    # Impulsive burn penceresi
│
├── utils/
│   └── quaternion.py            # q_to_DCM, euler_from_quaternion, get_quaternion_from_euler
│
└── docs/                        # Mimari ve sözleşme dokümantasyonu
    ├── ARCHITECTURE.md
    ├── CONFIG_CONTRACT.md
    ├── DATA_CONTRACT.md
    └── REFACTOR_RULES_AND_PLAN.md
```

**Veri akışı (kısaca):**  
`main.py` → theme → SpacecraftGUI → Run → `run_simulation` (GMAT + SatelliteSimulator) → dört dict doldurulur → Next → `MagneticFieldData(...)` → MagneticFieldGUI (harita, 3D küp, açısal hız, Btot).

---

## 2. Mimari Zayıflıklar (Dokümante; Değişiklik Opsiyonel)

### 2.1 Modül / paket yapısı

- **Legacy script’ler:** `SatMagSim_Base.py`, `SatMagSim.py`, `SatMagSim_Extended.py` kökte; tek önerilen giriş `main.py` (veya Extended). Diğerleri referans/karşılaştırma için kalabilir; hangisinin “ana” olduğu README’de netleştirildi.
- **GUI mixin’ler:** SpacecraftGUI ve MagneticFieldGUI mixin’lerle parçalı; sorumluluk sınırları `_frames`, `_figures`, `_simulation` içinde dokümante edilebilir.

### 2.2 Bağımlılık ve ortam

- **GMAT:** PyPI’da yok; `load_gmat.py` içinde `GmatInstall` kullanıcıya göre ayarlanmalı. README’de belirtildi.
- **requirements.txt:** Mevcut; sürüm aralıkları var. GMAT ayrı satırda “not PyPI” notu eklendi.

### 2.3 Dokümantasyon ve sözleşmeler

- **Code Wiki:** `docs/ARCHITECTURE.md`, `docs/CONFIG_CONTRACT.md`, `docs/DATA_CONTRACT.md` eklendi; README dokümantasyon indeksi olarak güncellendi.
- **Modül docstring’leri:** Birçok modülde kısa açıklama var; eksik olanlar ileride “ne yapar, hangi veriye dokunur” ile tamamlanabilir (davranış değişmeden).

### 2.4 UI ve tema

- **ui_system / common:** Tek kaynak kullanımı zaten var; sayılar ui_system’de. Tema yolu (dark-blue.json, Roboto) proje kökü + fallback; dokümante.
- **Pencere boyutları:** common’da SPACECRAFT_WINDOW_*, MAGNETIC_WINDOW_*; tutarlı.

### 2.5 Veri sözleşmeleri

- **data_* dict’leri:** `DATA_CONTRACT.md` ile şema dokümante edildi. Yeni alan eklenirse sözleşme güncellenmeli.
- **MagneticFieldData:** Constructor ve attribute’lar DATA_CONTRACT’ta; GUI’nin frame indeksi ile senkron kullanımı not edildi.

---

## 3. Refactor Planı (Sadece Dokümantasyon / İsteğe Bağlı Temizlik)

Aşağıdaki maddeler **davranışı değiştirmeyen** dokümantasyon ve isteğe bağlı düzenlemeler içindir.

### Faz 1 — Sözleşmeler ve dokümantasyon (tamamlandı)

1. **README.md** — Ana giriş: proje tanımı, çalıştırma, yapı, config, dokümantasyon tablosu, lisans notu.
2. **docs/ARCHITECTURE.md** — Amaç, bileşenler (core, gui, config), giriş noktaları, konvansiyonlar.
3. **docs/CONFIG_CONTRACT.md** — config.constants, config.theme, gui.ui_system, gui.common tabloları.
4. **docs/DATA_CONTRACT.md** — data_magnetic, data_dyn_kin, data_PV, data_geodetic ve MagneticFieldData şemaları.

### Faz 2 — İsteğe bağlı (kod dokunmadan)

5. **Modül docstring’leri** — Eksik paket/modüllere “ne yapar, hangi veriye dokunur” özeti; mevcut davranış aynı kalır.
6. **.gitignore** — `!README.md`, `!docs/**/*.md` ile dokümanların her zaman takip edilmesi.
7. **Legacy script açıklaması** — README veya docs’ta SatMagSim_Base / SatMagSim / Extended farkı kısaca açıklanabilir.

### Faz 3 — İleride (davranış korunarak)

8. **Loglama** — `print` yerine `logging` (mesaj metinleri aynı kalabilir).
9. **Büyük fonksiyonlar** — Parçalama sadece okunabilirlik için; çıktı ve sıra aynı kalmalı.
10. **Test** — Sadece yardımcı fonksiyonlar (utils.quaternion, config sabitleri) için birim testleri; simülasyon regression’ı yok.

---

## 4. Yapılmayacaklar (Kritik Kısıt)

- **Simülasyon mantığı:** GMAT propagasyonu, IGRF/T89, attitude (w, q) entegrasyonu, manyetik tork formülleri değişmeyecek.
- **Veri yapıları:** data_* dict’lerinin anahtarları ve liste elemanı formatları; MagneticFieldData attribute’ları ve birimleri (nT/1000, deg/s vb.) aynı kalacak.
- **GUI davranışı:** Pencere sırası (Spacecraft → Run → Next → MagneticField), grafik içerikleri ve senkron frame kullanımı korunacak.
- **GMAT parametreleri:** Force model, propagator ayarları, spacecraft alanları mevcut kodla uyumlu kalacak.

---

## 5. Sonraki adım

Bu belge **Faz 1** tamamlandıktan sonra güncellendi; **kodda değişiklik yapılmadı**. README ve docs/ dosyaları Code Wiki ve GitHub için tek referans noktasıdır. İleride Faz 2/3 maddeleri uygulanırken her adımda uygulama davranışı aynı kalacak şekilde ilerlenmelidir.
