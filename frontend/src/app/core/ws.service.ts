import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';
import { TranslationTarget, WsChunkResponse } from './models';

export interface WsHandshakeAck {
  ok: boolean;
  error?: string;
  lang?: string;
  target?: TranslationTarget;
}

@Injectable({ providedIn: 'root' })
export class WsService {
  private socket: WebSocket | null = null;
  private chunkSeq = 0;

  readonly chunks$ = new Subject<WsChunkResponse>();
  readonly status$ = new Subject<'open' | 'closed' | 'error' | 'handshake-ok' | 'handshake-fail'>();

  open(lang: string, target: TranslationTarget): Promise<WsHandshakeAck> {
    this.close();
    return new Promise((resolve, reject) => {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws';
      const url = `${proto}://${location.host}/api/ws/transcribe`;
      const s = new WebSocket(url);
      this.socket = s;

      s.onopen = () => {
        s.send(JSON.stringify({ lang, target }));
      };
      s.onmessage = (ev) => {
        let msg: any;
        try {
          msg = JSON.parse(ev.data);
        } catch {
          return;
        }
        if (typeof msg.ok === 'boolean') {
          if (msg.ok) this.status$.next('handshake-ok');
          else this.status$.next('handshake-fail');
          resolve(msg as WsHandshakeAck);
          return;
        }
        this.chunks$.next(msg as WsChunkResponse);
      };
      s.onerror = () => {
        this.status$.next('error');
        reject(new Error('ws error'));
      };
      s.onclose = () => {
        this.status$.next('closed');
      };
    });
  }

  sendChunk(pcm: ArrayBuffer): number {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error('ws not open');
    }
    const id = ++this.chunkSeq;
    this.socket.send(JSON.stringify({ chunk_id: id }));
    this.socket.send(pcm);
    return id;
  }

  close() {
    if (this.socket) {
      try {
        this.socket.close();
      } catch {
        /* noop */
      }
      this.socket = null;
    }
    this.chunkSeq = 0;
  }
}
