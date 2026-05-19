# classificar_empresas_rpe.py

from playwright.sync_api import sync_playwright
import pandas as pd
import time
import random

INPUT_FILE = "ids_validos.txt"
OUTPUT_FILE = "classificacao_empresas.xlsx"

BASE_URL = "https://registropublicodeemissoes.fgv.br/estatistica/estatistica-participantes/{}"

RESULTADOS = []


def extrair_classificacao(page, org_id):
    url = BASE_URL.format(org_id)

    try:
        print(f"\n================================================")
        print(f"PROCESSANDO ID {org_id}")
        print(f"URL: {url}")

        response = page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000
        )

        if not response:
            print("❌ Sem resposta")
            return None

        print(f"Status HTTP: {response.status}")

        if response.status != 200:
            print("❌ Página inválida")
            return None

        # aguarda carregamento angular
        page.wait_for_timeout(4000)

        # empresa
        nome = None
        classificacao = None

        # tenta localizar o bloco da árvore
        blocos = page.locator("ul.l-participants-tree li a.organization-type")
        total_blocos = blocos.count()

        print(f"Blocos encontrados: {total_blocos}")

        if total_blocos == 0:
            print("❌ Nenhum bloco encontrado")
            return None

        for i in range(total_blocos):

            bloco = blocos.nth(i)

            texto = bloco.inner_text().strip()

            print(f"Bloco {i}: {texto}")

            # captura classificação
            try:
                classificacao = bloco.locator("span.icon-group__icon").first.inner_text().strip()
            except Exception as e:
                print(f"Erro classificação: {e}")
                classificacao = None
            
            # captura nome
            try:
                nome = bloco.locator("span.text").first.inner_text().strip()
            except Exception as e:
                print(f"Erro nome: {e}")
                nome = None

            if classificacao:
                break

        print(f"Empresa: {nome}")
        print(f"Classificação: {classificacao}")

        return {
            "ID": org_id,
            "Empresa": nome,
            "Classificacao": classificacao
        }

    except Exception as e:
        print(f"❌ Erro em {org_id}: {e}")
        return None


def main():

    print("LENDO IDs...")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        ids = [linha.strip().zfill(4) for linha in f if linha.strip()]

    print(f"TOTAL IDs: {len(ids)}")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        context = browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
        )

        page = context.new_page()

        for idx, org_id in enumerate(ids, start=1):

            print(f"\n########## {idx}/{len(ids)} ##########")

            resultado = extrair_classificacao(page, org_id)

            if resultado:
                RESULTADOS.append(resultado)

            # pausa anti-bloqueio
            time.sleep(random.uniform(1.5, 3.5))

        browser.close()

    print("\nSALVANDO EXCEL...")

    df = pd.DataFrame(RESULTADOS)

    df.to_excel(OUTPUT_FILE, index=False)

    print(f"✅ FINALIZADO: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
