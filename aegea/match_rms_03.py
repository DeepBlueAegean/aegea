import os
import shutil
import subprocess
from pathlib import Path
from typing import Tuple

import numpy as np
import soundfile as sf
import xlsxwriter


def get_rms_and_peak(filepath: Path) -> Tuple[float, float]:
    """Computes the RMS and peak RMS values of a soundfile in dB."""
    data, _ = sf.read(filepath, dtype="int32")
    normalized_data = data / np.iinfo(np.int32).max
    rms_value_float = np.sqrt(np.mean(normalized_data**2))
    peak_value_float = np.max(np.abs(normalized_data))

    rms_value_db = 20 * np.log10(rms_value_float) if rms_value_float > 0 else -float("inf")
    peak_value_db = 20 * np.log10(peak_value_float) if peak_value_float > 0 else -float("inf")

    return rms_value_db, peak_value_db


def apply_compression_gain_and_limiting(
    input_file,
    output_file,
    gain_db,
    threshold_db=0,
    ratio=2,
    peak_limit=-0.5
):
    # Ensure threshold_db is within -30 to 0
    threshold_db = max(-30, min(threshold_db, 0))

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
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr = subprocess.DEVNULL)


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
            base_name = filename[:-len(target_suffix)]
            source_file = os.path.join(source_dir, base_name + source_suffix)
            target_file = os.path.join(target_dir, filename)
            output_file = os.path.join(output_dir, filename)

            if os.path.isfile(source_file) and os.path.isfile(target_file):
                print(f"\n=== Trying to match {filename}  ===\n")
                source_rms_db, _ = get_rms_and_peak(source_file)
                target_rms_db, target_peak_db = get_rms_and_peak(target_file)

                rms_difference = source_rms_db - target_rms_db

                if -rms_diff_threshold <= rms_difference <= rms_diff_threshold:
                    print(f"RMS difference ({rms_difference} dB) is within user_defined_rms_diff_threshold for file {filename}. Copying without processing.")
                    shutil.copy(target_file, output_file)

                elif rms_difference < 0:
                    # Only apply gain adjustment
                    adjusted_gain_db = rms_difference  
                    apply_compression_gain_and_limiting(
                        target_file,
                        output_file,
                        adjusted_gain_db,
                        threshold_db=-1,  # Default threshold for gain-only processing
                        ratio=1,          # No compression, only gain adjustment
                        peak_limit=peak_limit,
                    )
                    print(f"ELIF Applied gain adjustment : decreased {adjusted_gain_db} dB for file {filename}")

                else:
                    print("Using acompressor to scale file to increase rms.")
                    gain_db = rms_difference
                    print(f"target file {filename} loudness was {gain_db=} lower than source: output file compressed")
                    
                    # Calculate and clamp threshold_db within 0.5 to 1
                    threshold_db = -gain_db-2
                    print(f"{threshold_db=}")
                    
                    threshold_db = max(-40, min(threshold_db, 0))
                    print(f"threshold_db after clamping = {threshold_db} ")
 
                    apply_compression_gain_and_limiting(
                        target_file,
                        output_file,
                        gain_db,
                        threshold_db,
                        20,
                        peak_limit,
                    )
                    output_rms_db, _ = get_rms_and_peak(output_file)
                    rms_difference_out = source_rms_db - output_rms_db
                    print(f"{output_rms_db=}")
                    # if rms_difference_out > rms_diff_threshold:
                    #     print(f"Reprocessing file {filename} due to high output RMS difference of {rms_difference_out}.")
                    #     apply_compression_gain_and_limiting(
                    #         target_file,
                    #         output_file,
                    #         rms_difference_out,
                    #         -rms_difference_out-1,
                    #         20,
                    #         peak_limit,
                    #     )
                    #     print(f"Reprocessed rms output: {get_rms_and_peak(output_file)[0]}")

                print(f"Processed: {filename}")
            else:
                print(f"Missing matching file for: {filename}")

    compile_report(source_dir, target_dir, output_dir, source_suffix, target_suffix, report_path)
    print("Audio processing complete.")



def compile_report(source_folder, target_folder, output_folder, source_suffix, target_suffix, report_path):
    workbook = xlsxwriter.Workbook(report_path)
    worksheet = workbook.add_worksheet("RMS and Peak Levels")

    headers = ["File Name", "Source RMS (dB)", "Source Peak (dB)", "Target RMS (dB)", "Target Peak (dB)", "Output RMS (dB)", "Output Peak (dB)", "RMS Difference (dB)"]
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)

    row = 1
    for filename in os.listdir(output_folder):
        if filename.endswith(target_suffix):
            base_name = filename[:-len(target_suffix)]
            source_file = os.path.join(source_folder, base_name + source_suffix)
            target_file = os.path.join(target_folder, base_name + target_suffix)
            output_file = os.path.join(output_folder, filename)

            if os.path.isfile(source_file) and os.path.isfile(output_file):
                source_rms_db, source_peak_db = get_rms_and_peak(source_file)
                target_rms_db, target_peak_db = get_rms_and_peak(target_file)
                output_rms_db, output_peak_db = get_rms_and_peak(output_file)
                rms_difference_out = source_rms_db - output_rms_db

                worksheet.write(row, 0, filename)
                worksheet.write(row, 1, source_rms_db)
                worksheet.write(row, 2, source_peak_db)
                worksheet.write(row, 3, target_rms_db)
                worksheet.write(row, 4, target_peak_db)
                worksheet.write(row, 5, output_rms_db)
                worksheet.write(row, 6, output_peak_db)
                worksheet.write(row, 7, rms_difference_out)

                row += 1

    workbook.close()


def main():
    source_dir_input = input("Enter the path for the source directory: ")
    target_dir_input = input("Enter the path for the target directory: ")
    output_dir_input = input("Enter the path for the output directory: ")

    source_dir = Path(source_dir_input).resolve()
    target_dir = Path(target_dir_input).resolve()
    output_dir = Path(output_dir_input).resolve()

    report_path = output_dir / 'report.xlsx'
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
