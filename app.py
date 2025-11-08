import streamlit as st
import google.generativeai as genai
import os
import glob
import json
from datetime import datetime
from PIL import Image
from character_base import CharacterAI
from streamlit_autorefresh import st_autorefresh

# Configurar página
st.set_page_config(
    page_title="Character AI Creator",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("""
    <script>
    // --- Scroll automático hasta el último mensaje ---
    function autoScrollChat() {
    const chatContainer = document.querySelector('section[data-testid="stChatMessageContainer"]');
    if (chatContainer) {
        chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: 'smooth'
        });
    }
    }

    // Observar cuando se agregan nuevos mensajes
    const chatObserver = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
        if (mutation.addedNodes.length > 0) {
        autoScrollChat();
        }
    }
    });

    const initAutoScroll = () => {
    const chatContainer = document.querySelector('section[data-testid="stChatMessageContainer"]');
    if (chatContainer) {
        chatObserver.observe(chatContainer, { childList: true, subtree: true });
        autoScrollChat(); // desplazarse al final al iniciar
    } else {
        setTimeout(initAutoScroll, 500); // esperar a que aparezca
    }
    };

    window.addEventListener('load', initAutoScroll);
    setInterval(initAutoScroll, 2000); // reforzar en cada re-render
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

    # ===================== Interfaz de creación de personaje =====================
    def render_character_creator(self, available_images):
        st.subheader("🧠 Crear Personaje")

        if st.session_state.get("selected_image"):
            st.success(f"**Imagen seleccionada:** {os.path.basename(st.session_state.selected_image)}")
            self.display_image(st.session_state.selected_image, width=120)
        else:
            st.warning("⚠️ No hay imagen seleccionada")

        st.markdown("---")
        st.subheader("🖼️ Seleccionar Imagen")

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

        st.markdown("---")
        st.subheader("📝 Datos del Personaje")
        with st.form("character_form"):
            name = st.text_input("Nombre del Personaje:", placeholder="Ej: Merlin, Doctora Elena, etc.")
            personality = st.text_area("Personalidad:", height=120)
            greeting = st.text_area("Saludo Inicial:", height=80)
            selected_model = None
            if self.available_models:
                selected_model = st.selectbox("Modelo de IA:", self.available_models, index=0)
            create_btn = st.form_submit_button("🎭 Crear Personaje")

            if create_btn:
                if not name or not personality or not greeting:
                    st.error("⚠ Completa todos los campos")
                elif not st.session_state.selected_image:
                    st.error("⚠ Selecciona una imagen")
                else:
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
            
            # Botón para nuevo chat
            if st.button("🔄 Nuevo Chat", key="new_chat_btn", use_container_width=True):
                st.session_state.creator_mode = True
                st.session_state.messages = []
                st.session_state.character_instance = None
                st.session_state.current_character = None
                st.rerun()

        st.markdown("---")

        # Mostrar mensajes
        for message in st.session_state.messages:
            if message["role"] == "assistant":
                with st.chat_message("assistant", avatar=message.get('avatar_path')):
                    st.write(f"**{message.get('character', 'AI')}:** {message['content']}")
            else:
                with st.chat_message("user"):
                    st.write(message["content"])

        # Input de chat
        if prompt := st.chat_input("Escribe tu mensaje..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant", avatar=st.session_state.character_instance.profile_image_path):
                with st.spinner(f"{st.session_state.current_character} está pensando..."):
                    response = st.session_state.character_instance.generate_response(prompt)
                    st.write(f"**{st.session_state.current_character}:** {response}")

            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "character": st.session_state.current_character,
                "avatar_path": st.session_state.character_instance.profile_image_path
            })

    # ===================== Guardar / Cargar chats =====================
    def save_chat_history(self):
        if not st.session_state.messages or not st.session_state.character_instance:
            st.warning("⚠️ No hay conversación para guardar.")
            return

        filename = f"{st.session_state.current_character}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.chats_folder, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(st.session_state.messages, f, ensure_ascii=False, indent=2)
            st.success(f"💾 Chat guardado como `{filename}`")
        except Exception as e:
            st.error(f"⚠ Error guardando chat: {e}")

    def load_chat_history(self, selected_file):
        try:
            with open(selected_file, "r", encoding="utf-8") as f:
                messages = json.load(f)
            st.session_state.messages = messages
            
            # Restaurar el personaje
            if messages:
                first_message = next(
                    (m for m in messages if m.get("role") == "assistant"), None
                )
                if first_message:
                    name = first_message.get("character", "Personaje")
                    avatar_path = first_message.get("avatar_path", None)
                    st.session_state.current_character = name
                    st.session_state.character_instance = CharacterAI(
                        name=name,
                        personality="(restaurado desde chat guardado)",
                        greeting="(continuación de conversación anterior)",
                        profile_image_path=avatar_path,
                        model_name=self.available_models[0] if self.available_models else "unknown"
                    )
                    st.session_state.creator_mode = False
            
            st.success("📂 Chat cargado correctamente.")
        except Exception as e:
            st.error(f"⚠ Error cargando chat: {e}")

    # ===================== Main =====================
    def run(self):
        self.apply_custom_style()
        self.initialize_session_state()
        st_autorefresh(interval=2000, key="auto_refresh")

        # === Layout principal con menú fijo a la izquierda ===
        col_menu, col_main = st.columns([1, 4])

        # === Menú izquierdo fijo ===
        with col_menu:
            st.title("📋 Menú principal")
            
            if st.button("🏠 Home", key="btn_home", use_container_width=True):
                st.session_state.active_menu = "home"
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
                
                if st.session_state.character_instance and not st.session_state.creator_mode:
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
                st.title("🤖 Mis Chatbots")
                st.write("Aquí podrás listar, crear o gestionar tus chatbots.")
                
                if st.session_state.character_instance:
                    st.subheader("Personaje Actual")
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if os.path.exists(st.session_state.character_instance.profile_image_path):
                            self.display_image(st.session_state.character_instance.profile_image_path, width=100)
                    with col2:
                        st.write(f"**Nombre:** {st.session_state.current_character}")
                        st.write(f"**Modelo:** {st.session_state.character_instance.model_name}")
                        if st.button("💬 Ir al chat", use_container_width=True):
                            st.session_state.active_menu = "home"
                            st.rerun()
                else:
                    st.info("No hay personajes creados todavía.")



if __name__ == "__main__":
    app = CharacterCreatorApp()
    app.run()