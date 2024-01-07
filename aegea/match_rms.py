"""Dad-made original script."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Tuple

import numpy as np
import soundfile as sf
import xlwt


def get_rms_and_peak(
    filepath: Path
) -> Tuple[float, float]:
    """Computes the RMS and peak RMS values of a soundfile in dB.

    Args:
        filepath (Path): Audio file path.

    Returns:
        Tuple[float, float]: RMS and Peak RMS in dB.
    """
    # Read audiofile.
    data, _ = sf.read(filepath, dtype="int32")

    # Compute RMS + peak RMS
    normalized_data = data / np.iinfo(np.int32).max
    rms_value_float = np.sqrt(np.mean(normalized_data**2))
    peak_value_float = np.max(np.abs(normalized_data))

    # Convert RMS and peak RMS to dB.
    rms_value_db = (
        20 * np.log10(rms_value_float)
        if rms_value_float > 0 else -float("inf")
    )
    peak_value_db = (
        20 * np.log10(peak_value_float)
        if peak_value_float > 0 else -float("inf")
    )

    return rms_value_db, peak_value_db


def apply_compression_gain_and_limiting(
    input_file,
    output_file,
    gain_db,
    threshold_db=0,
    ratio=2,
    peak_limit=-0.5
):
    print(
        f"Applying compression, gain adjustment, peak limiting, and converting to 24-bit: Gain = {gain_db} dB, Threshold = {threshold_db} dB, Ratio = {ratio}, Peak Limit = {peak_limit} dB"
    )
    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-filter_complex",
        f"acompressor=threshold={threshold_db}dB:ratio={ratio}:attack=5:release=50, "
        + f"volume={gain_db}dB, "
        + f"alimiter=level_in=1:level_out={10**(peak_limit/20)}:limit=1",
        "-c:a",
        "pcm_s24le",
        output_file,
    ]
    subprocess.run(command)


def process_audio_files(
    source_dir,
    target_dir,
    output_dir,
    source_suffix,
    target_suffix,
    peak_limit,
    rms_diff_threshold,
    report_path,
):
    print("Starting audio processing...")

    for filename in os.listdir(target_dir):
        if filename.endswith(target_suffix):
            base_name = filename[: -len(target_suffix)]
            source_file = os.path.join(source_dir, base_name + source_suffix)
            target_file = os.path.join(target_dir, filename)
            output_file = os.path.join(output_dir, filename)

            if os.path.isfile(source_file) and os.path.isfile(target_file):
                source_rms_db, _ = get_rms_and_peak(source_file)
                target_rms_db, target_peak_db = get_rms_and_peak(target_file)

                rms_difference = abs(source_rms_db - target_rms_db)

                if rms_difference < rms_diff_threshold:
                    # No need to process.
                    print(
                        f"RMS difference ({rms_difference} dB) is below "
                        "threshold for file {filename}. Copying without "
                        "processing."
                    )
                    shutil.copy(target_file, output_file)

                else:
                    # Compress.
                    gain_db = source_rms_db - target_rms_db
                    adjusted_gain_db = (
                        gain_db + 2
                        if target_peak_db + gain_db > 0 else gain_db
                    )
                    apply_compression_gain_and_limiting(
                        target_file,
                        output_file,
                        adjusted_gain_db,
                        -adjusted_gain_db - 3,
                        20,
                        peak_limit,
                    )

                    # Check RMS difference after initial processing
                    output_rms_db, _ = get_rms_and_peak(output_file)
                    rms_difference_out = abs(source_rms_db - output_rms_db)
                    if rms_difference_out > rms_diff_threshold:
                        print(
                            f"Reprocessing file {filename} due to high RMS difference."
                        )
                        apply_compression_gain_and_limiting(
                            target_file,
                            output_file,
                            rms_difference_out,
                            -rms_difference_out,
                            20,
                            peak_limit,
                        )

                print(
                    f"rms_difference_out: {rms_difference_out}, rms_diff_threshold: {rms_diff_threshold}, "
                )
                print(f"Processed: {filename}")
            else:
                print(f"Missing matching file for: {filename}")

    # Compile report at the end
    compile_report(
        source_dir, output_dir, source_suffix, target_suffix, report_path
    )
    print("Audio processing complete.")


def compile_report(
    source_folder, output_folder, source_suffix, target_suffix, report_path
):
    book = xlwt.Workbook()
    sheet = book.add_sheet("RMS and Peak Levels")
    headers = [
        "File Name",
        "Source RMS (dB)",
        "Source Peak (dB)",
        "Output RMS (dB)",
        "Output Peak (dB)",
        "RMS Difference (dB)",
    ]
    for col, header in enumerate(headers):
        sheet.write(0, col, header)

    row = 1
    for filename in os.listdir(output_folder):
        if filename.endswith(target_suffix):
            base_name = filename[: -len(target_suffix)]
            source_file = os.path.join(source_folder, base_name + source_suffix)
            output_file = os.path.join(output_folder, filename)

            if os.path.isfile(source_file) and os.path.isfile(output_file):
                source_rms_db, source_peak_db = get_rms_and_peak(
                    source_file
                )
                output_rms_db, output_peak_db = get_rms_and_peak(
                    output_file
                )
                rms_difference_out = abs(source_rms_db - output_rms_db)

                sheet.write(row, 0, filename)
                sheet.write(row, 1, source_rms_db)
                sheet.write(row, 2, source_peak_db)
                sheet.write(row, 3, output_rms_db)
                sheet.write(row, 4, output_peak_db)
                sheet.write(row, 5, rms_difference_out)

                row += 1

    book.save(report_path)


def main():
    """Main entrypoint for this `dad_version.py` script."""

    test_dir = Path('./test').resolve()
    source_dir = test_dir / 'eng'
    target_dir = test_dir / 'ita'
    output_dir = test_dir / 'out'
    report_path = test_dir / 'report.xlsx'

    source_suffix = "_ENG.wav"
    target_suffix = "_ITA.wav"

    user_defined_peak_limit = -0.5
    user_defined_rms_diff_threshold = 2

    process_audio_files(
        source_dir,
        target_dir,
        output_dir,
        source_suffix,
        target_suffix,
        user_defined_peak_limit,
        user_defined_rms_diff_threshold,
        report_path,
    )


if __name__ == '__main__':
    main()
