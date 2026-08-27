import os
import glob
import time
import streamlit as st
from PIL import Image
from bokeh.models import CustomJS
from bokeh.models.widgets import Button
from streamlit_bokeh_events import streamlit_bokeh_events
from gtts import gTTS
from googletrans import Translator

# ---------- Configuración de Página ----------
st.set_page_config(
    page_title="Traductor por Voz",
    page_icon="🌐",
    layout="wide"
)

# ---------- Estilos Personalizados para UX ----------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }

    .sub-header {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }

    .card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }

    .status-badge {
        display: inline-block;
        background-color: #F0FDF4;
        border: 1px solid #DCFCE7;
        color: #166534;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Diccionarios de Configuración ----------
IDIOMAS = {
    "Español": "es",
    "Inglés": "en",
    "Francés": "fr",
    "Aleman": "de",
    "Japonés": "ja",
    "Coreano": "ko",
    "Mandarín": "zh-cn",
    "Bengali": "bn"
}

ACENTOS = {
    "Defecto": "com",
    "Español": "com.mx",
    "Reino Unido": "co.uk",
    "Estados Unidos": "com",
    "Canada": "ca",
    "Australia": "com.au",
    "Irlanda": "ie",
    "Sudáfrica": "co.za"
}

# ---------- Barra Lateral ----------
with st.sidebar:
    # Intentar cargar la imagen en PNG guardada
    try:
        image = Image.open('traductor.png')
        st.image(image, width=180)
    except Exception:
        # Respaldo en caso de que la imagen aún no esté en el directorio
        st.info("🖼️ Coloca 'traductor.png' en la carpeta raíz del proyecto.")

    st.subheader("⚙️ Configuración")
    st.write("Configura el idioma de origen y el resultado deseado para tu traducción por voz.")
    st.markdown("---")
    
    in_lang = st.selectbox("Idioma de Entrada (Voz)", list(IDIOMAS.keys()), index=0)
    out_lang = st.selectbox("Idioma de Salida (Traducción)", list(IDIOMAS.keys()), index=1)
    english_accent = st.selectbox("Acento/Región de salida", list(ACENTOS.keys()), index=0)
    
    display_output_text = st.checkbox("Mostrar texto traducido", value=True)

# ---------- Cuerpo Principal ----------
st.markdown('<div class="main-header">Traductor por Voz</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Presiona el botón para comenzar a hablar, nosotros lo traducimos y lo reproducimos.</div>', unsafe_allow_html=True)

col_mic, col_status = st.columns([1, 1], gap="medium")

with col_mic:
    st.markdown("### 1. Captura de Voz")
    
    # Configuración del botón de Bokeh
    stt_button = Button(label="🎤 Presionar para Hablar", width=280, height=45)
    stt_button.js_on_event("button_click", CustomJS(code=f"""
        var recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = '{IDIOMAS[in_lang]}';
     
        recognition.onresult = function (e) {{
            var value = "";
            for (var i = e.resultIndex; i < e.results.length; ++i) {{
                if (e.results[i].isFinal) {{
                    value += e.results[i][0].transcript;
                }}
            }}
            if (value != "") {{
                document.dispatchEvent(new CustomEvent("GET_TEXT", {{detail: value}}));
            }}
        }}
        recognition.start();
    """))

    result = streamlit_bokeh_events(
        stt_button,
        events="GET_TEXT",
        key="listen",
        refresh_on_update=False,
        override_height=60,
        debounce_time=0
    )

# ---------- Procesamiento de Traducción ----------
if result and "GET_TEXT" in result:
    captured_text = str(result.get("GET_TEXT"))

    with col_status:
        st.markdown("### 2. Texto Escuchado")
        st.info(f'"{captured_text}"')

    # Creación del directorio temporal si no existe
    if not os.path.exists("temp"):
        os.makedirs("temp")

    translator = Translator()
    input_code = IDIOMAS[in_lang]
    output_code = IDIOMAS[out_lang]
    tld_code = ACENTOS[english_accent]

    st.markdown("---")
    st.markdown("### 3. Resultado de la Traducción")

    with st.spinner("Traduciendo y generando audio..."):
        try:
            translation = translator.translate(captured_text, src=input_code, dest=output_code)
            trans_text = translation.text
            
            # Nombre seguro para el archivo de audio
            file_name = f"audio_{int(time.time())}"
            file_path = f"temp/{file_name}.mp3"
            
            tts = gTTS(trans_text, lang=output_code, tld=tld_code, slow=False)
            tts.save(file_path)

            col_audio, col_text = st.columns([1, 1], gap="medium")

            with col_audio:
                st.markdown("**Escuchar reproducción:**")
                with open(file_path, "rb") as audio_file:
                    st.audio(audio_file.read(), format="audio/mp3", start_time=0)

            if display_output_text:
                with col_text:
                    st.markdown("**Texto Traducido:**")
                    st.success(trans_text)

        except Exception as e:
            st.error(f"Hubo un error al procesar la traducción: {e}")

    # Limpieza de archivos de audio antiguos (más de 7 días)
    def remove_files(days=7):
        mp3_files = glob.glob("temp/*.mp3")
        now = time.time()
        n_seconds = days * 86400
        for f in mp3_files:
            if os.stat(f).st_mtime < now - n_seconds:
                try:
                    os.remove(f)
                except OSError:
                    pass

    remove_files(7)

else:
    with col_status:
        st.markdown("### 2. Estado")
        st.write("Esperando a que presiones el botón de captura...")


        
    



        
    


