'use client';

import { useState } from 'react';
import { FileAudio, Loader2, Play, Plus, RefreshCw, Music2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { AudioPlayerDialog } from './audio-player-dialog';
import { UploadAudioDialog } from './upload-audio-dialog';
import type { AudioFile } from '@/lib/types';
import { useToast } from '@/hooks/use-toast';

interface AudioPanelProps {
  audioFiles: AudioFile[];
  num_sounds: number;
  onRefresh: () => Promise<void>;
}

export function AudioPanel({ audioFiles, num_sounds,onRefresh }: AudioPanelProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [playingFile, setPlayingFile] = useState<string | null>(null);
  const { toast } = useToast();


  const handleRefresh = async () => {
    setIsRefreshing(true);
    await onRefresh();
    setIsRefreshing(false);
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const onUploadSuccess = () => {
    toast({
      title: "Upload Successful",
      description: "Your audio file has been added.",
    });
    handleRefresh();
  }

  return (
    <>
      <Card className="h-full flex flex-col bg-card/50 border-border/50">
        <CardHeader className="flex flex-row items-center justify-between py-3 px-4 border-b border-border/50">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <Music2 className="h-5 w-5 text-primary" />
            <span>Audio Library</span>
            <span className="text-sm text-muted-foreground">({num_sounds} sound)</span>
          </CardTitle>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="icon" onClick={() => setIsUploadOpen(true)} aria-label="Add audio">
              <Plus className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={handleRefresh} disabled={isRefreshing} aria-label="Refresh audio files">
              {isRefreshing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0 flex-1 min-h-0">
          <ScrollArea className="h-full">
            <div className="p-2 space-y-1">
              {audioFiles.length === 0 && !isRefreshing ? (
                <div className="text-center text-muted-foreground p-4 text-sm">No audio files found.</div>
              ) : (isRefreshing ? (
                Array.from({ length: 5 }).map((_, i) => <AudioItemSkeleton key={i} />)
              ) : (
                audioFiles.map((file) => (
                  <div key={file.name} className="flex items-center justify-between p-2 rounded-md hover:bg-secondary/50 group transition-colors">
                    <div className="flex items-center gap-3">
                      <FileAudio className="h-5 w-5 text-primary/80" />
                      <div className="flex flex-col">
                        <span className="text-sm font-medium max-w-[150px] truncate">{file.name}</span>
                        <span className="text-xs text-muted-foreground">{formatDuration(file.duration)}</span>
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" className="opacity-0 group-hover:opacity-100 transition-opacity" onClick={() => setPlayingFile(file.name)} aria-label={`Play ${file.name}`}>
                      <Play className="h-4 w-4 text-primary" />
                    </Button>
                  </div>
                ))
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
      <AudioPlayerDialog fileName={playingFile} onOpenChange={(open) => !open && setPlayingFile(null)} />
      <UploadAudioDialog 
        isOpen={isUploadOpen} 
        onOpenChange={setIsUploadOpen} 
        onUploadSuccess={onUploadSuccess}
      />
    </>
  );
}

function AudioItemSkeleton() {
    return (
        <div className="flex items-center gap-3 p-2">
            <Skeleton className="h-5 w-5 rounded" />
            <div className="flex flex-col gap-1 flex-1">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/4" />
            </div>
        </div>
    )
}
