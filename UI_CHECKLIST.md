# SpacecraftGUI — UI Sözleşmesi Checklist

## Teslim edilenler

1. **UI sözleşmesi (design system)**  
   `gui/ui_system.py` — spacing, panel, form row, section, action sabitleri.

2. **SpacecraftGUI sadece UI düzeni değişti**  
   - `gui/spacecraft_gui/window.py` — grid padding ve third_content row config ui_system ile.
   - `gui/spacecraft_gui/_frames.py` — tüm paneller ve form satırları ui_system ile (PAD, ROW_GAP, SECTION_GAP, LABEL_COL_MINSIZE, ENTRY_MIN_WIDTH, CANVAS_BG, BORDER_*).
   - `gui/spacecraft_gui/_figures.py` — canvas grid padding PAD/ROW_GAP.
   - `gui/common.py` — UI_SPACING / UI_PAD_SMALL artık ui_system’den (SPACE_2, SPACE_1).

3. **Preview flicker fix korundu**  
   - `window.py`: `_on_third_frame_configure`, `_sync_third_content_width` (debounce 150 ms, 2 px eşik).
   - `_figures.py`: `_on_preview_canvas_configure`, `_do_preview_canvas_resize` (aynı debounce ve 2 px eşik).

---

## Ekran görüntüsü talimatları

Uygulamayı çalıştırın:

```bash
python main.py
```

Şu 3 ekran görüntüsünü alın:

| Görüntü    | Açıklama |
|-----------|----------|
| **Normal** | Varsayılan pencere boyutu (örn. 1500×800). |
| **Dar**    | Pencereyi daraltın (min width 1160’a yakın). |
| **Geniş**  | Pencereyi genişletin (örn. tam ekran). |

Kaydedin: `screenshot_normal.png`, `screenshot_narrow.png`, `screenshot_wide.png` (veya projede belirttiğiniz isimler).

---

## Checklist — PASS / FAIL

Aşağıdakileri kontrol edin; geçiyorsa PASS, geçmiyorsa FAIL yazın.

| # | Soru | PASS/FAIL |
|---|------|-----------|
| 1 | Tüm sütunlarda spacing aynı mı? (sol / orta / sağ panel padding ve section araları) | |
| 2 | Input yükseklik / kenar yuvarlaklık aynı mı? (entry’ler aynı boyut) | |
| 3 | Preview butonu her boyutta görünüyor mu? | |
| 4 | Quaternion / Euler entry’leri kaybolmuyor mu? (dar ekranda da görünür) | |
| 5 | Garip arka plan katmanı var mı? (sağ sütunda tek panel rengi, ekstra frame yok) | |

---

## Sağ sütun bölümleri (referans)

- **Section A** — Preview (3D) / Normalized Vectors → tek canvas (siyah, border).
- **Section B** — Attitude: Quaternion (q1–q4) + Preview + checkbox; Euler (roll, pitch, yaw) + checkbox.
- **Section C** — Field / Map canvas (siyah, border).
- **Section D** — Altitude + Calculate (Calculate sağda).

Alt bar: Progress solda; sağda tek satır Deploy / Next / Cancel / Apply / Run.
