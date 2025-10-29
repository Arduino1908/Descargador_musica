from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import yt_dlp
import os
from pathlib import Path
import threading

app = Flask(__name__)
CORS(app)

# HTML optimizado para móviles y computadora
HTML = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎵 Descargar Música</title>
    <style>
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        body { 
            font-family: 'Arial', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 500px;
            width: 100%;
        }
        .logo {
            font-size: 4em;
            margin-bottom: 10px;
        }
        h1 {
            color: #333;
            margin-bottom: 15px;
            font-size: 2em;
        }
        .descripcion {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .input-url {
            width: 100%;
            padding: 15px;
            margin: 20px 0;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        .input-url:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .btn-descargar {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            border: none;
            padding: 16px 40px;
            font-size: 18px;
            font-weight: bold;
            border-radius: 10px;
            cursor: pointer;
            margin: 10px 0;
            width: 100%;
            transition: all 0.3s ease;
        }
        .btn-descargar:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4);
        }
        .btn-descargar:disabled {
            background: #cccccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .resultado {
            margin: 25px 0;
            padding: 20px;
            border-radius: 10px;
            display: none;
            font-size: 1.1em;
            line-height: 1.6;
        }
        .exito {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .procesando {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        .instrucciones {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin-top: 30px;
            text-align: left;
        }
        .instrucciones h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        .instrucciones ol {
            padding-left: 20px;
        }
        .instrucciones li {
            margin-bottom: 10px;
            color: #555;
        }
        .ejemplo-url {
            background: #e9ecef;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 0.9em;
            margin: 10px 0;
        }
        @media (max-width: 600px) {
            .container {
                padding: 25px;
                margin: 10px;
            }
            h1 {
                font-size: 1.8em;
            }
            .logo {
                font-size: 3em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- LOGO Y TÍTULO -->
        <div class="logo">🎵</div>
        <h1>Descargar Música</h1>
        
        <!-- DESCRIPCIÓN -->
        <p class="descripcion">
            Convierte videos de YouTube a audio<br>
            Fácil, rápido y gratis
        </p>
        
        <!-- FORMULARIO DE DESCARGA -->
        <input type="text" 
               class="input-url" 
               id="urlInput" 
               placeholder="https://www.youtube.com/watch?v=..."
               autocomplete="off">
        
        <!-- BOTÓN DE DESCARGA -->
        <button class="btn-descargar" id="btnDescargar" onclick="descargarMusica()">
            ⬇️ Descargar Audio
        </button>
        
        <!-- ÁREA DE RESULTADOS -->
        <div id="resultado" class="resultado"></div>
        
        <!-- INSTRUCCIONES -->
        <div class="instrucciones">
            <h3>💡 ¿Cómo usar?</h3>
            <ol>
                <li>Ve a YouTube y copia el enlace del video</li>
                <li>Pega el enlace en el campo de arriba</li>
                <li>Haz click en "Descargar Audio"</li>
                <li>¡El audio se descargará automáticamente!</li>
            </ol>
            
            <div class="ejemplo-url">
                Ejemplo: https://www.youtube.com/watch?v=dQw4w9WgXcQ
            </div>
        </div>
    </div>

    <!-- JAVASCRIPT -->
    <script>
        // Elementos de la página
        const urlInput = document.getElementById('urlInput');
        const btnDescargar = document.getElementById('btnDescargar');
        const resultado = document.getElementById('resultado');
        
        function descargarMusica() {
            const url = urlInput.value.trim();
            
            // Validaciones
            if (!url) {
                mostrarResultado('❌ Por favor, pega una URL de YouTube', 'error');
                return;
            }
            
            if (!esUrlYouTubeValida(url)) {
                mostrarResultado('❌ Esto no parece ser un enlace válido de YouTube', 'error');
                return;
            }
            
            // Iniciar descarga
            iniciarDescarga(url);
        }
        
        function esUrlYouTubeValida(url) {
            // Patrones de URLs de YouTube
            const patrones = [
                /youtube\.com\/watch\?v=/,
                /youtu\.be\//,
                /youtube\.com\/embed\//,
                /youtube\.com\/playlist\?list=/
            ];
            
            return patrones.some(patron => patron.test(url));
        }
        
        function iniciarDescarga(url) {
            // Deshabilitar botón
            btnDescargar.disabled = true;
            btnDescargar.textContent = '⏳ Descargando...';
            
            // Mostrar estado de procesamiento
            mostrarResultado('⏳ Conectando con el servidor...', 'procesando');
            
            // Enviar petición al servidor
            fetch('/descargar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({url: url})
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error del servidor');
                }
                return response.json();
            })
            .then(data => {
                mostrarResultado(data.message, data.success ? 'exito' : 'error');
            })
            .catch(error => {
                console.error('Error:', error);
                mostrarResultado('❌ Error de conexión con el servidor', 'error');
            })
            .finally(() => {
                // Rehabilitar botón
                btnDescargar.disabled = false;
                btnDescargar.textContent = '⬇️ Descargar Audio';
            });
        }
        
        function mostrarResultado(mensaje, tipo) {
            resultado.innerHTML = mensaje;
            resultado.className = 'resultado ' + tipo;
            resultado.style.display = 'block';
        }
        
        // Permitir usar la tecla Enter
        urlInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                descargarMusica();
            }
        });
        
        // Limpiar resultado cuando el usuario empiece a escribir
        urlInput.addEventListener('input', function() {
            resultado.style.display = 'none';
        });
        
        // Mensaje de bienvenida
        window.addEventListener('load', function() {
            urlInput.focus(); // Poner el cursor en el input
        });
    </script>
</body>
</html>
'''

def descargar_audio(url):
    """Descarga audio de YouTube sin FFmpeg"""
    try:
        print(f"🎵 Iniciando descarga: {url}")
        
        # Configuración SIN FFMPEG - audio directo
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }
        
        # Descargar
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            titulo = info.get('title', 'Canción')
            
        print(f"✅ Descarga completada: {titulo}")
        return True, f"✅ {titulo}"
        
    except Exception as e:
        print(f"❌ Error en descarga: {e}")
        return False, f"❌ Error: {str(e)}"

@app.route('/')
def home():
    """Página principal"""
    return render_template_string(HTML)

@app.route('/descargar', methods=['POST'])
def descargar():
    """Endpoint para descargar audio"""
    try:
        url = request.json.get('url', '')
        print(f"📥 URL recibida: {url}")
        
        if not url:
            return jsonify({'success': False, 'message': '❌ No hay URL'})
        
        # Descargar en hilo separado para no bloquear
        def tarea_descarga():
            success, message = descargar_audio(url)
            print(f"📤 Resultado: {message}")
        
        thread = threading.Thread(target=tarea_descarga)
        thread.start()
        
        return jsonify({
            'success': True, 
            'message': '⏳ Descargando audio... Esto puede tomar unos segundos.'
        })
        
    except Exception as e:
        print(f"🔥 ERROR en /descargar: {e}")
        return jsonify({'success': False, 'message': f'❌ Error del servidor: {str(e)}'})

@app.route('/status')
def status():
    """Endpoint para verificar que el servidor funciona"""
    return jsonify({'status': 'ok', 'message': '🚀 Servidor funcionando correctamente'})

if __name__ == '__main__':
    # Crear carpeta de descargas si no existe
    Path("downloads").mkdir(exist_ok=True)
    
    print("🎵 SERVIDOR WEB INICIADO")
    print("📍 Listo para subir a internet")
    print("📁 Las descargas se guardan en: downloads/")
    print("🔥 SIN FFMPEG - Audio directo M4A/WebM")
    print("=" * 50)
    
    # Obtener puerto del entorno (para hosting) o usar 8080 local
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)