'use client';

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';

interface LongTextDialogProps {
  content: string | null;
  onOpenChange: (open: boolean) => void;
}

export function LongTextDialog({ content, onOpenChange }: LongTextDialogProps) {
  const isOpen = content !== null;

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Full Text Content</DialogTitle>
          <DialogDescription>
            The full content of the selected TEXT field.
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="max-h-[60vh] mt-4 p-4 border rounded-md bg-muted/20">
          <pre className="whitespace-pre-wrap break-words font-code text-sm">
            {content}
          </pre>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
