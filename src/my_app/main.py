"""Entry point for PixelScan Image Compressor & Decompressor."""
import argparse
import sys
from pathlib import Path

# Add project root to sys.path to enable direct execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.my_app.core.pixel_coder import PixelCoder
from src.my_app.gui.app import launch_gui


def parse_args():
    parser = argparse.ArgumentParser(
        description="PixelScan: Row/Column Scanning Image Compressor & Decompressor"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the modern Tkinter Desktop GUI (default when no CLI flags provided)."
    )
    parser.add_argument(
        "--compress",
        type=str,
        help="Path to an image file to compress."
    )
    parser.add_argument(
        "--decompress",
        type=str,
        help="Path to a .icomp file to decompress."
    )
    parser.add_argument(
        "--mode",
        choices=["bin_smart", "bin_lossless", "delta", "pattern", "palette", "hex", "rle", "raw"],
        default="bin_smart",
        help="Compression mode: 'bin_smart' (default, smallest!), 'bin_lossless', 'delta', 'pattern', 'palette', 'hex', 'rle', or 'raw'."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output destination path for compressed package or restored image."
    )
    parser.add_argument(
        "--verify",
        nargs=2,
        metavar=("ORIGINAL", "RECONSTRUCTED"),
        help="Verify two images pixel-by-pixel for lossless equivalence."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # If CLI compression requested
    if args.compress:
        input_path = Path(args.compress)
        if not input_path.exists():
            print(f"Error: Input image not found: {input_path}")
            sys.exit(1)

        out_path = Path(args.output) if args.output else input_path.with_suffix(".icomp")
        print(f"Compressing {input_path} (mode={args.mode}) -> {out_path}...")
        result = PixelCoder.compress_image_to_file(input_path, out_path, mode=args.mode)
        print("Compression completed successfully!")
        print(f"- Algorithm: {result['mode'].upper()}")
        print(f"- Dimensions: {result['width']}x{result['height']}")
        print(f"- Total Pixels: {result['total_pixels']:,}")
        print(f"- Raw RGB Data: {result['raw_image_bytes'] / 1024:.2f} KB")
        print(f"- Original File: {result['original_file_size_bytes'] / 1024:.2f} KB")
        print(f"- Compressed Package: {result['compressed_size_bytes'] / 1024:.2f} KB")
        print(f"- Savings vs Raw Pixels: {result['space_savings_vs_raw_pct']:+.1f}%")
        print(f"- Saved to: {result['output_path']}")
        return

    # If CLI decompression requested
    if args.decompress:
        input_path = Path(args.decompress)
        if not input_path.exists():
            print(f"Error: Input file not found: {input_path}")
            sys.exit(1)

        out_path = Path(args.output) if args.output else input_path.with_suffix(".png")
        print(f"Decompressing {input_path} -> {out_path}...")
        img, result = PixelCoder.decompress_file_to_image(input_path, out_path)
        print("Decompression completed successfully!")
        print(f"- Restored Dimensions: {result['width']}x{result['height']}")
        print(f"- Format Decoded: {result.get('format', 'unknown').upper()}")
        print(f"- Saved Image: {out_path}")
        return

    # If CLI verification requested
    if args.verify:
        orig_p, recon_p = Path(args.verify[0]), Path(args.verify[1])
        print(f"Verifying {orig_p} vs {recon_p}...")
        res = PixelCoder.verify_lossless(orig_p, recon_p)
        if res["is_identical"]:
            print(f"SUCCESS: 100.0% lossless match ({res['total_pixels']:,} pixels identical, 0 errors).")
        else:
            print(f"MISMATCH: {res.get('mismatched_pixels', 0)} errors. Match: {res.get('match_percentage', 0):.2f}%")
        return

    # Default: launch Tkinter GUI
    launch_gui()


if __name__ == "__main__":
    main()
