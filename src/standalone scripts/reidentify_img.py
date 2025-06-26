### rename images based on CSV date and id
### not supposed to be run on the device, but on a computer in the jpegs/ folder

import csv
import os
import re

CSV_FILE = '../images.csv'
ID_HEADER = 'picture_id'
DATE_HEADER = 'date'
SINGLE_ID_FOLDERS = ['img', 'reference', 'diff']
BLOBS_FOLDER = 'blobs'

class DateFinder:
    """
    Class to find dates from image IDs based on a CSV file.
    """
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.id_date_map = {}
        self.load_csv()
        self.last_id = -1

    def load_csv(self):
        with open(self.csv_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                img_id = int(row[ID_HEADER])
                date_str = row[DATE_HEADER]
                self.id_date_map[img_id] = date_str

    def reset_last_id(self):
        self.last_id = -1

    def find_closest_id(self, img_id):
        # Find the closest id in id:date map using min with a key function
        if img_id in self.id_date_map:
            return img_id
        all_ids = sorted(self.id_date_map.keys())
        closest = min(all_ids, key=lambda x: abs(x - img_id))
        return closest

    def get_date_from_id_str(self, img_id_str):
        try:
            img_id = int(img_id_str)
        except ValueError:
            return None

        if img_id in self.id_date_map:
            self.last_id = img_id
            date_str = self.id_date_map[img_id]
        elif self.last_id != -1:
            date_str = self.id_date_map[self.last_id]
        else:
            date_str = self.id_date_map[self.find_closest_id(img_id)]

        return date_str
    
def find_existing_single_id_folders():
    single_id_folders = SINGLE_ID_FOLDERS

    print(os.listdir('.'))

    for folder in single_id_folders:
        if not os.path.exists(folder):
            single_id_folders.remove(folder)

    # add folders named with resolution and roi 
    # (assume no folders stating with numbers are used for other purposes)
    for name in os.listdir('.'):
        if os.path.isdir(name) and name[0].isdigit():
            single_id_folders.append(name)

    print(f"Found folders: {single_id_folders}")
    
    return single_id_folders


def rename_single_id_file(id, date_str, folder):
    """
    Rename a single image file based on its ID and date string.
    """
    old_filename = f"{id}.jpg"
    new_filename = f"{date_str}_{id}.jpg"
    
    old_path = os.path.join(folder, old_filename)
    new_path = os.path.join(folder, new_filename)

    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        print(f"Renamed: {old_filename} -> {new_filename}")
    else:
        print(f"File not found: {old_filename}")

def rename_blob_file(filename, img_id_str, date_str):
    suffix = filename[len(img_id_str):]
    new_name = f"{date_str}_{img_id_str}{suffix}"
    old_path = os.path.join(BLOBS_FOLDER, filename)
    new_path = os.path.join(BLOBS_FOLDER, new_name)
    os.rename(old_path, new_path)
    print(f"{BLOBS_FOLDER}: {filename} -> {new_name}")

date_finder = DateFinder(CSV_FILE)
single_id_folders = find_existing_single_id_folders()

# rename files such as 1234.jpg in img/, reference/ and diff/ folders
for folder in single_id_folders:
    filenames = os.listdir(folder)
    date_finder.reset_last_id()
    for filename in filenames:

        img_id_str = filename[:-4]
        date_str = date_finder.get_date_from_id_str(img_id_str)

        if date_str is None:
            print(f"Skipping file with non-numeric ID: {filename}")
            continue

        rename_single_id_file(img_id_str, date_str, folder)

# rename blobs
date_finder.reset_last_id()
for fname in os.listdir(BLOBS_FOLDER):
    match = re.match(r'^(\d+)[^0-9].*\.jpg$', fname)
    if not match:
        print(f"No match for file: {fname}")
        continue

    img_id_str = match.group(1)

    print(f"Processing blob file: {fname} with ID: {img_id_str}")

    date_str = date_finder.get_date_from_id_str(img_id_str)

    if date_str is None:
        print(f"Skipping file with non-numeric ID: {fname}")
        continue

    rename_blob_file(fname, img_id_str, date_str)