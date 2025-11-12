import os
import json
import time
import threading
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS


# Carrega variáveis de ambiente
load_dotenv()

# Inicializa a aplicação Flask
app = Flask(__name__)

# Configura o CORS pro frontend acessar a API
CORS(app) 


# --- Configuração da API de IA (Google Gemini) ---

"""
Configura o cliente da API Gemini.
É crucial que a variável de ambiente 'GOOGLE_API_KEY' esteja definida
corretamente no seu ambiente de produção (Render).
"""
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi encontrada.")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

except Exception as e:
    print(f"Erro fatal ao configurar a API Gemini: {e}")
    exit()


# --- Definição dos Prompts da IA ---

"""
Este prompt instrui a IA sobre o seu contexto (empresa financeira),
as categorias (Produtivo, Improdutivo), exemplos e o formato de saída.
"""
PROMPT_DE_CLASSIFICACAO = """
Você é um assistente automatizado de triagem de e-mails para uma GRANDE EMPRESA DO SETOR FINANCEIRO. Seu trabalho: **classificar cada e-mail** em uma das duas categorias definidas e **sugerir uma resposta** apropriada, clara e útil. Seja rigoroso: considere apenas como "Produtivo" o que for **relevante ao contexto financeiro** da empresa (conta, pagamento, fatura, cartão, fraude, extrato, empréstimo, limite, investimento, compliance, documentação, contrato, transferência, chargeback, reembolso, boleto, autorização, etc.). Tudo que for felicitação, agradecimento, spam, newsletters, assuntos pessoais ou pedidos relevantes apenas em outros setores (restaurante, evento social, compras pessoais) deve ser "Improdutivo".

REGRAS DE CLASSIFICAÇÃO (decisão explícita):
1. Marque **"Produtivo"** quando o e-mail:
   - Contiver um pedido de ação relacionado a produtos/serviços financeiros (ex.: "não consigo acessar minha conta", "status do processo 123", "estou com débito não reconhecido", "enviei documento em anexo para análise de crédito").
   - Solicitar suporte, contestação, reembolso, cancelamento, abertura/fechamento de serviços, documentos para compliance, confirmação de transação, ou reportar possível fraude.
   - Incluir anexos relevantes solicitando processamento ou revisão (contratos, comprovantes, documentos KYC).
   - Tiver menção explícita a contas, pagamentos, faturas, transferências, cartões, investimentos, empréstimos, compliance, ou números de protocolo.

2. Marque **"Improdutivo"** quando o e-mail:
   - For agradecimento, felicitação, convite social, spam, newsletter, ou conteúdo pessoal/irrelevante ao negócio financeiro (ex.: "obrigado", "feliz natal", "quero um pastel e um suco", "olá, tudo bem?").
   - Contiver assuntos que só seriam produtivos em outros setores (restaurante, logística de eventos, vendas de comida, etc.) sem relação com serviços financeiros.
   - For ambíguo e **não** contiver palavras-chave financeiras nem solicitação de ação (nestes casos, trate como "Improdutivo").

FORMATO DE SAÍDA OBRIGATÓRIO:
- **Retorne APENAS** um objeto JSON válido.
- O JSON deve ter exatamente duas chaves: `"categoria"` e `"resposta"`.
- `"categoria"` deve ser a string exata `"Produtivo"` ou `"Improdutivo"`.
- `"resposta"` **NUNCA** pode ficar vazia. Deve conter uma resposta curta (1–3 frases) em português brasileiro, tom formal e profissional, adaptada ao e-mail.
- Não adicione texto fora do JSON.

REGRAS PARA A RESPOSTA SUGERIDA:
- Para **Produtivo**: gere uma resposta que contenha:
  1. Reconhecimento claro do recebimento.
  2. Breve resumo do que será feito (sem dar prazos numéricos nem pedir que o remetente “aguarde” — ex.: "Nossa equipe recebeu sua solicitação e irá analisar."). **Evite** estimativas de tempo ou frases tipo "em breve" ou "aguarde".
  3. Se necessário, solicite **informação específica** faltante (ex.: número do contrato, comprovante, anexo). Use placeholders quando aplicável: `{número_protocolo}`, `{documento}`.
  4. Indique qual será o próximo passo prático (ex.: "encaminharemos ao time de análise de fraude" ou "abriremos um chamado interno para verificação").
- Para **Improdutivo**: resposta curta e educada (ex.: "Obrigado pela sua mensagem."). Pode oferecer um canal útil apenas se realmente aplicável (ex.: "Para assuntos sobre faturas, utilize suporte@empresa.com"), caso contrário mantenha apenas agradecimento.

VARIABILIDADE:
- Use linguagem variada — não retorne sempre a mesma frase-padrão. Adapte a mensagem ao conteúdo do e-mail (ex.: se o cliente enviou anexo, mencionar "recebemos o anexo"; se perguntou sobre status inclua referência a "seu pedido/protocolo" se existir).
- Se o e-mail menciona um número de caso/protocolo, inclua-o na resposta.

EXEMPLOS (apenas para orientar o comportamento — não devem aparecer no output):
- E-mail: "Não consigo acessar minha conta — erro 403" → Categoria: "Produtivo"; Resposta: "Recebemos seu relato sobre dificuldade de acesso. Encaminharemos ao time de suporte técnico para investigação. Por favor confirme seu CPF ou número de cliente para agilizar a análise."
- E-mail: "Feliz Natal!" → Categoria: "Improdutivo"; Resposta: "Obrigado pela sua mensagem! Desejamos boas festas."

INSTRUÇÃO FINAL:
Analise o e-mail entre as linhas:
---
{EMAIL_AQUI}
---
E gere **somente** o JSON com "categoria" e "resposta" seguindo todas as regras acima.
"""

"""
Este prompt instrui a IA para atuar como um assistente de escrita,
focando apenas em modificar o texto conforme a ação solicitada.
"""
PROMPT_DE_REVISAO = """
Você é um assistente de escrita profissional.
Execute a ação solicitada no texto fornecido e retorne APENAS o texto modificado, sem explicações, saudações ou formatação extra.

Ação: {ACAO}
Texto Original:
---
{TEXTO}
---

Texto Modificado:
"""


# --- Endpoints da API ---

@app.route('/api/classificar', methods=['POST'])
def classificarEmail():
    """
    Endpoint da API para classificar o texto de um email.
    
    Espera um JSON de entrada: {"email_texto": "..."}
    
    Retorna um JSON de saída: {"categoria": "...", "resposta": "..."}
    ou um JSON de erro: {"error": "..."}
    """
    
    dados = request.json
    if not dados:
        return jsonify({'error': 'Requisição deve conter JSON'}), 400

    texto_do_email = dados.get('email_texto')
    if not texto_do_email:
        return jsonify({'error': 'A chave "email_texto" é obrigatória.'}), 400

    print(f"Recebido para classificar: {texto_do_email[:50]}...")

    try:
        promptFinal = PROMPT_DE_CLASSIFICACAO.replace("{EMAIL_AQUI}", texto_do_email)
        response = model.generate_content(promptFinal)

        textoIA = response.text
        print(f"IA (Classificar) retornou: {textoIA}")
        
        # Limpa a resposta da IA, removendo backticks e espaços
        textoJson = textoIA.strip().replace("```json", "").replace("```", "").strip()

        # Valida se a resposta limpa é um JSON
        if not textoJson.startswith('{'):
            # Se não for um JSON, lança um erro com a resposta limpa
            raise Exception(f"A IA não retornou um JSON válido. Resposta limpa: {textoJson}")
            
        # Processa o JSON
        resultadoJson = json.loads(textoJson)

        categoria = resultadoJson.get("categoria")
        resposta = resultadoJson.get("resposta")

        if not categoria or not resposta:
             raise Exception("O JSON da IA não contém as chaves 'categoria' ou 'resposta'.")

        return jsonify({
            "categoria": categoria,
            "resposta": resposta
        })

    except Exception as e:
        print(f"Erro ao processar o email: {e}")
        return jsonify({
            'categoria': 'Erro',
            'resposta': f'Erro no servidor ao processar: {str(e)}'
        }), 500


@app.route('/api/revisar', methods=['POST'])
def revisarTexto():
    """
    Endpoint da API para revisar um texto com base numa ação.
    
    Espera um JSON de entrada: {"texto": "...", "acao": "..."}
    
    Retorna um JSON de saída: {"texto_revisado": "..."}
    ou um JSON de erro: {"error": "..."}
    """
    
    # Validação da entrada
    dados = request.json
    if not dados:
        return jsonify({'error': 'Requisição deve conter JSON'}), 400
    
    texto_original = dados.get('texto')
    acao = dados.get('acao')

    if not texto_original or not acao:
        return jsonify({'error': 'As chaves "texto" e "acao" são obrigatórias.'}), 400
    
    print(f"Recebido para revisar (Ação: {acao}): {texto_original[:50]}...")

    try:
        # Prepara e envia o prompt para o modelo Gemini
        promptFinal = PROMPT_DE_REVISAO.replace("{ACAO}", acao).replace("{TEXTO}", texto_original)
        response = model.generate_content(promptFinal)

        texto_revisado = response.text.strip()
        print(f"IA (Revisar) retornou: {texto_revisado[:50]}...")

        return jsonify({"texto_revisado": texto_revisado})

    except Exception as e:
        print(f"Erro ao revisar o texto: {e}")
        return jsonify({'error': f'Erro interno no servidor ao revisar: {str(e)}'}), 500


# --- Bot "Keep-Alive" para o Render ---

@app.route('/api/ping')
def ping():
    """
    Endpoint usado pelo bot keep-alive para manter o servidor
    do Render acordado. Apenas retorna um status 200.
    """
    return jsonify({"status": "alive"}), 200

def keep_alive_bot():
    """
    Função que corre numa thread separada.
    A cada 14 minutos, ela "visita" a própria URL do servidor
    para impedir que o serviço do Render durma.
    """
    # Espera 30s antes de começar, para o servidor arrancar
    time.sleep(30)
    print("Iniciando thread Keep-Alive.")
    
    while True:
        try:
            self_url = os.environ.get("RENDER_EXTERNAL_URL") 
            
            if self_url:
                # Faz a requisição para o endpoint /api/ping
                requests.get(f"{self_url}/api/ping")
                print(f"Keep-Alive: Ping enviado para {self_url}/api/ping")
            
            # Dorme por 14 minutos (15 min é o tempo limite do Render)
            time.sleep(840)
        
        except Exception as e:
            print(f"Erro na thread Keep-Alive: {e}")
            # Se der erro (ex: falha de rede), espera 5 minutos e tenta de novo
            time.sleep(300)

# Inicia a thread do bot. 'daemon=True' faz com que a thread
threading.Thread(target=keep_alive_bot, daemon=True).start()

if __name__ == '__main__':
    """
    Permite executar a aplicação localmente para desenvolvimento
    usando o comando 'python app.py'.
    O 'debug=True' faz o servidor reiniciar automaticamente
    quando há alterações no código.
    """
    app.run(debug=True, port=5000)