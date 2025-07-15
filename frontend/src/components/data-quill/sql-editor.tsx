'use client';

import { useState, forwardRef, useImperativeHandle, useRef } from 'react';
import { Play, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Editor, { type OnMount } from "@monaco-editor/react";
import type { editor } from "monaco-editor";

interface SqlEditorProps {
  onRunQuery: (query: string) => void;
  isQueryRunning: boolean;
}

export interface SqlEditorHandle {
  layout: () => void;
}

const defaultQuery = "SELECT * FROM songs LIMIT 10;";

export const SqlEditor = forwardRef<SqlEditorHandle, SqlEditorProps>(
  ({ onRunQuery, isQueryRunning }, ref) => {
    const [query, setQuery] = useState(defaultQuery);
    const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);

    const handleEditorDidMount: OnMount = (editor) => {
      editorRef.current = editor;
    };

    useImperativeHandle(ref, () => ({
      layout: () => {
        editorRef.current?.layout();
      },
    }));

    const handleRunQuery = () => {
      if (editorRef.current) {
        onRunQuery(editorRef.current.getValue());
      }
    };

    return (
      <Card className="h-full flex flex-col bg-card/50 border-border/50">
        <CardHeader className="flex flex-row items-center justify-between py-3 px-4 border-b border-border/50">
          <CardTitle className="text-lg font-semibold">SQL Editor</CardTitle>
          <Button
            onClick={handleRunQuery}
            disabled={isQueryRunning || !query.trim()}
            className="bg-primary hover:bg-primary/90 text-primary-foreground"
            aria-label="Run Query"
          >
            {isQueryRunning ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Play className="mr-2 h-4 w-4" />
            )}
            Run Query
          </Button>
        </CardHeader>
        <CardContent className="p-0 flex-1 relative">
           <Editor
            height="100%"
            defaultLanguage="sql"
            defaultValue={defaultQuery}
            theme="vs-dark"
            onMount={handleEditorDidMount}
            onChange={(value) => setQuery(value || "")}
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              wordWrap: 'on',
              scrollBeyondLastLine: false,
              automaticLayout: true,
            }}
          />
        </CardContent>
      </Card>
    );
  }
);

SqlEditor.displayName = 'SqlEditor';
