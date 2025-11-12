import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class CharacterAI:
    # Se utiliza 'gemini-2.0-flash' como valor predeterminado, aunque en _get_available_model
    # se fuerza a usar 'models/gemini-1.5-flash' por la lógica original, que he simplificado.
    DEFAULT_MODEL = "gemini-2.0-flash" 
    FALLBACK_MODEL = "models/gemini-1.5-flash" # Según la lógica de _get_available_model

    def __init__(self, name, personality, greeting, profile_image_path=None, model_name=None):
        self.name = name
        self.personality = personality
        self.greeting = greeting
        self.profile_image_path = profile_image_path 
        self.conversation_history = []
        
        # Configurar la API y seleccionar el modelo
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.model_name = model_name or self._get_available_model()
        self.model = genai.GenerativeModel(self.model_name)
        
    def _get_available_model(self):
        """Devolver 'models/gemini-1.5-flash' por defecto, siguiendo la lógica original."""
        print(f"Usando modelo: {self.FALLBACK_MODEL}")
        return self.FALLBACK_MODEL

    def get_system_prompt(self):
        """Genera el prompt del sistema y el historial de forma concisa."""
        history = self._format_conversation_history()
        
        # Uso de f-strings multilínea para claridad y concisión
        return f"""
        Eres {self.name}. {self.personality}
        
        Reglas importantes:
        - Responde SIEMPRE en primera persona como {self.name}
        - Mantén tu personalidad en cada respuesta
        - Sé coherente con tu carácter y forma de hablar
        - No rompas el personaje bajo ninguna circunstancia
        - Usa lenguaje natural y conversacional
        - Limita tus respuestas a 2-3 párrafos máximo
        
        Historial de conversación:
        {history}
        """
    
    def _format_conversation_history(self):
        """Formatea el historial de conversación (últimos 6 mensajes) de manera eficiente."""
        if not self.conversation_history:
            return "No hay historial previo."
        
        # Uso de comprensión de listas y join para formatear eficientemente
        return '\n'.join([
            f"{msg['role']}: {msg['content']}" 
            for msg in self.conversation_history[-6:]
        ])
    
    def generate_response(self, user_message):
        """Genera y registra la respuesta del personaje."""
        self.conversation_history.append({"role": "Usuario", "content": user_message})
        
        try:
            full_prompt = (
                f"{self.get_system_prompt()}\n\n"
                f"Usuario: {user_message}\n\n"
                f"{self.name}:"
            )
            
            # Generar respuesta
            response = self.model.generate_content(full_prompt)
            
            if response.text:
                bot_response = response.text.strip()
                self.conversation_history.append({"role": self.name, "content": bot_response})
                return bot_response
            else:
                return "Lo siento, no pude generar una respuesta en este momento."
                
        except Exception as e:
            # Manejo de errores más directo
            return f"Error: {e}"
    
    # Métodos restantes simplificados o mantenidos por su concisión
    def clear_history(self):
        """Borra el historial de conversación."""
        self.conversation_history = []
    
    def update_character(self, name=None, personality=None, greeting=None, profile_image_path=None):
        """Actualiza los atributos del personaje con un solo dict-like acceso."""
        # Uso de ternarios y 'or' para asignaciones condicionales concisas
        self.name = name or self.name
        self.personality = personality or self.personality
        self.greeting = greeting or self.greeting
        self.profile_image_path = profile_image_path or self.profile_image_path