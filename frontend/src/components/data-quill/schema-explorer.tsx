'use client';

import { useState } from 'react';
import { Database, Table, Key, FileJson, SigmaSquare, RefreshCw, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import type { Schema } from '@/lib/types';

interface SchemaExplorerProps {
  schema: Schema | null;
  onRefresh: () => Promise<void>;
}

export function SchemaExplorer({ schema, onRefresh }: SchemaExplorerProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await onRefresh();
    setIsRefreshing(false);
  };

  return (
    <Card className="h-full flex flex-col bg-card/50 border-border/50">
      <CardHeader className="flex flex-row items-center justify-between py-3 px-4 border-b border-border/50">
        <CardTitle className="text-lg font-semibold">Schema Explorer</CardTitle>
        <Button variant="ghost" size="icon" onClick={handleRefresh} disabled={isRefreshing} aria-label="Refresh Schema">
          {isRefreshing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
        </Button>
      </CardHeader>
      <CardContent className="p-0 flex-1 min-h-0">
        <ScrollArea className="h-full">
          <div className="p-4">
            {!schema || isRefreshing ? (
              <SchemaSkeleton />
            ) : (
              <div>
                <div className="flex items-center gap-2 mb-4 text-primary">
                  <Database className="h-5 w-5" />
                  <span className="font-semibold text-lg">{schema.db}</span>
                </div>
                <Accordion type="multiple" className="w-full">
                  {schema.tables.map((table) => (
                    <AccordionItem value={table.table_name} key={table.table_name} className="border-border/50">
                      <AccordionTrigger className="text-base hover:no-underline font-medium">
                        <div className="flex items-center gap-2">
                          <Table className="h-4 w-4 text-primary/80" />
                          <span>{table.table_name}</span>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="pl-4">
                        <div className="space-y-2">
                          <p className="text-sm font-medium text-muted-foreground">Fields</p>
                          <ul className="space-y-1.5 pl-4">
                            {table.fields.map((field) => (
                              <li key={field.name} className="flex items-center gap-2 text-sm">
                                {field.is_primary_key ? (
                                  <Key className="h-3.5 w-3.5 text-yellow-400" />
                                ) : (
                                  <FileJson className="h-3.5 w-3.5 text-primary/70" />
                                )}
                                <span className="font-code">{field.name}</span>
                                <span className="text-muted-foreground font-code text-xs">{field.type}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                        {table.indexes.length > 0 && (
                            <div className="space-y-2 mt-4">
                                <p className="text-sm font-medium text-muted-foreground">Indexes</p>
                                <ul className="space-y-1.5 pl-4">
                                    {table.indexes.map((index) => (
                                    <li key={index.field_name} className="flex items-center gap-2 text-sm">
                                        <SigmaSquare className="h-3.5 w-3.5 text-cyan-400" />
                                        <span className="font-code">{index.field_name}</span>
                                        <span className="text-muted-foreground font-code text-xs">({index.type})</span>
                                    </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function SchemaSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Skeleton className="h-6 w-6 rounded-full" />
        <Skeleton className="h-6 w-32" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
        <div className="pl-4 space-y-2 pt-2">
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-1/3" />
        </div>
      </div>
    </div>
  )
}
