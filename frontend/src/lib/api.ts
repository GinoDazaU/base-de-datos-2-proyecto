import type { Schema, QueryResult, AudioFile, AudioFileList } from './types';

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

let mockAudioFiles: AudioFile[] = [
    { name: "inspiring-cinematic-ambient.mp3", duration: 185 },
    { name: "corporate-uplifting.mp3", duration: 240 },
    { name: "electronic-modern-vlog.mp3", duration: 135 },
];

export const getSchema = async (): Promise<Schema> => {
    await sleep(500);
    return {
        db: "Sales DB",
        tables: [
            {
                table_name: "songs",
                fields: [
                    { name: "id", type: "INT", is_primary_key: true },
                    { name: "title", type: "VARCHAR(100)", is_primary_key: false },
                    { name: "sound_file", type: "SOUND", is_primary_key: false },
                    { name: "artist", type: "VARCHAR(100)", is_primary_key: false },
                    { name: "duration", type: "VARCHAR(10)", is_primary_key: false },
                    { name: "genre", type: "VARCHAR(50)", is_primary_key: false },
                    { name: "description", type: "TEXT", is_primary_key: false },
                ],
                indexes: [
                    { field_name: "id", type: "btree" }
                ]
            },
            {
                table_name: "artists",
                fields: [
                    { name: "id", type: "INT", is_primary_key: true },
                    { name: "name", type: "VARCHAR(100)", is_primary_key: false },
                ],
                indexes: [
                    { field_name: "id", type: "btree" }
                ]
            }
        ]
    };
};

export const runQuery = async (query: string): Promise<QueryResult> => {
    await sleep(1000);

    if (query.toLowerCase().includes("error")) {
        throw new Error("Syntax error in SQL query near 'error'.");
    }
    
    return {
        columns: [
            { field_name: 'id', type: "INT" },
            { field_name: 'title', type: "VARCHAR(50)" },
            { field_name: 'sound_file', type: "SOUND" },
            { field_name: 'description', type: "TEXT" },
        ],
        rows: [
            { id: 1, title: 'Inspiring Cinematic Ambient', sound_file: 'inspiring-cinematic-ambient.mp3', description: "This is a very long description designed to test the truncation and popup functionality. The purpose of this lengthy text is to ensure that the user interface correctly displays an ellipsis ('...') and provides a way for the user to view the full content in a separate dialog or modal window upon clicking it." },
            { id: 2, title: 'Corporate Uplifting', sound_file: 'corporate-uplifting.mp3', description: "A shorter description that should not be truncated." },
            { id: 3, title: 'Electronic Modern Vlog', sound_file: 'electronic-modern-vlog.mp3', description: "This track is perfect for modern video blogs and presentations that require an energetic and contemporary soundtrack." },
        ],
        message: "Query executed successfully.",
        count_rows: 3,
        time_execution: 123
    };
};

export const getAudioFiles = async (): Promise<AudioFileList> => {
    await sleep(300);
    return {
        file_sounds: [...mockAudioFiles],
    };
};

export const getSoundFile = async (fileName: string): Promise<string> => {
    await sleep(200);
    // In a real app, this would return a Blob URL or a stream. For this mock,
    // we return a placeholder audio URL. These are royalty-free.
    switch(fileName) {
        case 'inspiring-cinematic-ambient.mp3':
            return `https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Les_Patineurs/Inspiring_Cinematic_Ambient/Les_Patineurs_-_01_-_Inspiring_Cinematic_Ambient.mp3`;
        case 'corporate-uplifting.mp3':
            return `https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Scott_Holmes/Corporate__Uplifting/Scott_Holmes_-_10_-_Corporate__Uplifting.mp3`;
        case 'electronic-modern-vlog.mp3':
            return `https://files.freemusicarchive.org/storage-freemusicarchive-org/music/no_curator/Alex-Productions/Electronic_Modern_Vlog/Alex-Productions_-_02_-_Electronic_Modern_Vlog.mp3`;
        default:
            // Placeholder for newly uploaded files
            return `https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3`;
    }
};

export const uploadAudioFile = async (file: File): Promise<{ success: boolean; file: AudioFile }> => {
    await sleep(1500);
    const newFile: AudioFile = { name: file.name, duration: Math.floor(Math.random() * 200) + 60 };
    mockAudioFiles.unshift(newFile);
    return { success: true, file: newFile };
};
