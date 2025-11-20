import requests
import base64
import time
import sys

# --- CONFIGURAÇÕES ---
INSTANCE_NAME = "clinica_teste_01"
# Se estiver rodando no Windows (host), usa localhost
API_URL = "http://localhost:8080" 
API_KEY = "intellimed-secret-key-global"

headers = {
    "apikey": API_KEY,
    "Content-Type": "application/json"
}

def delete_instance():
    """Deleta a instância se ela já existir bugada"""
    print(f"🗑️  Verificando se '{INSTANCE_NAME}' já existe...")
    try:
        # Tenta deletar (Logout) para garantir limpeza
        requests.delete(f"{API_URL}/instance/delete/{INSTANCE_NAME}", headers=headers)
        requests.delete(f"{API_URL}/instance/logout/{INSTANCE_NAME}", headers=headers)
        print("   Limpeza concluída (se existia, foi apagada).")
    except:
        pass

def create_instance():
    print(f"🚀 Criando instância '{INSTANCE_NAME}'...")
    url = f"{API_URL}/instance/create"
    data = {
        "instanceName": INSTANCE_NAME,
        "token": "token-secreto-clinica",
        "qrcode": True,
        "integration": "WHATSAPP-BAILEYS"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code in [200, 201]:
            print("✅ Instância criada com sucesso.")
            
            # Às vezes o QR Code já vem na criação
            resp_json = response.json()
            if 'qrcode' in resp_json and 'base64' in resp_json['qrcode']:
                save_qr(resp_json['qrcode']['base64'])
                return "QR_JA_SALVO"
            return True
        elif response.status_code == 403:
            print("ℹ️ Instância já existe.")
            return True
        else:
            print(f"❌ Erro ao criar: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def get_qr_code():
    print("🔄 Solicitando QR Code (Aguarde)...")
    url = f"{API_URL}/instance/connect/{INSTANCE_NAME}"
    
    # Tenta 3 vezes com intervalo
    for i in range(3):
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if 'base64' in data:
                save_qr(data['base64'])
                return True
            elif 'instance' in data and data['instance']['state'] == 'open':
                print("\n✅ ATENÇÃO: Esta instância JÁ ESTÁ CONECTADA!")
                print("   Não precisa ler QR Code. Já está funcionando.")
                return True
            else:
                print(f"   Tentativa {i+1}: API ainda inicializando... ({data})")
                time.sleep(3)
        except Exception as e:
            print(f"   Erro na tentativa {i+1}: {e}")
            time.sleep(3)
            
    print("❌ Não foi possível obter o QR Code após tentativas.")
    return False

def save_qr(base64_code):
    clean_code = base64_code.replace("data:image/png;base64,", "")
    with open("whatsapp_qr.png", "wb") as fh:
        fh.write(base64.b64decode(clean_code))
    print("\n✨ SUCESSO! QR Code salvo em 'whatsapp_qr.png'.")
    print("👉 Abra a imagem AGORA e leia com o WhatsApp.")

if __name__ == "__main__":
    # 1. Limpa estado anterior
    delete_instance()
    time.sleep(2)
    
    # 2. Cria nova
    status = create_instance()
    
    if status == "QR_JA_SALVO":
        sys.exit(0)
        
    if status:
        # 3. Dá um tempo para o 'motor' do WhatsApp subir
        print("⏳ Aguardando 5 segundos para inicialização do motor...")
        time.sleep(5)
        get_qr_code()