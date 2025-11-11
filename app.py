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
Você é um assistente de triagem de emails para uma GRANDE EMPRESA DO SETOR FINANCEIRO.
O seu trabalho é classificar emails e sugerir respostas. Você deve ser rigoroso.

CATEGORIAS VÁLIDAS:
1. "Produtivo": Emails que requerem uma ação da equipe.
   - Exemplos: "não consigo acessar minha conta", "qual o status do meu caso 123?", "dúvidas sobre o sistema".
   - Resposta Sugerida para Produtivo: "Obrigado, recebemos sua solicitação e nossa equipe irá analisar em breve."

2. "Improdutivo": Emails que não necessitam de ação da equipe.
   - Exemplos: "obrigado", "feliz natal", spam, newsletters, ou emails *completamente irrelevantes* para o negócio financeiro (ex: "quero um pastel", "olá").
   - Resposta Sugerida para Improdutivo: "Obrigado pela sua mensagem!"

REGRAS DE FORMATAÇÃO:
- Retorne APENAS um objeto JSON válido.
- O JSON deve ter as chaves "categoria" e "resposta".
- NUNCA deixe a chave "resposta" vazia, mesmo para emails improdutivos.

Email para analisar:
---
{EMAIL_AQUI}
---
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
    
    # Validação da entrada
    dados = request.json
    if not dados:
        return jsonify({'error': 'Requisição deve conter JSON'}), 400

    texto_do_email = dados.get('email_texto')
    if not texto_do_email:
        return jsonify({'error': 'A chave "email_texto" é obrigatória.'}), 400

    print(f"Recebido para classificar: {texto_do_email[:50]}...")

    try:
        # Prepara e envia o prompt para o modelo Gemini
        promptFinal = PROMPT_DE_CLASSIFICACAO.replace("{EMAIL_AQUI}", texto_do_email)
        response = model.generate_content(promptFinal)

        textoIA = response.text
        print(f"IA (Classificar) retornou: {textoIA}")

        # Limpa e valida a resposta da IA
        if not textoIA.strip().startswith('{'):
            raise Exception(f"A IA não retornou um JSON válido. Resposta: {textoIA}")
            
        textoJson = textoIA.strip().replace("```json", "").replace("```", "").strip()
        resultadoJson = json.loads(textoJson)

        categoria = resultadoJson.get("categoria")
        resposta = resultadoJson.get("resposta")

        if not categoria or not resposta:
             raise Exception("O JSON da IA não contém as chaves 'categoria' ou 'resposta'.")

        # Retorna a resposta formatada para o frontend
        return jsonify({
            "categoria": categoria,
            "resposta": resposta
        })

    except Exception as e:
        print(f"Erro ao processar o email: {e}")
        # Retorna um erro que o frontend pode exibir
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