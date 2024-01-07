import tkinter as tk
from tkinter import filedialog
import os
import csv
import shutil

csv_path = None
src = None
dest = None

# Create the main window
window = tk.Tk()
window.title("Copy Files specified in .csv")

# Create a label to display the selected file name
csv_label = tk.Label(window, text="No .csv file selected.")
csv_label.pack()

# Create a button to open the file selection dialog
def choose_csv():
  global csv_path
  csv_path = filedialog.askopenfilename(parent=window, title="Choose a .csv file contatining the filenames")
  if csv_path: csv_label.config(text=csv_path.split("/")[-1])

csv_button = tk.Button(window, text="Choose a .csv file", command=choose_csv)
csv_button.pack()

# Create a label to display the selected source directory
src_label = tk.Label(window, text="No source directory chosen.", )
src_label.pack()

# Create a button to select the source folder
def choose_src():
  global src
  src = filedialog.askdirectory(initialdir=csv_path, parent=window, title="Choose a Source Folder")
  if src: src_label.config(text=src)

src_button = tk.Button(window, text="Choose Source Directory", command=choose_src)
src_button.pack()

# Create a label to display the selected dest directory
dest_label = tk.Label(window, text="No destination directory chosen.")
dest_label.pack()

#Create a button to select the source folder
def choose_dest():
  global dest
  dest = filedialog.askdirectory(initialdir=src, parent=window, title="Choose a Destination Folder")
  if dest: dest_label.config(text=dest)

dest_button = tk.Button(window, text="Choose Destination Folder", command=choose_dest)
dest_button.pack()

#Create a button to copy or move the files. 
def copy_files():
  with open(csv_path, 'r') as csv_file:
    reader = csv.reader(csv_file)
    for row in reader:
      for file_name in row:
        src_file = os.path.join(src, file_name)
        dest_file = os.path.join(dest, file_name)
        if os.path.exists(src_file):
          shutil.copy(src_file, dest_file)

def move_files():
  with open(csv_path, 'r') as csv_file:
    reader = csv.reader(csv_file)
    for row in reader:
      for file_name in row:
        src_file = os.path.join(src, file_name)
        dest_file = os.path.join(dest, file_name)
        if os.path.exists(src_file):
          shutil.move(src_file, dest_file)

copy_button = tk.Button(window, text="Copy Files!", command=copy_files)
copy_button.pack()

#Create a switch to decide whether to move or to copy the files. 
switch_state = tk.BooleanVar()

# Create a function to handle the switch state
def switch_handler():
  if switch_state.get():
    copy_button.config(text="Move Files!")
    copy_button.config(command=move_files)
  else:
    copy_button.config(text="Copy Files!")
    copy_button.config(command=copy_files)

# Create the switch
switch = tk.Checkbutton(window, text="Tick this if you want to move the files instead.", variable=switch_state, command=switch_handler)
switch.pack()

# Run the main loop
window.mainloop()
