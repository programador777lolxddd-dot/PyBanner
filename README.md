# PyBannerLibrary

Banners, títulos, marcos y separadores para la terminal con Python, sin dependencias externas.

## Instalación

```bash
pip install PyBannerLibrary
```

## Uso rápido

```python
from pybanner import show, title, box, separator, banner

show("Hola, mundo", color="cyan")
title("Mi programa", style="double")
box("Operación completada", color="green")
separator("-", length=40)
banner("PyBanner", subtitle="Terminal toolkit", color="magenta")
```

## Funciones

- `show(text, color=None, style="simple", center=False)`: muestra texto con formato opcional.
- `title(text, style="simple", color=None)`: muestra un título destacado.
- `box(text, color=None, style="single", padding=1)`: dibuja un marco.
- `separator(char="-", length=40, color=None)`: imprime una línea divisoria.
- `banner(text, subtitle=None, color=None, style="box")`: combina título y subtítulo.
- `set_color_mode(mode="auto")`: configura los colores ANSI (`auto`, `always` o `never`).

Colores disponibles: `red`, `green`, `yellow`, `blue`, `magenta`, `cyan` y `white`.

## Licencia

Apache-2.0. Consulta el archivo [LICENSE](LICENSE).
