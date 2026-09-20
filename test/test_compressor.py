"""Unit tests for PixelCoder image compressor and decompressor across all modes."""
import unittest
from pathlib import Path
from PIL import Image

from src.my_app.config import (
    ALL_MODES,
    MODE_BIN_LOSSLESS,
    MODE_BIN_SMART,
    MODE_DELTA,
    MODE_HEX,
    MODE_PALETTE,
    MODE_PATTERN,
    MODE_RAW,
    MODE_RLE,
)
from src.my_app.core.pixel_coder import PixelCoder


class TestPixelCoder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Prefer ICtest.jpeg if present; otherwise generate a clean 200x200 test sample
        cls.image_path = Path("images/ICtest.jpeg")
        if not cls.image_path.exists():
            cls.image_path = Path("images/test_sample.png")
            if not cls.image_path.exists():
                cls.image_path.parent.mkdir(parents=True, exist_ok=True)
                img = Image.new("RGB", (200, 200), color=(120, 150, 180))
                # Add some variation to test RLE and patterns
                for y in range(50, 150):
                    for x in range(50, 150):
                        img.putpixel((x, y), (200, 100, 50))
                img.save(cls.image_path)

    def _test_text_mode(self, mode_name: str):
        with Image.open(self.image_path) as img:
            w, h = img.size
        pixel_str, meta = PixelCoder.scan_image_to_string(self.image_path, mode=mode_name)
        self.assertEqual(meta["width"], w)
        self.assertEqual(meta["height"], h)
        self.assertEqual(meta["mode"], mode_name)
        self.assertEqual(meta["total_pixels"], w * h)

        reconstructed, recon_meta = PixelCoder.string_to_image(pixel_str)
        self.assertEqual(reconstructed.size, (w, h))
        self.assertEqual(recon_meta["total_pixels"], w * h)

        verification = PixelCoder.verify_lossless(self.image_path, reconstructed)
        self.assertTrue(verification["is_identical"], f"Mode {mode_name} failed lossless check!")
        self.assertEqual(verification["mismatched_pixels"], 0)
        self.assertEqual(verification["match_percentage"], 100.0)

    def test_delta_mode(self):
        self._test_text_mode(MODE_DELTA)

    def test_pattern_mode(self):
        self._test_text_mode(MODE_PATTERN)

    def test_palette_mode(self):
        self._test_text_mode(MODE_PALETTE)

    def test_hex_mode(self):
        self._test_text_mode(MODE_HEX)

    def test_rle_mode(self):
        self._test_text_mode(MODE_RLE)

    def test_raw_mode(self):
        self._test_text_mode(MODE_RAW)

    def test_binary_lossless_mode(self):
        out_icomp = Path("output/test_bin_lossless.icomp")
        out_png = Path("output/test_bin_lossless.png")
        try:
            with Image.open(self.image_path) as img:
                w, h = img.size
            res = PixelCoder.compress_image_to_file(self.image_path, out_icomp, mode=MODE_BIN_LOSSLESS)
            self.assertTrue(out_icomp.exists())

            recon_img, dec_meta = PixelCoder.decompress_file_to_image(out_icomp, out_png)
            self.assertEqual(recon_img.size, (w, h))
            self.assertEqual(dec_meta["format"], "bin_lossless")

            verification = PixelCoder.verify_lossless(self.image_path, recon_img)
            self.assertTrue(verification["is_identical"], "Binary Lossless must be 100% exact!")
        finally:
            if out_icomp.exists():
                out_icomp.unlink()
            if out_png.exists():
                out_png.unlink()

    def test_binary_smart_mode(self):
        out_icomp = Path("output/test_bin_smart.icomp")
        out_png = Path("output/test_bin_smart.png")
        try:
            with Image.open(self.image_path) as img:
                w, h = img.size
            res = PixelCoder.compress_image_to_file(self.image_path, out_icomp, mode=MODE_BIN_SMART, quality=80)
            self.assertTrue(out_icomp.exists())

            recon_img, dec_meta = PixelCoder.decompress_file_to_image(out_icomp, out_png)
            self.assertEqual(recon_img.size, (w, h))
            self.assertEqual(dec_meta["format"], "bin_smart")
        finally:
            if out_icomp.exists():
                out_icomp.unlink()
            if out_png.exists():
                out_png.unlink()

    def test_direct_formatter(self):
        webp_out = Path("output/test_direct.webp")
        jpeg_out = Path("output/test_direct.jpeg")
        png_out = Path("output/test_direct.png")
        try:
            # WebP test
            res_webp = PixelCoder.format_image_direct(self.image_path, webp_out, target_format="WEBP", quality=95)
            self.assertTrue(webp_out.exists())
            self.assertEqual(res_webp["target_format"], "WEBP")
            self.assertGreater(res_webp["output_size_bytes"], 0)

            # JPEG test
            res_jpeg = PixelCoder.format_image_direct(self.image_path, jpeg_out, target_format="JPEG", quality=95, subsampling=0)
            self.assertTrue(jpeg_out.exists())
            self.assertEqual(res_jpeg["target_format"], "JPEG")
            self.assertGreater(res_jpeg["output_size_bytes"], 0)

            # PNG test
            res_png = PixelCoder.format_image_direct(self.image_path, png_out, target_format="PNG", lossless=True)
            self.assertTrue(png_out.exists())
            self.assertEqual(res_png["target_format"], "PNG")
            self.assertGreater(res_png["output_size_bytes"], 0)
        finally:
            for p in (webp_out, jpeg_out, png_out):
                if p.exists():
                    p.unlink()


if __name__ == "__main__":
    unittest.main()

