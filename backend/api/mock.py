# Datos mock para el schema
SCHEMA_DATA = {
    "db": "Sales DB",
    "tables": [
        {
            "table_name": "songs",
            "fields": [
                {"name": "id", "type": "INT", "is_primary_key": True},
                {"name": "title", "type": "VARCHAR(100)", "is_primary_key": False},
                {"name": "sound_file", "type": "SOUND", "is_primary_key": False},
                {"name": "artist", "type": "VARCHAR(100)", "is_primary_key": False},
                {"name": "duration", "type": "VARCHAR(10)", "is_primary_key": False},
                {"name": "genre", "type": "VARCHAR(50)", "is_primary_key": False},
                {"name": "url", "type": "VARCHAR(300)", "is_primary_key": False}
            ],
            "indexes": [
                {"field_name": "id", "type": "btree"}
            ]
        }
    ]
}



# Datos mock para las consultas
QUERY_RESULT_DATA = {
    "columns": [
        {"field_name": "id", "type": "INT"},
        {"field_name": "title", "type": "VARCHAR(100)"},
        {"field_name": "sound_file", "type": "SOUND"},
        {"field_name": "artist", "type": "VARCHAR(100)"},
        {"field_name": "duration", "type": "VARCHAR(10)"},
        {"field_name": "genre", "type": "VARCHAR(50)"},
        {"field_name": "description", "type": "TEXT"}
    ],
    "rows": [
        {
            "id": 1,
            "title": "Bohemian Rhapsody",
            "sound_file": "0000001.mp3",
            "artist": "Queen",
            "duration": "5:55",
            "genre": "Rock",
            "description": "Una obra maestra del rock progresivo que combina elementos de ópera, balada y hard rock. Escrita por Freddie Mercury, es considerada una de las mejores canciones de todos los tiempos por su estructura única y complejidad musical."
        },
        {
            "id": 2,
            "title": "Imagine",
            "sound_file": "0000002.mp3",
            "artist": "John Lennon",
            "duration": "3:03",
            "genre": "Pop",
            "description": "Una canción icónica sobre la paz mundial y la unidad. John Lennon invita a imaginar un mundo sin divisiones religiosas, políticas o nacionales, convirtiéndose en un himno para la paz."
        },
        {
            "id": 3,
            "title": "Hotel California",
            "sound_file": "0000003.mp3",
            "artist": "Eagles",
            "duration": "6:30",
            "genre": "Rock",
            "description": "Una enigmática canción que narra la historia de un viajero que se detiene en un lujoso pero misterioso hotel del que aparentemente no puede escapar. Famosa por su memorable solo de guitarra final."
        }
    ],
    "message": "Consulta ejecutada correctamente.",
    "count_rows": 3,
    "time_execution": 150
}

# Datos mock para archivos de audio
AUDIO_FILES_DATA = {
    "file_sounds": [
        {"name": "0000001.mp3", "duration": 355},
        {"name": "0000002.mp3", "duration": 183},
        {"name": "0000003.mp3", "duration": 390}
    ]
}

# Endpoints


columns = [
    {"field_name": "id", "type": "INT"},
    {"field_name": "title", "type": "VARCHAR(100)"},
    {"field_name": "sound_file", "type": "SOUND"},
    {"field_name": "artist", "type": "VARCHAR(100)"},
    {"field_name": "duration", "type": "VARCHAR(10)"},
    {"field_name": "genre", "type": "VARCHAR(50)"},
    {"field_name": "description", "type": "TEXT"}
]

rows = [
    {
        "id": 1,
        "title": "Bohemian Rhapsody",
        "sound_file": "swift-valkyrie.mp3",
        "artist": "Queen",
        "duration": "5:55",
        "genre": "Rock",
        "description": "Una obra maestra del rock progresivo que combina elementos de ópera, balada y hard rock. Escrita por Freddie Mercury, es considerada una de las mejores canciones de todos los tiempos por su estructura única y complejidad musical."
    },
    {
        "id": 2,
        "title": "Imagine",
        "sound_file": "000002.mp3",
        "artist": "John Lennon",
        "duration": "3:03",
        "genre": "Pop",
        "description": "Una canción icónica sobre la paz mundial y la unidad. John Lennon invita a imaginar un mundo sin divisiones religiosas, políticas o nacionales, convirtiéndose en un himno para la paz."
    },
    {
        "id": 3,
        "title": "Hotel California",
        "sound_file": "000003.mp3",
        "artist": "Eagles",
        "duration": "6:30",
        "genre": "Rock",
        "description": "Una enigmática canción que narra la historia de un viajero que se detiene en un lujoso pero misterioso hotel del que aparentemente no puede escapar. Famosa por su memorable solo de guitarra final."
    }
]
