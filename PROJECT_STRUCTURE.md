# SatMagSim Extended – Proje Yapısı

## Tek giriş noktası

Programı çalıştırmak için **yalnızca** proje kökündeki `main.py` (veya `SatMagSim_Extended.py`) kullanılır:

```bash
python main.py
```

Başka bir `main.py` yoktur. Her GUI paketi kendi ana penceresini `window.py` içinde tanımlar; bu dosyalar “uygulama main’i” değil, ilgili pencerenin sınıfını içerir.

## Dizin yapısı

```
satmagsim/
├── main.py                 # Tek giriş noktası
├── SatMagSim_Extended.py    # Alternatif giriş
├── config/
│   ├── constants.py        # Sabitler (Constants)
│   └── theme.py            # Tema, script_dir, roboto_prop
├── core/
│   ├── gmat_sim.py         # GMAT, satellites, data yapıları
│   └── satellite_simulator.py
├── gui/
│   ├── common.py           # Ortak: fontlar, renkler, pencere sabitleri
│   ├── __init__.py         # SpacecraftGUI, MagneticFieldGUI, ImpulsiveBurnGUI
│   ├── spacecraft_gui/    # Uzay aracı parametre penceresi
│   │   ├── window.py       # SpacecraftGUI sınıfı (paketin ana penceresi)
│   │   ├── _frames.py
│   │   ├── _figures.py
│   │   ├── _attitude.py
│   │   └── _simulation.py
│   ├── magnetic_field_gui/ # Manyetik alan görselleştirme
│   │   ├── window.py       # MagneticFieldGUI sınıfı
│   │   ├── _figures.py
│   │   ├── _layout.py
│   │   ├── _animations.py
│   │   └── _serial_esp32.py
│   └── impulsive_burn_gui.py
└── utils/
    └── quaternion.py
```

## Ortak kullanım (gui/common.py)

- **Fontlar:** Pencere `__init__` içinde `get_default_font()`, `get_default_font_small()`, `get_button_font()` çağrılır (root oluştuktan sonra).
- **Renkler:** `FIGURE_FACECOLOR`, `AXIS_GRID_COLOR`, `TEXT_COLOR` (grafik ve CTk).
- **Pencere:** `SPACECRAFT_WINDOW_*`, `MAGNETIC_WINDOW_*` (minsize, varsayılan boyut).

Hepsi tek yerde tanımlı; tüm GUI’ler tutarlı görünür.

## Pencere davranışı

- **Yeniden boyutlandırma:** Tüm ana pencereler `resizable(True, True)` ve uygun `minsize` ile açılır.
- **Responsive:** Grid weight’ler ile içerik alanları pencereyle büyür/küçülür.
