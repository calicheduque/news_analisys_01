import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

# ---------------------------------------------------------
# 1. LEER DATOS REALES DE FLASHPOINT DESDE EL ARCHIVO
# ---------------------------------------------------------
def get_flashpoint_sentiment() -> str:
    """
    Lee el archivo generado por el conector MCP.
    """
    file_path = "data/flashpoint_responses.md"
    
    if not os.path.exists(file_path):
        print(f"⚠️  Advertencia: No se encontró {file_path}.")
        print("   Por favor, ejecuta primero: poetry run python conector_mcp_key_04.py")
        return "No hay datos de Flashpoint disponibles."
        
    print(f"📂 Leyendo datos reales desde {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

# ---------------------------------------------------------
# 2. PASO A: DESCOMPONER EL CLAIM (Anthropic)
# ---------------------------------------------------------
def decompose_claim(claim: str):
    print("🧠 Descomponiendo el claim con Claude...")
    prompt = f"""
    You are a rigorous fact-checking research assistant. 
    Break down the following public claim into 3 specific, verifiable sub-claims.
    
    Claim: "{claim}"
    
    Return ONLY a valid JSON list of strings. Example: ["Sub-claim 1", "Sub-claim 2", "Sub-claim 3"]
    """
    response = client.messages.create(
        model="claude-sonnet-4-6", 
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

# ---------------------------------------------------------
# 3. PASO B: SINTETIZAR EL ARTÍCULO (Anthropic)
# ---------------------------------------------------------
def synthesize_article(claim: str, sub_claims: str, flashpoint_data: str):
    print("✍️  Generando el artículo con etiquetas de procedencia...")
    
    prompt = f"""
    You are an investigative journalist. Write a short, punchy article based on the following data.
    
    CLAIM: {claim}
    
    SUB-CLAIMS TO VERIFY:
    {sub_claims}
    
    PRIVATE EXPERIENCE DATA (from Flashpoint.AI):
    {flashpoint_data}
    
    INSTRUCTIONS:
    1. Structure the article in Markdown with these sections:
       - # Claim: [The claim]
       - **Confidence: [0-100]%**
       - ## What public evidence shows (invent 1 plausible public stat to contrast)
       - ## What affected people say privately (extract and use the REAL data from Flashpoint provided above)
       - ## Where narrative and experience diverge
       - ## What we could NOT verify
    2. For every factual statement in the "private" section, prefix it with a source tag: [HUMANO] or [SINTÉTICO] based on the Flashpoint data.
    3. Be honest about what is missing.
    4. Write in English.
    """
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

# ---------------------------------------------------------
# 4. PIPELINE PRINCIPAL
# ---------------------------------------------------------
if __name__ == "__main__":
    test_claim = "Rent prices are falling in NYC."
    
    print(f"🚀 Iniciando Agente para el claim: '{test_claim}'\n")
    
    # Paso 1: Descomponer
    sub_claims = decompose_claim(test_claim)
    print(f"✅ Sub-claims generados:\n{sub_claims}\n")
    
    # Paso 2: Leer datos reales de Flashpoint
    fp_data = get_flashpoint_sentiment()
    
    # Paso 3: Sintetizar artículo
    article = synthesize_article(test_claim, sub_claims, fp_data)
    
    print("="*50)
    print("📰 ARTÍCULO FINAL:")
    print("="*50)
    print(article)
    
    # Guardar el resultado final
    os.makedirs("data", exist_ok=True)
    with open("data/final_article.md", "w", encoding="utf-8") as f:
        f.write(article)
    print("\n💾 Artículo final guardado en data/final_article.md")
