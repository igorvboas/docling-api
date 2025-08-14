import requests
import json
from typing import Optional

class DoclingAPIClient:
    """Cliente para a API Docling URL to Markdown"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        
    def health_check(self) -> dict:
        """Verifica se a API está funcionando"""
        try:
            response = requests.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "unreachable"}
    
    def convert_url(self, url: str, options: Optional[dict] = None) -> dict:
        """
        Converte uma URL em markdown
        
        Args:
            url (str): URL do site a ser convertido
            options (dict, optional): Opções adicionais
            
        Returns:
            dict: Resposta da API com o markdown ou erro
        """
        try:
            payload = {
                "url": url,
                "options": options or {}
            }
            
            response = requests.post(
                f"{self.base_url}/convert",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60  # 1 minuto timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Erro na requisição: {str(e)}",
                "processed_at": None
            }
    
    def convert_url_simple(self, url: str) -> dict:
        """
        Conversão simples via GET (para testes rápidos)
        """
        try:
            response = requests.get(
                f"{self.base_url}/convert",
                params={"url": url},
                timeout=60
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Erro na requisição: {str(e)}",
                "processed_at": None
            }

def test_different_markdown_types():
    """Testa diferentes tipos de markdown"""
    
    client = DoclingAPIClient()
    test_url = "https://noticias.r7.com/santa-catarina/nd-mais/renato-cariani-e-julio-balestrin-participam-de-evento-fitness-em-sc-14082025/"
    
    print("🧪 Testando diferentes tipos de markdown...")
    print(f"📋 URL: {test_url}")
    print("-" * 80)
    
    # Teste 1: Markdown Completo (padrão)
    print("\n1️⃣ Testando Markdown COMPLETO...")
    result_complete = client.convert_url(test_url, options={"markdown_type": "complete"})
    
    if result_complete.get("success"):
        markdown = result_complete.get("markdown", "")
        print(f"✅ Markdown completo gerado: {len(markdown)} caracteres")
        
        # Salvar arquivo completo
        with open("resultado_completo.md", 'w', encoding='utf-8') as f:
            f.write(markdown)
        print("💾 Salvo em: resultado_completo.md")
        
        # Mostrar preview
        print("\n📝 Preview (primeiros 300 caracteres):")
        print("-" * 50)
        print(markdown[:300] + "...")
        print("-" * 50)
    else:
        print(f"❌ Erro no completo: {result_complete.get('error')}")
    
    # Teste 2: Markdown Simples
    print("\n2️⃣ Testando Markdown SIMPLES...")
    result_simple = client.convert_url(test_url, options={"markdown_type": "simple"})
    
    if result_simple.get("success"):
        markdown = result_simple.get("markdown", "")
        print(f"✅ Markdown simples gerado: {len(markdown)} caracteres")
        
        # Salvar arquivo simples
        with open("resultado_simples.md", 'w', encoding='utf-8') as f:
            f.write(markdown)
        print("💾 Salvo em: resultado_simples.md")
        
        # Mostrar preview
        print("\n📝 Preview (primeiros 300 caracteres):")
        print("-" * 50)
        print(markdown[:300] + "...")
        print("-" * 50)
    else:
        print(f"❌ Erro no simples: {result_simple.get('error')}")
    
    # Comparação
    if result_complete.get("success") and result_simple.get("success"):
        complete_size = len(result_complete.get("markdown", ""))
        simple_size = len(result_simple.get("markdown", ""))
        reduction = ((complete_size - simple_size) / complete_size) * 100
        
        print(f"\n📊 Comparação:")
        print(f"   • Completo: {complete_size:,} caracteres")
        print(f"   • Simples:  {simple_size:,} caracteres")
        print(f"   • Redução:  {reduction:.1f}%")

def test_custom_options():
    """Testa opções customizadas"""
    client = DoclingAPIClient()
    
    print("\n🔧 Testando opções customizadas...")
    
    # Teste com timeout customizado
    options = {
        "markdown_type": "complete",
        "timeout": 60
    }
    
    result = client.convert_url("https://example.com", options=options)
    
    if result.get("success"):
        metadata = result.get("metadata", {})
        print(f"✅ Conversão com opções customizadas bem-sucedida!")
        print(f"📊 Tipo de markdown: {metadata.get('markdown_type')}")
        print(f"⏱️  Timeout usado: {options['timeout']}s")
    else:
        print(f"❌ Erro: {result.get('error')}")

def main():
    """Exemplo de uso do cliente"""
    
    # Inicializar cliente
    client = DoclingAPIClient()
    
    # Verificar saúde da API
    print("🔍 Verificando saúde da API...")
    health = client.health_check()
    print(f"Status: {health}")
    
    if health.get("status") != "healthy":
        print("❌ API não está saudável. Verifique se está rodando.")
        return
    
    # Teste básico
    print(f"\n🔄 Teste básico com markdown completo...")
    result = client.convert_url("https://example.com")
    
    if result.get("success"):
        print("✅ Conversão básica bem-sucedida!")
        metadata = result.get("metadata", {})
        print(f"📊 Tipo: {metadata.get('markdown_type', 'N/A')}")
        print(f"📏 Tamanho: {metadata.get('processed_markdown_length', 'N/A')} caracteres")
    else:
        print(f"❌ Erro no teste básico: {result.get('error')}")
        return
    
    # Testes avançados
    test_different_markdown_types()
    test_custom_options()

if __name__ == "__main__":
    main()