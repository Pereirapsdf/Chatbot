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
    layout="wide"
)

class CharacterCreatorApp:
    def __init__(self):
        self.available_models = self.get_available_models()
        self.images_folder = "character_images"
        self.chats_folder = "saved_chats"
        self.create_images_folder()
        self.create_chats_folder()
        
    def create_images_folder(self):
        """Crear carpeta de imágenes si no existe"""
        if not os.path.exists(self.images_folder):
            os.makedirs(self.images_folder)

    def create_chats_folder(self):
        """Crear carpeta de chats si no existe"""
        if not os.path.exists(self.chats_folder):
            os.makedirs(self.chats_folder)
    
    def get_available_images(self):
        """Obtener lista de imágenes disponibles en la carpeta"""
        image_extensions = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']
        available_images = []
        for ext in image_extensions:
            available_images.extend(glob.glob(f"{self.images_folder}/*.{ext}"))
            available_images.extend(glob.glob(f"{self.images_folder}/*.{ext.upper()}"))
        return available_images
    
    def get_available_models(self):
        """Obtener modelos disponibles desde Google Generative AI"""
        try:
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            models = genai.list_models()
            available_models = []
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    available_models.append(model.name)
            return available_models
        except Exception as e:
            st.error(f"Error conectando a la API: {e}")
            return []
    
    def display_image(self, image_path, width=100):
        """Mostrar imagen con tamaño controlado"""
        try:
            if image_path and os.path.exists(image_path):
                image = Image.open(image_path)
                st.image(image, width=width)
            else:
                st.warning("❌ Imagen no encontrada")
        except Exception as e:
            st.error(f"Error mostrando imagen: {e}")
    
    def initialize_session_state(self):
        if 'current_character' not in st.session_state:
            st.session_state.current_character = None
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'character_instance' not in st.session_state:
            st.session_state.character_instance = None
        if 'creator_mode' not in st.session_state:
            st.session_state.creator_mode = True  # Empieza en modo creación
        if 'selected_image' not in st.session_state:
            st.session_state.selected_image = None
    
    
    def save_chat_history(self):
        """Guardar historial de chat actual en un archivo JSON"""
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
            st.error(f"❌ Error guardando chat: {e}")

    def load_chat_history(self, selected_file):
        """Cargar un chat guardado desde archivo JSON"""
        try:
            with open(selected_file, "r", encoding="utf-8") as f:
                messages = json.load(f)
            st.session_state.messages = messages
            st.success("📂 Chat cargado correctamente.")
        except Exception as e:
            st.error(f"❌ Error cargando chat: {e}")

    def render_sidebar(self):
        with st.subheader:
            st.title("🎭 Character AI Creator")
            st.markdown("---")
        
        # Mostrar información de modelos disponibles
        st.subheader("🔧 Configuración")
        if self.available_models:
            st.success(f"✅ {len(self.available_models)} modelos disponibles")
        else:
            st.error("❌ No se pudieron cargar los modelos")
        
        # Cargar imágenes disponibles
        available_images = self.get_available_images()
        st.info(f"📁 {len(available_images)} imágenes en carpeta")
        
        st.markdown("---")

        # ==============================
        # 📂 NUEVA SECCIÓN: Cargar chat guardado
        # ==============================
        st.subheader("📂 Cargar Chat Guardado")

        saved_files = sorted(glob.glob(f"{self.chats_folder}/*.json"))
        if saved_files:
            file_to_load = st.selectbox(
                "Selecciona un chat para cargar:",
                options=saved_files,
                format_func=lambda x: os.path.basename(x)
            )
            if st.button("✅ Cargar Chat Guardado"):
                self.load_chat_history(file_to_load)

                # Recuperar info del personaje desde el primer mensaje
                if st.session_state.messages:
                    first_message = next((m for m in st.session_state.messages if m.get("role") == "assistant"), None)
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
                        st.success(f"💬 Chat de {name} restaurado correctamente.")
                        st.rerun()
        else:
            st.info("No hay chats guardados todavía.")

        st.markdown("---")
        
        # Botón para volver a crear personaje si ya hay uno
        if st.session_state.character_instance and not st.session_state.creator_mode:
            if st.button("🔄 Crear Nuevo Personaje"):
                st.session_state.creator_mode = True
                st.session_state.selected_image = None
                st.rerun()
        
      
        self.render_character_creator(available_images)
        
        if st.session_state.character_instance:
            st.markdown("---")
            st.subheader("Personaje Actual")
            
            if (st.session_state.character_instance.profile_image_path and 
                os.path.exists(st.session_state.character_instance.profile_image_path)):
                col1, col2 = st.columns([1, 2])
                with col1:
                    self.display_image(
                        st.session_state.character_instance.profile_image_path, 
                        width=60
                    )
                with col2:
                    st.info(f"**Nombre:** {st.session_state.character_instance.name}")
            else:
                st.info(f"**Nombre:** {st.session_state.character_instance.name}")
            
            st.info(f"**Modelo:** {st.session_state.character_instance.model_name}")
            
            if st.button("🔄 Nueva Conversación"):
                self.save_chat_history()
                st.session_state.messages = []
                st.session_state.character_instance.clear_history()
                st.rerun()

    
    
    def render_character_creator(self, available_images):
        st.subheader("Crear Personaje")
        
        # Mostrar imagen seleccionada actualmente PRIMERO
        if st.session_state.selected_image:
            st.success(f"**Imagen seleccionada:** {os.path.basename(st.session_state.selected_image)}")
            self.display_image(st.session_state.selected_image, width=120)
        else:
            st.warning("⚠️ No hay imagen seleccionada")
        
        st.markdown("---")
        
        # Selector de imagen desde carpeta
        st.subheader("🖼️ Seleccionar Imagen")
        
        if available_images:
            image_options = {os.path.basename(img): img for img in available_images}
            
            if image_options:
                selected_image_name = st.radio(
                    "Selecciona una imagen:",
                    options=list(image_options.keys()),
                    index=0,
                    key="image_selector"
                )
                
                if selected_image_name:
                    selected_image_path = image_options[selected_image_name]
                    st.write("**Vista previa:**")
                    self.display_image(selected_image_path, width=100)
                    
                    if st.button("✅ Confirmar selección", key="confirm_selection"):
                        st.session_state.selected_image = selected_image_path
                        st.rerun()
            else:
                st.warning("No hay imágenes disponibles")
        else:
            st.warning(f"📁 No hay imágenes en la carpeta '{self.images_folder}'")
            st.info("Agrega imágenes PNG, JPG, JPEG, etc. en la carpeta")
        
        st.markdown("---")
        st.subheader("📤 Subir Nueva Imagen")
        
        uploaded_file = st.file_uploader(
            "Subir imagen a la carpeta:",
            type=['png', 'jpg', 'jpeg', 'gif'],
            help="La imagen se guardará en la carpeta character_images",
            key="image_uploader"
        )
        
        if uploaded_file is not None:
            image_path = os.path.join(self.images_folder, uploaded_file.name)
            with open(image_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success(f"✅ Imagen guardada: {uploaded_file.name}")
            st.session_state.selected_image = image_path
            st.rerun()
        
        st.markdown("---")
        st.subheader("📝 Datos del Personaje")
        
        with st.form("character_form"):
            name = st.text_input("Nombre del Personaje:", placeholder="Ej: Merlin, Doctora Elena, etc.")
            personality = st.text_area(
                "Personalidad:",
                height=120,
                placeholder="Describe la personalidad, forma de hablar, intereses..."
            )
            greeting = st.text_area(
                "Saludo Inicial:",
                height=80,
                placeholder="Cómo saluda el personaje al iniciar..."
            )
            
            selected_model = None
            if self.available_models:
                selected_model = st.selectbox(
                    "Modelo de IA:",
                    self.available_models,
                    index=0
                )
            
            create_btn = st.form_submit_button("🎭 Crear Personaje")
            
            if create_btn:
                if not name or not personality or not greeting:
                    st.error("❌ Por favor completa todos los campos obligatorios")
                elif not st.session_state.selected_image:
                    st.error("❌ Por favor selecciona una imagen")
                else:
                    self.create_character(
                        name, 
                        personality, 
                        greeting, 
                        st.session_state.selected_image, 
                        selected_model
                    )
    def apply_custom_style(self):
        custom_css = """
            <style>
            /* Fondo general */
            [data-testid="stAppViewContainer"] {
                background-color: #FDFDFD;
                background-image: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                background-attachment: fixed;
             }
         /* Fondo del sidebar */
            [data-testid="stSidebar"] {
             background-color: #f1f3f8;
            }
            /* Cuadros de chat */
            div[data-testid="stChatMessage"] {
                border-radius: 10px;
                padding: 8px;
                margin: 5px 0;
            }   
        </style>
        """
        st.markdown(custom_css, unsafe_allow_html=True)

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
            st.session_state.messages = []
            st.session_state.creator_mode = False  
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": greeting,
                "character": name,
                "avatar_path": profile_image_path
            })
            
            st.success(f"¡Personaje {name} creado exitosamente!")
            st.rerun()
        except Exception as e:
            st.error(f"Error al crear el personaje: {str(e)}")
    
    def render_chat_interface(self):
        """Renderizar la interfaz del chat con imagen de perfil"""
        st.title("💬 Character AI Chat")
        st.markdown("---")
        
        if not st.session_state.character_instance:
            st.info("👈 Crea un personaje en la barra lateral para comenzar!")
            return
        
        col1, col2, col3 = st.columns([1, 3, 2])
        with col1:
            if (st.session_state.character_instance.profile_image_path and 
                os.path.exists(st.session_state.character_instance.profile_image_path)):
                self.display_image(
                    st.session_state.character_instance.profile_image_path, 
                    width=80
                )
        with col2:
            st.subheader(f"Conversando con: {st.session_state.current_character}")
            st.caption(f"Modelo: {st.session_state.character_instance.model_name}")
        with col3:
            st.markdown("### Opciones")
            if st.button("💾 Guardar Chat"):
                self.save_chat_history()
            folder = self.chats_folder
            saved_files = sorted(glob.glob(f"{folder}/*.json"))
            if saved_files:
                selected_file = st.selectbox("📂 Cargar Chat:", saved_files, key="load_chat_select")
                if st.button("✅ Cargar Chat"):
                    self.load_chat_history(selected_file)
                    st.rerun()
            if st.button("🗑️ Limpiar Chat"):
                self.save_chat_history()
                st.session_state.messages = []
                st.session_state.character_instance.clear_history()
                st.rerun()
        
        chat_container = st.container()
        self.render_chat_messages(chat_container)
        self.render_chat_input()
    
    def render_chat_messages(self, container):
        with container:
            for message in st.session_state.messages:
                if message["role"] == "assistant":
                    with st.chat_message("assistant", avatar=message.get('avatar_path')):
                        st.write(f"**{message.get('character', 'AI')}:** {message['content']}")
                else:
                    with st.chat_message("user"):
                        st.write(message["content"])
    
    def render_chat_input(self):
        if prompt := st.chat_input("Escribe tu mensaje aquí..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            self.generate_and_display_response(prompt)
    
    def generate_and_display_response(self, prompt):
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
    
    def run(self):
        self.initialize_session_state()
        self.render_sidebar()
        if st.session_state.character_instance and not st.session_state.creator_mode:
            self.render_chat_interface()
        else:
            if st.session_state.character_instance:
                st.info("💡 Usa el botón 'Crear Nuevo Personaje' en la barra lateral para modificar o crear otro personaje.")
            else:
                st.title("🎭 Character AI Creator")
                st.markdown("""
                ### Crea tu propio personaje de IA conversacional con imágenes locales
                
                **Instrucciones:**
                1. En la barra lateral 👈 selecciona o sube una imagen
                2. Completa nombre, personalidad y saludo
                3. Haz clic en "Crear Personaje"
                4. ¡Comienza a chatear!
                """)

if __name__ == "__main__":
    app = CharacterCreatorApp()
    app.run()
