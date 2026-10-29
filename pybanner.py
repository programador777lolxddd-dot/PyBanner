"""
PyBanner
========

Pequeña librería sin dependencias para crear banners, títulos, marcos y
separadores en la terminal, sin repetir llamadas a ``print()``.

Uso rápido::

    from pybanner import show, title, box, separator, banner

    show("Hola, mundo", color="cyan")
    title("Mi programa", style="double")
    box("Operación completada", color="green")
    separator("-", length=40)
    banner("PyBanner", subtitle="Terminal toolkit", color="magenta")

Colores
-------
Se admiten los nombres ``red``, ``green``, ``yellow``, ``blue``,
``magenta``, ``cyan`` y ``white``. Los códigos ANSI solo se emiten cuando
la salida es una terminal interactiva (modo ``auto``). El comportamiento
se puede cambiar con :func:`set_color_mode` o con la variable de entorno
``PYBANNER_COLOR`` (``auto``, ``always`` o ``never``). La variable estándar
``NO_COLOR`` también desactiva el color.

Estilos
-------
``simple``, ``minimal``, ``box`` (esquinas redondeadas), ``single``,
``double`` y ``ascii``.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import unicodedata
from typing import Dict, List, Optional, Sequence

__all__ = ["show", "title", "box", "separator", "banner", "set_color_mode"]
__version__ = "1.0.0"

# ---------------------------------------------------------------------------
# Constantes internas
# ---------------------------------------------------------------------------

_RESET: str = "\033[0m"

_COLORS: Dict[str, str] = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
}

_BORDERS: Dict[str, Dict[str, str]] = {
    "single": {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│"},
    "double": {"tl": "╔", "tr": "╗", "bl": "╚", "br": "╝", "h": "═", "v": "║"},
    "box": {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"},
    "ascii": {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|"},
}

_STYLES: Sequence[str] = ("simple", "minimal", "box", "single", "double", "ascii")

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# Modo global de color: "auto" | "always" | "never".
_color_mode: str = "auto"


# ---------------------------------------------------------------------------
# Configuración de color
# ---------------------------------------------------------------------------

def set_color_mode(mode: str = "auto") -> None:
    """Configura el modo global de emisión de color.

    Args:
        mode: ``"auto"`` (colorear solo si la salida es una terminal),
            ``"always"`` (forzar color) o ``"never"`` (desactivar color).

    Raises:
        TypeError: Si ``mode`` no es una cadena.
        ValueError: Si ``mode`` no es uno de los valores admitidos.
    """
    global _color_mode
    if not isinstance(mode, str):
        raise TypeError(f"mode debe ser str, se recibió {type(mode).__name__}")
    normalized = mode.strip().lower()
    if normalized not in ("auto", "always", "never"):
        raise ValueError(
            f"mode inválido: {mode!r}. Valores válidos: 'auto', 'always', 'never'"
        )
    _color_mode = normalized


def _use_color() -> bool:
    """Indica si deben emitirse secuencias ANSI en la salida estándar."""
    mode = os.environ.get("PYBANNER_COLOR", _color_mode).strip().lower()
    if mode not in ("auto", "always", "never"):
        mode = _color_mode
    if mode == "always":
        return True
    if mode == "never":
        return False
    if os.environ.get("NO_COLOR"):
        return False
    try:
        return bool(sys.stdout.isatty())
    except (AttributeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Validaciones
# ---------------------------------------------------------------------------

def _validate_color(color: Optional[str]) -> Optional[str]:
    """Valida y normaliza un nombre de color."""
    if color is None:
        return None
    if not isinstance(color, str):
        raise TypeError(f"color debe ser str o None, se recibió {type(color).__name__}")
    normalized = color.strip().lower()
    if normalized not in _COLORS:
        raise ValueError(
            f"color inválido: {color!r}. Válidos: {', '.join(_COLORS)}"
        )
    return normalized


def _validate_style(style: str, allowed: Sequence[str] = _STYLES) -> str:
    """Valida y normaliza un nombre de estilo."""
    if not isinstance(style, str):
        raise TypeError(f"style debe ser str, se recibió {type(style).__name__}")
    normalized = style.strip().lower()
    if normalized not in allowed:
        raise ValueError(
            f"style inválido: {style!r}. Válidos: {', '.join(allowed)}"
        )
    return normalized


def _validate_non_negative_int(value: object, name: str) -> int:
    """Valida que ``value`` sea un entero mayor o igual que cero."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} debe ser int, se recibió {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} no puede ser negativo (recibido {value})")
    return value


# ---------------------------------------------------------------------------
# Utilidades de texto / terminal
# ---------------------------------------------------------------------------

def _to_lines(text: object) -> List[str]:
    """Convierte cualquier valor en una lista de líneas normalizadas."""
    if text is None:
        return [""]
    if not isinstance(text, str):
        text = str(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.split("\n")


def _display_width(text: str) -> int:
    """Calcula el ancho visual de ``text`` ignorando códigos ANSI."""
    stripped = _ANSI_RE.sub("", text)
    width = 0
    for char in stripped:
        if unicodedata.combining(char):
            continue
        if unicodedata.category(char) in ("Mn", "Me", "Cf", "Cc"):
            continue
        width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return width


def _term_width() -> int:
    """Devuelve el ancho de la terminal (80 columnas como reserva)."""
    try:
        return shutil.get_terminal_size((80, 24)).columns
    except (OSError, ValueError):
        return 80


def _paint(text: str, color: Optional[str]) -> str:
    """Aplica color ANSI a ``text`` si procede."""
    if color is None or not _use_color():
        return text
    return f"{_COLORS[color]}{text}{_RESET}"


def _pad_center(text: str, width: int) -> str:
    """Rellena ``text`` con espacios hasta ``width``, centrándolo."""
    current = _display_width(text)
    if current >= width:
        return text
    left = (width - current) // 2
    right = width - current - left
    return " " * left + text + " " * right


def _center_block(lines: Sequence[str]) -> List[str]:
    """Centra cada línea respecto al ancho de la terminal."""
    term = _term_width()
    centered: List[str] = []
    for line in lines:
        left = max(0, (term - _display_width(line)) // 2)
        centered.append(" " * left + line)
    return centered


# ---------------------------------------------------------------------------
# Renderizado compartido
# ---------------------------------------------------------------------------

def _frame(
    lines: Sequence[str],
    border: Dict[str, str],
    padding: int = 0,
    color: Optional[str] = None,
) -> List[str]:
    """Envuelve ``lines`` con el marco descrito por ``border``."""
    inner = max((_display_width(line) for line in lines), default=0)
    pad = " " * padding
    total = inner + padding * 2

    top = border["tl"] + border["h"] * total + border["tr"]
    bottom = border["bl"] + border["h"] * total + border["br"]

    rendered: List[str] = [top]
    for line in lines:
        fill = " " * max(0, inner - _display_width(line))
        rendered.append(border["v"] + pad + line + fill + pad + border["v"])
    rendered.append(bottom)

    return [_paint(line, color) for line in rendered]


def _render_block(
    lines: Sequence[str],
    style: str,
    color: Optional[str] = None,
    padding: int = 0,
) -> List[str]:
    """Renderiza un bloque de líneas según el estilo indicado."""
    if style == "simple":
        return [_paint(line, color) for line in lines]
    if style == "minimal":
        return [_paint("│ " + line, color) for line in lines]
    return _frame(lines, _BORDERS[style], padding=padding, color=color)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def show(
    text: object,
    color: Optional[str] = None,
    style: str = "simple",
    center: bool = False,
) -> None:
    """Imprime ``text`` con formato opcional.

    Args:
        text: Contenido a mostrar. Cualquier objeto se convierte a ``str``.
            Se admiten varias líneas separadas por ``\\n``.
        color: Nombre de color ANSI o ``None``.
        style: ``simple``, ``minimal``, ``box``, ``single``, ``double``
            o ``ascii``.
        center: Si es ``True``, centra cada línea en la terminal.

    Raises:
        TypeError: Si ``color``, ``style`` o ``center`` tienen un tipo inválido.
        ValueError: Si ``color`` o ``style`` no son valores admitidos.
    """
    style = _validate_style(style)
    color = _validate_color(color)
    if not isinstance(center, bool):
        raise TypeError(f"center debe ser bool, se recibió {type(center).__name__}")

    rendered = _render_block(_to_lines(text), style, color, padding=0)
    if center:
        rendered = _center_block(rendered)

    for line in rendered:
        print(line)


def title(text: object, style: str = "simple", color: Optional[str] = None) -> None:
    """Imprime un título destacado.

    Con el estilo ``simple`` se dibuja un subrayado del ancho del título;
    con ``minimal`` se añade una barra lateral; el resto de estilos usa
    marcos adaptables al contenido.

    Args:
        text: Texto del título (admite multilínea y Unicode).
        style: ``simple``, ``minimal``, ``box``, ``single``, ``double``
            o ``ascii``.
        color: Nombre de color ANSI o ``None``.

    Raises:
        TypeError: Si ``color`` o ``style`` tienen un tipo inválido.
        ValueError: Si ``color`` o ``style`` no son valores admitidos.
    """
    style = _validate_style(style)
    color = _validate_color(color)
    lines = _to_lines(text)

    if style == "simple":
        width = max((_display_width(line) for line in lines), default=0)
        rendered = [_paint(line, color) for line in lines]
        rendered.append(_paint("─" * width, color))
    elif style == "minimal":
        rendered = [_paint("▌ " + line, color) for line in lines]
    else:
        rendered = _render_block(lines, style, color, padding=1)

    for line in rendered:
        print(line)


def box(
    text: object,
    color: Optional[str] = None,
    style: str = "single",
    padding: int = 1,
) -> None:
    """Dibuja un marco adaptable alrededor de ``text``.

    Args:
        text: Contenido del marco (admite multilínea y Unicode).
        color: Nombre de color ANSI o ``None``.
        style: ``box``, ``single``, ``double``, ``ascii``, ``minimal``
            o ``simple``. En ``minimal`` y ``simple`` no se dibuja marco
            y ``padding`` se ignora.
        padding: Espacios horizontales entre el borde y el contenido.

    Raises:
        TypeError: Si algún parámetro tiene un tipo inválido.
        ValueError: Si ``color``/``style`` no son válidos o ``padding`` < 0.
    """
    style = _validate_style(style)
    color = _validate_color(color)
    padding = _validate_non_negative_int(padding, "padding")

    for line in _render_block(_to_lines(text), style, color, padding=padding):
        print(line)


def separator(char: str = "-", length: int = 40, color: Optional[str] = None) -> None:
    """Dibuja una línea divisoria.

    Args:
        char: Carácter único con el que se construye la línea.
        length: Número de repeticiones del carácter.
        color: Nombre de color ANSI o ``None``.

    Raises:
        TypeError: Si ``char`` no es ``str`` o ``length`` no es ``int``.
        ValueError: Si ``char`` no es un carácter imprimible o ``length`` < 0.
    """
    if not isinstance(char, str):
        raise TypeError(f"char debe ser str, se recibió {type(char).__name__}")
    if len(char) != 1:
        raise ValueError("char debe ser un único carácter")
    if char in ("\n", "\r", "\t") or unicodedata.category(char) == "Cc":
        raise ValueError("char no puede ser un carácter de control")

    length = _validate_non_negative_int(length, "length")
    color = _validate_color(color)

    print(_paint(char * length, color))


def banner(
    text: object,
    subtitle: Optional[object] = None,
    color: Optional[str] = None,
    style: str = "box",
) -> None:
    """Combina título y subtítulo en un banner completo.

    Args:
        text: Título principal (admite multilínea).
        subtitle: Subtítulo opcional (admite multilínea). Si es ``None``
            no se añade.
        color: Nombre de color ANSI o ``None``.
        style: ``box``, ``single``, ``double``, ``ascii``, ``minimal``
            o ``simple``.

    Raises:
        TypeError: Si ``color`` o ``style`` tienen un tipo inválido.
        ValueError: Si ``color`` o ``style`` no son valores admitidos.
    """
    style = _validate_style(style)
    color = _validate_color(color)

    main_lines = _to_lines(text)
    sub_lines = _to_lines(subtitle) if subtitle is not None else []

    content: List[str] = list(main_lines)
    if sub_lines:
        divider_width = max(
            (_display_width(line) for line in main_lines + sub_lines), default=0
        )
        content.append("─" * divider_width)
        content.extend(sub_lines)

    if style in ("simple", "minimal"):
        rendered = _render_block(content, style, color, padding=1)
    else:
        block_width = max((_display_width(line) for line in content), default=0)
        centered = [_pad_center(line, block_width) for line in content]
        rendered = _render_block(centered, style, color, padding=1)

    for line in rendered:
        print(line)


# ---------------------------------------------------------------------------
# Demo oficial
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Demo oficial de PyBanner
    print("\n=== PyBanner · demo oficial ===\n")

    banner("PyBanner", subtitle="Terminal toolkit for Python", color="cyan")
    separator("=", 60, color="cyan")

    print("\n[show]")
    show("Texto simple sin color")
    show("Texto en verde", color="green")
    show("Texto centrado en la terminal", color="magenta", center=True)

    print("\n[title]")
    title("Título simple", color="blue")
    title("Título minimal", style="minimal", color="green")
    title("Título en caja", style="box", color="cyan")
    title("Título doble", style="double", color="yellow")
    title("Título ascii", style="ascii", color="red")

    print("\n[box]")
    box("Operación completada", color="green")
    box("Línea 1\nLínea 2\nLínea 3", style="double", color="cyan")
    box("Contenido vacío:\n", style="box", color="yellow")
    box("Unicode: ñ á é í ó ú 漢字 🐍", style="ascii", color="magenta")

    print("\n[separator]")
    separator("-", 40)
    separator("=", 40, color="blue")
    separator("*", 20, color="yellow")

    print("\n[banner]")
    banner("CHX Library", subtitle="Official Demo", color="cyan")
    banner("Solo título", style="double", color="green")
    banner(
        "Multilínea\nen banner",
        subtitle="con subtítulo\nen dos líneas",
        style="box",
        color="magenta",
    )

    print("\n[show con cada estilo]")
    for current_style in _STYLES:
        show(f"estilo = {current_style}", style=current_style, color="cyan")

    print()
    separator("=", 60, color="cyan")
    print("Fin de la demo.")