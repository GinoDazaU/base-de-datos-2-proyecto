'use client';

import { useEffect, useState, useRef } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { getSoundFile } from '@/lib/api';
import { Loader2, Music4, Disc3 } from 'lucide-react';
import { motion } from 'framer-motion';

interface AudioPlayerDialogProps {
  fileName: string | null;
  onOpenChange: (open: boolean) => void;
}

export function AudioPlayerDialog({ fileName, onOpenChange }: AudioPlayerDialogProps) {
  const [audioSrc, setAudioSrc] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    if (fileName) {
      setIsLoading(true);
      setError(null);
      setAudioSrc(null);
      setIsPlaying(false);
      getSoundFile(fileName)
        .then(setAudioSrc)
        .catch(() => setError('Failed to load audio file.'))
        .finally(() => setIsLoading(false));
    }
  }, [fileName]);
  
  useEffect(() => {
    const audioElement = audioRef.current;
    if (!audioElement) return;

    const onPlay = () => setIsPlaying(true);
    const onPause = () => setIsPlaying(false);
    
    audioElement.addEventListener('play', onPlay);
    audioElement.addEventListener('pause', onPause);
    
    // Set initial state
    setIsPlaying(!audioElement.paused);
    
    return () => {
      audioElement.removeEventListener('play', onPlay);
      audioElement.removeEventListener('pause', onPause);
    };
  }, [audioSrc]);

  const isOpen = fileName !== null;

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="bg-gradient-to-br from-background to-secondary/30 border-primary/20 sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-primary">
            <Music4 />
            Now Playing
          </DialogTitle>
          <DialogDescription className="truncate max-w-full pt-1">
            {fileName || '...'}
          </DialogDescription>
        </DialogHeader>
        <div className="mt-4 flex flex-col items-center justify-center gap-6 py-4">
          <motion.div
            className="relative"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1, type: 'spring', stiffness: 200 }}
          >
            <Disc3
              className={`h-40 w-40 text-primary/30 transition-transform duration-300 ${isPlaying ? 'animate-[spin_4s_linear_infinite]' : ''}`}
            />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="h-10 w-10 rounded-full bg-primary/90 shadow-lg"></div>
            </div>
             <div className="absolute inset-0 flex items-center justify-center">
              <div className="h-4 w-4 rounded-full bg-background border-2 border-primary/50"></div>
            </div>
          </motion.div>

          <div className="w-full h-20 flex items-center justify-center">
            {isLoading && <Loader2 className="h-8 w-8 animate-spin text-primary" />}
            {error && <p className="text-destructive">{error}</p>}
            {audioSrc && !isLoading && (
              <audio
                ref={audioRef}
                controls
                autoPlay
                className="w-full"
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
              >
                <source src={audioSrc} type="audio/mpeg" />
                Your browser does not support the audio element.
              </audio>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
