#!/bin/bash

# Script de instalación de dependencias LaTeX para el reporte OpenOB
# Autor: Lic. Manuel Vidal Alvarez - UNSA

echo "════════════════════════════════════════════════════════════"
echo "  Instalación de Dependencias LaTeX - Reporte OpenOB"
echo "════════════════════════════════════════════════════════════"
echo ""

# Detectar sistema operativo
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "❌ No se pudo detectar el sistema operativo"
    exit 1
fi

echo "Sistema operativo detectado: $OS"
echo ""

# Función para instalar en Ubuntu/Debian
install_ubuntu_debian() {
    echo "Instalando LaTeX en Ubuntu/Debian..."
    echo ""
    
    sudo apt-get update
    
    echo ""
    echo "¿Deseas instalar la distribución completa o mínima?"
    echo "1) Completa (texlive-full) - ~4 GB - Recomendado"
    echo "2) Mínima (texlive-latex-extra) - ~500 MB"
    echo ""
    read -p "Opción [1-2]: " OPTION
    
    case $OPTION in
        1)
            echo "Instalando distribución completa..."
            sudo apt-get install -y texlive-full texlive-lang-spanish
            ;;
        2)
            echo "Instalando distribución mínima..."
            sudo apt-get install -y texlive-latex-base \
                                     texlive-latex-extra \
                                     texlive-lang-spanish \
                                     texlive-fonts-recommended
            ;;
        *)
            echo "Opción inválida, instalando distribución completa..."
            sudo apt-get install -y texlive-full texlive-lang-spanish
            ;;
    esac
    
    # Herramientas adicionales
    echo ""
    echo "Instalando herramientas adicionales..."
    sudo apt-get install -y latexmk make
}

# Función para instalar en Fedora/RHEL
install_fedora() {
    echo "Instalando LaTeX en Fedora/RHEL..."
    echo ""
    sudo dnf install -y texlive-scheme-full latexmk make
}

# Función para instalar en Arch Linux
install_arch() {
    echo "Instalando LaTeX en Arch Linux..."
    echo ""
    sudo pacman -S texlive-most texlive-lang make
}

# Instalar según el sistema
case $OS in
    ubuntu|debian|pop)
        install_ubuntu_debian
        ;;
    fedora|rhel|centos)
        install_fedora
        ;;
    arch|manjaro)
        install_arch
        ;;
    *)
        echo "❌ Sistema operativo no soportado: $OS"
        echo ""
        echo "Por favor, instala LaTeX manualmente:"
        echo "- Ubuntu/Debian: sudo apt-get install texlive-full"
        echo "- Fedora: sudo dnf install texlive-scheme-full"
        echo "- Arch: sudo pacman -S texlive-most"
        exit 1
        ;;
esac

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Verificando instalación..."
echo "════════════════════════════════════════════════════════════"
echo ""

# Verificar pdflatex
if command -v pdflatex &> /dev/null; then
    VERSION=$(pdflatex --version | head -n1)
    echo "✓ pdflatex instalado: $VERSION"
else
    echo "✗ pdflatex NO instalado"
fi

# Verificar latexmk
if command -v latexmk &> /dev/null; then
    VERSION=$(latexmk --version | head -n1)
    echo "✓ latexmk instalado: $VERSION"
else
    echo "✗ latexmk NO instalado (opcional)"
fi

# Verificar make
if command -v make &> /dev/null; then
    VERSION=$(make --version | head -n1)
    echo "✓ make instalado: $VERSION"
else
    echo "✗ make NO instalado"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Instalación completada"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Para compilar el reporte:"
echo "  cd /home/server/openob/reporte"
echo "  make"
echo ""
echo "Para ver el PDF:"
echo "  make view"
echo ""
echo "Para ayuda:"
echo "  make help"
echo ""
