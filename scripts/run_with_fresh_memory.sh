#!/bin/bash
#
# Run Malinche with Fresh Memory
#
# Ten skrypt automatycznie resetuje pamięć i uruchamia transkrypcję.
# Użyj tego zamiast bezpośredniego wywołania python -m src.main
# aby za każdym razem widzieć pliki od 18 listopada.
#
# Użycie:
#   bash scripts/run_with_fresh_memory.sh
#   lub z własną datą:
#   bash scripts/run_with_fresh_memory.sh 2025-11-15
#

set -e

# Kolory
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Przejdź do katalogu projektu
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Malinche - Fresh Start${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Krok 1: Reset pamięci
echo -e "${YELLOW}Krok 1/2: Resetowanie pamięci...${NC}"
echo ""
bash scripts/reset_recorder_memory.sh "$@"
echo ""

# Krok 2: Uruchomienie transkrypcji
echo -e "${YELLOW}Krok 2/2: Uruchamianie transkrypcji...${NC}"
echo ""
echo -e "${GREEN}Rozpoczynam nasłuchiwanie na recorder...${NC}"
echo -e "${GREEN}(Naciśnij Ctrl+C aby zatrzymać)${NC}"
echo ""

python -m src.main





