from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional, Dict
from contextlib import asynccontextmanager
import asyncio
import aiohttp
import logging
from datetime import datetime
import uvicorn
import os
import tempfile
import platform
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importações do Docling
try:
    from docling.document_converter import DocumentConverter
    try:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        ADVANCED_FEATURES = True
    except ImportError:
        print("⚠️  Recursos avançados do Docling não disponíveis. Usando configuração básica.")
        ADVANCED_FEATURES = False
except ImportError as e:
    raise ImportError(f"Docling não está instalado. Execute: pip install docling\nErro: {e}")

# Models Pydantic
class URLRequest(BaseModel):
    url: HttpUrl
    options: Optional[Dict] = {}
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        url_str = str(v)
        if not (url_str.startswith('http://') or url_str.startswith('https://')):
            raise ValueError('URL deve começar com http:// ou https://')
        return v
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v):
        if v is None:
            return {}
        
        # Validar opções conhecidas
        valid_markdown_types = ['simple', 'complete']
        if 'markdown_type' in v and v['markdown_type'] not in valid_markdown_types:
            raise ValueError(f'markdown_type deve ser um de: {valid_markdown_types}')
            
        if 'timeout' in v and (not isinstance(v['timeout'], int) or v['timeout'] <= 0):
            raise ValueError('timeout deve ser um número inteiro positivo')
            
        return v

class ConversionResponse(BaseModel):
    success: bool
    markdown: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None
    processed_at: datetime

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    docling_available: bool

# Instância global do DocumentConverter
document_converter = None

def initialize_docling():
    """Inicializa o DocumentConverter do Docling"""
    global document_converter
    try:
        if ADVANCED_FEATURES:
            try:
                pipeline_options = PdfPipelineOptions()
                pipeline_options.do_ocr = True
                pipeline_options.do_table_structure = True
                
                document_converter = DocumentConverter(
                    format_options={
                        InputFormat.PDF: pipeline_options,
                    }
                )
            except Exception as e:
                logger.warning(f"Erro na configuração avançada: {e}. Usando configuração básica.")
                document_converter = DocumentConverter()
        else:
            document_converter = DocumentConverter()
            
        logger.info("DocumentConverter inicializado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar DocumentConverter: {str(e)}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Iniciando aplicação...")
    success = initialize_docling()
    if not success:
        logger.warning("Falha na inicialização do Docling")
    yield
    # Shutdown
    logger.info("Encerrando aplicação...")

# Inicialização da aplicação FastAPI
app = FastAPI(
    title="Docling URL to Markdown API",
    description="API para conversão de URLs de sites em markdown usando Docling",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def download_content(url: str, timeout: int = 30) -> tuple[bytes, dict]:
    """
    Baixa o conteúdo de uma URL e retorna também headers/metadados
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, 
                timeout=aiohttp.ClientTimeout(total=timeout),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            ) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    # Extrair metadados da resposta HTTP
                    response_metadata = {
                        'content_type': response.headers.get('content-type', ''),
                        'content_length': response.headers.get('content-length', ''),
                        'last_modified': response.headers.get('last-modified', ''),
                        'server': response.headers.get('server', ''),
                        'status_code': response.status
                    }
                    
                    return content, response_metadata
                else:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Erro ao acessar URL: Status {response.status}"
                    )
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=400, detail=f"Erro de conexão: {str(e)}")
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Timeout ao acessar a URL")

def process_markdown_content(markdown_content: str, markdown_type: str, url: str, response_metadata: dict) -> str:
    """
    Processa o markdown baseado no tipo solicitado (simple ou complete)
    """
    if markdown_type == "simple":
        return create_simple_markdown(markdown_content)
    else:  # complete (padrão)
        return create_complete_markdown(markdown_content, url, response_metadata)

def create_simple_markdown(markdown_content: str) -> str:
    """
    Cria versão simplificada do markdown - apenas conteúdo essencial
    """
    import re
    
    lines = markdown_content.split('\n')
    simple_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Manter apenas elementos básicos
        if (stripped.startswith('#') or  # Headers
            stripped.startswith('-') or  # Listas simples
            stripped.startswith('*') or  # Listas alternativas
            stripped.startswith('1.') or  # Listas numeradas
            (stripped and not stripped.startswith('|') and  # Não tabelas
             not stripped.startswith('![') and  # Não imagens
             not stripped.startswith('```') and  # Não blocos de código
             not stripped.startswith('>'))):  # Não citações
            simple_lines.append(line)
        elif stripped and not any(char in stripped for char in ['|', '![', '```', '>']):
            # Texto normal (parágrafos e links simples)
            simple_lines.append(line)
    
    # Limpar múltiplas linhas vazias
    result = '\n'.join(simple_lines)
    result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)
    
    return result.strip()

def create_complete_markdown(markdown_content: str, url: str, response_metadata: dict) -> str:
    """
    Cria versão completa do markdown com metadados e formatação preservada
    """
    complete_markdown = []
    
    # Cabeçalho com metadados
    complete_markdown.append("---")
    complete_markdown.append("# Documento Convertido")
    complete_markdown.append("")
    complete_markdown.append("**📄 Metadados do Documento:**")
    complete_markdown.append(f"- **URL Original:** {url}")
    complete_markdown.append(f"- **Data de Conversão:** {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
    
    if response_metadata.get('content_type'):
        complete_markdown.append(f"- **Tipo de Conteúdo:** {response_metadata['content_type']}")
    
    if response_metadata.get('last_modified'):
        complete_markdown.append(f"- **Última Modificação:** {response_metadata['last_modified']}")
    
    if response_metadata.get('server'):
        complete_markdown.append(f"- **Servidor:** {response_metadata['server']}")
    
    complete_markdown.append(f"- **Status HTTP:** {response_metadata.get('status_code', 'N/A')}")
    complete_markdown.append("")
    complete_markdown.append("---")
    complete_markdown.append("")
    
    # Conteúdo principal com formatação preservada
    complete_markdown.append("## 📋 Conteúdo Extraído")
    complete_markdown.append("")
    complete_markdown.append(markdown_content)
    complete_markdown.append("")
    
    # Rodapé
    complete_markdown.append("---")
    complete_markdown.append("")
    complete_markdown.append("*Documento processado pela API Docling*")
    complete_markdown.append(f"*Gerado em: {datetime.now().isoformat()}*")
    
    return '\n'.join(complete_markdown)

def convert_to_markdown(content: bytes, url: str, options: dict, response_metadata: dict) -> tuple[str, dict]:
    """
    Converte conteúdo baixado em markdown usando Docling
    """
    global document_converter
    
    if document_converter is None:
        raise HTTPException(status_code=500, detail="DocumentConverter não inicializado")
    
    try:
        # Cria diretório temporário compatível com Windows e Linux
        if platform.system() == "Windows":
            temp_base = Path(os.environ.get('TEMP', tempfile.gettempdir()))
        else:
            temp_base = Path(tempfile.gettempdir())
            
        temp_dir = temp_base / "docling_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Determina extensão baseada na URL
        file_extension = ".html"
        if url.endswith('.pdf'):
            file_extension = ".pdf"
        elif url.endswith('.docx'):
            file_extension = ".docx"
        elif url.endswith('.txt'):
            file_extension = ".txt"
        
        # Cria nome único para o arquivo
        timestamp = str(datetime.now().timestamp()).replace('.', '_')
        temp_file = temp_dir / f"temp_content_{timestamp}{file_extension}"
        
        logger.info(f"Salvando arquivo temporário em: {temp_file}")
        
        # Escreve conteúdo no arquivo temporário
        with open(temp_file, 'wb') as f:
            f.write(content)
        
        # Converte usando Docling
        logger.info(f"Convertendo arquivo: {temp_file}")
        result = document_converter.convert(str(temp_file))
        
        # Extrai markdown básico do Docling
        raw_markdown = result.document.export_to_markdown()
        
        # Processa o markdown baseado nas opções
        markdown_type = options.get('markdown_type', 'complete')  # Padrão: complete
        processed_markdown = process_markdown_content(raw_markdown, markdown_type, url, response_metadata)
        
        # Metadados expandidos
        metadata = {
            "source_url": url,
            "file_type": file_extension,
            "content_length": len(content),
            "markdown_type": markdown_type,
            "temp_file": str(temp_file),
            "conversion_time": datetime.now().isoformat(),
            "raw_markdown_length": len(raw_markdown),
            "processed_markdown_length": len(processed_markdown),
            "response_metadata": response_metadata
        }
        
        # Adiciona informações específicas do documento se disponíveis
        if hasattr(result.document, 'page_count'):
            metadata["pages"] = result.document.page_count
        else:
            metadata["pages"] = 1
            
        # Limpa arquivo temporário
        try:
            temp_file.unlink(missing_ok=True)
            logger.info("Arquivo temporário removido")
        except Exception as cleanup_error:
            logger.warning(f"Não foi possível remover arquivo temporário: {cleanup_error}")
        
        return processed_markdown, metadata
        
    except Exception as e:
        logger.error(f"Erro na conversão para markdown: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na conversão: {str(e)}")

@app.get("/", response_model=HealthResponse)
async def root():
    """Endpoint raiz - verificação de saúde da API"""
    return HealthResponse(
        status="running",
        timestamp=datetime.now(),
        docling_available=document_converter is not None
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Endpoint de verificação de saúde"""
    return HealthResponse(
        status="healthy" if document_converter is not None else "degraded",
        timestamp=datetime.now(),
        docling_available=document_converter is not None
    )

@app.post("/convert", response_model=ConversionResponse)
async def convert_url_to_markdown(request: URLRequest):
    """
    Converte uma URL em markdown
    
    - **url**: URL do site a ser convertido
    - **options**: Opções adicionais:
        - **markdown_type**: "simple" ou "complete" (padrão: "complete")
        - **timeout**: Timeout em segundos (padrão: 30)
    """
    try:
        url_str = str(request.url)
        options = request.options or {}
        
        # Extrair timeout das opções
        timeout = options.get('timeout', 30)
        markdown_type = options.get('markdown_type', 'complete')
        
        logger.info(f"Processando URL: {url_str} (tipo: {markdown_type})")
        
        # Baixa o conteúdo
        content, response_metadata = await download_content(url_str, timeout)
        
        # Converte para markdown
        markdown_content, metadata = convert_to_markdown(content, url_str, options, response_metadata)
        
        return ConversionResponse(
            success=True,
            markdown=markdown_content,
            metadata=metadata,
            processed_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        return ConversionResponse(
            success=False,
            error=f"Erro interno: {str(e)}",
            processed_at=datetime.now()
        )

@app.get("/convert")
async def convert_url_get(url: str):
    """Endpoint GET para conversão (para facilitar testes)"""
    try:
        request = URLRequest(url=url)
        return await convert_url_to_markdown(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    # Configuração para execução direta
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )