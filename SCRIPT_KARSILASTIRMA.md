# SatMagSim Script Karşılaştırması ve Son Sürüm Önerisi

## 1. Özet Tablo

| Özellik | SatMagSim_Base.py | SatMagSim.py | SatMagSim_Extended.py |
|--------|-------------------|--------------|------------------------|
| **Satır** | ~2585 | ~2651 | ~2991 |
| **Sınıf** | 6 | 6 | 7 |
| **Fonksiyon** | ~92 | ~93 | ~103 |
| **gmat.Clear() modül yüklemede** | Hayır | Evet | Hayır |
| **GMAT force model nerede** | Modül seviyesi (bir kez) | run_simulation() içinde (her çalıştırmada) | Modül seviyesi (bir kez) |
| **J_MATRIX** | Sadece köşegen | Tam (köşegen dışı terimler var) | Tam |
| **İmpulsif manevra (küresel/yerel)** | Hayır | Hayır | Evet |
| **GMAT script yükleme (LoadScript)** | Hayır | Hayır | Evet (sabit path) |
| **initial_Kepler.txt / dosyadan güncelleme** | Hayır | Hayır | Evet (sabit path) |
| **Koordinat seçimi (Local/Spherical)** | Hayır | Hayır | Evet |

---

## 2. Hangi Script En Doğru Çalışıyor?

**SatMagSim.py** mimari olarak en doğru tasarıma sahip:

- **GMAT her “Run/Calculate” için yeniden kuruluyor** (`run_simulation()` içinde `fm`, `earthgrav`, `pdprop`, `gator` vs. oluşturuluyor). Böylece:
  - Parametre değiştirip tekrar çalıştırdığınızda eski GMAT state’i kalmıyor.
  - Birden fazla simülasyon ardışık çalıştırma daha güvenilir.
- **gmat.Clear()** modül yüklenirken çağrılıyor; GMAT tarafı temiz başlıyor.
- **Tam J_MATRIX** (atalet matrisi köşegen dışı terimlerle) kullanılıyor; fiziksel model daha tam.

**SatMagSim_Base.py** ve **SatMagSim_Extended.py**’de GMAT force model **modül seviyesinde** bir kez kuruluyor. Bu da:

- İlk çalıştırmada doğru çalışır,
- Ama parametre değiştirip tekrar “Run” dediğinizde eski spacecraft/force model hâlâ kullanılabilir; davranış kafa karıştırıcı olabilir.

Bu yüzden **“en doğru çalışan”** olarak **SatMagSim.py** öne çıkıyor.

---

## 3. Hangi Script En Ayrıntılı?

**SatMagSim_Extended.py** en ayrıntılı ve en fazla özelliğe sahip:

- İmpulsif manevra (küresel: magnitude/azimuth/elevation; yerel: element1/2/3).
- Koordinat sistemi seçimi (Local / Spherical).
- GMAT script yükleme (`gmat.LoadScript`) ve thruster/ RocketTime ile entegrasyon.
- `initial_Kepler.txt` dosyasından Kepler elemanlarını okuyup `Constants.SATELLITE_PARAMS` ve GUI’yi güncelleme.
- Ek sınıf ve fonksiyon sayısı (7 sınıf, ~103 fonksiyon).

Ancak:

- **LoadScript** ve **initial_Kepler.txt** yolları sabit (GumushAerospace masaüstü). Sizin ortamınızda bu dosyalar yoksa bu kısımlar hata verir veya atlanmalıdır.
- Bu script “test” ve “maneuver” odaklı; hem ana simülasyon hem manevra testi için genişletilmiş bir sürüm gibi görünüyor.

Yani **“en ayrıntılı”** açısından **SatMagSim_Extended.py** önde, ama taşınabilirlik (path’ler) düzeltilmeden “ana ürün” gibi kullanmak riskli.

---

## 4. Son Sürüm Olarak Hangisi Seçilmeli?

Öneri:

- **Ana / son sürüm:** **SatMagSim.py**
  - GMAT’ı her çalıştırmada doğru şekilde kuruyor.
  - gmat.Clear() ile temiz başlangıç.
  - Tam J_MATRIX.
  - Harici dosya/path bağımlılığı yok; proje tek başına çalışır.

- **İsimlendirme:** Projede “main” ve “V2” denmesine rağmen, davranış ve mimari **SatMagSim.py** ile daha uyumlu. İsterseniz:
  - **SatMagSim.py**’i “son sürüm” ve ana giriş noktası kabul edebilirsiniz, veya
  - **SatMagSim_Base.py**’i koruyup, içindeki GMAT kurulumunu **SatMagSim.py**’deki gibi `run_simulation()` içine taşıyacak şekilde refactor edebilirsiniz (o zaman V2 hem isim hem mimari olarak “son sürüm” olur).

- **SatMagSim_Extended.py:** İmpulsif manevra ve dosyadan Kepler güncelleme gibi özellikler kalacaksa:
  - Path’leri (LoadScript, initial_Kepler.txt) proje dizinine veya ayarlanabilir yapıya çevirin.
  - Bu scripti “manevra testi / gelişmiş sürüm” olarak ayrı tutup, ana son sürüm olarak **SatMagSim.py** (veya refactor edilmiş Base) kullanın.

---

## 5. Test Önerisi

1. **SatMagSim.py** ile:
   - GUI’yi açın, bir kez “Calculate”/“Run” yapın.
   - Parametreleri değiştirip tekrar “Run” yapın; sonuçların yeni parametrelere göre değiştiğini kontrol edin.

2. **SatMagSim_Base.py** ile:
   - Aynı akışı tekrarlayın; özellikle parametre değiştirip ikinci “Run”da davranışın beklendiği gibi olup olmadığına bakın.

3. **SatMagSim_Extended.py** ile:
   - İmpulsif manevra ve koordinat seçimini deneyin.
   - LoadScript / initial_Kepler kullanacaksanız, path’leri kendi ortamınıza göre düzeltin veya dosyaları projeye kopyalayın.

Bu testlerden sonra “son sürüm”ü **SatMagSim.py** (veya refactor edilmiş Base) olarak sabitleyebilirsiniz; manevra ve ek özellikler için **SatMagSim_Extended.py** ayrı bir “gelişmiş/test” sürümü olarak kalabilir.
