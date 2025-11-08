import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class CharacterAI:
    def __init__(self, name, personality, greeting, profile_image_path=None, model_name="gemini-2.0-flash"):
        self.name = name
        self.personality = personality
        self.greeting = greeting
        self.profile_image_path = profile_image_path  # ✅ Nombre corregido
        self.conversation_history = []
        self.model_name = model_name
        # Configurar la API
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        
        # Detectar modelo automáticamente si no se especifica
        if model_name is None:
            self.model_name = self._get_available_model()
        else:
            self.model_name = model_name
            
        self.model = genai.GenerativeModel(self.model_name)
        
    def _get_available_model(self):
        """Detectar automáticamente modelos disponibles"""
        try:
            models = genai.list_models()
            
            # Priorizar estos modelos (orden de preferencia)
            preferred_models = [
                "models/gemini-1.5-flash",
                "models/gemini-1.5-pro",
                "models/gemini-pro",
                "models/gemini-1.0-pro",
            ]
            
            available_models = []
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    available_models.append(model.name)
            
            # Buscar modelos preferidos disponibles
            for preferred in preferred_models:
                if preferred in available_models:
                    print(f"Usando modelo: {preferred}")
                    return preferred
            
            # Si no encuentra los preferidos, usar el primero disponible
            if available_models:
                print(f"Usando modelo disponible: {available_models[0]}")
                return available_models[0]
            else:
                raise Exception("No hay modelos disponibles con generateContent")
                
        except Exception as e:
            print(f"Error detectando modelos: {e}")
            # Modelo por defecto como fallback
            return "models/gemini-1.5-flash"
        
    def get_system_prompt(self):
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
        {self._format_conversation_history()}
        """
    
    def _format_conversation_history(self):
        if not self.conversation_history:
            return "No hay historial previo."
        
        formatted = ""
        for msg in self.conversation_history[-6:]:  # Últimos 6 mensajes
            formatted += f"{msg['role']}: {msg['content']}\n"
        return formatted
    
    def generate_response(self, user_message):
        # Añadir mensaje del usuario al historial
        self.conversation_history.append({"role": "Usuario", "content": user_message})
        
        try:
            # Crear prompt completo
            full_prompt = f"{self.get_system_prompt()}\n\nUsuario: {user_message}\n\n{self.name}:"
            
            # Generar respuesta
            response = self.model.generate_content(full_prompt)
            
            if response.text:
                bot_response = response.text.strip()
                # Añadir respuesta al historial
                self.conversation_history.append({"role": self.name, "content": bot_response})
                return bot_response
            else:
                return "Lo siento, no pude generar una respuesta en este momento."
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def clear_history(self):
        self.conversation_history = []
    
    def update_character(self, name=None, personality=None, greeting=None, profile_image_path=None):
        if name:
            self.name = name
        if personality:
            self.personality = personality
        if greeting:
            self.greeting = greeting
        if profile_image_path:
            self.profile_image_path = profile_image_path