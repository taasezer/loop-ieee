#!/usr/bin/env python3
"""
LOOP Lojistik Platformu - Kurulum Scripti
Geliştirme ortamı için otomatik kurulum
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional

# Renkli terminal çıktısı için
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_colored(text: str, color: str = Colors.WHITE, bold: bool = False):
    """Renkli terminal çıktısı yazdır"""
    output = color
    if bold:
        output += Colors.BOLD
    output += text + Colors.END
    print(output)

def run_command(command: List[str], check: bool = True, cwd: Optional[str] = None) -> bool:
    """Komut çalıştır ve sonucu döndür"""
    try:
        result = subprocess.run(command, check=check, cwd=cwd, capture_output=True, text=True)
        if result.returncode == 0:
            return True
        else:
            print_colored(f"Hata: {' '.join(command)}", Colors.RED)
            print_colored(result.stderr, Colors.RED)
            return False
    except subprocess.CalledProcessError as e:
        print_colored(f"Komut başarısız: {' '.join(command)}", Colors.RED)
        print_colored(str(e), Colors.RED)
        return False

def check_python_version():
    """Python versiyonunu kontrol et"""
    print_colored("Python versiyonu kontrol ediliyor...", Colors.YELLOW)
    
    if sys.version_info < (3, 11):
        print_colored("Hata: Python 3.11 veya üzeri gereklidir!", Colors.RED, bold=True)
        print_colored(f"Mevcut versiyon: {sys.version}", Colors.RED)
        sys.exit(1)
    
    print_colored(f"✓ Python {sys.version.split()[0]} uyumlu", Colors.GREEN)

def check_dependencies():
    """Sistem bağımlılıklarını kontrol et"""
    print_colored("Sistem bağımlılıkları kontrol ediliyor...", Colors.YELLOW)
    
    required_tools = ['docker', 'docker-compose', 'git']
    missing_tools = []
    
    for tool in required_tools:
        if not shutil.which(tool):
            missing_tools.append(tool)
    
    if missing_tools:
        print_colored("Eksik araçlar bulundu:", Colors.RED, bold=True)
        for tool in missing_tools:
            print_colored(f"  - {tool}", Colors.RED)
        print_colored("\nLütfen eksik araçları kurun:", Colors.YELLOW)
        print_colored("  Docker: https://docs.docker.com/get-docker/", Colors.CYAN)
        print_colored("  Docker Compose: https://docs.docker.com/compose/install/", Colors.CYAN)
        return False
    
    print_colored("✓ Tüm sistem araçları mevcut", Colors.GREEN)
    return True

def create_virtual_environment():
    """Sanal ortam oluştur"""
    print_colored("Sanal ortam oluşturuluyor...", Colors.YELLOW)
    
    venv_path = Path("venv")
    if venv_path.exists():
        print_colored("Sanal ortam zaten mevcut", Colors.CYAN)
        return True
    
    if run_command([sys.executable, "-m", "venv", "venv"]):
        print_colored("✓ Sanal ortam oluşturuldu", Colors.GREEN)
        return True
    else:
        print_colored("✗ Sanal ortam oluşturulamadı", Colors.RED)
        return False

def install_python_dependencies():
    """Python bağımlılıklarını yükle"""
    print_colored("Python bağımlılıkları yükleniyor...", Colors.YELLOW)
    
    pip_cmd = "venv/bin/pip" if os.name != 'nt' else "venv\\Scripts\\pip.exe"
    
    # pip'i güncelle
    if not run_command([pip_cmd, "install", "--upgrade", "pip"]):
        return False
    
    # requirements.txt'den bağımlılıkları yükle
    if run_command([pip_cmd, "install", "-r", "requirements.txt"]):
        print_colored("✓ Python bağımlılıkları yüklendi", Colors.GREEN)
        return True
    else:
        print_colored("✗ Python bağımlılıkları yüklenemedi", Colors.RED)
        return False

def create_env_file():
    """.env dosyasını oluştur"""
    print_colored("Çevre değişkenleri ayarlanıyor...", Colors.YELLOW)
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print_colored("✓ .env dosyası zaten mevcut", Colors.CYAN)
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print_colored("✓ .env dosyası oluşturuldu", Colors.GREEN)
        print_colored("  Lütfen .env dosyasını düzenleyin ve API anahtarlarını girin", Colors.YELLOW)
        return True
    else:
        print_colored("✗ .env.example dosyası bulunamadı", Colors.RED)
        return False

def setup_pre_commit():
    """Pre-commit hook'ları kur"""
    print_colored("Pre-commit hook'lar kuruluyor...", Colors.YELLOW)
    
    if not Path(".pre-commit-config.yaml").exists():
        print_colored("Pre-commit konfigürasyonu bulunamadı, atlanıyor", Colors.CYAN)
        return True
    
    pre_commit_cmd = "venv/bin/pre-commit" if os.name != 'nt' else "venv\\Scripts\\pre-commit.exe"
    
    if run_command([pre_commit_cmd, "install"]):
        print_colored("✓ Pre-commit hook'lar kuruldu", Colors.GREEN)
        return True
    else:
        print_colored("✗ Pre-commit hook'lar kurulamadı", Colors.YELLOW)
        return False

def create_directories():
    """Gerekli dizinleri oluştur"""
    print_colored("Dizinler oluşturuluyor...", Colors.YELLOW)
    
    directories = [
        "logs",
        "data", 
        "ssl",
        "monitoring",
        "init-db"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print_colored(f"  ✓ {directory} dizini oluşturuldu", Colors.GREEN)

def check_docker_services():
    """Docker servislerini kontrol et"""
    print_colored("Docker servisleri kontrol ediliyor...", Colors.YELLOW)
    
    if not run_command(["docker", "info"], check=False):
        print_colored("✗ Docker servisi çalışmıyor", Colors.RED)
        print_colored("Lütfen Docker servisini başlatın", Colors.YELLOW)
        return False
    
    print_colored("✓ Docker servisi çalışıyor", Colors.GREEN)
    return True

def main():
    """Ana kurulum fonksiyonu"""
    print_colored("LOOP Lojistik Platformu - Kurulum", Colors.CYAN, bold=True)
    print_colored("=" * 50, Colors.CYAN)
    
    # Kontroller
    check_python_version()
    
    if not check_dependencies():
        print_colored("\nKurulum devam edemiyor. Lütfen eksik bağımlılıkları kurun.", Colors.RED, bold=True)
        return False
    
    # Kurulum adımları
    success = True
    
    # 1. Sanal ortam
    if not create_virtual_environment():
        success = False
    
    # 2. Python bağımlılıkları
    if not install_python_dependencies():
        success = False
    
    # 3. Çevre değişkenleri
    if not create_env_file():
        success = False
    
    # 4. Dizinler
    create_directories()
    
    # 5. Pre-commit
    setup_pre_commit()
    
    # 6. Docker kontrolü
    check_docker_services()
    
    print_colored("\n" + "=" * 50, Colors.CYAN)
    
    if success:
        print_colored("✓ Kurulum başarıyla tamamlandı!", Colors.GREEN, bold=True)
        print_colored("\nSonraki adımlar:", Colors.YELLOW, bold=True)
        print_colored("1. .env dosyasını düzenleyin ve API anahtarlarını girin", Colors.WHITE)
        print_colored("2. Docker servislerini başlatın: docker-compose up -d", Colors.WHITE)
        print_colored("3. API'yi test edin: curl http://localhost:8000/health", Colors.WHITE)
        print_colored("4. Swagger UI: http://localhost:8000/docs", Colors.WHITE)
    else:
        print_colored("✗ Kurulumda hatalar oluştu", Colors.RED, bold=True)
        print_colored("Lütfen hata mesajlarını kontrol edin", Colors.YELLOW)
    
    return success

if __name__ == "__main__":
    main()