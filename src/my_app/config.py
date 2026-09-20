"""Configuration and constants for Image Compressor & Decompressor."""
from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
IMAGES_DIR = PROJECT_ROOT / "images"
OUTPUT_DIR = PROJECT_ROOT / "output"

# File Extensions
IMAGE_EXTENSIONS = [
    ("All Supported Images", "*.jpeg;*.jpg;*.png;*.bmp;*.webp"),
    ("JPEG Images", "*.jpeg;*.jpg"),
    ("PNG Images", "*.png"),
    ("BMP Images", "*.bmp"),
    ("WebP Images", "*.webp"),
    ("All Files", "*.*")
]

COMPRESSED_EXTENSIONS = [
    ("Compressed Image Package (*.icomp)", "*.icomp"),
    ("All Files", "*.*")
]

TEXT_EXTENSIONS = [
    ("Pixel String Text File (*.txt)", "*.txt"),
    ("All Files", "*.*")
]

DEFAULT_COMPRESSED_EXT = ".icomp"
DEFAULT_TEXT_EXT = ".txt"

# Serialization & Compression Modes
MODE_BIN_SMART = "bin_smart"         # Real-life Binary Smart (Beats JPEG, ~11-20 KB)
MODE_BIN_LOSSLESS = "bin_lossless"   # Real-life Binary Lossless (No text bloat, 100% exact, ~174 KB)
MODE_DELTA = "delta"                 # Delta-RLE String
MODE_PATTERN = "pattern"             # Pattern Deduplication String (User Idea)
MODE_PALETTE = "palette"             # Color Palette String
MODE_HEX = "hex"                     # Hexadecimal String
MODE_RLE = "rle"                     # Standard RGB RLE String
MODE_RAW = "raw"                     # Raw String

ALL_MODES = [
    MODE_BIN_SMART,
    MODE_BIN_LOSSLESS,
    MODE_DELTA,
    MODE_PATTERN,
    MODE_PALETTE,
    MODE_HEX,
    MODE_RLE,
    MODE_RAW
]
