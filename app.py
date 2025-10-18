import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from character_base import CharacterAI

load_dotenv()

# Configurar página
st.set_page_config(
    page_title="Character AI Creator",
    page_icon="🎭",
    layout="wide"
)

class CharacterCreatorApp:
    def __init__(self):
        self.available_models = self.get_available_models()
        
    def get_available_models(self):
        """Obtener modelos disponibles"""
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
    
    def initialize_session_state(self):
        if 'current_character' not in st.session_state:
            st.session_state.current_character = None
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'character_instance' not in st.session_state:
            st.session_state.character_instance = None
        if 'creator_mode' not in st.session_state:
            st.session_state.creator_mode = True
    
    def render_sidebar(self):
        with st.sidebar:
            st.title("🎭 Character AI Creator")
            st.markdown("---")
            
            # Mostrar información de modelos disponibles
            st.subheader("🔧 Configuración")
            if self.available_models:
                st.success(f"✅ {len(self.available_models)} modelos disponibles")
                with st.expander("Ver modelos"):
                    for model in self.available_models:
                        st.code(model)
            else:
                st.error("❌ No se pudieron cargar los modelos")
                st.info("Verifica tu API key en el archivo .env")
            
            st.markdown("---")
            
            # Modo: Crear personaje
            self.render_character_creator()
            
            # Información del personaje actual
            if st.session_state.character_instance:
                st.markdown("---")
                st.subheader("Personaje Actual")
                st.info(f"**Nombre:** {st.session_state.character_instance.name}")
                st.info(f"**Modelo:** {st.session_state.character_instance.model_name}")
                
                if st.button("🔄 Nueva Conversación"):
                    st.session_state.messages = []
                    st.session_state.character_instance.clear_history()
                    st.rerun()
    
    def render_character_creator(self):
        st.subheader("Crear Personaje")
        
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
            
            # Selector de modelo si hay disponibles
            selected_model = None
            if self.available_models:
                selected_model = st.selectbox(
                    "Modelo de IA:",
                    self.available_models,
                    index=0
                )
            
            create_btn = st.form_submit_button("🎭 Crear Personaje")
            
            if create_btn and name and personality and greeting:
                self.create_character(name, personality, greeting, selected_model)
    
    def create_character(self, name, personality, greeting, model_name=None):
        try:
            st.session_state.character_instance = CharacterAI(
                name=name,
                personality=personality,
                greeting=greeting,
                model_name=model_name
            )
            st.session_state.current_character = name
            st.session_state.messages = []
            st.session_state.creator_mode = False
            
            # Añadir saludo inicial
            st.session_state.messages.append({
                "role": "assistant", 
                "content": greeting,
                "character": name
            })
            
            st.success(f"¡Personaje {name} creado exitosamente!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error al crear el personaje: {str(e)}")
    
    def render_chat(self):
        st.title("💬 Character AI Chat")
        st.markdown("---")
        
        if not st.session_state.character_instance:
            st.info("👈 Crea un personaje en la barra lateral para comenzar!")
            return
        
        # Header del chat
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"Conversando con: {st.session_state.current_character}")
            st.caption(f"Modelo: {st.session_state.character_instance.model_name}")
        with col2:
            if st.button("🗑️ Limpiar Chat"):
                st.session_state.messages = []
                st.session_state.character_instance.clear_history()
                st.rerun()
        
        # Mostrar mensajes del chat
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    if message["role"] == "assistant":
                        st.write(f"**{message.get('character', 'AI')}:** {message['content']}")
                    else:
                        st.write(message["content"])
        
        # Input del usuario
        if prompt := st.chat_input("Escribe tu mensaje aquí..."):
            # Añadir mensaje del usuario
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Mostrar mensaje del usuario
            with st.chat_message("user"):
                st.write(prompt)
            
            # Generar y mostrar respuesta
            with st.chat_message("assistant"):
                with st.spinner(f"{st.session_state.current_character} está pensando..."):
                    response = st.session_state.character_instance.generate_response(prompt)
                    st.write(f"**{st.session_state.current_character}:** {response}")
            
            # Añadir respuesta al historial de mensajes
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "character": st.session_state.current_character
            })
    
    def run(self):
        self.initialize_session_state()
        self.render_sidebar()
        
        if st.session_state.character_instance and not st.session_state.creator_mode:
            self.render_chat()
        else:
            # Mostrar página de bienvenida
            st.title("🎭 Character AI Creator")
            st.markdown("""
            ### Crea tu propio personaje de IA conversacional
            
            **Características:**
            - ✅ Detección automática de modelos disponibles
            - ✅ Crea personajes personalizados
            - ✅ Selección de modelo de IA
            - ✅ Conversaciones persistentes
            
            **Instrucciones:**
            1. Verifica que los modelos estén disponibles en la barra lateral 👈
            2. Crea tu personaje personalizado
            3. ¡Comienza a chatear!
            """)

if __name__ == "__main__":
    app = CharacterCreatorApp()
    app.run()