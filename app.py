import streamlit as st
import google.generativeai as genai
import os
import glob
import json
from datetime import datetime
from PIL import Image
from character_base import CharacterAI

# Configurar página
st.set_page_config(
    page_title="Character AI Creator",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Mantener espacio y estilo mínimo para el input */
    [data-testid="stAppViewContainer"] { overflow: visible !important; }
    .main .block-container { padding-bottom: 260px !important; }
    [data-testid="stChatInputContainer"], .stChatInputContainer {
    position: fixed !important;
    bottom: 0 !important;
    left: 260px !important;
    right: 0 !important;
    z-index: 2147483647 !important;
    background-color: #0e1117 !important;
    padding: 10px 16px !important;
    border-top: 1px solid #262730 !important;
    box-sizing: border-box !important;
    }
    section[data-testid="stChatMessageContainer"], .stChatMessageContainer {
    overflow-y: auto !important;
    max-height: calc(100vh - 180px) !important;
    box-sizing: border-box !important;
    }
    </style>

    <script>
    (function() {
    console.log("[CHAT-FIX] Iniciando script robusto de posicionamiento/scroll");

    // Varias formas de buscar elementos por si cambian los data-testids
    const inputSelectors = [
        '[data-testid="stChatInputContainer"]',
        '.stChatInputContainer',
        '[data-testid^="stChat"][data-testid$="InputContainer"]',
        '[role="textbox"]' // fallback débil
    ];
    const msgSelectors = [
        'section[data-testid="stChatMessageContainer"]',
        '.stChatMessageContainer',
        '[data-testid^="stChat"][data-testid$="MessageContainer"]'
    ];
    const sidebarSelector = 'section[data-testid="stSidebar"], .stSidebar';

    function queryFirst(selectors) {
        for (const s of selectors) {
        const el = document.querySelector(s);
        if (el) return el;
        }
        return null;
    }

    function getSidebarWidth() {
        const sb = document.querySelector(sidebarSelector);
        return sb ? Math.round(sb.getBoundingClientRect().width) : 0;
    }

    function moveAndFixInput() {
        try {
        const inputEl = queryFirst(inputSelectors);
        if (!inputEl) { console.debug("[CHAT-FIX] Input no hallado (aún)"); return null; }

        if (inputEl.parentElement !== document.body) {
            document.body.appendChild(inputEl);
            console.debug("[CHAT-FIX] Input movido al body");
        }

        const left = getSidebarWidth();
        inputEl.style.position = 'fixed';
        inputEl.style.bottom = '0px';
        inputEl.style.left = left + 'px';
        inputEl.style.right = '0px';
        inputEl.style.zIndex = '2147483647';
        inputEl.style.boxSizing = 'border-box';
        return inputEl;
        } catch (e) {
        console.error("[CHAT-FIX] Error en moveAndFixInput:", e);
        return null;
        }
    }

    function adjustMessageContainer(inputEl) {
        try {
        const msgEl = queryFirst(msgSelectors);
        if (!msgEl) { console.debug("[CHAT-FIX] Contenedor de mensajes no hallado (aún)"); return null; }

        const inputH = inputEl ? Math.round(inputEl.getBoundingClientRect().height) : 120;
        msgEl.style.paddingBottom = (inputH + 50) + 'px';
        msgEl.style.maxHeight = 'calc(100vh - ' + (inputH + 100) + 'px)';
        return msgEl;
        } catch (e) {
        console.error("[CHAT-FIX] Error en adjustMessageContainer:", e);
        return null;
        }
    }

    function scrollToBottom(msgEl, smooth=true) {
        try {
        if (!msgEl) return;
        msgEl.scrollTo({ top: msgEl.scrollHeight, behavior: smooth ? 'smooth' : 'auto' });
        } catch (e) {
        try { msgEl.scrollTop = msgEl.scrollHeight; } catch(_) {}
        }
    }

    // Observador de mensajes (auto-scroll)
    let msgObserver = null;
    function observeMessages(msgEl) {
        if (!msgEl) return;
        if (msgObserver) {
        try { msgObserver.disconnect(); } catch(e){}
        msgObserver = null;
        }
        msgObserver = new MutationObserver((mutations) => {
        for (const m of mutations) {
            if (m.addedNodes && m.addedNodes.length) {
            setTimeout(() => scrollToBottom(msgEl, true), 30);
            break;
            }
        }
        });
        msgObserver.observe(msgEl, { childList: true, subtree: true });
        setTimeout(() => scrollToBottom(msgEl, false), 60);
        console.debug("[CHAT-FIX] Observador de mensajes activo");
    }

    // Observador global para reaplicar cuando Streamlit re-renderiza
    const globalObserver = new MutationObserver((mutations) => {
        const inputEl = moveAndFixInput();
        const msgEl = adjustMessageContainer(inputEl);
        if (msgEl) observeMessages(msgEl);
    });

    // Reintentos con backoff si no encuentra elementos (hasta X ms)
    function startRobustLoop() {
        let attempts = 0;
        const maxAttempts = 120; // ~84s con el setInterval
        const iv = setInterval(() => {
        attempts++;
        const inputEl = moveAndFixInput();
        const msgEl = adjustMessageContainer(inputEl);
        if (msgEl) observeMessages(msgEl);

        if (document.body && !globalObserver) {
            try {
            globalObserver.observe(document.body, { childList: true, subtree: true });
            } catch(e){}
        }

        if (attempts >= maxAttempts) {
            clearInterval(iv);
            console.warn("[CHAT-FIX] Máximos intentos alcanzados; si no funciona, mirá la consola para debug.");
        }
        }, 700);
    }

    // Forzar corrección al hacer click en botones importantes (ej: Guardar)
    function attachButtonsHook() {
        document.addEventListener('click', (ev) => {
        try {
            const target = ev.target;
            if (!target) return;
            // detecta botones con emoji o textos frecuentes
            const text = (target.innerText || '').toLowerCase();
            if (text.includes('guardar') || text.includes('save') || text.includes('cargar') || text.includes('nuevo chat')) {
            setTimeout(() => {
                const inputEl = moveAndFixInput();
                const msgEl = adjustMessageContainer(inputEl);
                if (msgEl) scrollToBottom(msgEl, false);
                console.debug("[CHAT-FIX] Trigger por botón: reaplicado");
            }, 120);
            }
        } catch(e) { /* ignore */ }
        }, true);
    }

    // Resize listener
    window.addEventListener('resize', () => {
        const inputEl = queryFirst(inputSelectors);
        if (inputEl) inputEl.style.left = getSidebarWidth() + 'px';
    });

    // Inicio
    window.addEventListener('load', () => {
        console.debug("[CHAT-FIX] load -> iniciando loop");
        moveAndFixInput();
        adjustMessageContainer(queryFirst(inputSelectors));
        startRobustLoop();
        attachButtonsHook();
    });

    // También arrancar inmediatamente (en caso de hot reload)
    moveAndFixInput();
    adjustMessageContainer(queryFirst(inputSelectors));
    startRobustLoop();
    attachButtonsHook();

    })();
    </script>
""", unsafe_allow_html=True)



class CharacterCreatorApp:
    def __init__(self):
        self.available_models = self.get_available_models()
        self.images_folder = "character_images"
        self.chats_folder = "saved_chats"
        self.create_images_folder()
        self.create_chats_folder()

    # ===================== Carpetas =====================
    def create_images_folder(self):
        if not os.path.exists(self.images_folder):
            os.makedirs(self.images_folder)

    def create_chats_folder(self):
        if not os.path.exists(self.chats_folder):
            os.makedirs(self.chats_folder)

    # ===================== Obtener recursos =====================
    def get_available_images(self):
        image_extensions = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']
        available_images = []
        for ext in image_extensions:
            available_images.extend(glob.glob(f"{self.images_folder}/*.{ext}"))
            available_images.extend(glob.glob(f"{self.images_folder}/*.{ext.upper()}"))
        return available_images

    def get_available_models(self):
        try:
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            return ["models/gemini-2.0-flash", "models/gemini-2.0-flash-lite",
                    "models/gemini-2.5-flash-lite","models/gemini-flash-lite-latest"]
        except Exception as e:
            st.error(f"Error conectando a la API: {e}")
            return []

    # ===================== Session state =====================
    def initialize_session_state(self):
        defaults = {
            "current_character": None,
            "messages": [],
            "character_instance": None,
            "creator_mode": True,
            "selected_image": None,
            "active_menu": "home"
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    # ===================== Estilos =====================
    def apply_custom_style(self):
        css_path = os.path.join(os.path.dirname(__file__), "styles.css")
        if os.path.exists(css_path):
            with open(css_path) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # ===================== Mostrar imagen =====================
    def display_image(self, image_path, width=100):
        try:
            if image_path and os.path.exists(image_path):
                image = Image.open(image_path)
                st.image(image, width=width)
            else:
                st.warning("⚠ Imagen no encontrada")
        except Exception as e:
            st.error(f"Error mostrando imagen: {e}")

    # ===================== Crear personaje =====================
    def create_character(self, name, personality, greeting, profile_image_path, model_name=None):
        try:
            st.session_state.character_instance = CharacterAI(
                name=name,
                personality=personality,
                greeting=greeting,
                profile_image_path=profile_image_path,
                model_name=model_name
            )
            st.session_state.current_character = name
            st.session_state.messages = [{
                "role": "assistant",
                "content": greeting,
                "character": name,
                "avatar_path": profile_image_path
            }]
            st.session_state.creator_mode = False
            st.success(f"¡Personaje {name} creado exitosamente!")
            st.rerun()
        except Exception as e:
            st.error(f"Error al crear el personaje: {str(e)}")

    # ===================== Guardar personaje =====================
    def save_character(self, character_instance):
        if not os.path.exists(self.characters_folder):
            os.makedirs(self.characters_folder)
        filename = f"{character_instance.name}.json"
        filepath = os.path.join(self.characters_folder, filename)
        data = {
            "name": character_instance.name,
            "personality": character_instance.personality,
            "greeting": character_instance.greeting,
            "profile_image_path": character_instance.profile_image_path,
            "model_name": character_instance.model_name
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ===================== Renderizar interfaz de chatbots =====================
    def render_chatbots_interface(self):
        st.title("🤖 Mis Chatbots")
        characters_folder = self.characters_folder
        chatbot_files = sorted(glob.glob(f"{characters_folder}/*.json"))
        
        if chatbot_files:
            for file_path in chatbot_files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        character_data = json.load(f)
                    
                    name = character_data.get("name", "Desconocido")
                    image_path = character_data.get("profile_image_path")
                    personality = character_data.get("personality", "")
                    model_name = character_data.get("model_name", "Desconocido")

                    # Mostrar el personaje en columnas
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col1:
                        if image_path and os.path.exists(image_path):
                            self.display_image(image_path, width=80)
                    with col2:
                        st.subheader(name)
                        st.write(f"**Modelo:** {model_name}")
                        st.write(f"**Descripción:** {personality[:120]}{'...' if len(personality)>120 else ''}")
                    with col3:
                        if st.button(f"💬 Iniciar chat", key=f"chat_{name}"):
                            # Restaurar el personaje en session_state
                            st.session_state.current_character = name
                            st.session_state.character_instance = CharacterAI(
                                name=name,
                                personality=personality,
                                greeting=character_data.get("greeting", ""),
                                profile_image_path=image_path,
                                model_name=model_name
                            )
                            st.session_state.messages = [{
                                "role": "assistant",
                                "content": character_data.get("greeting", ""),
                                "character": name,
                                "avatar_path": image_path
                            }]
                            st.session_state.creator_mode = False
                            st.session_state.active_menu = "home"
                            st.rerun()

                except Exception as e:
                    st.error(f"❌ Error cargando chatbot: {e}")
        else:
            st.info("No tienes chatbots creados aún. Crea uno desde 'Home'.")

    # ===================== Interfaz de creación de personaje =====================
    def render_character_creator(self, available_images):
        st.subheader("🧠 Crear Personaje")

        if st.session_state.get("selected_image"):
            st.success(f"**Imagen seleccionada:** {os.path.basename(st.session_state.selected_image)}")
            self.display_image(st.session_state.selected_image, width=120)
        else:
            st.warning("⚠️ No hay imagen seleccionada")

        st.markdown("---")
        st.subheader("🖼️ Seleccionar o Subir Imagen")

        # Tabs para seleccionar o subir
        tab1, tab2 = st.tabs(["📂 Seleccionar existente", "⬆️ Subir nueva"])

        with tab1:
            if available_images:
                image_options = {os.path.basename(img): img for img in available_images}

                cols = st.columns([1, 2, 1])
                with cols[1]:
                    selected_image_name = st.radio(
                        "Selecciona una imagen:",
                        options=list(image_options.keys()),
                        index=0,
                        key="image_selector"
                    )
                    if selected_image_name:
                        selected_image_path = image_options[selected_image_name]
                        st.write("**Vista previa:**")
                        self.display_image(selected_image_path, width=180)

                        if st.button("✅ Confirmar selección", key="confirm_selection"):
                            st.session_state.selected_image = selected_image_path
                            st.rerun()
            else:
                st.warning(f"📂 No hay imágenes en la carpeta '{self.images_folder}'")

        with tab2:
            uploaded_file = st.file_uploader(
                "Sube una imagen para tu personaje:",
                type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'],
                key="image_uploader"
            )
            
            if uploaded_file is not None:
                # Mostrar vista previa
                st.write("**Vista previa:**")
                image = Image.open(uploaded_file)
                st.image(image, width=180)
                
                # Botón para guardar la imagen
                if st.button("💾 Guardar y usar esta imagen", key="save_uploaded_image"):
                    try:
                        # Guardar la imagen en la carpeta
                        file_path = os.path.join(self.images_folder, uploaded_file.name)
                        
                        # Si ya existe, agregar timestamp
                        if os.path.exists(file_path):
                            name, ext = os.path.splitext(uploaded_file.name)
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            file_path = os.path.join(self.images_folder, f"{name}_{timestamp}{ext}")
                        
                        # Guardar la imagen
                        image.save(file_path)
                        
                        # Seleccionar automáticamente
                        st.session_state.selected_image = file_path
                        st.success(f"Imagen guardada como {uploaded_file.name}!")
                    except Exception as e:
                        st.error(f"Error guardando la imagen: {e}")

    def run(self):
        self.initialize_session_state()
        self.apply_custom_style()

        # Menú de navegación
        menu = st.sidebar.radio("Menú", ["Home", "Chatbots"])

        if menu == "home":
            available_images = self.get_available_images()
            self.render_character_creator(available_images)

        elif menu == "chatbots":
            self.render_chatbots_interface()


if __name__ == "__main__":
    app = CharacterCreatorApp()
    app.run()