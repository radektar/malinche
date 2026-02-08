#!/bin/bash
# TEST M2: Brak internetu - skrypt pomocniczy

echo "============================================================"
echo "TEST M2: Brak internetu"
echo "============================================================"
echo ""
echo "Ten test wymaga manualnego wyłączenia WiFi przed uruchomieniem."
echo ""
echo "Kroki:"
echo "1. Usuń zależności (symulacja czystej instalacji)"
echo "2. WYŁĄCZ WiFi (System Settings → Network → WiFi: Off)"
echo "3. Uruchom aplikację: python -m src.menu_app"
echo "4. Sprawdź czy pojawia się komunikat o braku internetu"
echo ""
echo "============================================================"
echo ""

# Sprawdź czy zależności są zainstalowane
python3 << 'EOF'
from src.setup.downloader import DependencyDownloader
downloader = DependencyDownloader()
if downloader.check_all():
    print("⚠️  UWAGA: Zależności są zainstalowane!")
    print("   Aby przetestować brak internetu, najpierw usuń zależności:")
    print("   rm -rf ~/Library/Application\\ Support/Transrec/")
    print("")
    print("Czy chcesz usunąć zależności teraz? (y/n)"
    response = input()
    if response.lower() == 'y':
        import shutil
        import os
        support_dir = os.path.expanduser("~/Library/Application Support/Transrec")
        if os.path.exists(support_dir):
            shutil.rmtree(support_dir)
            print("✓ Zależności usunięte")
        else:
            print("✓ Katalog już nie istnieje")
    else:
        print("Zależności pozostają - test nie będzie działał poprawnie")
else:
    print("✓ Zależności nie są zainstalowane - gotowe do testu")
EOF

echo ""
echo "============================================================"
echo "Następne kroki:"
echo "1. WYŁĄCZ WiFi (System Settings → Network → WiFi: Off)"
echo "2. Uruchom: python -m src.menu_app"
echo "3. Sprawdź czy pojawia się dialog '⚠️ Brak połączenia'"
echo "4. Sprawdź logi: tail -f ~/Library/Logs/olympus_transcriber.log"
echo "============================================================"



