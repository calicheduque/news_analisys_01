import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

def probar_conexion():
    print("Conectando con Anthropic usando Poetry...")
    try:
        message = client.messages.create(
            model="claude-sonnet-5-5", 
            max_tokens=50,
            #temperature=0,
            messages=[
                {"role": "user", "content": "Responde solo con las palabras: 'API funcionando correctamente'."}
            ]
        )
        print("\n✅ ¡Éxito!")
        print("Respuesta de Claude:", message.content[0].text)
        
    except anthropic.AuthenticationError:
        print("\n❌ Error de Autenticación: La API key es inválida o fue revocada.")
    except anthropic.RateLimitError:
        print("\n❌ Error de Límite: Has excedido el límite o no tienes créditos.")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

if __name__ == "__main__":
    probar_conexion()
