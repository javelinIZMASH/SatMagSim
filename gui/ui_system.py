"""UI Design System — single source of truth for SpacecraftGUI (and future GUIs).

All layout uses only these constants. No arbitrary spacing numbers in UI code.
Mantık (simülasyon, thread, hesaplar) bu dosyaya bağlı değildir.
"""

# ─── 1) Spacing scale (tek kaynak) ───────────────────────────────────────────
SPACE_1 = 4
SPACE_2 = 8
SPACE_3 = 12
SPACE_4 = 16

# Rule: Use only SPACE_1..SPACE_4. No random numbers.

# ─── 2) Panel standard ───────────────────────────────────────────────────────
# Panel padding (inner content from border)
PAD = SPACE_3
# Sütunlar arası boşluk = sol kenar boşluğu (1. sütun solunda ne kadar varsa 2.ye geçmeden o kadar)
COL_GAP = PAD // 2
# Gap between rows inside a panel
ROW_GAP = SPACE_2
# Gap between sections (e.g. between two blocks in same column)
SECTION_GAP = SPACE_3
# Single border thickness and color for all panels
BORDER_WIDTH = 1
BORDER_COLOR = "white"
# Single panel background (left / middle / right columns same)
PANEL_BG = None  # None = use theme default; override to e.g. "#2B2B2B" if needed
# Canvas area (preview, map) background
CANVAS_BG = "#1a1a1a"

# ─── 3) Form row standard (universal) ───────────────────────────────────────
# Label column fixed minimum width (px)
LABEL_COL_MINSIZE = 160
# Controls column: weight=1, entries sticky="ew"
# Minimum entry width so it never collapses to 0
ENTRY_MIN_WIDTH = 90
# Sağ sütun Quaternion/Euler: input width küçük olsun, Preview butonu sığsın
RIGHT_COL_ENTRY_WIDTH = 65
# Sol/orta sütun: entry sütunu bu genişliği geçmesin (gereksiz boşluk kalmasın)
ENTRY_COL_MAX = 160
# Orta sütun 3’lü satırlar (torques, inertia, angular rate): kutu genişliği
MIDDLE_COL_ENTRY_WIDTH = 90
# Horizontal gap between label and controls
FORM_ROW_PADX = SPACE_2

# ─── 4) Section standard ───────────────────────────────────────────────────────
# Section header: same font (caller passes font), same vertical padding
SECTION_HEADER_PADY = (0, ROW_GAP)

# ─── 5) Action standard ───────────────────────────────────────────────────────
# Preview, Calculate, Run: always right-aligned
# Actions not on same row as inputs in a way that overlaps; on narrow screen
# actions can wrap to next line but alignment stays (e.g. right-aligned group)
ACTION_BUTTON_WIDTH = 100
ACTION_BUTTON_HEIGHT = 24
# Gap between action buttons
ACTION_GAP = SPACE_1

# ─── Bottom bar ───────────────────────────────────────────────────────────────
BOTTOM_BAR_ROW_HEIGHT = 44
BOTTOM_BAR_PAD_V = SPACE_2

# ─── Preview / third column: ekrana sığsın, altitude + harita görünsün ────────
PREVIEW_ROW_MINSIZE = 140
MAP_ROW_MINSIZE = 140
