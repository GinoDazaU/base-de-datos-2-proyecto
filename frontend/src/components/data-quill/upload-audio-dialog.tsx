'use client';

import { useState, type ChangeEvent, type FormEvent, useRef } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { uploadAudioFile } from '@/lib/api';
import { Loader2, UploadCloud, FileMusic } from 'lucide-react';
import { motion } from 'framer-motion';

interface UploadAudioDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onUploadSuccess: () => void;
}

export function UploadAudioDialog({ isOpen, onOpenChange, onUploadSuccess }: UploadAudioDialogProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      toast({
        variant: 'destructive',
        title: 'No file selected',
        description: 'Please select an audio file to upload.',
      });
      return;
    }

    setIsUploading(true);
    try {
      await uploadAudioFile(selectedFile);
      onUploadSuccess();
      onOpenChange(false);
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Upload failed',
        description: 'Could not upload the audio file. Please try again.',
      });
    } finally {
      setIsUploading(false);
    }
  };
  
  const handleOpenChange = (open: boolean) => {
    if (!open) {
      setSelectedFile(null);
      setIsUploading(false);
    }
    onOpenChange(open);
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="bg-gradient-to-br from-background to-secondary/30 border-primary/20">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UploadCloud className="text-primary"/>
            Upload Audio File
          </DialogTitle>
          <DialogDescription className="pt-1">
            Add a new MP3 audio file to your library.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="mt-4 space-y-6">
            <div 
              className="relative border-2 border-dashed border-border/50 rounded-lg p-8 flex flex-col items-center justify-center text-center cursor-pointer hover:border-primary/50 transition-colors"
              onClick={() => fileInputRef.current?.click()}
            >
                <FileMusic className="h-10 w-10 text-muted-foreground" />
                <p className="mt-2 text-sm text-muted-foreground">
                  {selectedFile ? 'File selected:' : 'Click or drag file to this area to upload'}
                </p>
                {selectedFile && (
                  <p className="font-medium text-foreground mt-1 truncate max-w-full px-4">{selectedFile.name}</p>
                )}
                <Input 
                  ref={fileInputRef}
                  id="audio-file" 
                  type="file" 
                  accept="audio/mpeg" 
                  onChange={handleFileChange}
                  className="sr-only"
                />
            </div>
            <DialogFooter>
                <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isUploading}>
                    Cancel
                </Button>
                <Button type="submit" disabled={!selectedFile || isUploading} className="bg-primary hover:bg-primary/90 text-primary-foreground">
                    {isUploading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <UploadCloud className="mr-2 h-4 w-4" />}
                    Upload
                </Button>
            </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
