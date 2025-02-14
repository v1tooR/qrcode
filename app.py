from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from io import BytesIO
import qrcode

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Necessário para mensagens flash

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        if not url:
            flash('Por favor, insira uma URL válida!')
            return redirect(url_for('index'))
        return render_template('index.html', url=url)
    return render_template('index.html', url=None)

@app.route('/generate-qr')
def generate_qr():
    url = request.args.get('url')
    download = 'download' in request.args  # Verifica se é para download

    if not url:
        return "URL não fornecida", 400

    # Configuração do QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Geração da imagem
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = BytesIO()
    img.save(img_bytes, 'JPEG')  # Salva como JPEG
    img_bytes.seek(0)

    return send_file(
        img_bytes,
        mimetype='image/jpeg',
        as_attachment=download,
        download_name='qrcode.jpg'
    )

if __name__ == '__main__':
    app.run(debug=True)