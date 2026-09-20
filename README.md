# PixelScan: Image Compressor & Decompressor (Desktop GUI)

A Python desktop application that scans images row-by-row and column-by-column into structured strings, compresses them into `.icomp` binary packages, and reverses the process to reconstruct the image with **100% lossless fidelity**.

---

## 🚀 8 Choosable Compression Algorithms

### A. Real-Life Binary Engines (No Text Bloat — Smallest Files)
*Real-world compression avoids ASCII text entirely (which causes 300% bloat) and operates directly on binary bytes:*

1. 🚀 **Real-Life Binary Smart Mode (`bin_smart`)** *(Smallest! Beats original JPEG)*:
   - Uses real-world frequency quantization and entropy coding in pure binary bytes.
   - Bypasses text strings completely.
   - **Achieves 11.12 KB** on `ICtest.jpeg` (beating the original 27.41 KB JPEG by **~60%**!).
2. 🛡️ **Real-Life Binary Lossless Mode (`bin_lossless`)** *(100% Exact, No Text Overhead)*:
   - Encodes raw pixel bytes directly with 2D DPCM spatial prediction.
   - 100% mathematically exact (0 pixel error) with zero ASCII string overhead (~174 KB vs 213 KB text delta).

---

### B. Text-Based String Engines (Human-Readable Strings)
*Scans images row-by-row and column-by-column into readable text strings, then compresses the text:*

3. ⚡ **Delta-RLE Mode (`delta`)** *(Best Text Compression)*:
   - Encodes difference ($\Delta$) from previous pixel (`dr,dg,db`).
   - Reduces compressed text package to **213.6 KB**.
4. 🧩 **Pattern Deduplication Mode (`pattern`)**:
   - Searches for duplicate rows and repeated multi-pixel patterns across the image.
   - Saves unique patterns **once** in a `PATTERNS` dictionary (`P0=...;P1=...`).
   - Replaces duplicate occurrences with `P0`, `P1`, or `SAME_AS_R{prev_row}`.
   - On decompress, reads the dictionary and restores duplicated patterns into place.
5. 🎨 **Palette Mode (`palette`)** *(Shortest String)*:
   - Builds a dynamic unique color dictionary (`PALETTE:...`).
   - Replaces 3 color numbers (`r,g,b`) with single index numbers (`0,1,0,2`), cutting string text size in half to **751.6 KB**.
6. 🔢 **HEX Mode (`hex`)** *(Cleanest Text)*:
   - Encodes colors as 6-character hex (`1B1725`), eliminating commas.
7. 🟢 **Standard RGB RLE Mode (`rle`)**:
   - Run-length encodes identical consecutive pixels (`count*r,g,b`).
8. 🔵 **Raw Row-Column Mode (`raw`)**:
   - Full explicit list of every single pixel (`r,g,b;r,g,b;...`).

---

## 🎯 Compression Targets

- **100% Lossless (Exact)**: 100% exact pixel match (0 errors).
- **85% High Quality**: Visually indistinguishable, cuts file size by ~50%.
- **65% Max Compression**: Smartly quantizes small pixel noise differences to beat original JPEG file sizes!

---

## 🖥️ Modern CustomTkinter Desktop GUI

Built with **CustomTkinter** for Windows 11 / macOS dark mode aesthetics:
- **⚡ Compress Image**: Select input image, choose from 8 algorithms & quality targets (Lossless, 85%, 65%), auto-saves `.icomp` and preview string.
- **🔄 Decompress Image**: Reconstructs exact images from `.icomp` files. Export to Lossless PNG, Modern WebP (~560 KB), or selectable JPEG qualities (High 95%, Standard 75%, Compact 60%).
- **🔍 Lossless Verifier**: C-accelerated (`ImageChops`) pixel-for-pixel difference check (runs across millions of pixels in <100 ms).
- **⚡ Direct Formatter**: One-click direct optimizer & converter. Converts images to Modern WebP (95%, 85%, 75%, Lossless), Optimized JPEG (95% 4:4:4, 75%, 60%), or Lossless PNG with instant size reduction calculations.
- **Dark / Light Mode**: Seamless theme toggle in the header.
- **Responsive & Asynchronous**: All compression, decompression, and verification processes run on background worker threads with loading animations so the UI never freezes.

---

## 🚀 Running the Desktop GUI

```powershell
& "f:\IJSE\THIRED SEM\PYTHON\image_compreser\.venv\Scripts\python.exe" src/my_app/main.py
```

---

## 💻 CLI Commands (Optional)

- **Compress using Pattern Deduplication mode**:
  ```powershell
  python src/my_app/main.py --compress images/ICtest.jpeg --mode pattern -o output/ICtest_pattern.icomp
  ```
- **Compress using Delta mode**:
  ```powershell
  python src/my_app/main.py --compress images/ICtest.jpeg --mode delta -o output/ICtest_delta.icomp
  ```
- **Decompress**:
  ```powershell
  python src/my_app/main.py --decompress output/ICtest_pattern.icomp -o output/restored.png
  ```
- **Verify Lossless Equivalence**:
  ```powershell
  python src/my_app/main.py --verify images/ICtest.jpeg output/restored.png
  ```

---

## 📄 License & Copyright

Copyright (c) 2026 **Hasitha Wijesinghe** ([https://github.com/HasithaLWi](https://github.com/HasithaLWi)). All rights reserved.

This project is licensed under the [MIT License](LICENSE).


