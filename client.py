import socket
import threading
import json
import time
import os

username = ""
chat_list = []
chat_storico = []


def riceviMsg(conn):
    global chat_list, chat_storico
    buffer = ""

    while True:
        try:
            data = conn.recv(2048).decode()
        except:
            break

        if not data:
            break

        buffer += data

        while "\n" in buffer:
            msg_str, buffer = buffer.split("\n", 1)
            msg = json.loads(msg_str)

            if msg["tipo"] == "caricaChat":
                chat_list = msg["chat"]

            elif msg["tipo"] == "chatAperta":
                chat_storico = msg["messaggi"]

            elif msg["tipo"] == "messaggio":
                pass


def inviaMsg(conn, msg):
    conn.sendall((json.dumps(msg) + "\n").encode())


# -------------------------
# MENU PRINCIPALE
# -------------------------

def menu_principale(conn):
    while True:
        os.system("cls")
        print("--- MENU PRINCIPALE ---")
        print("1) Vedi chat")
        print("2) Nuova chat privata")
        print("3) Crea gruppo")
        print("4) Esci")

        scelta = input("Scelta: ")

        if scelta == "1":
            menu_vedi_chat(conn)
        elif scelta == "2":
            nuova_chat_privata(conn)
        elif scelta == "3":
            crea_gruppo(conn)
        elif scelta == "4":
            print("Uscita...")
            conn.close()
            return


# -------------------------
# MENU 2: VEDI CHAT
# -------------------------

def menu_vedi_chat(conn):
    global chat_list

    inviaMsg(conn, {"tipo": "caricaChat", "sorgente": username})
    time.sleep(0.2)

    while True:
        clear()
        print("--- LE TUE CHAT ---")

        for i, c in enumerate(chat_list):
            print(f"{i+1}) {c}")

        print("0) Torna indietro")

        scelta = input("Scelta: ")

        if scelta == "0":
            return

        try:
            scelta = int(scelta)
            if 1 <= scelta <= len(chat_list):
                apri_chat(conn, chat_list[scelta-1])
        except:
            pass


# -------------------------
# CHAT
# -------------------------

def apri_chat(conn, nome_chat):
    global chat_storico

    destinazione = eval(nome_chat) if nome_chat.startswith("(") else nome_chat

    while True:
        # Richiede lo storico aggiornato
        inviaMsg(conn, {"tipo": "apriChat", "chat": nome_chat})
        time.sleep(0.2)

        # Ristampa la chat
        clear()
        print(f"--- CHAT {nome_chat} ---")
        for m in chat_storico:
            print(f"{m['sorgente']}: {m.get('testo','')}")
        print("------------------")

        testo = input("Scrivi messaggio (0 per uscire): ")
        if testo == "0":
            return

        inviaMsg(conn, {
            "tipo": "messaggio",
            "sorgente": username,
            "destinazione": destinazione,
            "testo": testo
        })


# -------------------------
# CREAZIONE CHAT E GRUPPI
# -------------------------

def nuova_chat_privata(conn):
    global username

    while True:
        user = input("Con chi vuoi parlare? ")
        if user != username:
            break
        print("Non puoi parlare con te stesso!")

    inviaMsg(conn, {"tipo": "iniziaConv", "membri": [username, user]})
    time.sleep(0.2)


def crea_gruppo(conn):
    membri = []

    while True:
        user = input("Aggiungi partecipante (0 per finire): ")
        if user == "0":
            break
        if user not in membri:
            membri.append(user)

    membri.append(username)
    nome = input("Nome del gruppo: ")

    inviaMsg(conn, {"tipo": "creaGruppo", "membri": membri, "destinazione": nome})
    time.sleep(0.2)


# -------------------------
# MAIN CLIENT
# -------------------------

def main():
    global username

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 5000))

    print("Connesso al server!\n")

    while True:
        username = input("Inserisci username: ")

        client.sendall(username.encode())

        risposta = client.recv(2048).decode()
        if risposta == "Username occupato":
            print("Username già in uso!")
        else:
            break


    threading.Thread(target=riceviMsg, args=(client,), daemon=True).start()

    menu_principale(client)


if __name__ == "__main__":
    main()
