import os
import pandas as pd
import wave
import contextlib
from datetime import datetime

def scan_and_record_wav_files_with_duration(base_folder):
    wav_files = []

    for root, dirs, files in os.walk(base_folder):
        for file in files:
            if file.endswith(".wav"):
                file_path = os.path.join(root, file)
                with contextlib.closing(wave.open(file_path, 'r')) as f:
                    frames = f.getnframes()
                    rate = f.getframerate()
                    duration = frames / float(rate)
                    duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}:{int((duration % 1) * 1000)}"
                    bit_depth = f.getsampwidth() * 8  # Convert sample width to bit depth

                folder_hierarchy = root.replace(base_folder, '').strip(os.sep).split(os.sep)
                folder_hierarchy.reverse()

                italian_file = file.replace('_ENG.wav', '_ITA.wav')

                shortened_file = file
                for ending in ['_a_ENG', '_b_ENG', '_c_ENG', '_d_ENG', '_e_ENG', '_f_ENG', '_ENG']:
                    if file.endswith(ending + '.wav'):
                        shortened_file = file.replace(ending + '.wav', '')
                        break

                # Append file name, Italian file name, shortened file name, duration, bit depth, and sample rate at the beginning
                wav_files.append([file, italian_file, shortened_file, duration_str, bit_depth, rate] + folder_hierarchy)

    df = pd.DataFrame(wav_files)
    df = df.apply(lambda x: pd.Series(x.dropna().values))

    # Adding headers to the DataFrame
    max_folders = df.shape[1] - 6  # Adjust for additional columns for bit depth and sample rate
    headers = ["EN FILE NAME", "ITA FILE NAME", "FILE NAME FOR SCRIPT", "File Length", "Bit Depth", "Sample Rate"] + [f"Folder {i+1}" for i in range(max_folders)]
    df.columns = headers[:df.shape[1]]

    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_folder_name = os.path.basename(os.path.normpath(base_folder))
    output_file_name = f"{base_folder_name}_{current_datetime}.xlsx"
    output_file = os.path.join(base_folder, output_file_name)

    df.to_excel(output_file, index=False)

    return output_file

if __name__ == "__main__":
    base_folder = input("Enter the path to the base folder: ")
    output_file = scan_and_record_wav_files_with_duration(base_folder)
    print(f"The Excel file has been saved to: {output_file}")
