# Makefile para compilar el reporte OpenOB en LaTeX

# Variables
LATEX = pdflatex
LATEXMK = latexmk
BIBTEX = bibtex
MAIN = reporte-openob
PDF = $(MAIN).pdf

# Opciones de compilación
LATEX_OPTS = -interaction=nonstopmode -halt-on-error

# Visor de PDF (cambiar según el sistema operativo)
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    PDF_VIEWER = xdg-open
endif
ifeq ($(UNAME_S),Darwin)
    PDF_VIEWER = open
endif

# Target por defecto
.PHONY: all
all: pdf

# Compilar el PDF (3 pasadas para referencias cruzadas y TOC)
.PHONY: pdf
pdf:
	@echo "========================================="
	@echo "Compilando reporte OpenOB..."
	@echo "========================================="
	$(LATEX) $(LATEX_OPTS) $(MAIN).tex
	@echo ""
	@echo "Segunda pasada (referencias)..."
	$(LATEX) $(LATEX_OPTS) $(MAIN).tex
	@echo ""
	@echo "Tercera pasada (tabla de contenidos)..."
	$(LATEX) $(LATEX_OPTS) $(MAIN).tex
	@echo ""
	@echo "========================================="
	@echo "✓ Compilación exitosa!"
	@echo "✓ Archivo generado: $(PDF)"
	@echo "========================================="

# Compilación rápida (una sola pasada)
.PHONY: quick
quick:
	@echo "Compilación rápida (una pasada)..."
	$(LATEX) $(LATEX_OPTS) $(MAIN).tex
	@echo "✓ Compilación rápida completada"

# Usar latexmk (automático)
.PHONY: latexmk
latexmk:
	@echo "Compilando con latexmk..."
	$(LATEXMK) -pdf $(MAIN).tex
	@echo "✓ Compilación con latexmk completada"

# Limpiar archivos temporales
.PHONY: clean
clean:
	@echo "Limpiando archivos temporales..."
	rm -f $(MAIN).aux $(MAIN).log $(MAIN).out $(MAIN).toc $(MAIN).lof $(MAIN).lot
	rm -f $(MAIN).fls $(MAIN).fdb_latexmk $(MAIN).synctex.gz
	rm -f $(MAIN).bbl $(MAIN).blg
	@echo "✓ Archivos temporales eliminados"

# Limpiar todo (incluyendo PDF)
.PHONY: distclean
distclean: clean
	@echo "Eliminando PDF..."
	rm -f $(PDF)
	@echo "✓ Limpieza completa"

# Ver el PDF generado
.PHONY: view
view: pdf
	@echo "Abriendo PDF..."
	$(PDF_VIEWER) $(PDF) &

# Compilar y ver
.PHONY: show
show: pdf view

# Verificar requisitos
.PHONY: check
check:
	@echo "Verificando requisitos..."
	@which $(LATEX) > /dev/null && echo "✓ pdflatex encontrado" || echo "✗ pdflatex NO encontrado"
	@which $(LATEXMK) > /dev/null && echo "✓ latexmk encontrado" || echo "✗ latexmk NO encontrado (opcional)"
	@which $(PDF_VIEWER) > /dev/null && echo "✓ Visor de PDF encontrado" || echo "✗ Visor de PDF NO encontrado"
	@echo ""
	@echo "Para instalar LaTeX en Ubuntu/Debian:"
	@echo "  sudo apt-get install texlive-full texlive-lang-spanish"

# Contar palabras (aproximado)
.PHONY: count
count:
	@echo "Contando palabras en el documento..."
	@detex $(MAIN).tex | wc -w
	@echo "Nota: Cuenta aproximada (sin comandos LaTeX)"

# Ayuda
.PHONY: help
help:
	@echo "Makefile para compilar el reporte OpenOB"
	@echo ""
	@echo "Uso: make [target]"
	@echo ""
	@echo "Targets disponibles:"
	@echo "  all (default) - Compilar el PDF completo"
	@echo "  pdf           - Compilar el PDF (3 pasadas)"
	@echo "  quick         - Compilación rápida (1 pasada)"
	@echo "  latexmk       - Compilar con latexmk (automático)"
	@echo "  clean         - Eliminar archivos temporales"
	@echo "  distclean     - Eliminar todo (incluyendo PDF)"
	@echo "  view          - Compilar y ver el PDF"
	@echo "  show          - Alias para 'view'"
	@echo "  check         - Verificar requisitos del sistema"
	@echo "  count         - Contar palabras aproximadas"
	@echo "  help          - Mostrar esta ayuda"
	@echo ""
	@echo "Ejemplos:"
	@echo "  make              # Compilar PDF"
	@echo "  make view         # Compilar y abrir PDF"
	@echo "  make clean        # Limpiar temporales"
	@echo "  make distclean    # Limpiar todo"

# Información del proyecto
.PHONY: info
info:
	@echo "========================================="
	@echo "Reporte OpenOB - Información"
	@echo "========================================="
	@echo "Documento:  Sistema de Retransmisión de Audio"
	@echo "Autor:      Lic. Manuel Vidal Alvarez"
	@echo "Institución: UNSA"
	@echo "Versión:    4.0.3"
	@echo "Fecha:      3 de Octubre 2025"
	@echo "========================================="
	@ls -lh $(PDF) 2>/dev/null || echo "PDF no generado aún (ejecuta 'make')"
	@echo "========================================="
