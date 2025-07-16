# **App Name**: DataQuill

## Core Features:

- Schema Explorer: Display a schema explorer panel that GETs a database schema and visualizes the tables, fields and indexes. The panel will include a refresh button to AVANZA ESTO re-fetching the schema.
- SQL Editor: Implement an SQL editor using Monaco Editor, allowing users to write and edit SQL queries.
- Query Execution and Results: Implement a 'Run Query' button that POSTs the SQL query and displays the tabular results (columns and rows). If any TEXT field size is too long then it includes a '...' button that on press opens a popup to show full content.
- SOUND Data Type: Handle SOUND file types. The Result area's tabular rows should use a button to allow the file sounds to play.
- Audio Panel: Display an audio panel with the list of available sound files GET from an API endpoint.
- Audio Management: In Audio Panel Implement 'Update' button which GETs data and implement a '+' button, with an upload function when pressing the + button to AVANZA ESTO adds audio with POST multipar and updates list of all audios .

## Style Guidelines:

- Primary color: Deep blue (#1A237E) to convey a sense of authority and intelligence.
- Background color: Dark grey (#212121) for a professional look and to reduce eye strain during extended use.
- Accent color: Teal (#008080) to provide contrast and highlight interactive elements, as in the Run Query button.
- Body and headline font: 'Inter', a grotesque-style sans-serif, providing a modern, neutral, and readable feel.
- Code font: 'Source Code Pro' for the SQL editor and displaying any code snippets.
- Use minimalist icons for database elements and controls, ensuring clarity and ease of use.
- Use subtle animations to signal loading states and transitions.