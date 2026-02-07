import socket
import threading
import json

# Dizionari per memorizzare i dati
utenti = {}          # username → connessione socket
gruppi = {}          # nome_gruppo → lista messaggi
chat_private = {}    # chiave_chat → lista messaggi

# Per evitare conflitti tra thread
lock = threading.Lock()

MAX_MESSAGGI = 500

def ricevi_messaggio(conn):
    """Riceve un messaggio JSON dal client"""
    dati = conn.recv(2048).decode()
    if not dati:
        return None
    
    # Prende solo il primo messaggio (fino al newline)
    if "\n" in dati:
        dati = dati.split("\n")[0]
    
    try:
        return json.loads(dati)
    except:
        return None

def invia_messaggio(conn, messaggio):
    """Invia un messaggio JSON al client"""
    try:
        testo = json.dumps(messaggio) + "\n"
        conn.sendall(testo.encode())
        return True
    except:
        return False

def gestisci_messaggio_chat(msg):
    """Salva e inoltra un messaggio a gruppo o chat privata"""
    mittente = msg["sorgente"]
    destinazione = msg["destinazione"]
    
    with lock:
        # È un gruppo?
        if destinazione in gruppi:
            # Aggiungi messaggio al gruppo
            gruppi[destinazione].append(msg)
            
            # Tieni solo gli ultimi MAX_MESSAGGI
            if len(gruppi[destinazione]) > MAX_MESSAGGI:
                gruppi[destinazione] = gruppi[destinazione][-MAX_MESSAGGI:]
            
            # Trova membri del gruppo dal primo messaggio
            membri = []
            for u in utenti.keys():
                membri.append(u)  # Semplificato: inoltra a tutti
        
        # È una chat privata
        else:
            chiave = tuple(sorted([mittente, destinazione]))
            
            # Crea la chat se non esiste
            if chiave not in chat_private:
                chat_private[chiave] = []
            
            # Aggiungi messaggio
            chat_private[chiave].append(msg)
            
            # Tieni solo gli ultimi MAX_MESSAGGI
            if len(chat_private[chiave]) > MAX_MESSAGGI:
                chat_private[chiave] = chat_private[chiave][-MAX_MESSAGGI:]
            
            membri = [mittente, destinazione]
    
    # Inoltra il messaggio ai membri (escluso mittente)
    for utente in membri:
        if utente != mittente and utente in utenti:
            invia_messaggio(utenti[utente], msg)

def crea_gruppo(msg):
    """Crea un nuovo gruppo"""
    nome_gruppo = msg["nome"]
    
    with lock:
        if nome_gruppo not in gruppi:
            gruppi[nome_gruppo] = []
            print(f"Gruppo '{nome_gruppo}' creato")

def carica_lista_chat(conn, username):
    """Invia al client la lista delle sue chat"""
    lista = []
    
    with lock:
        # Aggiungi tutti i gruppi
        for nome_gruppo in gruppi.keys():
            lista.append(nome_gruppo)
        
        # Aggiungi chat private dell'utente
        for chiave in chat_private.keys():
            if username in chiave:
                lista.append(chiave)
    
    risposta = {"tipo": "lista_chat", "chat": lista}
    invia_messaggio(conn, risposta)

def apri_chat(conn, nome_chat):
    """Invia lo storico di una chat"""
    messaggi = []
    
    with lock:
        # Gruppo
        if nome_chat in gruppi:
            messaggi = gruppi[nome_chat].copy()
        # Chat privata
        elif nome_chat in chat_private:
            messaggi = chat_private[nome_chat].copy()
    
    risposta = {"tipo": "storico", "messaggi": messaggi}
    invia_messaggio(conn, risposta)

def crea_chat_privata(conn, msg):
    """Crea o apre una chat privata"""
    chiave = msg["chat"]
    with lock:
        if chiave not in chat_private:
            chat_private[chiave] = []



def gestisci_client(conn, indirizzo):
    """Gestisce la connessione di un client"""
    username = None
    
    try:
        # 1. USERNAME
        while True:            
            username = conn.recv(1024).decode().strip()
            
            with lock:
                # Username già in uso?
                if username in utenti:
                    conn.sendall("False".encode())
                else:
                    utenti[username] = conn
                    conn.sendall("True".encode())
                    print(f"{username} connesso da {indirizzo}")
                    break
        
        # 2. LOOP PRINCIPALE
        while True:
            msg = ricevi_messaggio(conn)
            if not msg:
                break
            
            tipo = msg["tipo"]
            
            match tipo:
                case "messaggio":
                    gestisci_messaggio_chat(msg)
                case "crea_gruppo":
                    crea_gruppo(msg)
                case "crea_chat":
                    crea_chat_privata(conn, msg)
                case "carica_chat":
                    carica_lista_chat(conn, username)
                case "apri_chat":
                    apri_chat(conn, msg["chat"])
    
    except Exception as e:
        print(f"Errore con {username}: {e}")
        with lock:
            if username in utenti:
                del utenti[username]
            print(f"{username} disconnesso")
        
        conn.close()
    
def avvia_server():
    """Avvia il server"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 5000))
    server.listen(10)
    
    print("Server avviato sulla porta 5000")
    
    try:
        while True:
            conn, indirizzo = server.accept()
            thread = threading.Thread(target=gestisci_client, args=(conn, indirizzo))
            thread.start()
    
    except KeyboardInterrupt:
        print("\nServer in chiusura...")
        server.close()


if __name__ == "__main__":
    avvia_server()