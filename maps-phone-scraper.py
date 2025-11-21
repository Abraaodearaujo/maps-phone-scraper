#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import csv
import re
import random
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


TIPO_NEGOCIO = "exemplo"
ARQUIVO_CSV = "resultados.csv"
CFG_FILE = "lista.cfg"
MAX_RESULTS_POR_CIDADE = 1000
SCROLL_ITER_BLOCK = 10
MAX_EXPAND_TRIES = 120
SAVE_EVERY = 50
WAIT_SHORT = 1.0
WAIT_LONG = 3.0
NO_NEW_LIMIT = 3

phone_regex = re.compile(r"\(?\d{2}\)?\s?\d{4,5}[-\s]?\d{4}")


def format_phone_to_wa(text):
    digits = re.sub(r"\D", "", text)
    if digits.startswith("55"):
        digits = digits[2:]
    return "55" + digits


def try_find_phone_on_page(driver):
    xpaths = [
        "//button[contains(@aria-label, 'Telefone') or contains(@aria-label, 'Ligar') or contains(@aria-label, 'Phone') or contains(@aria-label, 'Call')]",
        "//button[contains(text(), 'Telefone') or contains(text(), 'Ligar') or contains(text(), 'Phone') or contains(text(), 'Call')]",
        "//div[@data-item-id='phone']",
        "//div[contains(@data-item-id, 'phone') or contains(@aria-label,'telefone') or contains(@aria-label,'phone')]"
    ]
    
    for xp in xpaths:
        try:
            elems = driver.find_elements(By.XPATH, xp)
            for e in elems:
                aria = (e.get_attribute("aria-label") or "").strip()
                text = (e.text or "").strip()
                candidate = aria if aria else text
                if candidate:
                    m = phone_regex.search(candidate)
                    if m:
                        return m.group(0)
        except Exception:
            pass

    try:
        candidates = driver.find_elements(By.XPATH, "//div|//span|//button|//li|//p|//section")
        for c in candidates:
            try:
                txt = c.text.strip()
                if not txt:
                    continue
                m = phone_regex.search(txt)
                if m:
                    return m.group(0)
            except Exception:
                continue
    except Exception:
        pass

    return None


def load_existing_data():
    cfg_links = set()
    csv_phones = set()
    
    if os.path.exists(CFG_FILE):
        with open(CFG_FILE, "r", encoding="utf-8") as fcfg:
            for ln in fcfg:
                ln = ln.strip()
                if ln:
                    cfg_links.add(ln)

    if os.path.exists(ARQUIVO_CSV):
        with open(ARQUIVO_CSV, "r", encoding="utf-8") as fcsv:
            reader = csv.DictReader(fcsv)
            for row in reader:
                if "Telefone" in row and row["Telefone"]:
                    tel_digits = re.sub(r"\D", "", row["Telefone"])
                    csv_phones.add(tel_digits)
                if "Link WhatsApp" in row and row["Link WhatsApp"]:
                    csv_phones.add(row["Link WhatsApp"])
    
    return cfg_links, csv_phones


def collect_links(driver, feed, max_results):
    links = []
    links_set = set()
    expand_tries = 0
    no_new_count = 0
    
    print("Expandindo feed e coletando links...")
    
    while len(links) < max_results and expand_tries < MAX_EXPAND_TRIES:
        expand_tries += 1
        new_found = 0

        for i in range(SCROLL_ITER_BLOCK):
            try:
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
            except Exception:
                driver.execute_script("window.scrollBy(0, 1000)")
            time.sleep(0.8 + random.random() * 0.7)

        cards = driver.find_elements(By.XPATH, "//div[@role='feed']//a[contains(@href, '/maps/place/')]")
        for c in cards:
            try:
                href = c.get_attribute("href")
                if href and ("/maps/place/" in href) and href not in links_set:
                    links_set.add(href)
                    links.append(href)
                    new_found += 1
            except Exception:
                continue

        print(f"  tentativa {expand_tries}: total links coletados = {len(links)}  (+{new_found})")

        if new_found == 0:
            no_new_count += 1
            print(f"    sem novos links nesta tentativa (repetições: {no_new_count}/{NO_NEW_LIMIT})")
            if no_new_count >= NO_NEW_LIMIT:
                print(f"    sem novos links por {NO_NEW_LIMIT} tentativas — processando {len(links)} links.")
                break
            sleep_more = 3 + random.random() * 4
            print(f"    aguardando {sleep_more:.1f}s antes da próxima tentativa")
            time.sleep(sleep_more)
        else:
            no_new_count = 0
            time.sleep(1 + random.random() * 0.8)

    print(f" Expansão finalizada. Links totais: {len(links)} (meta: {max_results})")
    return links


def process_links(driver, links, csv_writer, csv_file, existing_csv_phones, existing_cfg_links, cidade, max_results):
    processed = 0
    skipped_duplicates = 0
    
    for idx, link in enumerate(links):
        if processed >= max_results:
            break

        print(f"\n[{idx+1}/{len(links)}] Abrindo: {link}")
        try:
            driver.get(link)
        except Exception as e:
            print("  erro ao abrir link:", e)
            continue

        time.sleep(WAIT_LONG + random.random() * 1.5)
        
        try:
            nome = driver.find_element(By.XPATH, "//h1").text.strip()
        except:
            nome = link
        
        try:
            title_elem = driver.find_element(By.XPATH, "//h1")
            panel = title_elem.find_element(By.XPATH, "./ancestor::div[@role='region' or @role='main']")
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", panel)
        except:
            driver.execute_script("window.scrollBy(0, 600)")

        telefone = try_find_phone_on_page(driver)
        
        if telefone:
            tel_digits = re.sub(r"\D", "", telefone)
            if len(tel_digits) >= 10:
                wa = format_phone_to_wa(telefone)
                
                if tel_digits in existing_csv_phones or wa in existing_csv_phones or wa in existing_cfg_links:
                    print(f"  DUPLICADO: {telefone} -> {wa} já existe!")
                    skipped_duplicates += 1
                    continue
                
                print(f"  Telefone: {telefone} -> {wa}")

                csv_writer.writerow([nome, telefone, wa, cidade])
                csv_file.flush()
                
                existing_csv_phones.add(tel_digits)
                existing_csv_phones.add(wa)

                if wa not in existing_cfg_links:
                    with open(CFG_FILE, "a", encoding="utf-8") as fcfg:
                        fcfg.write(wa + "\n")
                    existing_cfg_links.add(wa)
                    print("    Adicionado em", CFG_FILE)

                processed += 1

                if processed % SAVE_EVERY == 0:
                    print(f"    Salvando progresso — {processed} salvos, {skipped_duplicates} duplicados ignorados.")
                    csv_file.flush()
                    time.sleep(1 + random.random() * 1.5)
            else:
                print("  Telefone extraído parece inválido:", telefone)
        else:
            print("  Telefone não encontrado nesta página.")

        time.sleep(1.5 + random.random() * 3.5)
    
    return processed, skipped_duplicates


def processar_cidade(driver, cidade, csv_writer, csv_file, existing_csv_phones, existing_cfg_links):
    print("\n" + "="*80)
    print(f" PROCESSANDO CIDADE: {cidade}")
    print("="*80 + "\n")
    
    try:
        search_url = f"https://www.google.com/maps/search/{TIPO_NEGOCIO}+em+{cidade}"
        print(f"🔗 Abrindo: {search_url}")
        driver.get(search_url)
        
        wait = WebDriverWait(driver, 15)
        feed = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='feed']")))
        time.sleep(2)

        links = collect_links(driver, feed, MAX_RESULTS_POR_CIDADE)

        processed, skipped = process_links(
            driver, links, csv_writer, csv_file, 
            existing_csv_phones, existing_cfg_links,
            cidade, MAX_RESULTS_POR_CIDADE
        )

        print(f"\n Cidade {cidade} finalizada!")
        print(f"   Total salvos: {processed}")
        print(f"   Duplicados ignorados: {skipped}")
        
        return processed, skipped

    except Exception as e:
        print(f"Erro ao processar cidade {cidade}:", e)
        return 0, 0


def coletar_cidades():
    cidades = []
    print("\n" + "="*80)
    print("CADASTRO DE CIDADES")
    print("="*80)
    print("Digite o nome de cada cidade e pressione ENTER")
    print("Digite '0' (zero) e pressione ENTER quando terminar")
    print("-"*80 + "\n")
    
    while True:
        cidade = input(f"Cidade #{len(cidades)+1}: ").strip()
        
        if cidade == "0":
            if len(cidades) == 0:
                print("\n  Você precisa cadastrar pelo menos 1 cidade!")
                continue
            else:
                break
        
        if cidade:
            cidades.append(cidade)
            print(f"    '{cidade}' adicionada!")
        else:
            print("     Nome vazio, tente novamente.")
    
    print("\n" + "="*80)
    print(f" Total de cidades cadastradas: {len(cidades)}")
    print("="*80)
    print(" Lista de cidades:")
    for idx, c in enumerate(cidades, 1):
        print(f"   {idx}. {c}")
    print("="*80 + "\n")
    
    confirma = input("Confirmar e iniciar? (S/N): ").strip().upper()
    if confirma != "S":
        print(" Operação cancelada pelo usuário.")
        exit()
    
    return cidades


def main():
    cidades = coletar_cidades()
    
    print("\n" + "="*80)
    print(f" INICIANDO SCRAPER GOOGLE MAPS - MÚLTIPLAS CIDADES")
    print(f" Total de cidades: {len(cidades)}")
    print(f" Tipo de negócio: {TIPO_NEGOCIO}")
    print(f" Máximo por cidade: {MAX_RESULTS_POR_CIDADE}")
    print("="*80 + "\n")
    
    existing_cfg_links, existing_csv_phones = load_existing_data()
    print(f" Números já existentes no CSV: {len(existing_csv_phones)}")
    print(f" Links já existentes no CFG: {len(existing_cfg_links)}")

    write_header = not os.path.exists(ARQUIVO_CSV)
    csv_file = open(ARQUIVO_CSV, "a", newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_file)
    if write_header:
        csv_writer.writerow(["Nome/LinkLocal", "Telefone", "Link WhatsApp", "Cidade"])

    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    total_processado = 0
    total_duplicados = 0

    try:
        for idx, cidade in enumerate(cidades, 1):
            print(f"\n{'='*80}")
            print(f"  CIDADE {idx}/{len(cidades)}: {cidade}")
            print(f"{'='*80}")
            
            processed, skipped = processar_cidade(
                driver, cidade, csv_writer, csv_file,
                existing_csv_phones, existing_cfg_links
            )
            
            total_processado += processed
            total_duplicados += skipped
            
            if idx < len(cidades):
                pausa = 5 + random.random() * 3
                print(f"\n  Pausando {pausa:.1f}s antes da próxima cidade...")
                time.sleep(pausa)

        print("\n" + "="*80)
        print("🎉 PROCESSO COMPLETO - TODAS AS CIDADES PROCESSADAS!")
        print("="*80)
        print(f" ESTATÍSTICAS FINAIS:")
        print(f"     Cidades processadas: {len(cidades)}")
        print(f"    Total de números salvos: {total_processado}")
        print(f"    Total de duplicados ignorados: {total_duplicados}")
        print(f"    Arquivo CSV: {ARQUIVO_CSV}")
        print(f"    Arquivo CFG: {CFG_FILE}")
        print("="*80 + "\n")

    except Exception as e:
        print(" Erro geral:", e)

    finally:
        csv_file.close()
        driver.quit()
        print("🔚 Navegador fechado. Processo finalizado.")


if __name__ == "__main__":
    main()