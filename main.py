import requests
from ddgs import DDGS
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import ollama

MODEL = "llama3.1:8b"

def logo():
    print("""
               ▄▄           ▄▄▄▄   ▄▄▄▄▄ 
               ██         ▄██▀▀██▄  ███  
███▄███▄ ▄███▄ ██ ▄█▀█▄   ███  ███  ███  
██ ██ ██ ██ ██ ██ ██▄█▀   ███▀▀███  ███  
██ ██ ██ ▀███▀ ██ ▀█▄▄▄   ███  ███ ▄███▄
    """)

# поиск ->
def search(query):
    with DDGS() as ddg:
        return list(ddg.text(query, max_results=5))

# скрейпинг ->
def scrape(url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3)
        soup = BeautifulSoup(r.text, "html.parser")
        return soup.get_text(separator=" ", strip=True)[:1500]
    except:
        return ""


def ask(query, history):

    results = search(query)
    urls = [r["href"] for r in results[:3]]

    with ThreadPoolExecutor(max_workers=3) as ex:
        texts = list(ex.map(scrape, urls))


    context = "\n".join(
        f"[{url}]\n{text}"
        for url, text in zip(urls, texts)
        if text
    )

    history.append({
        "role": "user",
        "content": (
            f"Ты поисковый ассистент. Отвечай кратко и по делу, только на основе источников.\n"
            f"Вопрос: {query}\n\n"
            f"Источники:\n{context}\n\n"
            f"В конце всегда указывай ссылки на источники."
)
    })


    full = ""
    print()
    for chunk in ollama.chat(model=MODEL, messages=history, stream=True):
        piece = chunk["message"]["content"]
        print(piece, end="", flush=True)
        full += piece
    print("\n")

    history.append({"role": "assistant", "content": full})
    return history


if __name__ == "__main__":
    logo()
    history = []

    while True:
        try:
            q = input("mole> ").strip()
            if q.lower() == "q":
                break
            if q:
                history = ask(q, history)
        except KeyboardInterrupt:
            break
