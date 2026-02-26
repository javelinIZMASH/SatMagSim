# Üç Script Arasındaki Ortaklar, Farklılıklar, Artılar ve Eksiler

**Dosyalar:** `SatMagSim_Base.py`, `SatMagSim.py`, `SatMagSim_Extended.py`

**Rol ve isimlendirme:**

| Dosya | Rol |
|-------|-----|
| **SatMagSim_Base.py** | En sade temel sürüm (minimal özellik seti, köşegen J, modül-seviye GMAT) |
| **SatMagSim.py** | En dengeli fiziksel simülasyon (ana üretim sürümü; run_simulation içinde GMAT, tam J, seperation/deployment) |
| **SatMagSim_Extended.py** | En geniş kabiliyet seti (impulsif manevra, LoadScript, initial_Kepler, Local/Spherical) |

**Extended diğerlerinin yaptıklarını yapabiliyor mu?** Evet. SatMagSim_Extended.py, Base ve Core’un yaptığı ana simülasyonu (Kepler elemanları, manyetik alan, animasyon, deployment/separation, tam J_MATRIX) aynı şekilde yapabilir; buna ek olarak impulsif manevra, koordinat seçimi (Local/Spherical), GMAT script yükleme ve initial_Kepler.txt ile Kepler güncelleme gibi ek özelliklere sahiptir. Tek mimari fark: Core’da GMAT her “Run”da `run_simulation()` içinde yeniden kurulur (parametre değişince daha tutarlı); Extended’da GMAT modül yüklenirken bir kez kurulur (Base gibi).

---

## 1. Ortak Özellikler (Aynı Olanlar)

### 1.1 Importlar ve Bağımlılıklar
- **Aynı kütüphaneler:** `math`, `numpy`, `pymap3d`, `datetime`, `time`, `threading`, `matplotlib`, `serial`, `geopack`, `spacepy`, `scipy`, `cartopy`, `tkinter`, `customtkinter`, `PIL`, `ctypes`, `load_gmat`.
- **Font ve tema:** Üçünde de proje dizini öncelikli, yoksa Gumush fallback; logo yoksa atlanıyor.
- **Entry point:** Hepsi `if __name__ == "__main__":` → `app = SpacecraftGUI()` → `app.mainloop()`.

### 1.2 Constants Sınıfı (Ortak Alanlar)
- **Ortak sabitler:** `MU`, `TRUE_ANOMALIES`, `ALTITUDE`, `R_RADIUS`, `q`, `w`, `SATELLITE_PARAMS`, `T_PERIOD`, `DISTURBANCE_TORQUES`, `PROPORTIONAL_CONSTANT`, `J_MATRIX` (içerik farkı var, aşağıda), `W_NOISE_SCALE`, `BTOT_NOISE_SCALE`, `STEP`, `NUM_STEPS`, `INTERVAL_DELAY`, `W_NOISE`, `BTOT_NOISE`, `SPECIFIC_TIME_STR`, `SPECIFIC_TIME`, `T0`, `INITIAL_UT`, `CUBE_SIZE`, `CUBE_ORIGIN`, `RESOLUTION_SCALE`, `RESOLUTION`, `KP_IDX`, `CURRENT_TIME`.

### 1.3 Ana Sınıflar (İsim ve Rol)
- **SpacecraftGUI(CTk):** Ana pencere; Kepler elemanları, fiziksel özellikler, simülasyon parametreleri, quaternion/Euler, harita/3D/2D grafikler, Calculate/Run, progress bar.
- **Satellite:** GMAT `Spacecraft` sarmalayıcı; `setup_spacecraft`, `get_state`, `get_name`.
- **SatelliteSimulator:** Dinamik/kinematik entegrasyon; `w_and_q`, `integrate_w_and_q`, `calculate_magnetic_fields`.
- **MagneticFieldData:** Geodetic, manyetik, PV, dyn_kin veri tutucusu.
- **MagneticFieldGUI:** Manyetik alan ve animasyon penceresi; fig1/fig2/fig3, checkbox’lar, `update_gui`, `update_fig1/2/3`.

### 1.4 GMAT Kullanımı (Ortak Yapı)
- **Force model:** Earth gravity (EGM96 8x8), PointMass (Luna, Sun), Drag (JacchiaRoberts), SRP.
- **Propagator:** PrinceDormand78, `pdprop`, `gator`.
- **Spacecraft:** `create_satellite` / `Satellite` ile oluşturulup `pdprop.AddPropObject` ile eklenmesi.
- **PotentialFile:** Üçünde de `get_gmat_data_path("gravity", "earth", "EGM96.cof")` kullanılıyor.

### 1.5 GUI Bileşenleri (Ortak)
- Zaman/tarih, koordinat sistemi, Kepler elemanları, fiziksel/aerodinamik özellikler, uzay aracı sabitleri, simülasyon parametreleri (NUM_STEPS, STEP, INTERVAL_DELAY, RESOLUTION_SCALE), progress bar, Calculate/Start Animation/Run, harita + 3D + 2D grafikler, quaternion/Euler/altitude bölümleri, logo (varsa).

---

## 2. Farklılıklar (Script Bazında)

### 2.1 SatMagSim_Base.py

| Konu | Durum |
|------|--------|
| **Satır / sınıf / fonksiyon** | ~2585 satır, 6 sınıf, ~92 fonksiyon |
| **Import** | Ek olarak `gc` var |
| **gmat.Clear()** | Modül seviyesinde **yok** |
| **GMAT force model** | **Modül seviyesinde** bir kez kuruluyor (satellites, fm, pdprop, gator script yüklenirken oluşturuluyor) |
| **J_MATRIX** | **Sadece köşegen:** `diag(0.000826, 0.000425, 0.0012)`; tam matris yorum satırında |
| **Constants** | `SEPERATION_TIME`, `DEPLOYMENT_TIMER` **yok** |
| **Simülasyon parametreleri GUI** | Sadece NUM_STEPS, STEP, INTERVAL_DELAY, RESOLUTION_SCALE (seperation/deployment alanları yok) |
| **İmpulsif manevra** | Yok |
| **GMAT LoadScript / initial_Kepler** | Yok |
| **Ek sınıf** | Yok (6 sınıf) |

### 2.2 SatMagSim.py

| Konu | Durum |
|------|--------|
| **Satır / sınıf / fonksiyon** | ~2651 satır, 6 sınıf, ~93 fonksiyon |
| **Import** | `gc` yok |
| **gmat.Clear()** | Modül yüklenirken **var** (load_gmat’tan hemen sonra) |
| **GMAT force model** | **run_simulation() içinde** her “Run”da yeniden kuruluyor (fm, earthgrav, pdprop, gator vs. fonksiyon içinde) |
| **J_MATRIX** | **Tam matris** (köşegen dışı terimler: 0.000001, 0.0000000619, -0.000002); köşegen-only yorum satırında |
| **Constants** | **SEPERATION_TIME = 10**, **DEPLOYMENT_TIMER = 20** var |
| **Simülasyon parametreleri GUI** | NUM_STEPS, STEP, INTERVAL_DELAY, RESOLUTION_SCALE + **seperation**, **deployment** (default_values ve apply’da) |
| **İmpulsif manevra** | Yok |
| **GMAT LoadScript / initial_Kepler** | Yok |
| **Ek sınıf** | Yok (6 sınıf) |

### 2.3 SatMagSim_Extended.py

| Konu | Durum |
|------|--------|
| **Satır / sınıf / fonksiyon** | ~2991 satır, **7 sınıf**, ~103 fonksiyon |
| **Import** | Ek olarak `import customtkinter as ctk` (ComboBox vb. için) |
| **gmat.Clear()** | Modül seviyesinde **yok** |
| **GMAT force model** | **Modül seviyesinde** bir kez (V2 ile aynı mantık) |
| **J_MATRIX** | **Tam matris** (SatMagSim.py ile aynı) |
| **Constants** | SEPERATION_TIME, DEPLOYMENT_TIMER + **impulsive_spherical_params** (magnitude, azimuth, elevation) + **impulsive_local_params** (element1, element2, element3) |
| **Simülasyon parametreleri GUI** | SatMagSim.py ile aynı (seperation, deployment dahil) |
| **İmpulsif manevra** | **Var:** küresel (magnitude/azimuth/elevation) ve yerel (element1/2/3), ayrı pencere, Apply/Run |
| **GMAT LoadScript** | **Var:** `gmat.LoadScript("C:\\Users\\GumushAerospace\\Desktop\\GMAT\\api\\Ex_ForceModels_Full.script")` (sabit path) |
| **initial_Kepler.txt** | **Var:** `update_satellite_params_from_file()`; path: `C:\\Users\\GumushAerospace\\Desktop\\GMAT\\output\\initial_Kepler.txt` |
| **Koordinat seçimi** | **Local / Spherical** için **CTkComboBox** ile seçim ve entry’lerin buna göre güncellenmesi |
| **Ek sınıf** | **ImpulsiveBurnGUI** (7. sınıf): impulsif manevra penceresi, koordinat combo, Apply, Run, `impulsive_run_simulation` |

---

## 3. Karşılaştırma Tablosu (Özet)

| Özellik | Base | SatMagSim (Core) | Extended |
|---------|---------|-----------|----------------|
| Satır sayısı | ~2585 | ~2651 | ~2991 |
| Sınıf sayısı | 6 | 6 | 7 |
| gmat.Clear() | Hayır | Evet | Hayır |
| GMAT nerede kurulur | Modül | run_simulation() | Modül |
| J_MATRIX | Köşegen | Tam | Tam |
| SEPERATION_TIME / DEPLOYMENT_TIMER | Hayır | Evet | Evet |
| Seperation/Deployment GUI | Hayır | Evet | Evet |
| İmpulsif manevra | Hayır | Hayır | Evet |
| LoadScript / initial_Kepler | Hayır | Hayır | Evet (sabit path) |
| Koordinat combo (Local/Spherical) | Hayır | Hayır | Evet |
| ImpulsiveBurnGUI | Hayır | Hayır | Evet |
| customtkinter as ctk | Hayır | Hayır | Evet |
| gc import | Evet | Hayır | Hayır |

---

## 4. Artılar ve Eksiler (Script Bazında)

### 4.1 SatMagSim_Base.py

**Artıları**
- İsimde “main” ve “V2” geçiyor; tek “resmi” sürüm gibi kullanılabilir.
- Köşegen J_MATRIX ile hesaplar daha basit; bazı senaryolarda yeterli.
- `gc` importu ile bellek yönetimi bilinçli kullanılabilir.
- Modül seviyesinde GMAT kurulumu: ilk çalıştırma tek seferlik, kod yapısı sade.

**Eksileri**
- GMAT **modül seviyesinde** kurulduğu için parametre değiştirip tekrar Run’da eski state kalma riski; tekrarlanan simülasyonlarda tutarsızlık olabilir.
- SEPERATION_TIME / DEPLOYMENT_TIMER ve ilgili GUI alanları yok; deployment/separation senaryoları doğrudan yok.
- Tam atalet matrisi yok (köşegen dışı terimler yok).
- gmat.Clear() olmadığı için import sırasında GMAT state’i başka bir kullanıma göre kirli kalabilir.

---

### 4.2 SatMagSim.py

**Artıları**
- GMAT **her Run’da run_simulation() içinde** kurulduğu için parametre değişince sonuç tutarlı; tekrarlanan çalıştırmalar güvenilir.
- **gmat.Clear()** ile modül yüklenirken temiz başlangıç.
- **Tam J_MATRIX** (köşegen dışı terimlerle); fiziksel model daha tam.
- SEPERATION_TIME ve DEPLOYMENT_TIMER hem Constants’ta hem GUI’de; deployment/separation senaryoları destekleniyor.
- Harici GMAT script veya initial_Kepler path’ine bağımlılık yok; tek başına çalışır.

**Eksileri**
- Her Run’da GMAT’ı yeniden kurmak ilk çalıştırmada bir miktar daha yavaş olabilir (pratikte genelde kabul edilebilir).
- İmpulsif manevra, LoadScript, dosyadan Kepler güncelleme gibi gelişmiş özellikler yok.
- İsimde “V2” veya “main” geçmiyor; proje içinde “ana sürüm” olduğu açık değil.

---

### 4.3 SatMagSim_Extended.py

**Artıları**
- **En fazla özellik:** impulsif manevra (küresel + yerel), koordinat seçimi (Local/Spherical), GMAT script yükleme, initial_Kepler.txt ile Kepler güncelleme.
- En uzun ve en ayrıntılı script; 7 sınıf, ~103 fonksiyon.
- Tam J_MATRIX ve SEPERATION_TIME / DEPLOYMENT_TIMER mevcut.
- ImpulsiveBurnGUI ile manevra testi için ayrı, net bir arayüz.

**Eksileri**
- **LoadScript** ve **initial_Kepler.txt** path’leri sabit (GumushAerospace); farklı makinede veya proje dizininde çalışmaz, taşınabilir değil.
- GMAT yine **modül seviyesinde** kuruluyor; parametre değiştirip tekrar Run’da state tutarsızlığı riski (SatMagSim.py’deki gibi değil).
- gmat.Clear() yok.
- İsim “test” ve “maneuver” içerdiği için ana ürün sürümü gibi görünmeyebilir; daha çok test/gelişmiş sürüm izlenimi verir.

---

## 5. Özet Tablo: Artı / Eksi

| Kriter | Base | SatMagSim (Core) | Extended |
|--------|---------|-----------|----------------|
| GMAT her Run’da yeniden kurulum | Eksi | Artı | Eksi |
| gmat.Clear() | Eksi | Artı | Eksi |
| Tam J_MATRIX | Eksi | Artı | Artı |
| Seperation/Deployment sabitleri ve GUI | Eksi | Artı | Artı |
| İmpulsif manevra + ImpulsiveBurnGUI | Eksi | Eksi | Artı |
| GMAT script + initial_Kepler entegrasyonu | Eksi | Eksi | Artı (path’ler sabit: Eksi) |
| Taşınabilirlik (sabit path yok) | Artı | Artı | Eksi |
| Kod sadeği / bakım kolaylığı | Orta | Orta | Daha karmaşık |
| “Ana sürüm” / “son sürüm” isimlendirmesi | Artı (V2/main) | Eksi | Eksi (test) |

---

## 6. Sonuç ve Öneri

- **Ortaklar:** Aynı import seti, font/tema/logo mantığı, Constants’ın büyük kısmı, SpacecraftGUI / Satellite / SatelliteSimulator / MagneticFieldData / MagneticFieldGUI, GMAT force model bileşenleri ve PotentialFile kullanımı, temel GUI yapısı.
- **Temel farklar:** GMAT’ın nerede kurulduğu (modül vs run_simulation), J_MATRIX (köşegen vs tam), SEPERATION_TIME/DEPLOYMENT_TIMER varlığı, impulsif manevra ve LoadScript/initial_Kepler sadece test_maneuver’da.
- **Mimari açıdan en doğru:** **SatMagSim.py** (GMAT her Run’da, gmat.Clear(), tam J, seperation/deployment, harici path yok).
- **En özellikçe zengin ama kırılgan:** **SatMagSim_Extended.py** (path’ler düzeltilirse “gelişmiş/manevra” sürümü olarak kullanılabilir).
- **Son sürüm kararı:** İsterseniz ana sürümü **SatMagSim.py** kabul edip, V2’yi ya refactor (GMAT’ı run_simulation içine almak) ya da isimde “V2” olan alternatif sürüm olarak bırakabilirsiniz; test_maneuver’ı ise path’ler proje/ortama göre yapılandırılarak “manevra/test” sürümü olarak tutabilirsiniz.
