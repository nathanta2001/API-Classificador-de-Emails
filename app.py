from flask import Flask, jsonify, request
from dotenv import load_dotenv
import os
import google.generativeai as genai
import json
from flask_cors import CORS
import threading  
import time       
import requests

# Carrega variáveis do arquivo .env
load_dotenv()
app = Flask(__name__)
CORS(app)  # Para requisições externas


"""
Configuração da API Gemini. Certifique-se de definir a variável de ambiente
GOOGLE_API_KEY com sua chave de API do Google Cloud antes de executar o aplicativo.
"""
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash")

except AttributeError as e:
    print(f"Erro: {e}")
    print("Erro: A variável de ambiente GOOGLE_API_KEY não foi encontrada.")
    exit()


# Prompt principal usado para classificar e gerar resposta automática de emails
PROMPT = """
Você é um assistente especializado em classificação e resposta de emails. Sua tarefa é: (1) Classificar o email recebido como Produtivo ou Improdutivo, e (2) Gerar uma resposta automática apropriada à classificação.

Definições:
Produtivo: O email exige ação, tomada de decisão ou resposta específica. Exemplos: dúvidas sobre sistema, solicitações de suporte, pedidos de status, envio de documentos, reclamações.
Improdutivo: O email não exige ação ou resposta obrigatória. Exemplos: agradecimentos, mensagens motivacionais, cumprimentos, avisos informativos sem solicitação.

Formato de Resposta (retorne exatamente em JSON):
{
"classificacao": "Produtivo ou Improdutivo",
"resposta_automatica": "Texto da resposta sugerida ou vazio"
}

Regras:
Se a classificação for Produtivo, gere uma resposta educada e direta, solicitando informações ou oferecendo solução.
Se for Improdutivo, a resposta pode ser curta ou até vazia.
Não inclua explicações fora do JSON.
Não acrescente nada além do JSON.

Email para análise: [email_aqui]
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

@app.route('/api/classificar', methods=['POST'])
def classificarEmail():
    """
    Classifica o texto de um email como 'Produtivo' ou 'Improdutivo',
    e retorna uma resposta gerada automaticamente.

    Retorno:
        JSON contendo:
        - categoria (str): Classificação do email.
        - resposta (str): Texto sugerido para resposta automática.
    """

    # Obtém o JSON enviado pelo frontend
    dados = request.json
    if not dados:
        return jsonify({'error': 'Requisição deve conter JSON (verifique o Content-Type)'}), 400

    # Extrai o texto do email
    texto_do_email = dados.get('email_texto')
    if not texto_do_email:
        return jsonify({'error': 'A chave "email_texto" é obrigatória.'}), 400

    print(f"Email recebido: {texto_do_email}")

    try:
        # Prepara o prompt para o modelo
        promptFinal = PROMPT.replace("[email_aqui]", texto_do_email)
        response = model.generate_content(promptFinal)

        # Limpeza do retorno da IA
        textoIA = response.text
        textoJson = textoIA.strip().replace("```json", "").replace("```", "").strip()

        print(f"Resposta da IA: {textoJson}")

        resultadoJson = json.loads(textoJson)

        # Retorno formatado para o frontend
        return jsonify({
            "categoria": resultadoJson.get("classificacao"),
            "resposta": resultadoJson.get("resposta_automatica")
        })

    except Exception as e:
        print(f"Erro ao processar o email: {e}")
        return jsonify({
            'categoria': 'Erro',
            'resposta': f'Erro ao processar: {str(e)}'
        }), 500

@app.route('/api/revisar', methods=['POST'])
def revisarTexto():
    dados = request.json
    if not dados:
        return jsonify({'error': 'Requisição deve conter JSON (verifique o Content-Type)'}), 400
    
    texto_original = dados.get('texto')
    acao = dados.get('acao')

    if not texto_original or not acao:
        return jsonify({'error': 'As chaves "texto" e "acao" são obrigatórias.'}), 400
    
    print(f"Revisando texto: {texto_original} com ação: {acao[:50]}")

    try:
        promptFinal = PROMPT_DE_REVISAO.replace("{ACAO}", acao).replace("{TEXTO}", texto_original)
        response = model.generate_content(promptFinal)

        texto_revisado = response.text.strip()

        print(f"Texto revisado pela IA: {texto_revisado[:50]}")

        return jsonify({"texto_revisado": texto_revisado})

    except Exception as e:
        print(f"Erro ao revisar o texto: {e}")
        return jsonify({
            'error': f'Erro ao revisar o texto: {str(e)}'
        }), 500

@app.route('/api/ping')
def ping():
    return jsonify({"status": "alive"}), 200

def keep_alive_bot():
    time.sleep(30)
    print("Iniciando thread Keep-Alive.")
    
    while True:
        try:
            self_url = os.environ.get("RENDER_EXTERNAL_URL") 
            
            if self_url:

                # requisição para o endpoint /api/ping
                requests.get(f"{self_url}/api/ping")
                print(f"Keep-Alive: Ping enviado para {self_url}/api/ping")
            
            # Dorme por 14 min (15 min é tempo limite do Render)
            time.sleep(840)
        
        except Exception as e:
            print(f"Erro na thread Keep-Alive: {e}")

            # se der erro espera 5 minutos e tenta de novo
            time.sleep(300)

threading.Thread(target=keep_alive_bot, daemon=True).start()

if __name__ == '__main__':
    app.run(debug=True, port=5000)