#!/bin/bash
#############################################
#  Aura's Bruter - Installation Script      #
#  For Kali Linux / Debian-based systems    #
#############################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                                                                   ║"
echo "║              AURA'S BRUTER - INSTALLATION SCRIPT                 ║"
echo "║                                                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running as root for apt commands
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Note: Running without root. Some system packages may require sudo.${NC}"
    SUDO="sudo"
else
    SUDO=""
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "\n${CYAN}[1/5] Checking system dependencies...${NC}"

# Check for Python 3.8+
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"
else
    echo -e "${RED}✗ Python 3 not found. Installing...${NC}"
    $SUDO apt-get update
    $SUDO apt-get install -y python3 python3-pip
fi

# Check for python3-venv
if ! python3 -c "import venv" &> /dev/null; then
    echo -e "${YELLOW}Installing python3-venv...${NC}"
    $SUDO apt-get update
    $SUDO apt-get install -y python3-venv
fi

echo -e "\n${CYAN}[2/5] Creating virtual environment...${NC}"

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

echo -e "\n${CYAN}[3/5] Installing Python dependencies...${NC}"

# Upgrade pip
pip install --upgrade pip > /dev/null 2>&1

# Install requirements
pip install -r requirements.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

echo -e "\n${CYAN}[4/5] Setting up directories...${NC}"

# Create necessary directories
mkdir -p sessions
mkdir -p logs
mkdir -p wordlists

echo -e "${GREEN}✓ Directories created${NC}"

echo -e "\n${CYAN}[5/5] Creating shell alias...${NC}"

# Create launcher script
cat > aura-bruter << 'EOF'
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/venv/bin/activate"
python "$SCRIPT_DIR/aura_bruter.py" "$@"
EOF

chmod +x aura-bruter
chmod +x aura_bruter.py

# Add alias to bashrc if not exists
ALIAS_LINE="alias aura-bruter='$SCRIPT_DIR/aura-bruter'"
if ! grep -q "aura-bruter" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# Aura's Bruter alias" >> ~/.bashrc
    echo "$ALIAS_LINE" >> ~/.bashrc
    echo -e "${GREEN}✓ Alias added to ~/.bashrc${NC}"
else
    echo -e "${GREEN}✓ Alias already exists${NC}"
fi

# Also add to .zshrc if it exists
if [ -f ~/.zshrc ]; then
    if ! grep -q "aura-bruter" ~/.zshrc 2>/dev/null; then
        echo "" >> ~/.zshrc
        echo "# Aura's Bruter alias" >> ~/.zshrc
        echo "$ALIAS_LINE" >> ~/.zshrc
        echo -e "${GREEN}✓ Alias added to ~/.zshrc${NC}"
    fi
fi

echo -e "\n${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                    INSTALLATION COMPLETE! 🎉${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"

echo -e "\n${CYAN}Usage:${NC}"
echo -e "  ${YELLOW}./aura-bruter${NC}               # Interactive mode"
echo -e "  ${YELLOW}./aura-bruter --help${NC}        # Show help"
echo -e "  ${YELLOW}aura-bruter${NC}                 # Use alias (restart shell first)"

echo -e "\n${CYAN}Quick Start:${NC}"
echo -e "  1. Run: ${YELLOW}source ~/.bashrc${NC} or restart your terminal"
echo -e "  2. Run: ${YELLOW}aura-bruter${NC}"

echo -e "\n${RED}⚠️  DISCLAIMER: Use responsibly and only on systems you own!${NC}\n"
