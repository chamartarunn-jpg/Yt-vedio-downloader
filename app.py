import os
from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def home():
    # यह लाइन सीधे आपके बनाए हुए templates/index.html को लोड करेगी
    return render_template('index.html')

@app.route('/fetch-info', methods=['POST'])
def fetch_info():
    video_url = request.form.get('url')
    ydl_opts = {'skip_download': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats = []
            seen_resolutions = set()
            
            for f in info.get('formats', []):
                height = f.get('height')
                if height and height >= 360 and f.get('vcodec') != 'none':
                    res_label = f"{height}p"
                    if height == 1080: res_label = "1080p Full HD"
                    elif height == 1440: res_label = "2K Quad HD"
                    elif height >= 2160: res_label = "4K Ultra HD"
                    
                    if res_label not in seen_resolutions:
                        seen_resolutions.add(res_label)
                        formats.append({'format_id': f.get('format_id'), 'quality': res_label})
            
            formats.sort(key=lambda x: int(''.join(filter(str.isdigit, x['quality']))), reverse=True)
            return jsonify({'title': info.get('title'), 'thumbnail': info.get('thumbnail'), 'formats': formats})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/download', methods=['POST'])
def download_video():
    video_url = request.form.get('url')
    format_id = request.form.get('format_id')
    
    ydl_opts = {
        'format': f'{format_id}+bestaudio/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'merge_output_format': 'mp4',
        'postprocessor_args': ['-c:v', 'copy', '-c:a', 'copy']
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            if not filename.endswith('.mp4'):
                filename = os.path.splitext(filename) + '.mp4'
            just_filename = os.path.basename(filename)
            return send_from_directory(DOWNLOAD_FOLDER, just_filename, as_attachment=True)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
