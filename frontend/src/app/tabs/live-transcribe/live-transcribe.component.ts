import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { Subscription } from 'rxjs';
import { LanguageStateService } from '../../core/language-state.service';
import { WsService } from '../../core/ws.service';
import { WsChunkResponse } from '../../core/models';
import { MicService } from './mic.service';

interface ChunkRow extends WsChunkResponse {
  ts: string;
}

@Component({
  selector: 'app-live-transcribe',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatProgressBarModule,
  ],
  templateUrl: './live-transcribe.component.html',
  styleUrl: './live-transcribe.component.scss',
})
export class LiveTranscribeComponent {
  state = inject(LanguageStateService);
  private mic = inject(MicService);
  private ws = inject(WsService);

  recording = signal(false);
  level = signal(0);
  rows = signal<ChunkRow[]>([]);
  error = signal<string | null>(null);

  private subs: Subscription[] = [];

  async toggle() {
    if (this.recording()) {
      await this.stop();
    } else {
      await this.start();
    }
  }

  async start() {
    this.error.set(null);
    this.rows.set([]);
    try {
      const ack = await this.ws.open(this.state.selectedIso(), this.state.target());
      if (!ack.ok) {
        this.error.set(ack.error ?? 'handshake failed');
        return;
      }
      this.subs.push(
        this.mic.chunks$.subscribe((buf) => {
          try {
            this.ws.sendChunk(buf);
          } catch (e: any) {
            this.error.set(e.message);
          }
        }),
      );
      this.subs.push(this.mic.level$.subscribe((l) => this.level.set(l)));
      this.subs.push(
        this.ws.chunks$.subscribe((c) => {
          this.rows.update((rs) => [
            ...rs,
            { ...c, ts: new Date().toISOString().slice(11, 19) },
          ]);
        }),
      );
      await this.mic.start();
      this.recording.set(true);
    } catch (e: any) {
      this.error.set(e.message ?? 'mic/ws start failed');
    }
  }

  async stop() {
    await this.mic.stop();
    this.ws.close();
    this.subs.forEach((s) => s.unsubscribe());
    this.subs = [];
    this.recording.set(false);
    this.level.set(0);
  }
}
