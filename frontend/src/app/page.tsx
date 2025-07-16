'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { Database } from 'lucide-react';
import { SchemaExplorer } from '@/components/data-quill/schema-explorer';
import { SqlEditor, type SqlEditorHandle } from '@/components/data-quill/sql-editor';
import { ResultsTable } from '@/components/data-quill/results-table';
import { AudioPanel } from '@/components/data-quill/audio-panel';
import { getAudioFiles, getSchema, runQuery } from '@/lib/api';
import type { QueryResult, Schema, AudioFile } from '@/lib/types';

export default function Home() {
  const [schema, setSchema] = useState<Schema | null>(null);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [audioFiles, setAudioFiles] = useState<AudioFile[]>([]);
  const [isQueryRunning, setIsQueryRunning] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);
  const editorRef = useRef<SqlEditorHandle>(null);

  const fetchSchema = useCallback(async () => {
    const data = await getSchema();
    setSchema(data);
  }, []);

  const fetchAudioFiles = useCallback(async () => {
    const data = await getAudioFiles();
    setAudioFiles(data.file_sounds);
  }, []);

  useEffect(() => {
    fetchSchema();
    fetchAudioFiles();
  }, [fetchSchema, fetchAudioFiles]);

  const handleRunQuery = async (query: string) => {
    setIsQueryRunning(true);
    setQueryError(null);
    setQueryResult(null);
    try {
      const result = await runQuery(query);
      setQueryResult(result);
    } catch (error) {
      if (error instanceof Error) {
        setQueryError(error.message);
      } else {
        setQueryError('An unknown error occurred.');
      }
    } finally {
      setIsQueryRunning(false);
    }
  };

  const handleEditorPanelResize = () => {
    editorRef.current?.layout();
  };

  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      <header className="flex items-center justify-between px-4 py-2 border-b border-border/50">
        <div className="flex items-center gap-2 text-primary">
          <Database className="h-6 w-6" />
          <h1 className="text-xl font-bold tracking-wider">DataQuill</h1>
        </div>
        <div />
      </header>

      <main className="flex-1 overflow-hidden">
        <PanelGroup direction="horizontal" className="h-full">
          <Panel defaultSize={20} minSize={15}>
            <div className="h-full p-2">
              <SchemaExplorer schema={schema} onRefresh={fetchSchema} />
            </div>
          </Panel>
          <PanelResizeHandle className="w-px bg-border/50 hover:bg-primary/50 transition-colors" />
          <Panel defaultSize={55} minSize={30}>
            <PanelGroup direction="vertical">
              <Panel defaultSize={40} minSize={20} onResize={handleEditorPanelResize}>
                <div className="h-full p-2 pl-0">
                  <SqlEditor ref={editorRef} onRunQuery={handleRunQuery} isQueryRunning={isQueryRunning} />
                </div>
              </Panel>
              <PanelResizeHandle className="h-px bg-border/50 hover:bg-primary/50 transition-colors" />
              <Panel defaultSize={60} minSize={20}>
                <div className="h-full p-2 pl-0">
                  <ResultsTable result={queryResult} isLoading={isQueryRunning} error={queryError} />
                </div>
              </Panel>
            </PanelGroup>
          </Panel>
          <PanelResizeHandle className="w-px bg-border/50 hover:bg-primary/50 transition-colors" />
          <Panel defaultSize={25} minSize={15}>
            <div className="h-full p-2">
              <AudioPanel audioFiles={audioFiles} onRefresh={fetchAudioFiles} />
            </div>
          </Panel>
        </PanelGroup>
      </main>
    </div>
  );
}
