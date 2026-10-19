"""Reviewed Commons fixtures, no network or DB. See database/13-imagenes-demo.md."""

from urllib.parse import quote, unquote

CC0 = ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/")
BY4 = ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/")
SA4 = ("CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/")
SA3 = ("CC BY-SA 3.0", "https://creativecommons.org/licenses/by-sa/3.0/")
SA25 = ("CC BY-SA 2.5", "https://creativecommons.org/licenses/by-sa/2.5/")
PD = ("Dominio público (PD-self)", "https://commons.wikimedia.org/wiki/Template:PD-self")


def _asset(path, author, license_info, kind, description, *, software=None, thumbnail=True):
    name = path.rsplit("/", 1)[1]
    title = unquote(name).replace("_", " ")
    page = "https://commons.wikimedia.org/wiki/File:" + quote(unquote(name), safe="()")
    if thumbnail:
        suffix = ".png" if name.endswith(".svg") else ""
        url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{path}/960px-{name}{suffix}"
    else:
        url = f"https://upload.wikimedia.org/wikipedia/commons/{path}"
    return {
        "url": url,
        "alt": f"{description}. Representación ilustrativa; no documenta el acontecimiento demo.",
        "type": kind,
        "credit": f"{author} — {title}; Wikimedia Commons: {page}",
        "rights": f"{license_info[0]} — {license_info[1]}; sin cambios editoriales; se usa el archivo original o su miniatura de Commons según corresponde.",
        "aiDisclosure": (
            f"Imagen generada mediante IA ({software}, según la página de Commons); "
            "no es evidencia fotográfica del acontecimiento ficticio. DEMO / SYNTHETIC DATA."
            if kind == "ai_generated" else None
        ),
    }


def _icon(path, description):
    return _asset(path, "Copyright 2019 Twitter, Inc and other contributors", BY4,
                  "illustration", description)


_ASSETS = {
    "garden": _asset("3/37/Garden.jpg", "Shengzhi Li", SA25, "photograph", "Fotografía de un jardín de Nueva York"),
    "pitch": _asset("d/d7/Football_pitch.jpg", "LensEye Media", SA4, "photograph", "Fotografía de una cancha de fútbol"),
    "room": _asset("f/fb/Meeting_room.jpg", "Rashtriya Paryavaran", SA4, "photograph", "Fotografía de una sala de reuniones"),
    "park": _asset("3/34/Heerde_-_Vosbergerweg_-_Park.jpg", "Koosg", SA3, "photograph", "Fotografía de un parque en Vosbergen, Heerde"),
    "guitar": _asset("c/c2/Acoustic_guitar.jpg", "Massimo Giuliani", PD, "photograph", "Fotografía de una guitarra acústica", thumbnail=False),
    "shelves": _asset("1/18/Two_bookshelves_full_of_books_belonging_to_Unitedmissionary_%282010%29.jpg", "Unitedmissionary", SA3, "photograph", "Fotografía de dos estanterías con libros"),
    "bicycles": _asset("c/c1/Three_rusty_bicycles.jpg", "Pratap555", SA4, "photograph", "Fotografía de tres bicicletas estacionadas"),
    "books": _icon("2/21/Twemoji_1f4da.svg", "Ilustración de libros"),
    "shop": _icon("4/4c/Twemoji_1f3ea.svg", "Ilustración de una tienda"),
    "walking": _icon("5/54/Twemoji_1f6b6.svg", "Ilustración de una persona caminando"),
    "bird": _icon("5/5a/Twemoji_1f426.svg", "Ilustración de un ave"),
    "water": _icon("6/6a/Twemoji_1f4a7.svg", "Ilustración de una gota de agua"),
    "computer": _icon("f/fd/Twemoji_1f4bb.svg", "Ilustración de una computadora portátil"),
    "mail": _icon("8/82/Twemoji_1f4ee.svg", "Ilustración de un buzón postal"),
    "tree": _icon("1/1c/Twemoji_1f333.svg", "Ilustración de un árbol"),
    "craft": _asset("7/7b/Collage_con_materiales_reciclados_generado_por_Gemini.png", "Gemini", CC0,
                     "ai_generated", "Collage artificial de un ave con apariencia de materiales reciclados",
                     software="Gemini"),
    "lamp": _asset(
        "d/d4/DALL%C2%B7E_2025-02-21_17.55.25_-_A_sleek_RGB_light_stick_designed_for_fill_lighting%2C_featuring_a_modern%2C_minimalistic_design_with_a_slim%2C_cylindrical_shape._The_stick_emits_a_soft%2C_co.webp",
        "ChatGPT DALLE", BY4, "ai_generated", "Imagen artificial de una lámpara RGB",
        software="ChatGPT DALLE", thumbnail=False),
    "food": _asset("8/83/Generative_AI_can_be_used_to_create_realistic_images_of_food_dishes.jpg",
                    "Dennis Sylvester Hurd", CC0, "ai_generated", "Platos de comida generados artificialmente",
                    software="Midjourney"),
    "safety": _asset("7/78/Safety_Management_Cycle_diagram.png",
                      "OpenAI ChatGPT (GPT-5.6 Sol), using OpenAI image generation", BY4,
                      "ai_generated", "Diagrama artificial del ciclo de gestión de seguridad; no es una guía de evacuación",
                      software="OpenAI ChatGPT (GPT-5.6 Sol), según declaración del archivo"),
}

# Explicit topic-appropriate selection; no random services or runtime discovery.
_BY_SLUG = {
    "demo-ca-01-sensores-jardin": "garden",
    "demo-ca-02-club-lectura": "books",
    "demo-mx-01-teatro-barrial": "craft",
    "demo-gt-01-mercado-comunitario": "shop",
    "demo-gt-02-liga-fin-semana": "pitch",
    "demo-cr-01-monitoreo-quebradas": "water",
    "demo-cr-02-paseo-peatonal": "walking",
    "demo-ar-01-asamblea-salon": "room",
    "demo-br-01-caminatas-matutinas": "park",
    "demo-br-02-taller-reparacion": "lamp",
    "demo-cu-01-talleres-escritura": "books",
    "demo-jm-01-noche-acustica": "guitar",
    "demo-es-01-conteo-aves": "bird",
    "demo-fr-01-ruta-lectura": "shelves",
    "demo-jp-01-estacion-lluvia": "water",
    "demo-cn-01-clubes-cocina": "food",
    "demo-cn-02-estiramiento-parques": "park",
    "demo-eg-01-postales-escuelas": "mail",
    "demo-za-01-limpieza-parques": "park",
    "demo-au-01-ciclismo-recreativo": "bicycles",
    "demo-au-02-curso-computadoras": "computer",
    "demo-nz-01-simulacro-evacuacion": "safety",
    "demo-nz-02-foro-plazas": "tree",
}


def get_demo_image(slug: str) -> dict:
    """Return an independent copy; unknown visible slugs fail closed."""
    return dict(_ASSETS[_BY_SLUG[slug]])
