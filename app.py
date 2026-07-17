import os
from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/fetch-info', methods=['POST'])
def fetch_info():
    # फ्रंटएंड अगर JSON भेज रहा है तो request.json काम करेगा, नहीं तो request.form
    data = request.get_json(silent=True) or request.form
    video_url = data.get('url')

    if not video_url:
        return jsonify({'error': 'URL is required'}), 400

    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True
    }
    
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
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download_video():
    data = request.get_json(silent=True) or request.form
    video_url = data.get('url')
    format_id = data.get('format_id')
    
    if not video_url or not format_id:
        return jsonify({'error': 'Missing parameters'}), 400
    
    ydl_opts = {
        # ध्यान दें: Render पर बिना FFmpeg के मर्ज फेल होगा, इसलिए सिंगल फाइल डाउनलोड के लिए 'format_id' रखें
        'format': f'{format_id}', 
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            just_filename = os.path.basename(filename)
            return send_from_directory(DOWNLOAD_FOLDER, just_filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
            return send_from_directory(DOWNLOAD_FOLDER, just_filename, as_attachment=True)
    except Exception as e:
        return f"Download Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
