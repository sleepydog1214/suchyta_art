import dropbox
import config

ACCESS_TOKEN = config.DB_TOKEN
dbx = dropbox.Dropbox(ACCESS_TOKEN)

try:
    result = dbx.files_list_folder('/art_001')
    print("Root folder contents:")
    for entry in result.entries:
        print(entry.name)
except dropbox.exceptions.ApiError as e:
    print("Error:", e)
