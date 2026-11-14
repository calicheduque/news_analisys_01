import asyncio
import json
import os
from urllib.parse import parse_qs, urlparse
import httpx2
from pydantic import AnyUrl
from mcp import Client
from mcp.client.auth import AuthorizationCodeResult, OAuthClientProvider
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken

class InMemoryTokenStorage:
    def __init__(self) -> None:
        self.tokens: OAuthToken | None = None
        self.client_info: OAuthClientInformationFull | None = None
    async def get_tokens(self) -> OAuthToken | None: return self.tokens
    async def set_tokens(self, tokens: OAuthToken) -> None: self.tokens = tokens
    async def get_client_info(self) -> OAuthClientInformationFull | None: return self.client_info
    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None: self.client_info = client_info

async def open_browser(authorization_url: str) -> None:
    print(f"\n🌐 Abre esta URL en tu navegador:\n{authorization_url}\n")

async def wait_for_callback() -> AuthorizationCodeResult:
    redirect_url = input("Pega la URL completa a la que fuiste redirigido: ")
    params = parse_qs(urlparse(redirect_url).query)
    return AuthorizationCodeResult(
        code=params["code"][0],
        state=params["state"][0],
        iss=params["iss"][0] if "iss" in params else None,
    )

async def main():
    # Crear la carpeta 'data' si no existe
    os.makedirs("data", exist_ok=True)

    oauth_auth = OAuthClientProvider(
        server_url="https://api.flashpoint.ai/mcp",
        client_metadata=OAuthClientMetadata(
            client_name="Hackathon News Analysis Agent",
            redirect_uris=[AnyUrl("http://localhost:3030/callback")],
            scope="user",
        ),
        storage=InMemoryTokenStorage(),
        redirect_handler=open_browser,
        callback_handler=wait_for_callback,
    )

    async with httpx2.AsyncClient(
        auth=oauth_auth, 
        follow_redirects=True,
        timeout=httpx2.Timeout(30.0, read=300.0)
    ) as http_client:
        transport = streamable_http_client(
            "https://api.flashpoint.ai/mcp", 
            http_client=http_client
        )
        
        async with Client(transport) as client:
            print("✅ Conectado al servidor MCP de Flashpoint.")
            
            # --- PASO 1: CREAR LA ENCUESTA ---
            print("\n⏳ Creando la encuesta y lanzando panel sintético (esto toma ~40 seg)...")
            result = await client.call_tool(
                "tool_survey",
                {
                    "brief": "Create a 5-question survey about rent prices in NYC for renters in Harlem. Field it with 20 synthetic respondents."
                }
            )
            
            # Guardar la metadata de la encuesta
            raw_text = result.content[0].text
            data = json.loads(raw_text)
            survey_id = data["result"]["survey_id"]
            
            with open("data/survey_meta.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            print(f"✅ Encuesta creada con ID: {survey_id}")
            print("⏳ Solicitando los resultados de la encuesta al orquestador...")
            
            # --- PASO 2: PEDIR LOS DATOS ---
            chat_result = await client.call_tool(
                "chat",
                {
                    "message": f"Can you show me the detailed responses and analysis for survey_id: {survey_id}? Please summarize what the Harlem renters said in a structured format."
                }
            )
            
            # Extraer el texto de la respuesta
            response_text = ""
            for content in chat_result.content:
                if hasattr(content, 'text'):
                    response_text += content.text + "\n"
            
            # Guardar el resultado en formato Markdown (para la Persona B y C)
            with open("data/flashpoint_responses.md", "w", encoding="utf-8") as f:
                f.write(response_text)
                
            # Guardar el resultado crudo en formato JSON (para el orquestador)
            with open("data/flashpoint_responses.json", "w", encoding="utf-8") as f:
                # Asumiendo que chat_result tiene un formato estructurado, 
                # si no, guardamos el texto en un JSON simple.
                json.dump({"raw_text": response_text}, f, indent=2, ensure_ascii=False)
            
            print("\n✅ RESULTADOS GUARDADOS EXITOSAMENTE EN LA CARPETA 'data/'")
            print("  - data/survey_meta.json")
            print("  - data/flashpoint_responses.md")
            print("  - data/flashpoint_responses.json")

if __name__ == "__main__":
    asyncio.run(main())
