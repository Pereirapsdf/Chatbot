import streamlit as st
import google.generativeai as genai
import os
import glob
import json
import uuid
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
            return ["models/gemini-2.0-flash"]
        except Exception as e:
            st.error(f"Error conectando a la API: {e}")
            return []
        
    @staticmethod
    def generate_unique_id():
        return str(uuid.uuid4()) 
    
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
    def create_character(self, name, personality, greeting, profile_image_path, model_name): 
        try:
            # Forzamos que siempre se use el modelo 'gemini-2.0-flash'
            model_name = "gemini-2.0-flash"

            # Validar que el modelo sea uno de los modelos permitidos
            valid_models = ["gemini-2.0-flash"]
            if model_name not in valid_models:
                raise ValueError(f"El modelo '{model_name}' no es válido. Usa uno de los modelos disponibles: {', '.join(valid_models)}")

            # Crear la instancia del personaje con el modelo fijo
            st.session_state.character_instance = CharacterAI(
                name=name,
                personality=personality,
                greeting=greeting,
                profile_image_path=profile_image_path,
                model_name=model_name
            )

            # Generar un unique_id para el personaje
            st.session_state.character_instance.unique_id = CharacterCreatorApp.generate_unique_id()

            st.session_state.current_character = name
            st.session_state.messages = [{
                "role": personality,
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
# Guardar los datos del personaje (incluyendo el modelo)
    def save_character(self, character_instance):
        characters_folder = "characters"
        if not os.path.exists(characters_folder):
            os.makedirs(characters_folder)

        # Usamos el unique_id como parte del nombre del archivo
        filename = f"{character_instance.name}_{character_instance.unique_id}.json"
        filepath = os.path.join(characters_folder, filename)

        # Guardamos los datos del personaje (incluido el modelo)
        data = {
            "name": character_instance.name,
            "personality": character_instance.personality,
            "greeting": character_instance.greeting,
            "profile_image_path": character_instance.profile_image_path,
            "model_name": character_instance.model_name,
            "unique_id": character_instance.unique_id,
            "messages": st.session_state.messages
        }
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            st.success(f"Personaje {character_instance.name} guardado exitosamente con ID {character_instance.unique_id}")
        except Exception as e:
            st.error(f"Error al guardar el personaje: {e}")


    # ===================== Interfaz de creación de personaje =====================
    def render_character_creator(self, available_images):
            """Renderizar la interfaz de creación del personaje."""
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
                            st.success(f"✅ Imagen guardada como: {os.path.basename(file_path)}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al guardar la imagen: {e}")

            st.markdown("---")
            st.subheader("📝 Datos del Personaje")
            with st.form("character_form"):
                name = st.text_input("Nombre del Personaje:", placeholder="Ej: Merlin, Doctora Elena, etc.")
                personality = st.text_area("Personalidad:", height=120)
                greeting = st.text_area("Saludo Inicial:", height=80)
                
                # Asignar el modelo "gemini-2.0-flash" de manera fija
                selected_model = "gemini-2.0-flash"
                
                create_btn = st.form_submit_button("🎭 Crear Personaje")

                if create_btn:
                    if not name or not personality or not greeting:
                        st.error("⚠ Completa todos los campos")
                    elif not st.session_state.selected_image:
                        st.error("⚠ Selecciona una imagen")
                    else:
                        # Pasar el modelo "gemini-2.0-flash" al crear el personaje
                        self.create_character(name, personality, greeting, st.session_state.selected_image, selected_model)




  # ===================== Interfaz de chat =====================
    def render_chat_interface(self):
        if not st.session_state.character_instance:
            st.info("👈 Crea un personaje primero.")
            return

        # Header con información del personaje y botones de acción
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            if os.path.exists(st.session_state.character_instance.profile_image_path):
                self.display_image(st.session_state.character_instance.profile_image_path, width=80)
        with col2:
            st.subheader(f"Conversando con: {st.session_state.current_character}")
            st.caption(f"Modelo: {st.session_state.character_instance.model_name}")
        with col3:
            # Botón para guardar chat
            if st.button("💾 Guardar", key="save_chat_btn", use_container_width=True):
                self.save_chat_history()
            
            # Botón para nuevo chat (limpia conversación pero mantiene el bot)
            if st.button("🔄 Nuevo Chat", key="new_chat_btn", use_container_width=True):
                # Mantener el personaje pero reiniciar la conversación
                greeting = st.session_state.character_instance.greeting
                st.session_state.messages = [{
                    "role": st.session_state.character_instance.personality,
                    "content": greeting,
                    "character": st.session_state.current_character,
                    "avatar_path": st.session_state.character_instance.profile_image_path
                }]
                # Limpiar historial del personaje
                st.session_state.character_instance.clear_history()
                st.success("🆕 Nueva conversación iniciada")
                st.rerun()

        st.markdown("---")

        # Mostrar mensajes con el bot a la IZQUIERDA y el usuario a la DERECHA
        for message in st.session_state.messages:
            if message["role"] == st.session_state.character_instance.personality:  # Mensaje del bot
                # BOT A LA IZQUIERDA con avatar
                with st.chat_message("assistant", avatar=message.get('avatar_path')):
                    st.write(f"**{st.session_state.current_character}:** {message['content']}")
            else:  # Mensaje del usuario
                # USUARIO A LA DERECHA sin avatar (o con avatar por defecto)
                with st.chat_message("user"):
                    st.write(message["content"])

        # Input de chat
        if prompt := st.chat_input("Escribe tu mensaje..."):
            # Añadir el mensaje del usuario
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            # Generar la respuesta del personaje
            with st.chat_message("assistant", avatar=st.session_state.character_instance.profile_image_path):
                with st.spinner(f"{st.session_state.current_character} está pensando..."):
                    response = st.session_state.character_instance.generate_response(prompt)
                    st.write(f"**{st.session_state.current_character}:** {response}")

            # Añadir la respuesta al historial de mensajes
            st.session_state.messages.append({
                "role": st.session_state.character_instance.personality,
                "content": response,
                "character": st.session_state.current_character,
                "avatar_path": st.session_state.character_instance.profile_image_path
            })
    # ===================== Guardar / Cargar chats =====================
    def save_chat_history(self):
        """Guardar chat con TODOS los datos del personaje y sobrescribir si ya existe."""
        if not st.session_state.messages or not st.session_state.character_instance:
            st.warning("⚠️ No hay conversación para guardar.")
            return

        # Usar el unique_id del personaje o crear uno si no existe
        if not hasattr(st.session_state.character_instance, 'unique_id'):
            st.session_state.character_instance.unique_id = CharacterCreatorApp.generate_unique_id()

        # Usamos el unique_id como nombre del archivo
        file_name = f"{st.session_state.character_instance.unique_id}.json"
        filepath = os.path.join(self.chats_folder, file_name)

        try:
            # Preparar los datos a guardar
            data = {
                "name": st.session_state.character_instance.name,
                "personality": st.session_state.character_instance.personality,
                "greeting": st.session_state.character_instance.greeting,
                "profile_image_path": st.session_state.character_instance.profile_image_path,
                "model_name": st.session_state.character_instance.model_name,
                "messages": st.session_state.messages,
                "unique_id": st.session_state.character_instance.unique_id  # Guardamos el ID único
            }

            # Revisamos si el archivo ya existe
            if os.path.exists(filepath):
                # Avisar que será sobrescrito
                st.warning(f"⚠️ El archivo con el ID `{st.session_state.character_instance.unique_id}` ya existe. Será sobrescrito.")
            else:
                st.success(f"💾 Guardando chat como nuevo archivo `{file_name}`")

            # Guardamos el archivo con el nombre basado en el ID único (si el archivo existe o no)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            st.success(f"💾 Chat guardado correctamente como `{os.path.basename(filepath)}`")

        except Exception as e:
            st.error(f"⚠ Error al guardar chat: {e}")
    def load_chat_history(self, selected_file):
        """Cargar chat con validación de estructura"""
        try:
            with open(selected_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Verificar si el archivo tiene los campos necesarios
            if isinstance(data, dict) and "messages" in data:
                # Verificar si tiene los datos del personaje
                if "name" in data and "personality" in data and "greeting" in data:
                    # Cargar la información del personaje
                    model_name = data.get("model_name", "gemini-2.0-flash")
                    
                    # *** EXTRAER unique_id ANTES de crear el personaje ***
                    # Si el archivo tiene unique_id, usarlo; si no, extraerlo del nombre del archivo
                    if "unique_id" in data:
                        unique_id = data["unique_id"]
                    else:
                        # Extraer el unique_id del nombre del archivo (sin la extensión .json)
                        file_name = os.path.basename(selected_file)
                        unique_id = os.path.splitext(file_name)[0]
                    
                    # Crear el objeto de personaje
                    st.session_state.character_instance = CharacterAI(
                        name=data["name"],
                        personality=data["personality"],
                        greeting=data["greeting"],
                        profile_image_path=data["profile_image_path"],
                        model_name=model_name
                    )
                    
                    # Asignar el unique_id al personaje
                    st.session_state.character_instance.unique_id = unique_id
                    
                    st.session_state.current_character = data["name"]
                    
                    # Procesar los mensajes
                    processed_messages = []
                    for msg in data["messages"]:
                        if "role" in msg:
                            processed_messages.append({
                                "role": msg["role"],
                                "content": msg["content"],
                                "character": msg.get("character", data["name"]),
                                "avatar_path": msg.get("avatar_path", data["profile_image_path"])
                            })
                    
                    st.session_state.messages = processed_messages
                    st.session_state.creator_mode = False
                    st.success(f"📂 Chat cargado correctamente. ID: {unique_id}, Modelo: {model_name}")
                else:
                    st.error("❌ El archivo no contiene la información completa del personaje.")
            else:
                st.error("❌ El archivo no tiene la estructura esperada.")
                        
        except Exception as e:
            st.error(f"⚠️ Error cargando chat: {e}")


    def render_chatbots_interface(self):
        st.title("🤖 Mis Chatbots")
        
        # Obtener los archivos JSON de la carpeta de chats guardados
        characters_folder = self.chats_folder  # Usar la carpeta correcta
        chatbot_files = sorted(glob.glob(f"{characters_folder}/*.json"))

        if chatbot_files:
            for file_path in chatbot_files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        # Cargar los datos del archivo JSON
                        data = json.load(f)
                        
                        # Comprobar que los datos están en formato dict y contienen 'messages'
                        if isinstance(data, dict) and "messages" in data:
                            # Asegurarse de que tiene la información del personaje
                            if "name" in data and "personality" in data and "greeting" in data:
                                # Verificar el modelo si está presente
                                model_name = data.get("model_name", "gemini-2.0-flash")
                                
                                # *** EXTRAER unique_id del archivo ***
                                if "unique_id" in data:
                                    unique_id = data["unique_id"]
                                else:
                                    # Extraer del nombre del archivo
                                    file_name = os.path.basename(file_path)
                                    unique_id = os.path.splitext(file_name)[0]
                                
                                # Mostrar la imagen, nombre y personalidad
                                col1, col2, col3 = st.columns([1, 3, 1])
                                
                                with col1:
                                    # Mostrar la imagen del personaje si existe
                                    if data["profile_image_path"] and os.path.exists(data["profile_image_path"]):
                                        self.display_image(data["profile_image_path"], width=80)
                                
                                with col2:
                                    # Mostrar el nombre y personalidad del personaje
                                    st.subheader(data["name"])
                                    st.write(f"**Personalidad:** {data['personality']}")
                                
                                with col3:
                                    # Botón para iniciar chat con el personaje
                                    if st.button(f"💬 Iniciar chat con {data['name']}", key=f"chat_{unique_id}"):
                                        # Restaurar el personaje en session_state
                                        st.session_state.current_character = data["name"]
                                        st.session_state.character_instance = CharacterAI(
                                            name=data["name"],
                                            personality=data["personality"],
                                            greeting="(Continuación del chat guardado)",
                                            profile_image_path=data["profile_image_path"],
                                            model_name=model_name
                                        )
                                        
                                        # *** ASIGNAR unique_id AL PERSONAJE ***
                                        st.session_state.character_instance.unique_id = unique_id
                                        
                                        # Restaurar los mensajes de la conversación
                                        st.session_state.messages = data["messages"]
                                        st.session_state.creator_mode = False
                                        st.session_state.active_menu = "home"
                                        st.rerun()

                            else:
                                st.error(f"❌ El archivo {file_path} no contiene la información completa del personaje.")
                        else:
                            st.error(f"❌ El archivo {file_path} no tiene la estructura esperada (debe contener una clave 'messages' con una lista de mensajes).")
                except Exception as e:
                    st.error(f"❌ Error cargando chatbot desde el archivo {file_path}: {e}")
        else:
            st.info("No tienes chatbots creados aún. Crea uno desde 'Home'.")
    # ===================== Main =====================
    def run(self):
        self.apply_custom_style()
        self.initialize_session_state()

        # === Layout principal con menú fijo a la izquierda ===
        col_menu, col_main = st.columns([1, 4])

        # === Menú izquierdo fijo ===
        with col_menu:
            st.title("📋 Menú principal")
            
            if st.button("🏠 Home", key="btn_home", use_container_width=True):
                # Resetear todo para crear un nuevo bot
                st.session_state.active_menu = "home"
                st.session_state.creator_mode = True
                st.session_state.messages = []
                st.session_state.character_instance = None
                st.session_state.current_character = None
                st.session_state.selected_image = None
                st.rerun()

            if st.button("💬 Chats", key="btn_chats", use_container_width=True):
                st.session_state.active_menu = "chats"
                st.rerun()

            if st.button("🤖 Chatbots", key="btn_chatbots", use_container_width=True):
                st.session_state.active_menu = "chatbots"
                st.rerun()

        # === Contenido principal según menú seleccionado ===
        with col_main:
            menu = st.session_state.active_menu

            # === HOME ===
            if menu == "home":
                st.title("🎭 Character AI Creator")
                st.caption("Crea, personaliza y conversa con tus personajes de IA")

                available_images = self.get_available_images()
                
                # Verificar que haya personaje Y que NO esté en modo creador
                if st.session_state.character_instance and not st.session_state.get("creator_mode", True):
                    self.render_chat_interface()
                else:
                    self.render_character_creator(available_images)

            # === CHATS ===
            elif menu == "chats":
                st.title("💬 Chats guardados")
                saved_files = sorted(glob.glob(f"{self.chats_folder}/*.json"))
                if saved_files:
                    file_to_load = st.selectbox("Selecciona un chat:", saved_files)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📂 Cargar chat", use_container_width=True):
                            with st.spinner("Cargando chat..."):
                                self.load_chat_history(file_to_load)
                                st.session_state.active_menu = "home"
                                st.rerun()
                    with col2:
                        if st.button("🗑️ Eliminar chat", use_container_width=True):
                            try:
                                os.remove(file_to_load)
                                st.success(f"✅ Chat eliminado: {os.path.basename(file_to_load)}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error al eliminar: {e}")
                else:
                    st.info("No hay chats disponibles.")

            # === CHATBOTS ===
            elif menu == "chatbots":
                 self.render_chatbots_interface()

if __name__ == "__main__":
    app = CharacterCreatorApp()
    app.run()