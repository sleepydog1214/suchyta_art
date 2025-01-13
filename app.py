from flask import Flask, render_template, url_for, send_file, Response
import dropbox
import config

app = Flask(__name__)

# Dropbox configuration
ACCESS_TOKEN = config.DB_TOKEN
DROPBOX_FOLDER_PATH = config.DB_DIR
dbx = dropbox.Dropbox(ACCESS_TOKEN)

def get_images_from_dropbox():
    """Fetch image file metadata and generate thumbnail and full image URLs."""
    files = dbx.files_list_folder(DROPBOX_FOLDER_PATH).entries
    images = []

    for file in files:
        if isinstance(file, dropbox.files.FileMetadata):
            try:
                # Get shared link for the full image
                shared_link = dbx.sharing_create_shared_link_with_settings(file.path_lower)
                full_image_url = url_for('get_full_image', path=file.path_lower)
            except dropbox.exceptions.ApiError as e:
                if isinstance(e.error, dropbox.sharing.CreateSharedLinkWithSettingsError) and e.error.is_shared_link_already_exists():
                    shared_link = dbx.sharing_list_shared_links(file.path_lower).links[0]
                    full_image_url = url_for('get_full_image', path=file.path_lower)
                else:
                    raise

            # Add the thumbnail route URL for each image
            images.append({
                'name': file.name,
                'thumbnail_url': url_for('get_thumbnail', path=file.path_lower),
                'full_image_url': full_image_url
            })

    return images

@app.route('/thumbnail/<path:path>')
def get_thumbnail(path):
    """Fetch and return a thumbnail image from Dropbox."""
    try:
        # Fetch thumbnail bytes from Dropbox
        thumbnail_result, thumbnail_response = dbx.files_get_thumbnail_v2(
            dropbox.files.PathOrLink.path(f"/{path}"),
            size=dropbox.files.ThumbnailSize.w128h128,
            format=dropbox.files.ThumbnailFormat.jpeg
        )
        thumbnail_bytes = thumbnail_response.content

        # Return the thumbnail as an image response
        return Response(thumbnail_bytes, mimetype='image/jpeg')

    except dropbox.exceptions.ApiError as e:
        return f"Error fetching thumbnail: {e}", 500

@app.route('/full_image/<path:path>')
def get_full_image(path):
    """Fetch and return the full-size image from Dropbox."""
    try:
        # Ensure the path starts with a '/'
        if not path.startswith('/'):
            path = f'/{path}'

        # Fetch full-size image bytes from Dropbox
        metadata, response = dbx.files_download(path)
        image_bytes = response.content

        # Return the full-size image as an image response
        return Response(image_bytes, mimetype='image/jpeg')

    except dropbox.exceptions.ApiError as e:
        return f"Error fetching full-size image: {e}", 500

@app.route('/')
def index():
    """Home page displaying a grid of thumbnails."""
    images = get_images_from_dropbox()
    return render_template('index.html', images=images)

@app.route('/image/<path:image_url>')
def show_image(image_url):
    """Page to display the full image."""
    return render_template('image.html', image_url=image_url)

if __name__ == '__main__':
    app.run(debug=True)