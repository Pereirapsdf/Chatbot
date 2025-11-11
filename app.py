import streamlit as st
import google.generativeai as genai
import os
import json
import uuid
from datetime import datetime
from PIL import Image
from pathlib import Path
# Se asume que character_base.py (CharacterAI) existe y está correcto.
from character_base import CharacterAI 

# --- Configuración y Estilos Críticos ---
st.set_page_config(
    page_title="Character AI Creator",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo crítico para fijar el input de chat (necesario para la UX)
st.markdown("""
    <style>
    .main .block-container { padding-bottom: 260px !important; }
    [data-testid="stChatInputContainer"] {
        position: fixed !important;
        bottom: 0 !important;
        left: 260px !important; /* Ajuste manual sin JS complejo */
        right: 0 !important;
        z-index: 2147483647 !important;
        background-color: #0e1117 !important;
        padding: 10px 16px !important;
        border-top: 1px solid #262730 !important;
    }
    </style>
""", unsafe_allow_html=True)
# Se elimina el script robusto de JS por ser demasiado verboso.

class CharacterCreatorApp:
    IMAGES_FOLDER = "character_images"
    CHATS_FOLDER = "saved_chats"
    CHARACTERS_FOLDER = "characters"
    
    def __init__(self):
        self._setup_folders()
        self.initialize_session_state()

    # ===================== Setup y Utilidades =====================
    def _setup_folders(self):
        Path(self.IMAGES_FOLDER).mkdir(exist_ok=True)
        Path(self.CHATS_FOLDER).mkdir(exist_ok=True)
        Path(self.CHARACTERS_FOLDER).mkdir(exist_ok=True)

    def get_available_images(self):
        return sorted([str(p) for p in Path(self.IMAGES_FOLDER).glob("*") 
                       if p.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']])

    def initialize_session_state(self):
        defaults = {
            "current_character": None, "messages": [],
            "character_instance": None, "creator_mode": True,
            "selected_image": None, "active_menu": "home"
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
                
        # Configurar la API Key aquí (se asume que CharacterAI lo usa)
        if 'GOOGLE_API_KEY' in os.environ:
             genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
        elif 'api_configured' not in st.session_state:
             st.warning("⚠️ La variable de entorno 'GOOGLE_API_KEY' no está configurada.")
             st.session_state.api_configured = False


    def display_image(self, image_path, width=100):
        if image_path and Path(image_path).exists():
            st.image(Image.open(image_path), width=width)
        else:
            st.warning("⚠ Imagen no encontrada")

    @staticmethod
    def generate_unique_id():
        return str(uuid.uuid4())

    # ===================== Lógica de Personaje/Chat =====================
    def create_character(self, name, personality, greeting, profile_image_path): 
        try:
            model_name = "gemini-2.0-flash" # Fijo
            
            st.session_state.character_instance = CharacterAI(
                name=name, personality=personality, greeting=greeting, 
                profile_image_path=profile_image_path, model_name=model_name
            )
            st.session_state.character_instance.unique_id = self.generate_unique_id()

            st.session_state.current_character = name
            st.session_state.messages = [{
                "role": name, # Usar el nombre como role para identificarlo
                "content": greeting,
                "avatar_path": profile_image_path
            }]
            st.session_state.creator_mode = False
            st.success(f"¡Personaje **{name}** creado exitosamente!")
            st.rerun()

        except Exception as e:
            st.error(f"Error al crear el personaje: {str(e)}")

    def save_character_and_chat(self, character_instance, is_chat=True):
        """Guarda tanto el personaje (base) como el chat (completo)."""
        folder = self.CHATS_FOLDER if is_chat else self.CHARACTERS_FOLDER
        
        if not character_instance:
            st.warning("⚠️ No hay datos para guardar.")
            return

        unique_id = getattr(character_instance, 'unique_id', self.generate_unique_id())
        setattr(character_instance, 'unique_id', unique_id) # Asegurar que el ID esté en la instancia

        data = {
            "name": character_instance.name, "personality": character_instance.personality,
            "greeting": character_instance.greeting, "profile_image_path": character_instance.profile_image_path,
            "model_name": character_instance.model_name, "unique_id": unique_id,
        }
        if is_chat:
            data["messages"] = st.session_state.messages

        filepath = Path(folder) / f"{unique_id}.json" # Usar ID como nombre de archivo para chats

        try:
            if is_chat and filepath.exists():
                st.warning(f"⚠️ El chat con ID `{unique_id}` será sobrescrito.")
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            st.success(f"💾 {'Chat' if is_chat else 'Personaje base'} guardado correctamente.")

        except Exception as e:
            st.error(f"⚠ Error al guardar: {e}")

    def load_chat_history(self, selected_file):
        try:
            with open(selected_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validar y cargar datos del personaje
            if not all(k in data for k in ["name", "personality", "greeting", "messages"]):
                st.error("❌ El archivo no contiene la información mínima requerida (nombre, personalidad, saludo, mensajes).")
                return

            model_name = data.get("model_name", "gemini-2.0-flash")
            unique_id = data.get("unique_id", Path(selected_file).stem)

            st.session_state.character_instance = CharacterAI(
                name=data["name"], personality=data["personality"], greeting=data["greeting"],
                profile_image_path=data["profile_image_path"], model_name=model_name
            )
            st.session_state.character_instance.unique_id = unique_id
            st.session_state.current_character = data["name"]
            st.session_state.messages = data["messages"]
            st.session_state.creator_mode = False
            
            # Limpiar historial de chat para la instancia nueva si es necesario (el contexto se recrea desde 'messages')
            st.session_state.character_instance.clear_history() 

            st.success(f"📂 Chat cargado. ID: {unique_id}, Modelo: {model_name}")
            st.rerun()

        except Exception as e:
            st.error(f"⚠️ Error cargando chat: {e}")

    # ===================== Renderizado de Vistas =====================
    def render_character_creator(self, available_images):
        st.subheader("🧠 Crear Personaje")

        if st.session_state.selected_image:
            st.success(f"**Imagen seleccionada:** {Path(st.session_state.selected_image).name}")
            self.display_image(st.session_state.selected_image, width=120)
        else:
            st.warning("⚠️ No hay imagen seleccionada")

        st.markdown("---")
        tab1, tab2 = st.tabs(["📂 Seleccionar existente", "⬆️ Subir nueva"])

        with tab1:
            if available_images:
                cols = st.columns([1, 2, 1])
                with cols[1]:
                    selected_image_path = st.radio("Selecciona una imagen:", options=available_images, format_func=lambda x: Path(x).name, index=0)
                    self.display_image(selected_image_path, width=180)

                    if st.button("✅ Confirmar selección", key="confirm_selection"):
                        st.session_state.selected_image = selected_image_path
                        st.rerun()
            else:
                st.info(f"📂 No hay imágenes en '{self.IMAGES_FOLDER}'")

        with tab2:
            uploaded_file = st.file_uploader("Sube una imagen:", type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'])
            if uploaded_file:
                st.image(Image.open(uploaded_file), width=180, caption="Vista previa")
                if st.button("💾 Guardar y usar esta imagen", key="save_uploaded_image"):
                    try:
                        file_path = Path(self.IMAGES_FOLDER) / uploaded_file.name
                        if file_path.exists(): # Evitar sobrescribir
                            name, ext = file_path.stem, file_path.suffix
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            file_path = Path(self.IMAGES_FOLDER) / f"{name}_{timestamp}{ext}"

                        Image.open(uploaded_file).save(file_path)
                        st.session_state.selected_image = str(file_path)
                        st.success(f"✅ Imagen guardada: {file_path.name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al guardar la imagen: {e}")

        st.markdown("---")
        st.subheader("📝 Datos del Personaje")
        with st.form("character_form"):
            name = st.text_input("Nombre del Personaje:", placeholder="Ej: Merlin")
            personality = st.text_area("Personalidad:", height=120)
            greeting = st.text_area("Saludo Inicial:", height=80)
            st.caption(f"Modelo IA fijo: **{'gemini-2.0-flash'}**")

            if st.form_submit_button("🎭 Crear Personaje"):
                if not all([name, personality, greeting, st.session_state.selected_image]):
                    st.error("⚠ Completa todos los campos y selecciona una imagen.")
                else:
                    self.create_character(name, personality, greeting, st.session_state.selected_image)
    # --- Fragmento de la Clase CharacterCreatorApp (Código Corregido) ---

        def render_chatbots_interface(self):
            st.title("🤖 Mis Chatbots")
            chatbot_files = sorted(Path(self.CHATS_FOLDER).glob("*.json"))

            if chatbot_files:
                for file_path in chatbot_files:
                    try:
                        data = json.loads(file_path.read_text(encoding="utf-8"))
                        
                        if not all(k in data for k in ["name", "personality", "profile_image_path"]): continue
                        
                        unique_id = data.get("unique_id", file_path.stem)
                        
                        col1, col2, col3 = st.columns([1, 3, 1])
                        with col1: self.display_image(data["profile_image_path"], width=80)
                        with col2:
                            st.subheader(data["name"])
                            st.caption(f"**Personalidad:** {data['personality']}")
                            st.caption(f"Último chat: {len(data['messages'])} mensajes")
                        with col3:
                            # Al hacer clic, cargamos el chat completo y el load_chat_history hace el rerun y cambia el menú
                            if st.button(f"💬 Iniciar chat con {data['name']}", key=f"chat_{unique_id}", use_container_width=True):
                                self.load_chat_history(str(file_path))
                                # ¡El rerun ya lo hace load_chat_history, no necesitamos nada más aquí!

                    except Exception as e:
                        st.error(f"❌ Error cargando chatbot desde {file_path.name}: {e}")
            else:
                st.info("No tienes chatbots guardados. Crea y guarda un chat desde 'Home'.")

    def render_chatbots_interface(self):
        st.title("🤖 Mis Chatbots")
        chatbot_files = sorted(Path(self.CHATS_FOLDER).glob("*.json"))

        if chatbot_files:
            for file_path in chatbot_files:
                try:
                    data = json.loads(file_path.read_text(encoding="utf-8"))
                    
                    if not all(k in data for k in ["name", "personality", "profile_image_path"]): continue
                    
                    unique_id = data.get("unique_id", file_path.stem)
                    
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col1: self.display_image(data["profile_image_path"], width=80)
                    with col2:
                        st.subheader(data["name"])
                        st.caption(f"**Personalidad:** {data['personality']}")
                        st.caption(f"Último chat: {len(data['messages'])} mensajes")
                    with col3:
                        if st.button(f"💬 Iniciar chat con {data['name']}", key=f"chat_{unique_id}", use_container_width=True):
                            self.load_chat_history(str(file_path))
                            st.session_state.active_menu = "home"

                except Exception as e:
                    st.error(f"❌ Error cargando chatbot desde {file_path.name}: {e}")
        else:
            st.info("No tienes chatbots guardados. Crea y guarda un chat desde 'Home'.")

    # ===================== Main Loop =====================
    def run(self):
        col_menu, col_main = st.columns([1, 4])

        with col_menu:
            st.title("📋 Menú")
            
            # Botones de navegación simplificados
            if st.button("🏠 Home", key="btn_home", use_container_width=True):
                st.session_state.update({"active_menu": "home", "creator_mode": True, "messages": [], "character_instance": None, "current_character": None, "selected_image": None})
                st.rerun()

            if st.button("🤖 Chatbots", key="btn_chatbots", use_container_width=True):
                st.session_state.active_menu = "chatbots"
                st.rerun()

        with col_main:
            menu = st.session_state.active_menu

            if menu == "home":
                st.title("🎭 Character AI Creator")
                st.caption("Crea, personaliza y conversa con tus personajes de IA")
                
                if st.session_state.character_instance and not st.session_state.creator_mode:
                    self.render_chat_interface()
                else:
                    self.render_character_creator(self.get_available_images())

            elif menu == "chatbots":
                 self.render_chatbots_interface()


if __name__ == "__main__":
    app = CharacterCreatorApp()
    app.run()