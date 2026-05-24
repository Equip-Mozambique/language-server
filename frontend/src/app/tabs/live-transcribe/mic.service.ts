import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

/**
 * Captures mic at 16 kHz mono, emits PCM-int16 chunks every CHUNK_SECONDS.
 *
 * v1 uses AudioContext + ScriptProcessorNode (deprecated but universal).
 * v2 should switch to @ricky0123/vad-web for silero-vad-based segmentation.
 */
@Injectable({ providedIn: 'root' })
export class MicService {
  readonly chunks$ = new Subject<ArrayBuffer>();
  readonly level$ = new Subject<number>();

  private ctx: AudioContext | null = null;
  private stream: MediaStream | null = null;
  private processor: ScriptProcessorNode | null = null;
  private buffer: number[] = [];
  private chunkSamples = 0;

  static readonly TARGET_SR = 16_000;
  static readonly CHUNK_SECONDS = 4;

  async start(): Promise<void> {
    if (this.ctx) return;

    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, sampleRate: MicService.TARGET_SR } as MediaTrackConstraints,
    });

    // Some browsers refuse a forced sampleRate. We resample on the fly if needed.
    const ctx = new AudioContext();
    this.ctx = ctx;
    this.chunkSamples = MicService.TARGET_SR * MicService.CHUNK_SECONDS;

    const src = ctx.createMediaStreamSource(this.stream);
    const bufferSize = 4096;
    const sp = ctx.createScriptProcessor(bufferSize, 1, 1);
    this.processor = sp;

    const ratio = ctx.sampleRate / MicService.TARGET_SR;

    sp.onaudioprocess = (e) => {
      const input = e.inputBuffer.getChannelData(0);

      // RMS level for UI viz
      let acc = 0;
      for (let i = 0; i < input.length; i++) acc += input[i] * input[i];
      this.level$.next(Math.sqrt(acc / input.length));

      // Linear-interp downsample → TARGET_SR
      const outLen = Math.floor(input.length / ratio);
      for (let i = 0; i < outLen; i++) {
        const idx = i * ratio;
        const lo = Math.floor(idx);
        const hi = Math.min(lo + 1, input.length - 1);
        const t = idx - lo;
        this.buffer.push(input[lo] * (1 - t) + input[hi] * t);
      }

      while (this.buffer.length >= this.chunkSamples) {
        const slice = this.buffer.splice(0, this.chunkSamples);
        const pcm = new Int16Array(slice.length);
        for (let i = 0; i < slice.length; i++) {
          const s = Math.max(-1, Math.min(1, slice[i]));
          pcm[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
        }
        this.chunks$.next(pcm.buffer);
      }
    };

    src.connect(sp);
    sp.connect(ctx.destination);
  }

  async stop(): Promise<void> {
    if (this.processor) {
      try {
        this.processor.disconnect();
      } catch {
        /* noop */
      }
      this.processor = null;
    }
    if (this.stream) {
      this.stream.getTracks().forEach((t) => t.stop());
      this.stream = null;
    }
    if (this.ctx) {
      await this.ctx.close();
      this.ctx = null;
    }
    this.buffer = [];
  }
}
