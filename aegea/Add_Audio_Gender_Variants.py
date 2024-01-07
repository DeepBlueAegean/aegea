import os
import shutil
import pandas as pd
import openpyxl


#cancella il file indicato nella prima colonna del xls e 
#lo duplica con files uguali ma rinominati come nelle colonne
#seguenti di excel, finchè trova una colonna vuota
#Il file di excel non deve avere header.
#
#

def rename_and_duplicate_files(target_directory, excel_file_path):
    try:
        # Load the Excel file
        df = pd.read_excel(excel_file_path, header=None)

        # Iterate through each row in the dataframe
        for _, row in df.iterrows():
            original_file_name = row[0]
            new_file_names = row[1:].dropna().tolist()

            # Search for the file in the target directory and subdirectories
            for root, dirs, files in os.walk(target_directory):
                if original_file_name in files:
                    original_file_path = os.path.join(root, original_file_name)

                    # Create copies with new names
                    for new_name in new_file_names:
                        new_file_path = os.path.join(root, new_name)
                        shutil.copy2(original_file_path, new_file_path)

                    # Delete the original file
                    os.remove(original_file_path)
                    break

    except FileNotFoundError as fnf_error:
        print(f"File not found: {fnf_error}")
    except PermissionError as permission_error:
        print(f"Permission denied: {permission_error}")
    except Exception as e:
        print(f"An error occurred: {e}")

# User can define the target directory and Excel file path here
target_directory = input("Enter the path to the target directory: ")
excel_file_path = input("Enter the path to the Excel file: ")

# Run the function with the user-defined paths
rename_and_duplicate_files(target_directory, excel_file_path)
