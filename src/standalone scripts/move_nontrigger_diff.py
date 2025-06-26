import os

DIFF_FOLDER = 'diff'
IMG_FOLDER = 'img'
DEST_FOLDER = 'diff_nontrigger'

if not os.path.exists(DEST_FOLDER):
    os.mkdir(DEST_FOLDER)
    print(f"Created destination folder: {DEST_FOLDER}")

img_filenames = os.listdir(IMG_FOLDER)

for filename in os.listdir(DIFF_FOLDER):

    if not filename in img_filenames:
        # filename = filename[:-4]
        # strs = filename.split('_')
        # img_id_str, date_str = strs[1], strs[0]
        old_path = os.path.join(DIFF_FOLDER, filename)
        new_path = os.path.join(DEST_FOLDER, filename)
        os.rename(old_path, new_path)
    

    
