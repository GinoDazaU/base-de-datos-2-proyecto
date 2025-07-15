export interface Field {
  name: string;
  type: string;
  is_primary_key: boolean;
}

export interface Index {
  field_name: string;
  type: string;
}

export interface Table {
  table_name: string;
  fields: Field[];
  indexes: Index[];
}

export interface Schema {
  db: string;
  tables: Table[];
}

export interface Column {
  field_name: string;
  type: string;
}

export interface QueryResult {
  columns: Column[];
  rows: Record<string, any>[];
  message: string;
  count_rows: number;
  time_execution: number;
}

export interface AudioFile {
  name: string;
  duration: number;
}

export interface AudioFileList {
    file_sounds: AudioFile[];
}
