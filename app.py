from flask import Flask, render_template, request, flash, redirect, url_for
from flask import make_response
from io import BytesIO
import qrcode
import base64
import xml.etree.ElementTree as ET
from PIL import Image

app = Flask(__name__)
app.secret_key = "sua_chave_secreta_aqui"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Obter dados do formulário
        url = request.form.get('url')
        fill_color = request.form.get('fill_color', '#000000')
        back_color = request.form.get('back_color', '#FFFFFF')
        logo_file = request.files.get('logo')

        if not url:
            flash('Por favor, insira uma URL válida!')
            return redirect(url_for('index'))

        try:
            # Gerar QR Code básico
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(fill_color=fill_color, back_color=back_color).convert('RGBA')

            # Adicionar logo se fornecido
            if logo_file and logo_file.filename:
                logo = Image.open(logo_file).convert('RGBA')
                logo_size = int(img.size[0] * 0.25)
                logo = logo.resize((logo_size, logo_size))
                
                pos = (
                    (img.size[0] - logo_size) // 2,
                    (img.size[1] - logo_size) // 2
                )
                img.paste(logo, pos, logo)

            # Preparar imagem para exibição
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            return render_template('index.html', qr_image=img_str)

        except Exception as e:
            flash(f'Erro ao gerar QR Code: {str(e)}')
            return redirect(url_for('index'))

    return render_template('index.html', qr_image=None)

#SVG

@app.route('/download-svg', methods=['POST'])
def download_svg():
    try:
        data = request.form.get('url')
        fill_color = request.form.get('fill_color', '#000000')
        back_color = request.form.get('back_color', '#FFFFFF')
        logo_file = request.files.get('logo')

        # Gerar QR Code básico
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # Criar SVG
        factory = qrcode.image.svg.SvgPathImage
        img = qr.make_image(image_factory=factory)
        img.save(stream := BytesIO())
        svg_content = stream.getvalue().decode()

        # Aplicar cores
        root = ET.fromstring(svg_content)
        for element in root.iter('{http://www.w3.org/2000/svg}path'):
            if 'fill' in element.attrib:
                element.attrib['fill'] = fill_color
        root.attrib['fill'] = back_color

        # Adicionar logo
        if logo_file and logo_file.filename:
            logo = Image.open(logo_file).convert('RGBA')
            logo_size = int(img.size[0] * 0.25)
            logo = logo.resize((logo_size, logo_size))
            
            # Converter logo para base64
            buffered = BytesIO()
            logo.save(buffered, format='PNG')
            logo_b64 = base64.b64encode(buffered.getvalue()).decode()
            
            # Adicionar elemento de imagem ao SVG
            ns = {'svg': 'http://www.w3.org/2000/svg'}
            image = ET.SubElement(root, 'image', {
                'x': str((img.size[0] - logo_size) // 2),
                'y': str((img.size[0] - logo_size) // 2),
                'width': str(logo_size),
                'height': str(logo_size),
                'href': f'data:image/png;base64,{logo_b64}'
            })

        # Gerar resposta
        response = make_response(ET.tostring(root))
        response.headers.set('Content-Type', 'image/svg+xml')
        response.headers.set('Content-Disposition', 'attachment', filename='qrcode.svg')
        return response

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)