"""Modern Tkinter Desktop GUI for Image Compression and Decompression."""
from __future__ import annotations

import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from PIL import Image, ImageTk

from src.my_app.config import (
    ALL_MODES,
    COMPRESSED_EXTENSIONS,
    DEFAULT_COMPRESSED_EXT,
    DEFAULT_TEXT_EXT,
    IMAGE_EXTENSIONS,
    IMAGES_DIR,
    MODE_BIN_LOSSLESS,
    MODE_BIN_SMART,
    MODE_DELTA,
    MODE_PATTERN,
    MODE_HEX,
    MODE_PALETTE,
    MODE_RAW,
    MODE_RLE,
    OUTPUT_DIR,
    TEXT_EXTENSIONS,
)
from src.my_app.core.pixel_coder import PixelCoder

# Color Palette (Catppuccin Mocha inspired dark theme)
BG_DARK = "#181825"
BG_PANEL = "#1e1e2e"
BG_CARD = "#2a2b3d"
BG_INPUT = "#313244"
FG_MAIN = "#cdd6f4"
FG_MUTED = "#a6adc8"
FG_SUBTLE = "#6c7086"
ACCENT_BLUE = "#89b4fa"
ACCENT_GREEN = "#a6e3a1"
ACCENT_YELLOW = "#f9e2af"
ACCENT_RED = "#f38ba8"
ACCENT_PURPLE = "#cba6f7"
BORDER_COLOR = "#45475a"


class ImageCompressorApp(tk.Tk):
    """Main Tkinter GUI Application for Image Compression and Decompression."""

    def __init__(self):
        super().__init__()

        self.title("PixelScan Image Compressor & Decompressor")
        self.geometry("1080x840")
        self.minsize(980, 740)
        self.configure(bg=BG_DARK)

        # State variables
        self.compress_image_path: Optional[Path] = None
        self.compress_image_obj: Optional[Image.Image] = None
        self.generated_pixel_str: Optional[str] = None
        self.compression_stats: Optional[dict] = None
        self.compressed_bytes: Optional[bytes] = None
        self.last_saved_icomp_path: Optional[Path] = None

        self.decompress_file_path: Optional[Path] = None
        self.reconstructed_image_obj: Optional[Image.Image] = None
        self.decompression_stats: Optional[dict] = None

        # Mode variable (Default to real-life Binary Smart mode for genuine small files)
        self.string_mode_var = tk.StringVar(value=MODE_BIN_SMART)

        # Quality variable (100 = Lossless, 85 = High Quality, 65 = Max Compression)
        self.quality_var = tk.IntVar(value=100)

        # JPEG Export Quality (User selectable: 95 = High Quality, 75 = Standard, 60 = Compact)
        self.jpeg_export_quality_var = tk.IntVar(value=95)

        self._setup_styles()
        self._build_ui()

        # Check if default test image exists and pre-load it for convenience
        default_test_img = IMAGES_DIR / "ICtest.jpeg"
        if default_test_img.exists():
            self._load_compress_image(default_test_img)

    def _setup_styles(self):
        """Configures ttk styles for the modern dark theme."""
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(".", background=BG_DARK, foreground=FG_MAIN, font=("Segoe UI", 10))
        style.configure("TFrame", background=BG_DARK)
        style.configure("Panel.TFrame", background=BG_PANEL)
        style.configure("Card.TFrame", background=BG_CARD)

        # Notebook (Tabs)
        style.configure(
            "TNotebook",
            background=BG_DARK,
            borderwidth=0,
            tabmargins=[10, 10, 10, 0]
        )
        style.configure(
            "TNotebook.Tab",
            background=BG_PANEL,
            foreground=FG_MUTED,
            padding=[20, 10],
            font=("Segoe UI", 11, "bold"),
            borderwidth=0
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", BG_CARD)],
            foreground=[("selected", ACCENT_BLUE)]
        )

        # Buttons
        style.configure(
            "Primary.TButton",
            background=ACCENT_BLUE,
            foreground="#11111b",
            font=("Segoe UI", 10, "bold"),
            padding=[14, 8],
            borderwidth=0
        )
        style.map("Primary.TButton", background=[("active", "#b4befe")])

        style.configure(
            "Success.TButton",
            background=ACCENT_GREEN,
            foreground="#11111b",
            font=("Segoe UI", 10, "bold"),
            padding=[14, 8],
            borderwidth=0
        )
        style.map("Success.TButton", background=[("active", "#94e2d5")])

        style.configure(
            "Secondary.TButton",
            background=BG_INPUT,
            foreground=FG_MAIN,
            font=("Segoe UI", 9),
            padding=[10, 6],
            borderwidth=0
        )
        style.map("Secondary.TButton", background=[("active", BORDER_COLOR)])

        # Radio buttons
        style.configure(
            "TRadiobutton",
            background=BG_INPUT,
            foreground=FG_MAIN,
            font=("Segoe UI", 9)
        )
        style.map(
            "TRadiobutton",
            background=[("active", BG_INPUT)],
            foreground=[("selected", ACCENT_BLUE)]
        )

        # Progressbar
        style.configure(
            "TProgressbar",
            troughcolor=BG_INPUT,
            background=ACCENT_BLUE,
            thickness=6
        )

        # Scrollbars
        style.configure(
            "Vertical.TScrollbar",
            background=BG_INPUT,
            troughcolor=BG_DARK,
            bordercolor=BG_DARK,
            arrowcolor=FG_MUTED,
            relief="flat"
        )

    def _build_ui(self):
        """Constructs the complete application UI."""
        # Top Header Bar
        header = tk.Frame(self, bg=BG_PANEL, height=65)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        title_label = tk.Label(
            header,
            text="⚡ PixelScan Image Compressor & Decompressor",
            font=("Segoe UI", 16, "bold"),
            bg=BG_PANEL,
            fg=ACCENT_BLUE
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)

        subtitle_label = tk.Label(
            header,
            text="Row/Column Pixel Scanning • Auto-Save to Output • 5 Algorithms",
            font=("Segoe UI", 9),
            bg=BG_PANEL,
            fg=FG_MUTED
        )
        subtitle_label.pack(side=tk.RIGHT, padx=20, pady=15)

        # Notebook Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=8)

        # Tab 1: Compress
        self.compress_tab = ttk.Frame(self.notebook, style="Panel.TFrame")
        self.notebook.add(self.compress_tab, text="  🗜️  Compress Image  ")
        self._build_compress_tab()

        # Tab 2: Decompress
        self.decompress_tab = ttk.Frame(self.notebook, style="Panel.TFrame")
        self.notebook.add(self.decompress_tab, text="  🔓  Decompress Image  ")
        self._build_decompress_tab()

        # Tab 3: Lossless Verifier
        self.verifier_tab = ttk.Frame(self.notebook, style="Panel.TFrame")
        self.notebook.add(self.verifier_tab, text="  🔍  Lossless Verifier  ")
        self._build_verifier_tab()

        # Status Bar
        self.status_bar = tk.Label(
            self,
            text="Ready. Load an image to begin.",
            font=("Segoe UI", 9),
            bg="#11111b",
            fg=FG_MUTED,
            anchor="w",
            padx=15,
            pady=4
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    # -------------------------------------------------------------------------
    # TAB 1: COMPRESS
    # -------------------------------------------------------------------------
    def _build_compress_tab(self):
        pane = tk.PanedWindow(self.compress_tab, orient=tk.HORIZONTAL, bg=BG_DARK, sashwidth=6)
        pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # Left Column: Image Selection & Preview
        left_frame = tk.Frame(pane, bg=BG_CARD, padx=15, pady=12)
        pane.add(left_frame, minsize=370)

        lbl_step1 = tk.Label(left_frame, text="Step 1: Select Input Image", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=ACCENT_BLUE)
        lbl_step1.pack(anchor="w")

        btn_browse = ttk.Button(left_frame, text="📂 Browse Image...", style="Secondary.TButton", command=self._browse_compress_image)
        btn_browse.pack(fill=tk.X, pady=(8, 4))

        self.lbl_comp_file_path = tk.Label(left_frame, text="No image selected", font=("Segoe UI", 9), bg=BG_CARD, fg=FG_MUTED, wraplength=340, justify="left")
        self.lbl_comp_file_path.pack(anchor="w", pady=(0, 8))

        # Canvas for Image Preview
        self.comp_preview_canvas = tk.Canvas(left_frame, bg=BG_INPUT, width=310, height=310, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.comp_preview_canvas.pack(pady=4)
        self.comp_preview_canvas.create_text(155, 155, text="Image Preview", fill=FG_SUBTLE, font=("Segoe UI", 11))

        self.lbl_comp_dims = tk.Label(left_frame, text="Dimensions: - | Size: - | Mode: -", font=("Segoe UI", 9), bg=BG_CARD, fg=FG_MAIN)
        self.lbl_comp_dims.pack(pady=4)

        # Open Output Folder Button on Left
        btn_open_out = ttk.Button(left_frame, text="📁 Open Output Folder", style="Secondary.TButton", command=self._open_output_folder)
        btn_open_out.pack(fill=tk.X, pady=(10, 0))

        # Right Column: Scrollable Container for Configuration, Scan & Actions
        right_container = tk.Frame(pane, bg=BG_CARD)
        pane.add(right_container, minsize=540)

        right_canvas = tk.Canvas(right_container, bg=BG_CARD, highlightthickness=0)
        right_scrollbar = ttk.Scrollbar(right_container, orient="vertical", command=right_canvas.yview)
        right_canvas.configure(yscrollcommand=right_scrollbar.set)

        right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = tk.Frame(right_canvas, bg=BG_CARD, padx=15, pady=12)
        right_canvas_win = right_canvas.create_window((0, 0), window=right_frame, anchor="nw")

        def _configure_right_frame(event):
            right_canvas.configure(scrollregion=right_canvas.bbox("all"))

        def _configure_right_canvas(event):
            right_canvas.itemconfig(right_canvas_win, width=event.width)

        right_frame.bind("<Configure>", _configure_right_frame)
        right_canvas.bind("<Configure>", _configure_right_canvas)

        def _on_compress_mousewheel(event):
            right_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        right_container.bind("<Enter>", lambda e: right_canvas.bind_all("<MouseWheel>", _on_compress_mousewheel))
        right_container.bind("<Leave>", lambda e: right_canvas.unbind_all("<MouseWheel>"))

        # Step 2: Serialization Mode Options
        lbl_step2 = tk.Label(right_frame, text="Step 2: Choose Compression Algorithm", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=ACCENT_BLUE)
        lbl_step2.pack(anchor="w")

        mode_frame = tk.Frame(right_frame, bg=BG_INPUT, padx=10, pady=6, highlightthickness=1, highlightbackground=BORDER_COLOR)
        mode_frame.pack(fill=tk.X, pady=(4, 8))

        # --- Real-Life Binary Section ---
        lbl_bin_hdr = tk.Label(mode_frame, text="🚀 REAL-LIFE BINARY ENGINE (NO TEXT BLOAT — SMALLEST FILES):", font=("Segoe UI", 8, "bold"), bg=BG_INPUT, fg=ACCENT_GREEN)
        lbl_bin_hdr.pack(anchor="w", pady=(2, 1))

        rb_bin_smart = ttk.Radiobutton(
            mode_frame,
            text="🚀 Real-Life Binary Smart Mode (Smallest! ~11-20 KB, Beats JPEG!)\n   Uses real frequency quantization directly in binary. Bypasses text strings completely.",
            value=MODE_BIN_SMART,
            variable=self.string_mode_var
        )
        rb_bin_smart.pack(anchor="w", pady=2)

        rb_bin_lossless = ttk.Radiobutton(
            mode_frame,
            text="🛡️ Real-Life Binary Lossless Mode (No text bloat, 100% exact pixels: ~174 KB)\n   Encodes raw bytes directly with 2D DPCM prediction. Zero text inflation.",
            value=MODE_BIN_LOSSLESS,
            variable=self.string_mode_var
        )
        rb_bin_lossless.pack(anchor="w", pady=2)

        # --- Text String Section ---
        lbl_txt_hdr = tk.Label(mode_frame, text="📝 TEXT-BASED STRING ENGINES (HUMAN-READABLE STRINGS):", font=("Segoe UI", 8, "bold"), bg=BG_INPUT, fg=ACCENT_BLUE)
        lbl_txt_hdr.pack(anchor="w", pady=(6, 1))

        # 1. DELTA
        rb_delta = ttk.Radiobutton(
            mode_frame,
            text="⚡ Delta-RLE String Mode — Stores pixel differences (dr,dg,db)",
            value=MODE_DELTA,
            variable=self.string_mode_var
        )
        rb_delta.pack(anchor="w", pady=1)

        # 2. PATTERN (User Idea)
        rb_pattern = ttk.Radiobutton(
            mode_frame,
            text="🧩 Pattern Deduplication Mode (Your Idea!) — Saves repeated patterns once, places on decompress",
            value=MODE_PATTERN,
            variable=self.string_mode_var
        )
        rb_pattern.pack(anchor="w", pady=1)

        # 3. PALETTE
        rb_palette = ttk.Radiobutton(
            mode_frame,
            text="🎨 Palette String Mode — Unique color index table (0,1,0,2)",
            value=MODE_PALETTE,
            variable=self.string_mode_var
        )
        rb_palette.pack(anchor="w", pady=1)

        # 4. HEX
        rb_hex = ttk.Radiobutton(
            mode_frame,
            text="🔢 HEX String Mode — 6-char hex (1B1725), removes all commas",
            value=MODE_HEX,
            variable=self.string_mode_var
        )
        rb_hex.pack(anchor="w", pady=1)

        # 5. RLE
        rb_rle = ttk.Radiobutton(
            mode_frame,
            text="🟢 Standard RGB RLE Mode — Run-length encodes identical pixels as count*r,g,b",
            value=MODE_RLE,
            variable=self.string_mode_var
        )
        rb_rle.pack(anchor="w", pady=1)

        # 6. RAW
        rb_raw = ttk.Radiobutton(
            mode_frame,
            text="🔵 Raw Row-Column Mode — Full explicit pixel list: R0:r,g,b;r,g,b;...",
            value=MODE_RAW,
            variable=self.string_mode_var
        )
        rb_raw.pack(anchor="w", pady=1)

        # Quality / Compression Preset
        qual_frame = tk.Frame(right_frame, bg=BG_CARD)
        qual_frame.pack(fill=tk.X, pady=(2, 8))

        lbl_qual = tk.Label(qual_frame, text="Compression Target:", font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=FG_MAIN)
        lbl_qual.pack(side=tk.LEFT, padx=(0, 10))

        rb_q100 = ttk.Radiobutton(qual_frame, text="100% Lossless (Exact)", value=100, variable=self.quality_var)
        rb_q100.pack(side=tk.LEFT, padx=5)

        rb_q85 = ttk.Radiobutton(qual_frame, text="85% High Quality (Smaller)", value=85, variable=self.quality_var)
        rb_q85.pack(side=tk.LEFT, padx=5)

        rb_q65 = ttk.Radiobutton(qual_frame, text="65% Max Compression (Beats JPEG)", value=65, variable=self.quality_var)
        rb_q65.pack(side=tk.LEFT, padx=5)

        # Step 3: Compress Button & Progress
        lbl_step3 = tk.Label(right_frame, text="Step 3: Scan Pixels & Compress (Auto-saves to output/)", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=ACCENT_BLUE)
        lbl_step3.pack(anchor="w")

        btn_row = tk.Frame(right_frame, bg=BG_CARD)
        btn_row.pack(fill=tk.X, pady=4)

        self.btn_run_compress = ttk.Button(
            btn_row,
            text="⚡ Compress Image",
            style="Primary.TButton",
            command=self._start_compress_thread
        )
        self.btn_run_compress.pack(side=tk.LEFT, padx=(0, 10))

        self.comp_progressbar = ttk.Progressbar(btn_row, mode="indeterminate", style="TProgressbar")

        # Stats Panel
        self.comp_stats_frame = tk.Frame(right_frame, bg=BG_INPUT, padx=12, pady=6, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.comp_stats_frame.pack(fill=tk.X, pady=(2, 6))

        self.lbl_comp_stats = tk.Label(
            self.comp_stats_frame,
            text="Compression statistics will appear here after scanning.",
            font=("Consolas", 9),
            bg=BG_INPUT,
            fg=FG_MUTED,
            justify="left",
            anchor="w"
        )
        self.lbl_comp_stats.pack(anchor="w")

        # Auto-saved notification banner
        self.lbl_autosave_notice = tk.Label(
            right_frame,
            text="💡 Tip: Clicking 'Compress Image' automatically saves the .icomp file directly to the output/ folder.",
            font=("Segoe UI", 8, "italic"),
            bg=BG_CARD,
            fg=FG_MUTED,
            anchor="w"
        )
        self.lbl_autosave_notice.pack(anchor="w", pady=(0, 4))

        # Pixel String Preview Box
        lbl_str_preview = tk.Label(right_frame, text="Pixel String Snippet (Row/Column Structure):", font=("Segoe UI", 10, "bold"), bg=BG_CARD, fg=FG_MAIN)
        lbl_str_preview.pack(anchor="w", pady=(2, 2))

        self.txt_string_preview = tk.Text(
            right_frame,
            height=4,
            bg="#11111b",
            fg=ACCENT_GREEN,
            insertbackground=FG_MAIN,
            font=("Consolas", 8),
            wrap=tk.NONE,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR
        )
        self.txt_string_preview.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        # Step 4: Export Options
        lbl_step4 = tk.Label(right_frame, text="Step 4: Manual Save / Export", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=ACCENT_BLUE)
        lbl_step4.pack(anchor="w")

        export_row = tk.Frame(right_frame, bg=BG_CARD)
        export_row.pack(fill=tk.X, pady=(2, 0))

        self.btn_save_icomp = ttk.Button(
            export_row,
            text="💾 Save Copy As (.icomp)",
            style="Success.TButton",
            state=tk.DISABLED,
            command=self._save_compressed_file
        )
        self.btn_save_icomp.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_save_txt = ttk.Button(
            export_row,
            text="📄 Save Pixel String (.txt)",
            style="Secondary.TButton",
            state=tk.DISABLED,
            command=self._save_pixel_string_file
        )
        self.btn_save_txt.pack(side=tk.LEFT, padx=(0, 8))

        btn_open_folder = ttk.Button(
            export_row,
            text="📁 Open output/ Folder",
            style="Secondary.TButton",
            command=self._open_output_folder
        )
        btn_open_folder.pack(side=tk.LEFT)

    # -------------------------------------------------------------------------
    # TAB 2: DECOMPRESS
    # -------------------------------------------------------------------------
    def _build_decompress_tab(self):
        pane = tk.PanedWindow(self.decompress_tab, orient=tk.HORIZONTAL, bg=BG_DARK, sashwidth=6)
        pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left Column: Scrollable File Selection & Actions
        left_container = tk.Frame(pane, bg=BG_CARD)
        pane.add(left_container, minsize=400)

        left_canvas = tk.Canvas(left_container, bg=BG_CARD, highlightthickness=0)
        left_scrollbar = ttk.Scrollbar(left_container, orient="vertical", command=left_canvas.yview)
        left_canvas.configure(yscrollcommand=left_scrollbar.set)

        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(left_canvas, bg=BG_CARD, padx=15, pady=15)
        left_canvas_win = left_canvas.create_window((0, 0), window=left_frame, anchor="nw")

        def _configure_left_frame(event):
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))

        def _configure_left_canvas(event):
            left_canvas.itemconfig(left_canvas_win, width=event.width)

        left_frame.bind("<Configure>", _configure_left_frame)
        left_canvas.bind("<Configure>", _configure_left_canvas)

        def _on_decomp_mousewheel(event):
            left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        left_container.bind("<Enter>", lambda e: left_canvas.bind_all("<MouseWheel>", _on_decomp_mousewheel))
        left_container.bind("<Leave>", lambda e: left_canvas.unbind_all("<MouseWheel>"))

        lbl_decomp_step1 = tk.Label(left_frame, text="Step 1: Select Compressed File", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=ACCENT_PURPLE)
        lbl_decomp_step1.pack(anchor="w")

        btn_browse_decomp = ttk.Button(left_frame, text="📂 Browse .icomp File...", style="Secondary.TButton", command=self._browse_decompress_file)
        btn_browse_decomp.pack(fill=tk.X, pady=(10, 5))

        self.lbl_decomp_file_path = tk.Label(left_frame, text="No .icomp file selected", font=("Segoe UI", 9), bg=BG_CARD, fg=FG_MUTED, wraplength=350, justify="left")
        self.lbl_decomp_file_path.pack(anchor="w", pady=(0, 15))

        lbl_decomp_step2 = tk.Label(left_frame, text="Step 2: Decompress & Reconstruct", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=ACCENT_PURPLE)
        lbl_decomp_step2.pack(anchor="w")

        self.btn_run_decompress = ttk.Button(
            left_frame,
            text="🔄 Decompress & Reconstruct Image",
            style="Primary.TButton",
            state=tk.DISABLED,
            command=self._start_decompress_thread
        )
        self.btn_run_decompress.pack(fill=tk.X, pady=10)

        self.decomp_progressbar = ttk.Progressbar(left_frame, mode="indeterminate", style="TProgressbar")

        # Decompression Stats
        self.decomp_stats_frame = tk.Frame(left_frame, bg=BG_INPUT, padx=12, pady=10, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.decomp_stats_frame.pack(fill=tk.X, pady=10)

        self.lbl_decomp_stats = tk.Label(
            self.decomp_stats_frame,
            text="Reconstruction details will appear here.",
            font=("Consolas", 9),
            bg=BG_INPUT,
            fg=FG_MUTED,
            justify="left",
            anchor="w"
        )
        self.lbl_decomp_stats.pack(anchor="w")

        # Save Restored Image
        lbl_decomp_step3 = tk.Label(left_frame, text="Step 3: Save Restored Image", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=ACCENT_PURPLE)
        lbl_decomp_step3.pack(anchor="w", pady=(10, 5))

        self.btn_save_restored_png = ttk.Button(
            left_frame,
            text="💾 Save as Lossless PNG (Exact Pixels, ~4 MB)",
            style="Success.TButton",
            state=tk.DISABLED,
            command=lambda: self._save_restored_image(format_ext=".png")
        )
        self.btn_save_restored_png.pack(fill=tk.X, pady=(4, 6))

        self.btn_save_restored_webp = ttk.Button(
            left_frame,
            text="🚀 Save as Modern WebP (~560 KB, Best Size & Quality)",
            style="Primary.TButton",
            state=tk.DISABLED,
            command=lambda: self._save_restored_image(format_ext=".webp")
        )
        self.btn_save_restored_webp.pack(fill=tk.X, pady=(0, 8))

        # JPEG Export Quality Selection Box
        jpeg_box = tk.Frame(left_frame, bg=BG_INPUT, padx=10, pady=6, highlightthickness=1, highlightbackground=BORDER_COLOR)
        jpeg_box.pack(fill=tk.X, pady=(0, 6))

        lbl_jpeg_qual = tk.Label(jpeg_box, text="Choose JPEG Export Quality:", font=("Segoe UI", 9, "bold"), bg=BG_INPUT, fg=FG_MAIN)
        lbl_jpeg_qual.pack(anchor="w", pady=(0, 3))

        rb_jpeg_high = ttk.Radiobutton(
            jpeg_box,
            text="⭐ High Quality 95% (~914 KB, Matches Camera)",
            value=95,
            variable=self.jpeg_export_quality_var
        )
        rb_jpeg_high.pack(anchor="w", pady=1)

        rb_jpeg_std = ttk.Radiobutton(
            jpeg_box,
            text="⚡ Standard 75% (~187 KB, Compact)",
            value=75,
            variable=self.jpeg_export_quality_var
        )
        rb_jpeg_std.pack(anchor="w", pady=1)

        rb_jpeg_small = ttk.Radiobutton(
            jpeg_box,
            text="📦 Small 60% (~130 KB, Max Compression)",
            value=60,
            variable=self.jpeg_export_quality_var
        )
        rb_jpeg_small.pack(anchor="w", pady=1)

        self.btn_save_restored_jpeg = ttk.Button(
            left_frame,
            text="💾 Save as JPEG (Using Selected Quality)",
            style="Secondary.TButton",
            state=tk.DISABLED,
            command=lambda: self._save_restored_image(format_ext=".jpeg")
        )
        self.btn_save_restored_jpeg.pack(fill=tk.X, pady=(0, 10))

        # Right Column: Reconstructed Image Preview
        right_frame = tk.Frame(pane, bg=BG_CARD, padx=15, pady=15)
        pane.add(right_frame, minsize=420)

        lbl_recon_title = tk.Label(right_frame, text="Reconstructed Image Preview", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=ACCENT_GREEN)
        lbl_recon_title.pack(anchor="w")

        self.decomp_preview_canvas = tk.Canvas(right_frame, bg=BG_INPUT, width=380, height=380, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.decomp_preview_canvas.pack(pady=10)
        self.decomp_preview_canvas.create_text(190, 190, text="Decompressed Image Preview", fill=FG_SUBTLE, font=("Segoe UI", 11))

        self.lbl_recon_dims = tk.Label(right_frame, text="Dimensions: - | Total Pixels: -", font=("Segoe UI", 10), bg=BG_CARD, fg=FG_MAIN)
        self.lbl_recon_dims.pack(pady=5)

    # -------------------------------------------------------------------------
    # TAB 3: LOSSLESS VERIFIER
    # -------------------------------------------------------------------------
    def _build_verifier_tab(self):
        container = tk.Frame(self.verifier_tab, bg=BG_CARD, padx=25, pady=20)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        title = tk.Label(container, text="🔍 Lossless Pixel-for-Pixel Verifier", font=("Segoe UI", 14, "bold"), bg=BG_CARD, fg=ACCENT_YELLOW)
        title.pack(anchor="w")

        desc = tk.Label(
            container,
            text="Verifies that the reconstructed image matches the original image with 100% precision (0 mismatched pixels).",
            font=("Segoe UI", 10),
            bg=BG_CARD,
            fg=FG_MUTED
        )
        desc.pack(anchor="w", pady=(4, 15))

        self.btn_verify = ttk.Button(container, text="🔬 Run Verification On Current Images", style="Primary.TButton", command=self._start_verification_thread)
        self.btn_verify.pack(anchor="w", pady=(0, 10))

        self.verifier_progressbar = ttk.Progressbar(container, mode="indeterminate", style="TProgressbar")

        self.verifier_results_frame = tk.Frame(container, bg=BG_INPUT, padx=20, pady=15, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.verifier_results_frame.pack(fill=tk.BOTH, expand=True)

        self.lbl_verifier_output = tk.Label(
            self.verifier_results_frame,
            text="Compress an image and decompress it, then click 'Run Verification' to check lossless fidelity.",
            font=("Consolas", 10),
            bg=BG_INPUT,
            fg=FG_MAIN,
            justify="left",
            anchor="nw"
        )
        self.lbl_verifier_output.pack(fill=tk.BOTH, expand=True)

    # -------------------------------------------------------------------------
    # COMPRESS EVENT HANDLERS
    # -------------------------------------------------------------------------
    def _browse_compress_image(self):
        initial_dir = IMAGES_DIR if IMAGES_DIR.exists() else Path.cwd()
        file_path = filedialog.askopenfilename(
            title="Select Image to Compress",
            initialdir=str(initial_dir),
            filetypes=IMAGE_EXTENSIONS
        )
        if file_path:
            self._load_compress_image(Path(file_path))

    def _load_compress_image(self, path: Path):
        try:
            self.compress_image_path = path
            self.compress_image_obj = Image.open(path)

            file_size_kb = path.stat().st_size / 1024
            w, h = self.compress_image_obj.size
            mode = self.compress_image_obj.mode

            self.lbl_comp_file_path.config(text=f"Selected: {path.name} ({path.parent})")
            self.lbl_comp_dims.config(text=f"Dimensions: {w}x{h} | Size: {file_size_kb:.1f} KB | Mode: {mode}")

            self._display_preview(self.comp_preview_canvas, self.compress_image_obj)
            self._set_status(f"Loaded image {path.name} ({w}x{h})")
        except Exception as e:
            messagebox.showerror("Error Opening Image", f"Failed to open image:\n{e}")

    def _start_compress_thread(self):
        if not self.compress_image_obj:
            messagebox.showwarning("No Image Selected", "Please select an image first.")
            return

        self.btn_run_compress.config(text="⏳ Compressing... (Please wait)", state=tk.DISABLED)
        self.comp_progressbar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.comp_progressbar.start(10)
        self._set_status("Scanning image and compressing...")
        self.update_idletasks()

        mode = self.string_mode_var.get()
        quality = self.quality_var.get()
        threading.Thread(target=self._execute_compression, args=(mode, quality), daemon=True).start()

    def _execute_compression(self, mode: str, quality: int):
        try:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            img_stem = self.compress_image_path.stem if self.compress_image_path else "compressed"
            qual_suffix = f"_q{quality}" if (mode == MODE_BIN_SMART or quality < 100) else ""
            auto_icomp_path = OUTPUT_DIR / f"{img_stem}_{mode}{qual_suffix}.icomp"
            auto_txt_path = OUTPUT_DIR / f"{img_stem}_{mode}{qual_suffix}_pixels.txt"

            if mode in (MODE_BIN_SMART, MODE_BIN_LOSSLESS):
                # -------------------------------------------------------------
                # REAL-LIFE BINARY ENGINE (Direct pure binary compression)
                # -------------------------------------------------------------
                stats = PixelCoder.compress_image_to_file(
                    self.compress_image_path or self.compress_image_obj,
                    auto_icomp_path,
                    mode=mode,
                    quality=quality
                )
                with open(auto_icomp_path, "rb") as f:
                    compressed_bytes = f.read()

                # Generate informational header for the .txt file
                pixel_str, _ = PixelCoder.scan_image_to_string(
                    self.compress_image_obj,
                    mode=mode,
                    quality=quality
                )
                with open(auto_txt_path, "w", encoding="utf-8") as f:
                    f.write(pixel_str)
            else:
                # -------------------------------------------------------------
                # TEXT-BASED STRING ENGINES (Delta, Pattern, Palette, Hex, RLE, Raw)
                # -------------------------------------------------------------
                pixel_str, scan_meta = PixelCoder.scan_image_to_string(
                    self.compress_image_obj,
                    mode=mode,
                    quality=quality
                )
                compressed_bytes = PixelCoder.compress_pixel_string(pixel_str)

                with open(auto_icomp_path, "wb") as f:
                    f.write(compressed_bytes)
                with open(auto_txt_path, "w", encoding="utf-8") as f:
                    f.write(pixel_str)

                orig_size = self.compress_image_path.stat().st_size if self.compress_image_path else 0
                raw_size = scan_meta["raw_image_bytes"]
                comp_size = len(compressed_bytes)

                savings_raw = ((raw_size - comp_size) / raw_size * 100) if raw_size > 0 else 0.0
                savings_file = ((orig_size - comp_size) / orig_size * 100) if orig_size > 0 else 0.0

                stats = {
                    **scan_meta,
                    "original_file_size_bytes": orig_size,
                    "raw_image_bytes": raw_size,
                    "compressed_size_bytes": comp_size,
                    "space_savings_vs_raw_pct": savings_raw,
                    "space_savings_vs_file_pct": savings_file,
                }

            self.after(0, self._on_compression_complete, pixel_str, compressed_bytes, stats, auto_icomp_path)
        except Exception as e:
            self.after(0, self._on_compression_error, str(e))

    def _on_compression_complete(self, pixel_str: str, compressed_bytes: bytes, stats: dict, auto_icomp_path: Path):
        self.generated_pixel_str = pixel_str
        self.compressed_bytes = compressed_bytes
        self.compression_stats = stats

        self.comp_progressbar.stop()
        self.comp_progressbar.pack_forget()
        self.btn_run_compress.config(text="⚡ Compress Image", state=tk.NORMAL)
        self.btn_save_icomp.config(state=tk.NORMAL)
        self.btn_save_txt.config(state=tk.NORMAL)

        self.last_saved_icomp_path = auto_icomp_path

        # Also auto-load this saved file into the Decompress tab
        self._load_decompress_file(auto_icomp_path)

        # Update stats label
        orig_kb = stats["original_file_size_bytes"] / 1024
        raw_kb = stats["raw_image_bytes"] / 1024
        comp_kb = stats["compressed_size_bytes"] / 1024
        str_kb = stats.get("string_size_bytes", 0) / 1024
        str_len = stats.get("string_length_chars", 0)
        savings_raw = stats["space_savings_vs_raw_pct"]
        savings_file = stats["space_savings_vs_file_pct"]

        stats_text = (
            f"✅ Compression Succeeded & Automatically Saved!\n"
            f"• Algorithm: {stats['mode'].upper()} (Quality={stats.get('quality', 100)}%)\n"
            f"• Scanned Pixels: {stats['total_pixels']:,} ({stats['width']}x{stats['height']})\n"
            f"• Raw Uncompressed Pixels: {raw_kb:.2f} KB ({stats['raw_image_bytes']:,} bytes)\n"
            f"• Original File on Disk: {orig_kb:.2f} KB\n"
            f"• Pixel String / Info Size: {str_kb:.2f} KB ({str_len:,} chars)\n"
            f"• Compressed Package (.icomp): {comp_kb:.2f} KB\n"
            f"• Savings vs Raw Image Data: {savings_raw:+.1f}%\n"
            f"• Difference vs Disk File: {savings_file:+.1f}%\n"
            f"• 💾 Saved to: output/{auto_icomp_path.name}"
        )
        self.lbl_comp_stats.config(text=stats_text, fg=ACCENT_GREEN)

        self.lbl_autosave_notice.config(
            text=f"✅ Automatically saved to output/{auto_icomp_path.name} ({comp_kb:.2f} KB)",
            fg=ACCENT_GREEN
        )

        # Show snippet of pixel string
        lines = pixel_str.splitlines()
        preview_lines = lines[:15]
        if len(lines) > 15:
            preview_lines.append(f"... ({len(lines) - 15} more rows)")
        self.txt_string_preview.delete("1.0", tk.END)
        self.txt_string_preview.insert("1.0", "\n".join(preview_lines))

        self._set_status(f"Compression completed & saved: output/{auto_icomp_path.name} ({comp_kb:.2f} KB)")

    def _on_compression_error(self, error_msg: str):
        self.comp_progressbar.stop()
        self.comp_progressbar.pack_forget()
        self.btn_run_compress.config(text="⚡ Compress Image", state=tk.NORMAL)
        self.lbl_comp_stats.config(text=f"❌ Error during compression:\n{error_msg}", fg=ACCENT_RED)
        messagebox.showerror("Compression Error", f"Failed to compress image:\n{error_msg}")
        self._set_status("Compression failed.")

    def _open_output_folder(self):
        """Opens the output directory in Windows Explorer."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(str(OUTPUT_DIR))

    def _save_compressed_file(self):
        if not self.compressed_bytes:
            return
        OUTPUT_DIR.mkdir(exist_ok=True)
        mode = self.string_mode_var.get()
        initial_name = f"{self.compress_image_path.stem}_{mode}{DEFAULT_COMPRESSED_EXT}" if self.compress_image_path else f"compressed_{mode}.icomp"
        file_path = filedialog.asksaveasfilename(
            title="Save Compressed File Copy",
            initialdir=str(OUTPUT_DIR),
            initialfile=initial_name,
            defaultextension=DEFAULT_COMPRESSED_EXT,
            filetypes=COMPRESSED_EXTENSIONS
        )
        if file_path:
            with open(file_path, "wb") as f:
                f.write(self.compressed_bytes)
            self._set_status(f"Saved compressed package to {Path(file_path).name}")
            self._load_decompress_file(Path(file_path))
            messagebox.showinfo("Saved", f"Compressed file saved successfully to:\n{file_path}")

    def _save_pixel_string_file(self):
        if not self.generated_pixel_str:
            return
        OUTPUT_DIR.mkdir(exist_ok=True)
        mode = self.string_mode_var.get()
        initial_name = f"{self.compress_image_path.stem}_{mode}_pixels{DEFAULT_TEXT_EXT}" if self.compress_image_path else f"pixels_{mode}.txt"
        file_path = filedialog.asksaveasfilename(
            title="Save Pixel String Text File",
            initialdir=str(OUTPUT_DIR),
            initialfile=initial_name,
            defaultextension=DEFAULT_TEXT_EXT,
            filetypes=TEXT_EXTENSIONS
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.generated_pixel_str)
            self._set_status(f"Saved pixel string to {Path(file_path).name}")
            messagebox.showinfo("Saved", f"Pixel string saved successfully to:\n{file_path}")

    # -------------------------------------------------------------------------
    # DECOMPRESS EVENT HANDLERS
    # -------------------------------------------------------------------------
    def _browse_decompress_file(self):
        initial_dir = OUTPUT_DIR if OUTPUT_DIR.exists() else Path.cwd()
        file_path = filedialog.askopenfilename(
            title="Select Compressed File to Decompress",
            initialdir=str(initial_dir),
            filetypes=COMPRESSED_EXTENSIONS
        )
        if file_path:
            self._load_decompress_file(Path(file_path))

    def _load_decompress_file(self, path: Path):
        self.decompress_file_path = path
        size_kb = path.stat().st_size / 1024
        self.lbl_decomp_file_path.config(text=f"Selected: {path.name} ({size_kb:.2f} KB)")
        self.btn_run_decompress.config(state=tk.NORMAL)
        self._set_status(f"Loaded compressed file {path.name}")

    def _start_decompress_thread(self):
        if not self.decompress_file_path:
            return
        self.btn_run_decompress.config(text="⏳ Decompressing... (Please wait)", state=tk.DISABLED)
        self.decomp_progressbar.pack(fill=tk.X, pady=5)
        self.decomp_progressbar.start(10)
        self._set_status("Decompressing file and reconstructing image pixels...")
        self.update_idletasks()

        threading.Thread(target=self._execute_decompression, daemon=True).start()

    def _execute_decompression(self):
        try:
            recon_img, recon_meta = PixelCoder.decompress_file_to_image(self.decompress_file_path)
            self.after(0, self._on_decompression_complete, recon_img, recon_meta)
        except Exception as e:
            self.after(0, self._on_decompression_error, str(e))

    def _on_decompression_complete(self, recon_img: Image.Image, recon_meta: dict):
        self.reconstructed_image_obj = recon_img
        self.decompression_stats = recon_meta

        self.decomp_progressbar.stop()
        self.decomp_progressbar.pack_forget()
        self.btn_run_decompress.config(text="🔄 Decompress & Reconstruct Image", state=tk.NORMAL)
        self.btn_save_restored_png.config(state=tk.NORMAL)
        self.btn_save_restored_webp.config(state=tk.NORMAL)
        self.btn_save_restored_jpeg.config(state=tk.NORMAL)

        w, h = recon_img.size
        self.lbl_recon_dims.config(text=f"Dimensions: {w}x{h} | Total Pixels: {w*h:,}")
        self._display_preview(self.decomp_preview_canvas, recon_img)

        format_name = recon_meta.get("format", "unknown").upper()
        q_info = f" (Q-Factor={recon_meta['q_factor']})" if "q_factor" in recon_meta else ""
        stats_text = (
            f"✅ Reconstructed Successfully!\n"
            f"• Format Decoded: {format_name}{q_info}\n"
            f"• Reconstructed Size: {w}x{h} ({w*h:,} pixels)\n"
            f"• Decompression Duration: {recon_meta.get('reconstruction_time_sec', 0.0):.3f}s"
        )
        self.lbl_decomp_stats.config(text=stats_text, fg=ACCENT_GREEN)
        self._set_status(f"Decompression completed: {w}x{h} image restored.")

    def _on_decompression_error(self, error_msg: str):
        self.decomp_progressbar.stop()
        self.decomp_progressbar.pack_forget()
        self.btn_run_decompress.config(text="🔄 Decompress & Reconstruct Image", state=tk.NORMAL)
        self.lbl_decomp_stats.config(text=f"❌ Error during decompression:\n{error_msg}", fg=ACCENT_RED)
        messagebox.showerror("Decompression Error", f"Failed to decompress file:\n{error_msg}")
        self._set_status("Decompression failed.")

    def _save_restored_image(self, format_ext: str = ".png"):
        if not self.reconstructed_image_obj:
            return
        OUTPUT_DIR.mkdir(exist_ok=True)
        initial_name = "reconstructed_image" + format_ext
        if format_ext == ".png":
            types = [("PNG Image (*.png)", "*.png"), ("All Files", "*.*")]
        elif format_ext in (".jpeg", ".jpg"):
            types = [("JPEG Image (*.jpeg;*.jpg)", "*.jpeg;*.jpg"), ("All Files", "*.*")]
        elif format_ext == ".webp":
            types = [("WebP Image (*.webp)", "*.webp"), ("All Files", "*.*")]
        else:
            types = [("All Files", "*.*")]

        file_path = filedialog.asksaveasfilename(
            title=f"Save Restored Image ({format_ext.upper()})",
            initialdir=str(OUTPUT_DIR),
            initialfile=initial_name,
            defaultextension=format_ext,
            filetypes=types
        )
        if file_path:
            save_img = self.reconstructed_image_obj
            if format_ext in (".jpeg", ".jpg"):
                if save_img.mode == "RGBA":
                    save_img = save_img.convert("RGB")
                q = self.jpeg_export_quality_var.get()
                sub = 0 if q >= 90 else 2
                save_img.save(file_path, quality=q, subsampling=sub)
            elif format_ext == ".webp":
                save_img.save(file_path, format="WEBP", quality=95)
            else:
                save_img.save(file_path)
            self._set_status(f"Saved restored image to {Path(file_path).name}")
            messagebox.showinfo("Saved", f"Restored image saved successfully to:\n{file_path}")

    # -------------------------------------------------------------------------
    # VERIFIER EVENT HANDLERS (Asynchronous with visual progress)
    # -------------------------------------------------------------------------
    def _start_verification_thread(self):
        if not self.compress_image_obj:
            messagebox.showwarning("Missing Original", "Please load an original image first in the 'Compress' tab.")
            return
        if not self.reconstructed_image_obj:
            messagebox.showwarning("Missing Reconstructed", "Please decompress an image first in the 'Decompress' tab.")
            return

        self.btn_verify.config(text="⏳ Verifying Pixels... (Please wait)", state=tk.DISABLED)
        self.verifier_progressbar.pack(anchor="w", fill=tk.X, pady=(0, 15))
        self.verifier_progressbar.start(10)
        self._set_status("Running pixel-by-pixel verification...")
        self.update_idletasks()

        threading.Thread(target=self._execute_verification, daemon=True).start()

    def _execute_verification(self):
        try:
            verification = PixelCoder.verify_lossless(self.compress_image_obj, self.reconstructed_image_obj)
            self.after(0, self._on_verification_complete, verification)
        except Exception as e:
            self.after(0, self._on_verification_error, str(e))

    def _on_verification_complete(self, verification: dict):
        self.verifier_progressbar.stop()
        self.verifier_progressbar.pack_forget()
        self.btn_verify.config(text="🔬 Run Verification On Current Images", state=tk.NORMAL)

        if verification["is_identical"]:
            report = (
                f"🎉 VERIFICATION PASSED: 100.0% LOSSLESS!\n\n"
                f"• Total Pixels Checked: {verification['total_pixels']:,}\n"
                f"• Exactly Matched Pixels: {verification['matched_pixels']:,}\n"
                f"• Mismatched Pixels: 0\n"
                f"• Maximum Pixel Difference: 0\n"
                f"• Match Percentage: 100.000%\n\n"
                f"The reconstructed image is identical to the original down to the exact pixel color values."
            )
            self.lbl_verifier_output.config(text=report, fg=ACCENT_GREEN)
            self._set_status("Lossless verification passed: 100% identical!")
        else:
            report = (
                f"⚠️ VERIFICATION DETECTED DIFFERENCES\n\n"
                f"• Total Pixels: {verification.get('total_pixels', 'N/A'):,}\n"
                f"• Matched Pixels: {verification.get('matched_pixels', 'N/A'):,}\n"
                f"• Mismatched Pixels: {verification.get('mismatched_pixels', 'N/A'):,}\n"
                f"• Match Percentage: {verification.get('match_percentage', 0.0):.2f}%\n"
                f"• Max Difference: {verification.get('max_difference', 'N/A')}\n"
                f"(Note: If you used Quality < 100%, slight quantization differences are expected for smaller file size)."
            )
            self.lbl_verifier_output.config(text=report, fg=ACCENT_YELLOW)
            self._set_status("Verification complete.")

    def _on_verification_error(self, error_msg: str):
        self.verifier_progressbar.stop()
        self.verifier_progressbar.pack_forget()
        self.btn_verify.config(text="🔬 Run Verification On Current Images", state=tk.NORMAL)
        messagebox.showerror("Verification Error", f"Failed to verify images:\n{error_msg}")
        self._set_status("Verification failed.")

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------
    def _display_preview(self, canvas: tk.Canvas, img: Image.Image):
        canvas_w = canvas.winfo_reqwidth() or 310
        canvas_h = canvas.winfo_reqheight() or 310

        thumb = img.copy()
        thumb.thumbnail((canvas_w - 20, canvas_h - 20), Image.Resampling.BILINEAR)

        photo = ImageTk.PhotoImage(thumb)
        canvas.delete("all")
        canvas.create_image(canvas_w // 2, canvas_h // 2, image=photo)
        canvas.image = photo

    def _set_status(self, text: str):
        self.status_bar.config(text=f"Status: {text}")


def launch_gui():
    """Launches the Tkinter application."""
    app = ImageCompressorApp()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
