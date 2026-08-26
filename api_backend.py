#!/usr/bin/env python3
"""
API Backend Flask para CHK Tropa do Bom e Novo
Integra validador_5.py + main.py com interface HTML
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import time
from validador_5 import Validador3DS

app = Flask(__name__)
CORS(app)  # Permite requisições do HTML

# Status global
status_validacao = {
    "rodando": False,
    "atual": 0,
    "total": 0,
    "cartao_atual": "",
    "resultados": []
}

@app.route('/api/health', methods=['GET'])
def health():
    """Verifica se API está online"""
    return jsonify({"status": "online", "message": "API CHK Tropa funcionando!"})

@app.route('/api/validar', methods=['POST'])
def validar_cartoes():
    """
    Endpoint principal para validar cartões
    Recebe: {"cartoes": ["4532015112830366|12|2027|123", ...]}
    Retorna: {"sucesso": true, "resultados": [...]}
    """
    try:
        data = request.get_json()
        cartoes = data.get('cartoes', [])
        
        if not cartoes:
            return jsonify({"sucesso": False, "erro": "Nenhum cartão fornecido"}), 400
        
        # Resetar status
        status_validacao["rodando"] = True
        status_validacao["total"] = len(cartoes)
        status_validacao["atual"] = 0
        status_validacao["resultados"] = []
        
        # Processar cada cartão
        for i, linha in enumerate(cartoes, 1):
            if not status_validacao["rodando"]:
                break  # Parado pelo usuário
            
            partes = linha.split("|")
            if len(partes) != 4:
                resultado = {
                    "index": i,
                    "cartao": linha,
                    "status": "ERRO",
                    "mensagem": "Formato inválido",
                    "tempo": 0,
                    "isLive": False
                }
                status_validacao["resultados"].append(resultado)
                continue
            
            numero, mes, ano, cvv = partes
            status_validacao["cartao_atual"] = f"{numero}|{mes}|{ano}|{cvv}"
            status_validacao["atual"] = i
            
            # Criar instância do validador
            validador = Validador3DS()
            
            # Validar cartão
            start_time = time.time()
            resultado_texto = validador.verificar_cartao(numero, mes, ano, cvv, i, len(cartoes))
            tempo_total = round(time.time() - start_time, 2)
            
            # Parsear resultado
            is_live = "✅" in resultado_texto
            is_vbv = "VBV/SMS" in resultado_texto
            is_die = "❌" in resultado_texto or "DIE" in resultado_texto
            
            # Extrair mensagem
            if is_live or is_vbv:
                # Extrair banco e mensagem
                partes_resultado = resultado_texto.split(" - ")
                if len(partes_resultado) >= 3:
                    status = "LIVE" if is_live else "VBV"
                    banco = partes_resultado[2] if len(partes_resultado) > 2 else "Desconhecido"
                    mensagem = " - ".join(partes_resultado[3:]) if len(partes_resultado) > 3 else "Aprovado"
                else:
                    status = "LIVE" if is_live else "VBV"
                    banco = "Desconhecido"
                    mensagem = resultado_texto
            else:
                status = "DIE"
                banco = ""
                mensagem = resultado_texto
            
            resultado = {
                "index": i,
                "cartao": f"{numero}|{mes}|{ano}|{cvv}",
                "numero_mascarado": f"{numero[:6]}******{numero[-4:]}",
                "bandeira": validador.detectBandeira(numero) if hasattr(validador, 'detectBandeira') else "UNKNOWN",
                "status": status,
                "banco": banco,
                "mensagem": mensagem,
                "tempo": tempo_total,
                "isLive": is_live or is_vbv,
                "resultado_completo": resultado_texto
            }
            
            status_validacao["resultados"].append(resultado)
            
            # Aguardar entre validações (evitar bloqueio)
            if i < len(cartoes):
                time.sleep(5)
        
        status_validacao["rodando"] = False
        
        return jsonify({
            "sucesso": True,
            "total": len(cartoes),
            "processados": len(status_validacao["resultados"]),
            "aprovados": sum(1 for r in status_validacao["resultados"] if r["isLive"]),
            "recusados": sum(1 for r in status_validacao["resultados"] if not r["isLive"]),
            "resultados": status_validacao["resultados"]
        })
        
    except Exception as e:
        status_validacao["rodando"] = False
        return jsonify({"sucesso": False, "erro": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Retorna o status atual da validação"""
    return jsonify(status_validacao)

@app.route('/api/parar', methods=['POST'])
def parar_validacao():
    """Para a validação em andamento"""
    status_validacao["rodando"] = False
    return jsonify({"sucesso": True, "mensagem": "Validação interrompida"})

def detectBandeira(numero):
    """Detecta a bandeira do cartão"""
    num = numero.replace(" ", "").replace("-", "")
    if num.startswith('4'):
        return 'VISA'
    elif num.startswith(('51', '52', '53', '54', '55')):
        return 'MASTERCARD'
    elif num.startswith(('34', '37')):
        return 'AMEX'
    elif num.startswith(('4011', '4312', '4389', '4514', '4573', '5067', '5090', '6277', '6362', '6363', '6504', '6505', '6516')):
        return 'ELO'
    elif num.startswith('6'):
        return 'DISCOVER'
    return 'UNKNOWN'

if __name__ == '__main__':
    import os
    
    # Porta para produção (Render, Railway, etc)
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 60)
    print("🚀 API CHK TROPA DO BOM E NOVO")
    print("=" * 60)
    print()
    print(f"✅ API iniciando na porta {port}...")
    print()
    
    # Só mostra IPs locais se não estiver em produção
    if port == 5000:
        print("📱 Acesse o painel:")
        print("   http://localhost:5000")
        print()
        print("🌐 Para acessar do celular na mesma rede:")
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            print(f"   http://{ip}:5000")
        except:
            print("   (Configure o IP manualmente)")
        finally:
            s.close()
        print()
        print("🛑 Para parar: CTRL+C")
    else:
        print("🌐 Rodando em produção")
        print(f"   Porta: {port}")
    
    print("=" * 60)
    print()
    
    app.run(host='0.0.0.0', port=port, debug=False)
