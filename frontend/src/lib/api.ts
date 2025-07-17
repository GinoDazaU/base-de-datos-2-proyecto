import type { Schema, QueryResult, AudioFile, AudioFileList } from './types';
import axios from "axios";

// Usa variables de entorno de Next.js
// NEXT_PUBLIC_API_URL es accesible tanto en el cliente como en el servidor
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"; 

const api = axios.create({ baseURL: API_URL });

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

let mockAudioFiles: AudioFile[] = [
    { name: "inspiring-cinematic-ambient.mp3", duration: 185 },
    { name: "corporate-uplifting.mp3", duration: 240 },
    { name: "electronic-modern-vlog.mp3", duration: 135 },
];

export const getSchema = async (): Promise<Schema> => {
    try {
        const response = await api.get(`/schema`)
        return response.data
    
    } catch (error) {
        return {
            db: "Sales DB",
            tables: []
        };
    }
    /*
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
    };*/
};

export const runQuery = async (query: string): Promise<QueryResult> => {
    const response = await api.post(`/query`,{consulta:query})
    return response.data 
};

export const getAudioFiles = async (): Promise<AudioFileList> => {
    try {
        const response = await api.get(`/audio-files`)
        return response.data
    
    } catch (error) {
        return {
            file_sounds: [],
            num_sounds:0,
        };
    }
};
export const getSoundFile = async (fileName: string): Promise<string> => {
    return `http://localhost:8000/audio?file_name=${encodeURIComponent(fileName)}`;
};

export const uploadAudioFile = async (file: File): Promise<{ success: boolean; file: AudioFile }> => {
    const formData = new FormData();
    formData.append("file", file);  // El campo debe llamarse igual que en FastAPI: "file"

    const response = await api.post("/upload-audio", formData, {
        headers: {
            "Content-Type": "multipart/form-data"
        }
    });
    return response.data; 
};
