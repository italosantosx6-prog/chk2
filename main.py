#!/usr/bin/env python3
import time
import random
import sys
import os
from validador_5 import Validador3DS

def ler_cartoes_do_stdin():
    print("\n" + "="*60)
    print("📋 COLE A LISTA DE CARTÕES")
    print("="*60)
    print("Formato: numero|mes|ano|cvv (um por linha)")
    print("Pressione Enter duas vezes para finalizar.")
    print("-"*60)
    cartoes = []
    linhas_vazias = 0
    while True:
        try:
            linha = input().strip()
            if linha == "":
                linhas_vazias += 1
                if linhas_vazias >= 2:
                    break
                continue
            linhas_vazias = 0
            cartoes.append(linha)
        except KeyboardInterrupt:
            print("\n\n⏹️  Interrompido pelo usuário. Saindo...")
            sys.exit(0)
    return cartoes

def main():
    print("="*60)
    print("🔥 VALIDADOR 3DS - CHECKOUT 5")
    print("="*60)
    cartoes = ler_cartoes_do_stdin()
    if not cartoes:
        print("❌ Nenhum cartão fornecido. Saindo.")
        return
    total = len(cartoes)
    print(f"\n📊 Total de cartões: {total}")
    print("-"*60)
    resultados = []
    aprovados = []
    for i, linha in enumerate(cartoes, 1):
        partes = linha.split("|")
        if len(partes) != 4:
            print(f"❌ Linha inválida: {linha}")
            continue
        numero, mes, ano, cvv = partes
        tentativas = 0
        resultado = None
        while tentativas < 2:
            tentativas += 1
            print(f"\n🔍 Verificando {i}/{total} (Tentativa {tentativas}/2)...")
            validador_local = Validador3DS()
            resultado = validador_local.verificar_cartao(numero, mes, ano, cvv, i, total)
            if "UNAVAILABLE" in resultado:
                print(f"   ⏳ 3DS indisponível, tentando novamente em 20s...")
                time.sleep(20)
            else:
                break
        resultados.append(resultado)
        print(resultado)
        if "✅" in resultado and "UNAVAILABLE" not in resultado:
            aprovados.append(f"{numero}|{mes}|{ano}|{cvv}")
        print("-"*60)
        if i < total:
            espera = random.randint(10, 20)
            print(f"⏳ Aguardando {espera}s para evitar bloqueio...")
            time.sleep(espera)
    print("\n" + "="*60)
    print("📊 RESUMO FINAL")
    print("="*60)
    lives = [r for r in resultados if "LIVE" in r and "UNAVAILABLE" not in r]
    vbv = [r for r in resultados if "VBV/SMS" in r and "UNAVAILABLE" not in r]
    dies = [r for r in resultados if "DIE" in r or "ERRO" in r or "BLOQUEADO" in r]
    unavailable = [r for r in resultados if "UNAVAILABLE" in r]
    print(f"✅ LIVE: {len(lives)}")
    print(f"🔶 VBV/SMS: {len(vbv)}")
    print(f"❌ DIE/ERRO: {len(dies)}")
    print(f"⚠️ UNAVAILABLE: {len(unavailable)}")
    if aprovados:
        print("\n" + "="*60)
        print("✅ CARTÕES APROVADOS (LIVE + VBV/SMS)")
        print("="*60)
        for idx, cartao in enumerate(aprovados, 1):
            print(f"{idx}. {cartao}")
        print("="*60)
        resposta = input("\n📁 Deseja salvar os aprovados em um arquivo .txt? (s/N): ").strip().lower()
        if resposta in ('s', 'sim', 'y', 'yes'):
            nome_arquivo = input("Digite o nome do arquivo (padrão: aprovados.txt): ").strip()
            if not nome_arquivo:
                nome_arquivo = "aprovados.txt"
            if not nome_arquivo.endswith(".txt"):
                nome_arquivo += ".txt"
            try:
                with open(nome_arquivo, "w", encoding="utf-8") as f:
                    for cartao in aprovados:
                        f.write(cartao + "\n")
                print(f"✅ Arquivo salvo: {nome_arquivo}")
            except Exception as e:
                print(f"❌ Erro ao salvar o arquivo: {e}")
    else:
        print("\n❌ Nenhum cartão aprovado.")
    try:
        with open("resultados.txt", "w", encoding="utf-8") as f:
            f.write("="*60 + "\n")
            f.write("RESULTADOS DA VERIFICACAO\n")
            f.write("="*60 + "\n\n")
            for r in resultados:
                f.write(r + "\n")
            f.write("\n" + "="*60 + "\n")
            f.write(f"✅ LIVE: {len(lives)}\n")
            f.write(f"🔶 VBV/SMS: {len(vbv)}\n")
            f.write(f"❌ DIE/ERRO: {len(dies)}\n")
            f.write(f"⚠️ UNAVAILABLE: {len(unavailable)}\n")
        print("\n📄 Log completo salvo em resultados.txt")
    except Exception as e:
        print(f"⚠️ Erro ao salvar resultados.txt: {e}")
    print("\n🏁 Finalizado.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrompido pelo usuário. Saindo...")
        sys.exit(0)