# Docling URL to Markdown API

API desenvolvida em Python usando FastAPI e Docling para conversão de URLs de sites em markdown.

## 🚀 Características

- **Conversão de URLs**: Converte qualquer site público em markdown
- **Suporte a múltiplos formatos**: HTML, PDF, DOC, TXT via URLs
- **API REST**: Interface simples e documentada
- **Processamento assíncrono**: Operações não-bloqueantes
- **Metadados detalhados**: Informações sobre o conteúdo processado
- **Validação robusta**: Validação de URLs e tratamento de erros
- **Docker ready**: Containerização inclusa

## 📋 Pré-requisitos

- Python 3.11+
- pip
- Docker (opcional)

## 🛠 Instalação

### Instalação local

1. Clone ou crie os arquivos do projeto
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

### Instalação com Docker

```bash
# Construir imagem
docker build -t docling-api .

# Executar container
docker run -p 8000:8000 docling-api
```

## 🚦 Execução

### Execução local

```bash
# Método 1: Usando uvicorn diretamente
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Método 2: Executando o arquivo main.py
python main.py
```

### Execução com Docker

```bash
docker run -p 8000:8000 docling-api
```

A API estará disponível em: `http://localhost:8000`

## 📖 Documentação da API

### Endpoints principais

#### GET `/`
Verificação básica da API

**Resposta:**
```json
{
  "status": "running",
  "timestamp": "2025-01-15T10:30:00",
  "docling_available": true
}
```

#### GET `/health`
Verificação detalhada de saúde

#### POST `/convert`
Converte uma URL em markdown

**Request Body:**
```json
{
  "url": "https://example.com",
  "options": {}
}
```

**Response (Sucesso):**
```json
{
  "success": true,
  "markdown": "# Example Domain\n\nThis domain is for use in examples...",
  "metadata": {
    "source_url": "https://example.com",
    "file_type": ".html",
    "content_length": 1256,
    "pages": 1,
    "conversion_time": "2025-01-15T10:30:00"
  },
  "processed_at": "2025-01-15T10:30:00"
}
```

**Response (Erro):**
```json
{
  "success": false,
  "error": "Erro de conexão: Connection timeout",
  "processed_at": "2025-01-15T10:30:00"
}
```

#### GET `/convert?url=<URL>`
Conversão via GET (para testes rápidos)

### Documentação interativa

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 💻 Exemplos de uso

### cURL

```bash
# Verificar saúde
curl http://localhost:8000/health

# Converter URL (POST)
curl -X POST "http://localhost:8000/convert" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Converter URL (GET)
curl "http://localhost:8000/convert?url=https://example.com"
```

### Python

```python
import requests

# Converter URL
response = requests.post(
    "http://localhost:8000/convert",
    json={"url": "https://example.com"}
)

result = response.json()
if result["success"]:
    print(result["markdown"])
else:
    print("Erro:", result["error"])
```

### JavaScript

```javascript
// Converter URL
fetch('http://localhost:8000/convert', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    url: 'https://example.com'
  })
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log(data.markdown);
  } else {
    console.error('Erro:', data.error);
  }
});
```

## 🧪 Testando

Execute o cliente de exemplo:

```bash
python client_example.py
```

Este script irá:
1. Verificar a saúde da API
2. Testar conversão de URLs de exemplo
3. Salvar os resultados em arquivos markdown

## ⚙️ Configurações

### Variáveis de ambiente

- `PYTHONPATH`: Caminho Python (padrão: `/app`)
- `PYTHONUNBUFFERED`: Output sem buffer (padrão: `1`)

### Timeouts

- Download de conteúdo: 30 segundos
- Timeout de requisição: 60 segundos

### Limitações

- URLs devem ser públicamente acessíveis
- Tamanho máximo de conteúdo limitado pela memória disponível
- Alguns sites podem bloquear requests automatizados

## 🛡️ Tratamento de erros

A API trata os seguintes tipos de erro:

- **400**: URL inválida ou inacessível
- **408**: Timeout na requisição
- **500**: Erro interno do servidor ou conversão

### Códigos de erro comuns

- `Connection timeout`: Timeout ao acessar URL
- `Status XXX`: Código de status HTTP não-sucesso
- `DocumentConverter não inicializado`: Problema na inicialização do Docling
- `Erro na conversão`: Falha no processamento do conteúdo

## 🔧 Desenvolvimento

### Estrutura do projeto

```
.
├── main.py              # Aplicação principal
├── requirements.txt     # Dependências
├── Dockerfile          # Container Docker
├── client_example.py   # Cliente de exemplo
└── README.md           # Esta documentação
```

### Adicionando funcionalidades

1. **Novos formatos**: Modifique a função `convert_to_markdown()`
2. **Opções customizadas**: Expanda o modelo `URLRequest`
3. **Cache**: Adicione Redis ou cache em memória
4. **Rate limiting**: Implemente limitação de requests

## 🐛 Resolução de problemas

### Erro na instalação do Docling

```bash
# Certifique-se de ter as dependências do sistema
sudo apt-get install gcc g++ libffi-dev libssl-dev

# Reinstale o Docling
pip install --force-reinstall docling
```

### API não responde

1. Verifique se todas as dependências estão instaladas
2. Confirme que a porta 8000 está disponível
3. Verifique os logs para erros de inicialização

### Conversão falha

1. Teste com URLs simples (ex: `https://example.com`)
2. Verifique se o site está acessível
3. Confirme se o site não bloqueia user-agents automatizados

## 📄 Licença

Este projeto é fornecido como exemplo e pode ser modificado conforme necessário.

## 🤝 Contribuição

Para contribuir:
1. Faça um fork do projeto
2. Crie uma branch para sua feature
3. Faça commit das suas mudanças
4. Abra um Pull Request

---

**Desenvolvido com FastAPI + Docling** 🚀