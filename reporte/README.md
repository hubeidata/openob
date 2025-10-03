# Reporte Técnico - Sistema OpenOB Repeater

## Autor
**Lic. Manuel Vidal Alvarez**  
Licenciado en Ciencias de la Computación  
Universidad Nacional de San Agustín de Arequipa (UNSA)  
Líder del Proyecto

## Descripción
Este directorio contiene el reporte técnico completo del proyecto de retransmisión de audio por internet implementado con OpenOB.

## Archivos
- `reporte-openob.tex` - Documento principal en LaTeX
- `Makefile` - Automatización de compilación
- `README.md` - Este archivo
- `logo-unsa.png` - Logo de la UNSA (opcional)

## Compilación

### Opción 1: Usando Make (Recomendado)
```bash
# Compilar el PDF
make

# Limpiar archivos temporales
make clean

# Limpiar todo (incluyendo PDF)
make distclean

# Ver el PDF
make view
```

### Opción 2: Compilación Manual
```bash
# Primera compilación
pdflatex reporte-openob.tex

# Segunda compilación (para referencias cruzadas)
pdflatex reporte-openob.tex

# Tercera compilación (para tabla de contenidos)
pdflatex reporte-openob.tex
```

### Opción 3: Usando latexmk (Automático)
```bash
latexmk -pdf reporte-openob.tex
```

## Requisitos

### Distribución LaTeX
Necesitas tener instalado un sistema LaTeX completo:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install texlive-full texlive-lang-spanish
```

**Fedora/RHEL:**
```bash
sudo dnf install texlive-scheme-full
```

**macOS (con Homebrew):**
```bash
brew install --cask mactex
```

**Windows:**
- Descargar e instalar [MiKTeX](https://miktex.org/) o [TeX Live](https://www.tug.org/texlive/)

### Paquetes LaTeX Necesarios
El documento utiliza los siguientes paquetes:
- inputenc (UTF-8)
- babel (español)
- graphicx
- float
- listings
- xcolor
- hyperref
- geometry
- fancyhdr
- titlesec
- enumitem
- booktabs
- caption
- subcaption

## Estructura del Documento

1. **Portada** - Título, autor, afiliación
2. **Resumen Ejecutivo** - Síntesis del proyecto
3. **Tabla de Contenidos** - Navegación
4. **Introducción** - Contexto y objetivos
5. **Marco Teórico** - Fundamentos técnicos
6. **Arquitectura** - Diseño del sistema
7. **Implementación** - Código y desarrollo
8. **Resultados** - Métricas y pruebas
9. **Documentación** - Scripts y guías
10. **Monitoreo** - Herramientas de diagnóstico
11. **Problemas y Soluciones** - Debugging
12. **Conclusiones** - Logros y trabajo futuro
13. **Referencias** - Bibliografía
14. **Anexos** - Comandos y especificaciones

## Logo de la UNSA

El documento incluye una referencia al logo de la UNSA. Para añadirlo:

1. Obtén el logo oficial de la UNSA en formato PNG
2. Nómbralo `logo-unsa.png`
3. Colócalo en el directorio `reporte/`

Si no tienes el logo, puedes comentar la línea en el archivo `.tex`:
```latex
% \includegraphics[width=5cm]{logo-unsa.png}\\[1cm]
```

## Personalización

### Cambiar Márgenes
Edita la sección `geometry`:
```latex
\geometry{
    a4paper,
    left=2.5cm,    % Margen izquierdo
    right=2.5cm,   % Margen derecho
    top=3cm,       % Margen superior
    bottom=3cm     % Margen inferior
}
```

### Cambiar Colores de Enlaces
Edita `hyperref`:
```latex
\hypersetup{
    colorlinks=true,
    linkcolor=blue,      % Color de enlaces internos
    filecolor=magenta,   % Color de enlaces a archivos
    urlcolor=cyan,       % Color de URLs
}
```

### Estilo de Código
Modifica `lstdefinestyle` para cambiar la apariencia del código.

## Salida

El documento compilado genera:
- `reporte-openob.pdf` - Documento final (aprox. 25-30 páginas)

## Contenido Destacado

### Figuras
- Topología de red del sistema
- Diagramas de flujo

### Tablas
- Stack tecnológico
- Métricas de rendimiento
- Comparación GStreamer vs UDP
- Scripts desarrollados
- Especificaciones técnicas

### Listados de Código
- Método `build_sockets()`
- Thread receptor RTP
- Método de reenvío
- Auto-registro en Redis
- Scripts bash

## Tamaño Aproximado
- **Páginas:** 25-30
- **Palabras:** ~8,000
- **Figuras/Tablas:** 10+
- **Listados de código:** 8+

## Versiones

- **Versión 1.0** - 3 de Octubre 2025
  - Reporte completo del proyecto
  - Documentación de arquitectura UDP
  - Resultados de pruebas
  - Conclusiones y trabajo futuro

## Contacto

**Lic. Manuel Vidal Alvarez**  
Universidad Nacional de San Agustín de Arequipa  
Facultad de Ingeniería de Producción y Servicios  
Escuela Profesional de Ciencias de la Computación  

---

**Fecha de creación:** 3 de Octubre 2025  
**Versión del documento:** 1.0  
**Sistema documentado:** OpenOB 4.0.3 con UDP Repeater
