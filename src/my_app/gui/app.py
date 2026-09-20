"""Modern Desktop GUI for Image Compression and Decompression built with CustomTkinter.

Copyright (c) 2026 Hasitha Wijesinghe (https://github.com/HasithaLWi)
Licensed under the MIT License.
"""

import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk
from PIL import Image

from src.my_app.config import (
    ALL_MODES,
    APP_VERSION,
    COMPRESSED_EXTENSIONS,
    DEFAULT_COMPRESSED_EXT,
    DEFAULT_TEXT_EXT,
    IMAGE_EXTENSIONS,
    IMAGES_DIR,
    MODE_BIN_LOSSLESS,
    MODE_BIN_SMART,
    MODE_DELTA,
    MODE_HEX,
    MODE_PALETTE,
    MODE_PATTERN,
    MODE_RAW,
    MODE_RLE,
    OUTPUT_DIR,
    TEXT_EXTENSIONS,
)
from src.my_app.core.pixel_coder import PixelCoder

# Set CustomTkinter Theme & Appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Modern Palette
COLOR_PRIMARY = "#3b82f6"       # Blue
COLOR_PRIMARY_HOVER = "#2563eb"
COLOR_SUCCESS = "#10b981"       # Emerald Green
COLOR_SUCCESS_HOVER = "#059669"
COLOR_SECONDARY = "#374151"     # Dark Slate
COLOR_SECONDARY_HOVER = "#4b5563"
COLOR_CARD = "#1e1e2e"          # Catppuccin Dark Card
COLOR_CARD_SUB = "#282a36"      # Sub-card background
COLOR_TEXT_MUTED = "#9ca3af"


class ImageCompressorApp(ctk.CTk):
    """Main CustomTkinter Desktop Application for Image Compression and Decompression."""

    def __init__(self):
        super().__init__()

        self.title(f"⚡ PixelScan — Image Compressor & Decompressor (v{APP_VERSION})")
        self.geometry("1140x880")
        self.minsize(1020, 760)

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

        # Direct Formatter variables
        self.formatter_image_path: Optional[Path] = None
        self.formatter_image_obj: Optional[Image.Image] = None
        self.formatter_preset_var = ctk.StringVar(value="webp_95")
        self.last_formatted_path: Optional[Path] = None

        # Mode variable (Default to real-life Binary Smart mode for genuine small files)
        self.string_mode_var = ctk.StringVar(value=MODE_BIN_SMART)

        # Quality variable (100 = Lossless, 85 = High Quality, 65 = Max Compression)
        self.quality_var = ctk.IntVar(value=100)

        # JPEG Export Quality (User selectable: 95 = High Quality, 75 = Standard, 60 = Compact)
        self.jpeg_export_quality_var = ctk.IntVar(value=95)

        self._build_ui()

        # Check for test image and pre-load if present
        default_test_img = IMAGES_DIR / "ICtest.jpeg"
        if default_test_img.exists():
            self._load_compress_image(default_test_img)
            self._load_formatter_image(default_test_img)
        else:
            images = list(IMAGES_DIR.glob("*.jpeg")) + list(IMAGES_DIR.glob("*.jpg")) + list(IMAGES_DIR.glob("*.png"))
            if images:
                self._load_compress_image(images[0])
                self._load_formatter_image(images[0])

    def _build_ui(self):
        """Constructs the complete CustomTkinter application UI."""
        # -------------------------------------------------------------
        # Top Header Bar
        # -------------------------------------------------------------
        header = ctk.CTkFrame(self, corner_radius=0, fg_color=COLOR_CARD, height=65)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side=tk.LEFT, padx=20, pady=10)

        lbl_title = ctk.CTkLabel(
            title_box,
            text="⚡ PixelScan Image Compressor & Decompressor",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLOR_PRIMARY
        )
        lbl_title.pack(anchor="w")

        lbl_sub = ctk.CTkLabel(
            title_box,
            text="High-Performance Binary Compression & Lossless Deduplication Suite",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_MUTED
        )
        lbl_sub.pack(anchor="w")

        # Appearance Mode Toggle on Right
        self.theme_switch = ctk.CTkSwitch(
            header,
            text="Dark Mode",
            command=self._toggle_appearance_mode,
            onvalue="Dark",
            offvalue="Light",
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.theme_switch.select()
        self.theme_switch.pack(side=tk.RIGHT, padx=(5, 20), pady=15)

        # About Button in Header
        btn_about = ctk.CTkButton(
            header,
            text="ℹ️ About",
            width=75,
            height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            command=self._show_about_dialog
        )
        btn_about.pack(side=tk.RIGHT, padx=(0, 5), pady=15)

        # -------------------------------------------------------------
        # Main Tabview
        # -------------------------------------------------------------
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=12,
            segmented_button_selected_color=COLOR_PRIMARY,
            segmented_button_selected_hover_color=COLOR_PRIMARY_HOVER
        )
        self.tabview.pack(fill=tk.BOTH, expand=True, padx=15, pady=(10, 5))

        self.tab_compress = self.tabview.add("⚡ Compress Image")
        self.tab_decompress = self.tabview.add("🔄 Decompress Image")
        self.tab_verifier = self.tabview.add("🔍 Lossless Verifier")
        self.tab_formatter = self.tabview.add("⚡ Direct Formatter")

        self._build_compress_tab()
        self._build_decompress_tab()
        self._build_verifier_tab()
        self._build_formatter_tab()

        # -------------------------------------------------------------
        # Bottom Status Bar
        # -------------------------------------------------------------
        status_bar_frame = ctk.CTkFrame(self, height=28, corner_radius=0, fg_color=COLOR_CARD)
        status_bar_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar_frame.pack_propagate(False)

        self.status_bar = ctk.CTkLabel(
            status_bar_frame,
            text="Ready. Select an image to begin.",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLOR_TEXT_MUTED,
            anchor="w"
        )
        self.status_bar.pack(side=tk.LEFT, padx=15)

        lbl_copyright = ctk.CTkLabel(
            status_bar_frame,
            text="© 2026 Hasitha Wijesinghe | MIT License",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLOR_TEXT_MUTED
        )
        lbl_copyright.pack(side=tk.RIGHT, padx=15)

    def _toggle_appearance_mode(self):
        if self.theme_switch.get() == "Dark":
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")

    # =========================================================================
    # TAB 1: COMPRESS
    # =========================================================================
    def _build_compress_tab(self):
        parent = self.tab_compress

        # Horizontal Split: Left (Image & Preview), Right (Scrollable Options & Stats)
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left Column: Image Selection & Preview
        left_frame = ctk.CTkFrame(container, corner_radius=10, fg_color=COLOR_CARD, width=360)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=5)
        left_frame.pack_propagate(False)

        lbl_step1 = ctk.CTkLabel(
            left_frame,
            text="Step 1: Select Input Image",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLOR_PRIMARY
        )
        lbl_step1.pack(anchor="w", padx=15, pady=(15, 6))

        btn_browse = ctk.CTkButton(
            left_frame,
            text="📂 Browse Image...",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=self._browse_compress_image
        )
        btn_browse.pack(fill=tk.X, padx=15, pady=(0, 6))

        self.lbl_comp_file_path = ctk.CTkLabel(
            left_frame,
            text="No image selected",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLOR_TEXT_MUTED,
            wraplength=320,
            justify="left"
        )
        self.lbl_comp_file_path.pack(anchor="w", padx=15, pady=(0, 6))

        # Preview Container
        preview_box = ctk.CTkFrame(left_frame, corner_radius=8, fg_color=COLOR_CARD_SUB, height=310)
        preview_box.pack(fill=tk.X, padx=15, pady=4)
        preview_box.pack_propagate(False)

        self.lbl_comp_preview = ctk.CTkLabel(preview_box, text="Image Preview", text_color=COLOR_TEXT_MUTED)
        self.lbl_comp_preview.pack(expand=True)

        self.lbl_comp_dims = ctk.CTkLabel(
            left_frame,
            text="Dimensions: - | Size: - | Mode: -",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLOR_TEXT_MUTED
        )
        self.lbl_comp_dims.pack(padx=15, pady=(6, 10))

        btn_open_out = ctk.CTkButton(
            left_frame,
            text="📁 Open Output Folder",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            command=self._open_output_folder
        )
        btn_open_out.pack(fill=tk.X, padx=15, pady=(0, 15))

        # Right Column: Built-in CTkScrollableFrame
        right_scroll = ctk.CTkScrollableFrame(container, corner_radius=10, fg_color=COLOR_CARD)
        right_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)

        # Step 2: Choose Algorithm
        lbl_step2 = ctk.CTkLabel(
            right_scroll,
            text="Step 2: Choose Compression Algorithm",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLOR_PRIMARY
        )
        lbl_step2.pack(anchor="w", padx=10, pady=(10, 4))

        mode_box = ctk.CTkFrame(right_scroll, corner_radius=8, fg_color=COLOR_CARD_SUB)
        mode_box.pack(fill=tk.X, padx=10, pady=(0, 8))

        # Binary Engines Section
        lbl_bin_hdr = ctk.CTkLabel(
            mode_box,
            text="🚀 BINARY ENGINES (PURE BINARY — SMALLEST FILES):",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=COLOR_SUCCESS
        )
        lbl_bin_hdr.pack(anchor="w", padx=12, pady=(8, 2))

        rb_bin_smart = ctk.CTkRadioButton(
            mode_box,
            text="🚀 Binary Smart Mode (High Compression, Beats JPEG)\n   Frequency quantization in pure binary. Bypasses text strings completely.",
            value=MODE_BIN_SMART,
            variable=self.string_mode_var,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        rb_bin_smart.pack(anchor="w", padx=12, pady=3)

        rb_bin_lossless = ctk.CTkRadioButton(
            mode_box,
            text="🛡️ Binary Lossless Mode (100% Exact Pixels, Zero Text Overhead)\n   Encodes raw bytes directly with 2D DPCM spatial prediction.",
            value=MODE_BIN_LOSSLESS,
            variable=self.string_mode_var,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        rb_bin_lossless.pack(anchor="w", padx=12, pady=3)

        # Text-Based Section
        lbl_txt_hdr = ctk.CTkLabel(
            mode_box,
            text="📝 TEXT-BASED STRING ENGINES (HUMAN-READABLE):",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=COLOR_PRIMARY
        )
        lbl_txt_hdr.pack(anchor="w", padx=12, pady=(10, 2))

        text_modes = [
            (MODE_DELTA, "⚡ Delta-RLE String Mode — Stores pixel differences (dr,dg,db)"),
            (MODE_PATTERN, "🧩 Pattern Deduplication Mode — Stores repeated patterns once, restores on decompress"),
            (MODE_PALETTE, "🎨 Palette String Mode — Unique color index table (0,1,0,2)"),
            (MODE_HEX, "🔢 HEX String Mode — 6-char hex (1B1725), removes all commas"),
            (MODE_RLE, "🟢 Standard RGB RLE Mode — Run-length encodes identical pixels as count*r,g,b"),
            (MODE_RAW, "🔵 Raw Row-Column Mode — Full explicit pixel list: R0:r,g,b;r,g,b;...")
        ]
        for val, txt in text_modes:
            rb = ctk.CTkRadioButton(
                mode_box,
                text=txt,
                value=val,
                variable=self.string_mode_var,
                font=ctk.CTkFont(family="Segoe UI", size=11)
            )
            rb.pack(anchor="w", padx=12, pady=2)

        # Compression Target / Quality
        qual_frame = ctk.CTkFrame(right_scroll, fg_color="transparent")
        qual_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        lbl_qual = ctk.CTkLabel(
            qual_frame,
            text="Compression Target:",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        )
        lbl_qual.pack(side=tk.LEFT, padx=(0, 10))

        rb_q100 = ctk.CTkRadioButton(qual_frame, text="100% Lossless (Exact)", value=100, variable=self.quality_var, font=ctk.CTkFont(family="Segoe UI", size=11))
        rb_q100.pack(side=tk.LEFT, padx=6)

        rb_q85 = ctk.CTkRadioButton(qual_frame, text="85% High Quality (Smaller)", value=85, variable=self.quality_var, font=ctk.CTkFont(family="Segoe UI", size=11))
        rb_q85.pack(side=tk.LEFT, padx=6)

        rb_q65 = ctk.CTkRadioButton(qual_frame, text="65% Max Compression", value=65, variable=self.quality_var, font=ctk.CTkFont(family="Segoe UI", size=11))
        rb_q65.pack(side=tk.LEFT, padx=6)

        # Step 3: Scan & Compress
        lbl_step3 = ctk.CTkLabel(
            right_scroll,
            text="Step 3: Scan Pixels & Compress (Auto-saves to output/)",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLOR_PRIMARY
        )
        lbl_step3.pack(anchor="w", padx=10, pady=(4, 4))

        action_row = ctk.CTkFrame(right_scroll, fg_color="transparent")
        action_row.pack(fill=tk.X, padx=10, pady=(0, 6))

        self.btn_run_compress = ctk.CTkButton(
            action_row,
            text="⚡ Compress Image",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            height=36,
            command=self._start_compress_thread
        )
        self.btn_run_compress.pack(side=tk.LEFT, padx=(0, 10))

        self.comp_progressbar = ctk.CTkProgressBar(action_row, mode="indeterminate", width=220)

        # Stats Card
        self.comp_stats_box = ctk.CTkFrame(right_scroll, corner_radius=8, fg_color=COLOR_CARD_SUB)
        self.comp_stats_box.pack(fill=tk.X, padx=10, pady=(0, 8))

        self.lbl_comp_stats = ctk.CTkLabel(
            self.comp_stats_box,
            text="Compression statistics will appear here after scanning.",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLOR_TEXT_MUTED,
            justify="left",
            anchor="w"
        )
        self.lbl_comp_stats.pack(anchor="w", padx=12, pady=10)

        self.lbl_autosave_notice = ctk.CTkLabel(
            right_scroll,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLOR_SUCCESS,
            anchor="w"
        )
        self.lbl_autosave_notice.pack(anchor="w", padx=10, pady=(0, 4))

        # Pixel String Preview Box
        lbl_str_preview = ctk.CTkLabel(
            right_scroll,
            text="Pixel String Snippet (Row/Column Structure):",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        )
        lbl_str_preview.pack(anchor="w", padx=10, pady=(2, 2))

        self.txt_string_preview = ctk.CTkTextbox(
            right_scroll,
            height=90,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color="#11111b",
            text_color=COLOR_SUCCESS
        )
        self.txt_string_preview.pack(fill=tk.X, padx=10, pady=(0, 8))

        # Step 4: Export Options
        lbl_step4 = ctk.CTkLabel(
            right_scroll,
            text="Step 4: Manual Save / Export",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLOR_PRIMARY
        )
        lbl_step4.pack(anchor="w", padx=10, pady=(4, 4))

        export_row = ctk.CTkFrame(right_scroll, fg_color="transparent")
        export_row.pack(fill=tk.X, padx=10, pady=(0, 15))

        self.btn_save_icomp = ctk.CTkButton(
            export_row,
            text="💾 Save Copy As (.icomp)",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            state="disabled",
            command=self._save_compressed_file
        )
        self.btn_save_icomp.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_save_txt = ctk.CTkButton(
            export_row,
            text="📄 Save Pixel String (.txt)",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            state="disabled",
            command=self._save_pixel_string_file
        )
        self.btn_save_txt.pack(side=tk.LEFT, padx=(0, 8))

        btn_open_folder = ctk.CTkButton(
            export_row,
            text="📁 Open output/ Folder",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            command=self._open_output_folder
        )
        btn_open_folder.pack(side=tk.LEFT)

    # =========================================================================
    # TAB 2: DECOMPRESS
    # =========================================================================
    def _build_decompress_tab(self):
        parent = self.tab_decompress

        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left Column: CTkScrollableFrame for controls
        left_scroll = ctk.CTkScrollableFrame(container, corner_radius=10, fg_color=COLOR_CARD, width=440)
        left_scroll.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=5)

        lbl_decomp_step1 = ctk.CTkLabel(
            left_scroll,
            text="Step 1: Select Compressed File",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cba6f7"
        )
        lbl_decomp_step1.pack(anchor="w", padx=10, pady=(10, 4))

        btn_browse_decomp = ctk.CTkButton(
            left_scroll,
            text="📂 Browse .icomp File...",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            command=self._browse_decompress_file
        )
        btn_browse_decomp.pack(fill=tk.X, padx=10, pady=(0, 6))

        self.lbl_decomp_file_path = ctk.CTkLabel(
            left_scroll,
            text="No .icomp file selected",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLOR_TEXT_MUTED,
            wraplength=400,
            justify="left"
        )
        self.lbl_decomp_file_path.pack(anchor="w", padx=10, pady=(0, 10))

        # Step 2: Decompress & Reconstruct
        lbl_decomp_step2 = ctk.CTkLabel(
            left_scroll,
            text="Step 2: Decompress & Reconstruct",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cba6f7"
        )
        lbl_decomp_step2.pack(anchor="w", padx=10, pady=(4, 4))

        self.btn_run_decompress = ctk.CTkButton(
            left_scroll,
            text="🔄 Decompress & Reconstruct Image",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#8b5cf6",
            hover_color="#7c3aed",
            state="disabled",
            height=36,
            command=self._start_decompress_thread
        )
        self.btn_run_decompress.pack(fill=tk.X, padx=10, pady=(0, 6))

        self.decomp_progressbar = ctk.CTkProgressBar(left_scroll, mode="indeterminate")

        # Decompression Stats Card
        self.decomp_stats_frame = ctk.CTkFrame(left_scroll, corner_radius=8, fg_color=COLOR_CARD_SUB)
        self.decomp_stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.lbl_decomp_stats = ctk.CTkLabel(
            self.decomp_stats_frame,
            text="Reconstruction details will appear here.",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLOR_TEXT_MUTED,
            justify="left",
            anchor="w"
        )
        self.lbl_decomp_stats.pack(anchor="w", padx=12, pady=10)

        # Step 3: Save Restored Image
        lbl_decomp_step3 = ctk.CTkLabel(
            left_scroll,
            text="Step 3: Save Restored Image",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#cba6f7"
        )
        lbl_decomp_step3.pack(anchor="w", padx=10, pady=(4, 4))

        self.btn_save_restored_png = ctk.CTkButton(
            left_scroll,
            text="💾 Save as Lossless PNG (Exact Pixels)",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            state="disabled",
            command=lambda: self._save_restored_image(format_ext=".png")
        )
        self.btn_save_restored_png.pack(fill=tk.X, padx=10, pady=(0, 6))

        self.btn_save_restored_webp = ctk.CTkButton(
            left_scroll,
            text="🚀 Save as Modern WebP (Best Size & Quality)",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            state="disabled",
            command=lambda: self._save_restored_image(format_ext=".webp")
        )
        self.btn_save_restored_webp.pack(fill=tk.X, padx=10, pady=(0, 8))

        # JPEG Quality Choice Frame
        jpeg_box = ctk.CTkFrame(left_scroll, corner_radius=8, fg_color=COLOR_CARD_SUB)
        jpeg_box.pack(fill=tk.X, padx=10, pady=(0, 8))

        lbl_jpeg_qual = ctk.CTkLabel(
            jpeg_box,
            text="Choose JPEG Export Quality:",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
        )
        lbl_jpeg_qual.pack(anchor="w", padx=12, pady=(6, 3))

        rb_jpeg_high = ctk.CTkRadioButton(
            jpeg_box,
            text="⭐ High Quality 95% (Full Color Resolution)",
            value=95,
            variable=self.jpeg_export_quality_var,
            font=ctk.CTkFont(family="Segoe UI", size=10)
        )
        rb_jpeg_high.pack(anchor="w", padx=12, pady=2)

        rb_jpeg_std = ctk.CTkRadioButton(
            jpeg_box,
            text="⚡ Standard 75% (Balanced Compression)",
            value=75,
            variable=self.jpeg_export_quality_var,
            font=ctk.CTkFont(family="Segoe UI", size=10)
        )
        rb_jpeg_std.pack(anchor="w", padx=12, pady=2)

        rb_jpeg_small = ctk.CTkRadioButton(
            jpeg_box,
            text="📦 Compact 60% (Maximum Compression)",
            value=60,
            variable=self.jpeg_export_quality_var,
            font=ctk.CTkFont(family="Segoe UI", size=10)
        )
        rb_jpeg_small.pack(anchor="w", padx=12, pady=(2, 6))

        self.btn_save_restored_jpeg = ctk.CTkButton(
            left_scroll,
            text="💾 Save as JPEG (Using Selected Quality)",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            state="disabled",
            command=lambda: self._save_restored_image(format_ext=".jpeg")
        )
        self.btn_save_restored_jpeg.pack(fill=tk.X, padx=10, pady=(0, 15))

        # Right Column: Reconstructed Image Preview
        right_frame = ctk.CTkFrame(container, corner_radius=10, fg_color=COLOR_CARD)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)

        lbl_recon_title = ctk.CTkLabel(
            right_frame,
            text="Reconstructed Image Preview",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=COLOR_SUCCESS
        )
        lbl_recon_title.pack(anchor="w", padx=15, pady=(15, 6))

        recon_box = ctk.CTkFrame(right_frame, corner_radius=8, fg_color=COLOR_CARD_SUB)
        recon_box.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        self.lbl_decomp_preview = ctk.CTkLabel(recon_box, text="Decompressed Image Preview", text_color=COLOR_TEXT_MUTED)
        self.lbl_decomp_preview.pack(expand=True)

        self.lbl_recon_dims = ctk.CTkLabel(
            right_frame,
            text="Dimensions: - | Total Pixels: -",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_MUTED
        )
        self.lbl_recon_dims.pack(padx=15, pady=(0, 15))

    # =========================================================================
    # TAB 3: LOSSLESS VERIFIER
    # =========================================================================
    def _build_verifier_tab(self):
        parent = self.tab_verifier

        container = ctk.CTkFrame(parent, corner_radius=10, fg_color=COLOR_CARD)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        title = ctk.CTkLabel(
            container,
            text="🔍 Lossless Pixel-for-Pixel Verifier",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#f9e2af"
        )
        title.pack(anchor="w", padx=20, pady=(20, 4))

        desc = ctk.CTkLabel(
            container,
            text="Verifies that the reconstructed image matches the original image with 100% precision (0 mismatched pixels).",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_MUTED
        )
        desc.pack(anchor="w", padx=20, pady=(0, 15))

        self.btn_verify = ctk.CTkButton(
            container,
            text="🔬 Run Verification On Current Images",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            height=36,
            command=self._start_verification_thread
        )
        self.btn_verify.pack(anchor="w", padx=20, pady=(0, 10))

        self.verifier_progressbar = ctk.CTkProgressBar(container, mode="indeterminate", width=300)

        self.verifier_results_frame = ctk.CTkFrame(container, corner_radius=8, fg_color=COLOR_CARD_SUB)
        self.verifier_results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        self.lbl_verifier_output = ctk.CTkLabel(
            self.verifier_results_frame,
            text="Compress an image and decompress it, then click 'Run Verification' to check lossless fidelity.",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLOR_TEXT_MUTED,
            justify="left",
            anchor="nw"
        )
        self.lbl_verifier_output.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

    # =========================================================================
    # COMPRESS EVENT HANDLERS
    # =========================================================================
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

            self.lbl_comp_file_path.configure(text=f"Selected: {path.name}")
            self.lbl_comp_dims.configure(text=f"Dimensions: {w}x{h} | Size: {file_size_kb:.1f} KB | Mode: {mode}")

            self._display_preview(self.lbl_comp_preview, self.compress_image_obj)
            self._set_status(f"Loaded image {path.name} ({w}x{h})")

            # Also sync to Direct Formatter if empty
            if self.formatter_image_path is None:
                self._load_formatter_image(path)
        except Exception as e:
            messagebox.showerror("Error Opening Image", f"Failed to open image:\n{e}")

    def _start_compress_thread(self):
        if not self.compress_image_obj:
            messagebox.showwarning("No Image Selected", "Please select an image first.")
            return

        self.btn_run_compress.configure(text="⏳ Compressing... (Please wait)", state="disabled")
        self.comp_progressbar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.comp_progressbar.start()
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
                stats = PixelCoder.compress_image_to_file(
                    self.compress_image_path or self.compress_image_obj,
                    auto_icomp_path,
                    mode=mode,
                    quality=quality
                )
                with open(auto_icomp_path, "rb") as f:
                    compressed_bytes = f.read()

                pixel_str, _ = PixelCoder.scan_image_to_string(
                    self.compress_image_obj,
                    mode=mode,
                    quality=quality
                )
                with open(auto_txt_path, "w", encoding="utf-8") as f:
                    f.write(pixel_str)
            else:
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
        self.btn_run_compress.configure(text="⚡ Compress Image", state="normal")
        self.btn_save_icomp.configure(state="normal")
        self.btn_save_txt.configure(state="normal")

        self.last_saved_icomp_path = auto_icomp_path
        self._load_decompress_file(auto_icomp_path)

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
        self.lbl_comp_stats.configure(text=stats_text, text_color=COLOR_SUCCESS)
        self.lbl_autosave_notice.configure(
            text=f"✅ Automatically saved to output/{auto_icomp_path.name} ({comp_kb:.2f} KB)",
            text_color=COLOR_SUCCESS
        )

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
        self.btn_run_compress.configure(text="⚡ Compress Image", state="normal")
        self.lbl_comp_stats.configure(text=f"❌ Error during compression:\n{error_msg}", text_color="#ef4444")
        messagebox.showerror("Compression Error", f"Failed to compress image:\n{error_msg}")
        self._set_status("Compression failed.")

    def _open_output_folder(self):
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

    # =========================================================================
    # DECOMPRESS EVENT HANDLERS
    # =========================================================================
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
        self.lbl_decomp_file_path.configure(text=f"Selected: {path.name} ({size_kb:.2f} KB)")
        self.btn_run_decompress.configure(state="normal")
        self._set_status(f"Loaded compressed file {path.name}")

    def _start_decompress_thread(self):
        if not self.decompress_file_path:
            return
        self.btn_run_decompress.configure(text="⏳ Decompressing... (Please wait)", state="disabled")
        self.decomp_progressbar.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.decomp_progressbar.start()
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
        self.btn_run_decompress.configure(text="🔄 Decompress & Reconstruct Image", state="normal")
        self.btn_save_restored_png.configure(state="normal")
        self.btn_save_restored_webp.configure(state="normal")
        self.btn_save_restored_jpeg.configure(state="normal")

        w, h = recon_img.size
        self.lbl_recon_dims.configure(text=f"Dimensions: {w}x{h} | Total Pixels: {w*h:,}")
        self._display_preview(self.lbl_decomp_preview, recon_img)

        format_name = recon_meta.get("format", "unknown").upper()
        q_info = f" (Q-Factor={recon_meta['q_factor']})" if "q_factor" in recon_meta else ""
        stats_text = (
            f"✅ Reconstructed Successfully!\n"
            f"• Format Decoded: {format_name}{q_info}\n"
            f"• Reconstructed Size: {w}x{h} ({w*h:,} pixels)\n"
            f"• Decompression Duration: {recon_meta.get('reconstruction_time_sec', 0.0):.3f}s"
        )
        self.lbl_decomp_stats.configure(text=stats_text, text_color=COLOR_SUCCESS)
        self._set_status(f"Decompression completed: {w}x{h} image restored.")

    def _on_decompression_error(self, error_msg: str):
        self.decomp_progressbar.stop()
        self.decomp_progressbar.pack_forget()
        self.btn_run_decompress.configure(text="🔄 Decompress & Reconstruct Image", state="normal")
        self.lbl_decomp_stats.configure(text=f"❌ Error during decompression:\n{error_msg}", text_color="#ef4444")
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

    # =========================================================================
    # VERIFIER EVENT HANDLERS
    # =========================================================================
    def _start_verification_thread(self):
        if not self.compress_image_obj:
            messagebox.showwarning("Missing Original", "Please load an original image first in the 'Compress' tab.")
            return
        if not self.reconstructed_image_obj:
            messagebox.showwarning("Missing Reconstructed", "Please decompress an image first in the 'Decompress' tab.")
            return

        self.btn_verify.configure(text="⏳ Verifying Pixels... (Please wait)", state="disabled")
        self.verifier_progressbar.pack(anchor="w", padx=20, pady=(0, 15))
        self.verifier_progressbar.start()
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
        self.btn_verify.configure(text="🔬 Run Verification On Current Images", state="normal")

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
            self.lbl_verifier_output.configure(text=report, text_color=COLOR_SUCCESS)
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
            self.lbl_verifier_output.configure(text=report, text_color="#facc15")
            self._set_status("Verification complete.")

    def _on_verification_error(self, error_msg: str):
        self.verifier_progressbar.stop()
        self.verifier_progressbar.pack_forget()
        self.btn_verify.configure(text="🔬 Run Verification On Current Images", state="normal")
        messagebox.showerror("Verification Error", f"Failed to verify images:\n{error_msg}")
        self._set_status("Verification failed.")

    # =========================================================================
    # TAB 4: DIRECT FORMATTER
    # =========================================================================
    def _build_formatter_tab(self):
        parent = self.tab_formatter

        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left Column: Image Selection & Preview
        left_frame = ctk.CTkFrame(container, corner_radius=10, fg_color=COLOR_CARD, width=360)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=5)
        left_frame.pack_propagate(False)

        lbl_step1 = ctk.CTkLabel(
            left_frame,
            text="Step 1: Select Input Image",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#f59e0b"
        )
        lbl_step1.pack(anchor="w", padx=15, pady=(15, 6))

        btn_browse = ctk.CTkButton(
            left_frame,
            text="📂 Browse Image...",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#f59e0b",
            hover_color="#d97706",
            command=self._browse_formatter_image
        )
        btn_browse.pack(fill=tk.X, padx=15, pady=(0, 6))

        self.lbl_format_file_path = ctk.CTkLabel(
            left_frame,
            text="No image selected",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLOR_TEXT_MUTED,
            wraplength=320,
            justify="left"
        )
        self.lbl_format_file_path.pack(anchor="w", padx=15, pady=(0, 6))

        # Preview Container
        preview_box = ctk.CTkFrame(left_frame, corner_radius=8, fg_color=COLOR_CARD_SUB, height=310)
        preview_box.pack(fill=tk.X, padx=15, pady=4)
        preview_box.pack_propagate(False)

        self.lbl_format_preview = ctk.CTkLabel(preview_box, text="Image Preview", text_color=COLOR_TEXT_MUTED)
        self.lbl_format_preview.pack(expand=True)

        self.lbl_format_dims = ctk.CTkLabel(
            left_frame,
            text="Dimensions: - | Size: - | Mode: -",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLOR_TEXT_MUTED
        )
        self.lbl_format_dims.pack(padx=15, pady=(6, 10))

        btn_open_out = ctk.CTkButton(
            left_frame,
            text="📁 Open Output Folder",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            command=self._open_output_folder
        )
        btn_open_out.pack(fill=tk.X, padx=15, pady=(0, 15))

        # Right Column: Scrollable Format Options & Action
        right_scroll = ctk.CTkScrollableFrame(container, corner_radius=10, fg_color=COLOR_CARD)
        right_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)

        lbl_step2 = ctk.CTkLabel(
            right_scroll,
            text="Step 2: Choose Output Format & Quality Preset",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#f59e0b"
        )
        lbl_step2.pack(anchor="w", padx=10, pady=(10, 4))

        preset_box = ctk.CTkFrame(right_scroll, corner_radius=8, fg_color=COLOR_CARD_SUB)
        preset_box.pack(fill=tk.X, padx=10, pady=(0, 8))

        # Modern WebP Section
        lbl_webp_hdr = ctk.CTkLabel(
            preset_box,
            text="🚀 MODERN WEBP FORMAT (RECOMMENDED — BEST COMPRESSION & QUALITY):",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=COLOR_SUCCESS
        )
        lbl_webp_hdr.pack(anchor="w", padx=12, pady=(8, 2))

        rb_w95 = ctk.CTkRadioButton(
            preset_box,
            text="🚀 WebP High Quality 95% (Near-Lossless, Superior Compression)\n   Preserves crisp details with advanced entropy coding. Recommended for photos & web.",
            value="webp_95",
            variable=self.formatter_preset_var,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        rb_w95.pack(anchor="w", padx=12, pady=3)

        rb_w85 = ctk.CTkRadioButton(
            preset_box,
            text="⚡ WebP Balanced 85% (Optimized Web Delivery)\n   Optimal balance between high visual fidelity and fast loading.",
            value="webp_85",
            variable=self.formatter_preset_var,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        rb_w85.pack(anchor="w", padx=12, pady=3)

        rb_w75 = ctk.CTkRadioButton(
            preset_box,
            text="📦 WebP Standard 75% (Maximum WebP Compression)\n   Lightweight file size while retaining good visual clarity.",
            value="webp_75",
            variable=self.formatter_preset_var,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        rb_w75.pack(anchor="w", padx=12, pady=3)

        rb_wlossless = ctk.CTkRadioButton(
            preset_box,
            text="🛡️ WebP Lossless 100% (Bit-for-Bit Exact Pixels)\n   True mathematical lossless encoding without any pixel error.",
            value="webp_lossless",
            variable=self.formatter_preset_var,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        rb_wlossless.pack(anchor="w", padx=12, pady=3)

        # Optimized JPEG Section
        lbl_jpeg_hdr = ctk.CTkLabel(
            preset_box,
            text="📸 OPTIMIZED JPEG FORMAT (UNIVERSAL COMPATIBILITY):",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=COLOR_PRIMARY
        )
        lbl_jpeg_hdr.pack(anchor="w", padx=12, pady=(10, 2))

        rb_j95 = ctk.CTkRadioButton(
            preset_box,
            text="⭐ JPEG High Quality 95% (Full 4:4:4 Chroma Subsampling)\n   Strips bloated metadata while keeping full color resolution without color bleed.",
            value="jpeg_95",
            variable=self.formatter_preset_var,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        rb_j95.pack(anchor="w", padx=12, pady=3)

        rb_j75 = ctk.CTkRadioButton(
            preset_box,
            text="⚡ JPEG Standard 75% (Standard 4:2:0 Subsampling)\n   Balanced compression, perfect for general web sharing and documents.",
            value="jpeg_75",
            variable=self.formatter_preset_var,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        rb_j75.pack(anchor="w", padx=12, pady=3)

        rb_j60 = ctk.CTkRadioButton(
            preset_box,
            text="📦 JPEG Compact 60% (Maximum JPEG Compression)\n   Smallest JPEG file size for thumbnails and previews.",
            value="jpeg_60",
            variable=self.formatter_preset_var,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        rb_j60.pack(anchor="w", padx=12, pady=3)

        # Lossless PNG Section
        lbl_png_hdr = ctk.CTkLabel(
            preset_box,
            text="💎 LOSSLESS PNG FORMAT (PRESERVES TRANSPARENCY):",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#cba6f7"
        )
        lbl_png_hdr.pack(anchor="w", padx=12, pady=(10, 2))

        rb_png = ctk.CTkRadioButton(
            preset_box,
            text="💎 Lossless PNG (Optimized zlib Level 9)\n   Preserves full alpha transparency with 100% exact pixels.",
            value="png_lossless",
            variable=self.formatter_preset_var,
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        rb_png.pack(anchor="w", padx=12, pady=(3, 8))

        # Step 3: Run Format & Optimize
        lbl_step3 = ctk.CTkLabel(
            right_scroll,
            text="Step 3: Convert & Optimize (Auto-saves to output/)",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#f59e0b"
        )
        lbl_step3.pack(anchor="w", padx=10, pady=(4, 4))

        format_action_row = ctk.CTkFrame(right_scroll, fg_color="transparent")
        format_action_row.pack(fill=tk.X, padx=10, pady=(0, 6))

        self.btn_run_format = ctk.CTkButton(
            format_action_row,
            text="⚡ Format & Optimize Now",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#f59e0b",
            hover_color="#d97706",
            height=36,
            command=self._start_format_thread
        )
        self.btn_run_format.pack(side=tk.LEFT, padx=(0, 10))

        self.format_progressbar = ctk.CTkProgressBar(format_action_row, mode="indeterminate", width=220)

        # Stats Card
        self.format_stats_box = ctk.CTkFrame(right_scroll, corner_radius=8, fg_color=COLOR_CARD_SUB)
        self.format_stats_box.pack(fill=tk.X, padx=10, pady=(0, 8))

        self.lbl_format_stats = ctk.CTkLabel(
            self.format_stats_box,
            text="Formatting statistics and size reduction comparison will appear here.",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=COLOR_TEXT_MUTED,
            justify="left",
            anchor="w"
        )
        self.lbl_format_stats.pack(anchor="w", padx=12, pady=10)

        self.lbl_format_autosave_notice = ctk.CTkLabel(
            right_scroll,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLOR_SUCCESS,
            anchor="w"
        )
        self.lbl_format_autosave_notice.pack(anchor="w", padx=10, pady=(0, 8))

        # Step 4: Actions
        lbl_step4 = ctk.CTkLabel(
            right_scroll,
            text="Step 4: Output Actions",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#f59e0b"
        )
        lbl_step4.pack(anchor="w", padx=10, pady=(4, 4))

        actions_row = ctk.CTkFrame(right_scroll, fg_color="transparent")
        actions_row.pack(fill=tk.X, padx=10, pady=(0, 15))

        self.btn_open_formatted_file = ctk.CTkButton(
            actions_row,
            text="👁️ Open Formatted Image",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            state="disabled",
            command=self._open_last_formatted_file
        )
        self.btn_open_formatted_file.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_save_format_copy = ctk.CTkButton(
            actions_row,
            text="💾 Save Copy As...",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            state="disabled",
            command=self._save_formatted_file_copy
        )
        self.btn_save_format_copy.pack(side=tk.LEFT, padx=(0, 8))

        btn_open_folder2 = ctk.CTkButton(
            actions_row,
            text="📁 Open output/ Folder",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            command=self._open_output_folder
        )
        btn_open_folder2.pack(side=tk.LEFT)

    # =========================================================================
    # DIRECT FORMATTER EVENT HANDLERS
    # =========================================================================
    def _browse_formatter_image(self):
        initial_dir = IMAGES_DIR if IMAGES_DIR.exists() else Path.cwd()
        file_path = filedialog.askopenfilename(
            title="Select Image to Format & Optimize",
            initialdir=str(initial_dir),
            filetypes=IMAGE_EXTENSIONS
        )
        if file_path:
            self._load_formatter_image(Path(file_path))

    def _load_formatter_image(self, path: Path):
        try:
            self.formatter_image_path = path
            self.formatter_image_obj = Image.open(path)

            file_size_kb = path.stat().st_size / 1024
            w, h = self.formatter_image_obj.size
            mode = self.formatter_image_obj.mode

            self.lbl_format_file_path.configure(text=f"Selected: {path.name}")
            self.lbl_format_dims.configure(text=f"Dimensions: {w}x{h} | Size: {file_size_kb:.1f} KB | Mode: {mode}")

            self._display_preview(self.lbl_format_preview, self.formatter_image_obj)
            self._set_status(f"Loaded image {path.name} for direct formatting ({w}x{h})")
        except Exception as e:
            messagebox.showerror("Error Opening Image", f"Failed to open image:\n{e}")

    def _start_format_thread(self):
        if not self.formatter_image_obj:
            messagebox.showwarning("No Image Selected", "Please select an image first.")
            return

        self.btn_run_format.configure(text="⏳ Formatting & Optimizing... (Please wait)", state="disabled")
        self.format_progressbar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.format_progressbar.start()
        self._set_status("Directly formatting and optimizing image...")
        self.update_idletasks()

        preset = self.formatter_preset_var.get()
        threading.Thread(target=self._execute_formatting, args=(preset,), daemon=True).start()

    def _execute_formatting(self, preset: str):
        try:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            stem = self.formatter_image_path.stem if self.formatter_image_path else "formatted"

            if preset == "webp_95":
                out_path = OUTPUT_DIR / f"{stem}_optimized_q95.webp"
                result = PixelCoder.format_image_direct(
                    self.formatter_image_path or self.formatter_image_obj,
                    out_path, target_format="WEBP", quality=95
                )
            elif preset == "webp_85":
                out_path = OUTPUT_DIR / f"{stem}_optimized_q85.webp"
                result = PixelCoder.format_image_direct(
                    self.formatter_image_path or self.formatter_image_obj,
                    out_path, target_format="WEBP", quality=85
                )
            elif preset == "webp_75":
                out_path = OUTPUT_DIR / f"{stem}_optimized_q75.webp"
                result = PixelCoder.format_image_direct(
                    self.formatter_image_path or self.formatter_image_obj,
                    out_path, target_format="WEBP", quality=75
                )
            elif preset == "webp_lossless":
                out_path = OUTPUT_DIR / f"{stem}_lossless.webp"
                result = PixelCoder.format_image_direct(
                    self.formatter_image_path or self.formatter_image_obj,
                    out_path, target_format="WEBP", quality=100, lossless=True
                )
            elif preset == "jpeg_95":
                out_path = OUTPUT_DIR / f"{stem}_optimized_q95.jpeg"
                result = PixelCoder.format_image_direct(
                    self.formatter_image_path or self.formatter_image_obj,
                    out_path, target_format="JPEG", quality=95, subsampling=0
                )
            elif preset == "jpeg_75":
                out_path = OUTPUT_DIR / f"{stem}_optimized_q75.jpeg"
                result = PixelCoder.format_image_direct(
                    self.formatter_image_path or self.formatter_image_obj,
                    out_path, target_format="JPEG", quality=75, subsampling=2
                )
            elif preset == "jpeg_60":
                out_path = OUTPUT_DIR / f"{stem}_optimized_q60.jpeg"
                result = PixelCoder.format_image_direct(
                    self.formatter_image_path or self.formatter_image_obj,
                    out_path, target_format="JPEG", quality=60, subsampling=2
                )
            elif preset == "png_lossless":
                out_path = OUTPUT_DIR / f"{stem}_optimized.png"
                result = PixelCoder.format_image_direct(
                    self.formatter_image_path or self.formatter_image_obj,
                    out_path, target_format="PNG", lossless=True
                )
            else:
                out_path = OUTPUT_DIR / f"{stem}_optimized.webp"
                result = PixelCoder.format_image_direct(
                    self.formatter_image_path or self.formatter_image_obj,
                    out_path, target_format="WEBP", quality=95
                )

            self.after(0, self._on_format_complete, result)
        except Exception as e:
            self.after(0, self._on_format_error, str(e))

    def _on_format_complete(self, result: dict):
        self.last_formatted_path = result["output_path"]

        self.format_progressbar.stop()
        self.format_progressbar.pack_forget()
        self.btn_run_format.configure(text="⚡ Format & Optimize Now", state="normal")
        self.btn_open_formatted_file.configure(state="normal")
        self.btn_save_format_copy.configure(state="normal")

        orig_kb = result["original_size_bytes"] / 1024
        out_kb = result["output_size_bytes"] / 1024
        savings_kb = result["savings_bytes"] / 1024
        savings_pct = result["savings_pct"]

        stats_text = (
            f"🎉 Formatting Succeeded & Automatically Saved!\n"
            f"• Output Format: {result['target_format']} (Quality={result['quality']}%)\n"
            f"• Dimensions: {result['width']}x{result['height']}\n"
            f"• Original File on Disk: {orig_kb:.2f} KB ({result['original_size_bytes']:,} bytes)\n"
            f"• Optimized Output Size: {out_kb:.2f} KB ({result['output_size_bytes']:,} bytes)\n"
            f"• Space Saved: {savings_pct:+.1f}% ({savings_kb:.1f} KB saved)\n"
            f"• Processing Time: {result['duration_sec']:.3f}s\n"
            f"• 💾 Saved to: output/{result['output_path'].name}"
        )
        self.lbl_format_stats.configure(text=stats_text, text_color=COLOR_SUCCESS)
        self.lbl_format_autosave_notice.configure(
            text=f"✅ Automatically saved to output/{result['output_path'].name} ({out_kb:.2f} KB)",
            text_color=COLOR_SUCCESS
        )
        self._set_status(f"Format complete: output/{result['output_path'].name} ({out_kb:.2f} KB, {savings_pct:+.1f}%)")

    def _on_format_error(self, error_msg: str):
        self.format_progressbar.stop()
        self.format_progressbar.pack_forget()
        self.btn_run_format.configure(text="⚡ Format & Optimize Now", state="normal")
        self.lbl_format_stats.configure(text=f"❌ Error during formatting:\n{error_msg}", text_color="#ef4444")
        messagebox.showerror("Formatting Error", f"Failed to format image:\n{error_msg}")
        self._set_status("Formatting failed.")

    def _open_last_formatted_file(self):
        if self.last_formatted_path and self.last_formatted_path.exists():
            os.startfile(str(self.last_formatted_path))

    def _save_formatted_file_copy(self):
        if not self.last_formatted_path or not self.last_formatted_path.exists():
            return
        ext = self.last_formatted_path.suffix.lower()
        if ext == ".webp":
            types = [("WebP Image (*.webp)", "*.webp"), ("All Files", "*.*")]
        elif ext in (".jpeg", ".jpg"):
            types = [("JPEG Image (*.jpeg;*.jpg)", "*.jpeg;*.jpg"), ("All Files", "*.*")]
        elif ext == ".png":
            types = [("PNG Image (*.png)", "*.png"), ("All Files", "*.*")]
        else:
            types = [("All Files", "*.*")]

        file_path = filedialog.asksaveasfilename(
            title="Save Formatted Copy As...",
            initialdir=str(OUTPUT_DIR),
            initialfile=self.last_formatted_path.name,
            defaultextension=ext,
            filetypes=types
        )
        if file_path:
            with open(self.last_formatted_path, "rb") as src_f, open(file_path, "wb") as dst_f:
                dst_f.write(src_f.read())
            self._set_status(f"Saved copy to {Path(file_path).name}")
            messagebox.showinfo("Saved", f"Copy saved successfully to:\n{file_path}")

    # =========================================================================
    # HELPERS
    # =========================================================================
    def _display_preview(self, label: ctk.CTkLabel, img: Image.Image, max_w: int = 320, max_h: int = 300):
        """Creates a high-DPI aspect-ratio preserved preview in a CTkLabel."""
        orig_w, orig_h = img.size
        ratio = min(max_w / orig_w, max_h / orig_h)
        thumb_w = max(1, int(orig_w * ratio))
        thumb_h = max(1, int(orig_h * ratio))

        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(thumb_w, thumb_h))
        label.configure(image=ctk_img, text="")
        label.image = ctk_img

    def _set_status(self, text: str):
        self.status_bar.configure(text=f"Status: {text}")

    def _show_about_dialog(self):
        """Displays an attractive About dialog with author and copyright details."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("About PixelScan")
        dialog.geometry("480x340")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)

        # Center relative to main app window
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 480) // 2
        y = self.winfo_y() + (self.winfo_height() - 340) // 2
        dialog.geometry(f"+{x}+{y}")

        card = ctk.CTkFrame(dialog, corner_radius=12, fg_color=COLOR_CARD)
        card.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        lbl_app_title = ctk.CTkLabel(
            card,
            text="⚡ PixelScan Image Compressor",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLOR_PRIMARY
        )
        lbl_app_title.pack(pady=(20, 4))

        lbl_ver = ctk.CTkLabel(
            card,
            text=f"Version {APP_VERSION} — CustomTkinter Edition",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLOR_TEXT_MUTED
        )
        lbl_ver.pack(pady=(0, 15))

        info_text = (
            "An advanced image compression, decompression,\n"
            "lossless pixel verification, and direct optimization suite.\n\n"
            "Developed by: Hasitha Wijesinghe\n"
            "GitHub: https://github.com/HasithaLWi\n"
            "License: MIT License\n\n"
            "Copyright © 2026 Hasitha Wijesinghe. All rights reserved."
        )
        lbl_info = ctk.CTkLabel(
            card,
            text=info_text,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#e2e8f0",
            justify="center"
        )
        lbl_info.pack(pady=(0, 20))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=(0, 15))

        btn_view_license = ctk.CTkButton(
            btn_row,
            text="📄 View License",
            width=120,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=COLOR_SECONDARY,
            hover_color=COLOR_SECONDARY_HOVER,
            command=self._show_license_dialog
        )
        btn_view_license.pack(side=tk.LEFT, padx=6)

        btn_close = ctk.CTkButton(
            btn_row,
            text="Close",
            width=100,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=dialog.destroy
        )
        btn_close.pack(side=tk.LEFT, padx=6)

    def _show_license_dialog(self):
        """Displays the full MIT license text in a modal dialog."""
        lic_dialog = ctk.CTkToplevel(self)
        lic_dialog.title("PixelScan — MIT License")
        lic_dialog.geometry("560x420")
        lic_dialog.resizable(False, False)
        lic_dialog.attributes("-topmost", True)

        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 560) // 2
        y = self.winfo_y() + (self.winfo_height() - 420) // 2
        lic_dialog.geometry(f"+{x}+{y}")

        card = ctk.CTkFrame(lic_dialog, corner_radius=12, fg_color=COLOR_CARD)
        card.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        lbl_title = ctk.CTkLabel(
            card,
            text="MIT License",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLOR_PRIMARY
        )
        lbl_title.pack(pady=(15, 6))

        txt_box = ctk.CTkTextbox(
            card,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#11111b",
            text_color="#cdd6f4"
        )
        txt_box.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 12))

        license_path = Path(__file__).resolve().parent.parent.parent.parent / "LICENSE"
        if license_path.exists():
            try:
                license_text = license_path.read_text(encoding="utf-8")
            except Exception:
                license_text = self._get_default_license_text()
        else:
            license_text = self._get_default_license_text()

        txt_box.insert("1.0", license_text)
        txt_box.configure(state="disabled")

        btn_close = ctk.CTkButton(
            card,
            text="Close",
            width=100,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=lic_dialog.destroy
        )
        btn_close.pack(pady=(0, 15))

    def _get_default_license_text(self) -> str:
        return (
            "MIT License\n\n"
            "Copyright (c) 2026 Hasitha Wijesinghe (https://github.com/HasithaLWi)\n\n"
            "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
            "of this software and associated documentation files (the \"Software\"), to deal\n"
            "in the Software without restriction, including without limitation the rights\n"
            "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
            "copies of the Software, and to permit persons to whom the Software is\n"
            "furnished to do so, subject to the following conditions:\n\n"
            "The above copyright notice and this permission notice shall be included in all\n"
            "copies or substantial portions of the Software.\n\n"
            "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
            "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
            "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
            "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
            "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
            "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
            "SOFTWARE."
        )



def launch_gui():
    """Launches the CustomTkinter desktop application."""
    app = ImageCompressorApp()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
