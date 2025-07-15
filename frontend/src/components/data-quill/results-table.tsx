'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { AlertTriangle, DatabaseZap, MoreHorizontal, Play } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { Skeleton } from '../ui/skeleton';
import { LongTextDialog } from './long-text-dialog';
import { AudioPlayerDialog } from './audio-player-dialog';
import type { QueryResult } from '@/lib/types';
import { cn } from '@/lib/utils';

interface ResultsTableProps {
  result: QueryResult | null;
  isLoading: boolean;
  error: string | null;
}

const MAX_TEXT_LENGTH = 50;
const MIN_COL_WIDTH = 50;
const DEFAULT_COL_WIDTH = 150;

export function ResultsTable({ result, isLoading, error }: ResultsTableProps) {
  const [longTextContent, setLongTextContent] = useState<string | null>(null);
  const [audioFile, setAudioFile] = useState<string | null>(null);
  const [colWidths, setColWidths] = useState<Record<string, number>>({});
  
  const tableRef = useRef<HTMLTableElement>(null);
  const resizingColIndex = useRef<number | null>(null);
  const startX = useRef(0);
  const startWidth = useRef(0);

  useEffect(() => {
    if (result?.columns) {
      const initialWidths = result.columns.reduce((acc, col) => {
        acc[col.field_name] = DEFAULT_COL_WIDTH;
        return acc;
      }, {} as Record<string, number>);
      setColWidths(initialWidths);
    }
  }, [result?.columns]);

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>, index: number) => {
    resizingColIndex.current = index;
    startX.current = e.clientX;
    const th = e.currentTarget.parentElement;
    if (th) {
        startWidth.current = th.offsetWidth;
    }
    document.body.classList.add('resizing');
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (resizingColIndex.current === null || !result?.columns) return;

    const newWidth = startWidth.current + e.clientX - startX.current;
    if (newWidth > MIN_COL_WIDTH) {
      const colName = result.columns[resizingColIndex.current].field_name;
      setColWidths(prev => ({
        ...prev,
        [colName]: newWidth,
      }));
    }
  }, [result?.columns]);

  const handleMouseUp = useCallback(() => {
    resizingColIndex.current = null;
    document.body.classList.remove('resizing');
    window.removeEventListener('mousemove', handleMouseMove);
    window.removeEventListener('mouseup', handleMouseUp);
  }, [handleMouseMove]);
  

  const renderCellContent = (row: Record<string, any>, column: { field_name: string; type: string }) => {
    const content = row[column.field_name];

    if (content === null || content === undefined) {
      return <span className="text-muted-foreground/50 italic">NULL</span>;
    }

    if (column.type === 'SOUND') {
      return (
        <Button variant="ghost" size="icon" onClick={() => setAudioFile(content)} aria-label={`Play ${content}`}>
          <Play className="h-4 w-4 text-primary" />
        </Button>
      );
    }

    if (column.type === 'TEXT' && typeof content === 'string' && content.length > MAX_TEXT_LENGTH) {
      return (
        <div className="flex items-center gap-2">
          <span className="font-code">{`${content.substring(0, MAX_TEXT_LENGTH)}...`}</span>
          <Button variant="ghost" size="icon" onClick={() => setLongTextContent(content)} aria-label="View full text">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </div>
      );
    }

    return <span className="font-code">{String(content)}</span>;
  };
  
  const tableWidth = result ? Object.values(colWidths).reduce((sum, width) => sum + width, 0) : '100%';

  const renderContent = () => {
    if (isLoading) {
      return <ResultsSkeleton />;
    }

    if (error) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-destructive p-4">
          <AlertTriangle className="h-12 w-12 mb-4" />
          <p className="text-lg font-semibold">Query Failed</p>
          <p className="font-code bg-destructive/10 p-2 rounded-md mt-2 text-sm">{error}</p>
        </div>
      );
    }

    if (!result) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-muted-foreground p-4">
          <DatabaseZap className="h-12 w-12 mb-4 text-primary/50" />
          <p className="text-lg font-semibold">No results</p>
          <p>Run a query to see the results here.</p>
        </div>
      );
    }
    
    return (
      <>
        <ScrollArea className="flex-1" type="always">
          <div className="table-container">
            <Table ref={tableRef} className="resizable-table" style={{ width: tableWidth }}>
              <colgroup>
                {result.columns.map(col => (
                  <col key={col.field_name} style={{ width: colWidths[col.field_name] }} />
                ))}
              </colgroup>
              <TableHeader className="sticky top-0 bg-card z-10 border-b border-border/50">
                <TableRow>
                  {result.columns.map((col, index) => (
                    <TableHead key={col.field_name} className="relative">
                      {col.field_name}
                      <div
                        className="resizable-handle"
                        onMouseDown={(e) => handleMouseDown(e, index)}
                      />
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {result.rows.map((row, index) => (
                  <TableRow key={index} className="border-border/50">
                    {result.columns.map((col) => (
                      <TableCell key={col.field_name}>
                        {renderCellContent(row, col)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <ScrollBar orientation="horizontal" />
        </ScrollArea>
        <CardFooter className="py-2 px-4 border-t border-border/50 text-xs text-muted-foreground justify-end flex-shrink-0">
            <span>{result.count_rows} rows in {result.time_execution}ms</span>
        </CardFooter>
      </>
    );
  };


  return (
    <>
      <Card className="h-full flex flex-col bg-card/50 border-border/50">
        <CardHeader className="py-3 px-4 border-b border-border/50 flex-shrink-0">
          <CardTitle className="text-lg font-semibold">Result</CardTitle>
          {result && <CardDescription>{result.message}</CardDescription>}
        </CardHeader>
        <CardContent className="p-0 flex-1 flex flex-col min-h-0">
          {renderContent()}
        </CardContent>
      </Card>
      <LongTextDialog content={longTextContent} onOpenChange={(open) => !open && setLongTextContent(null)} />
      <AudioPlayerDialog fileName={audioFile} onOpenChange={(open) => !open && setAudioFile(null)} />
    </>
  );
}

function ResultsSkeleton() {
    return (
        <div className="p-4 space-y-2 h-full">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-[80%]" />
        </div>
    )
}
