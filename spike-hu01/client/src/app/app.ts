import { Component, OnDestroy, signal } from '@angular/core';
import { RemoteTrack, Room, RoomEvent, Track } from 'livekit-client';

type Estado = 'desconectado' | 'conectando' | 'conectado';

/**
 * Cliente mínimo del spike HU-01 (no productivo).
 * Conecta a una sala de LiveKit, publica el micrófono y reproduce el audio remoto.
 * La URL y el token se pegan en la pantalla: nada sensible queda en el código.
 */
@Component({
  selector: 'app-root',
  template: `
    <main>
      <h1>Spike HU-01 · Sala de prueba</h1>

      <label>URL del proyecto <input #url placeholder="wss://..." /></label>
      <label>Token <input #token /></label>

      <button (click)="conectar(url.value, token.value)" [disabled]="estado() !== 'desconectado'">
        Entrar a la sala
      </button>
      <button (click)="salir()" [disabled]="estado() !== 'conectado'">Salir de la sala</button>

      <p>Estado: {{ estado() }}</p>
      @if (error()) {
        <p class="error">{{ error() }}</p>
      }

      <h2>En la sala</h2>
      <ul>
        @for (p of participantes(); track p) {
          <li>{{ p }}</li>
        } @empty {
          <li>Nadie todavía.</li>
        }
      </ul>
    </main>
  `,
  styles: `
    main { font-family: system-ui, sans-serif; max-width: 36rem; margin: 2rem auto; display: grid; gap: 0.75rem; }
    label { display: grid; gap: 0.25rem; }
    input { padding: 0.4rem; font: inherit; }
    .error { color: #b00020; }
  `,
})
export class App implements OnDestroy {
  private readonly room = new Room();

  readonly estado = signal<Estado>('desconectado');
  readonly participantes = signal<string[]>([]);
  readonly error = signal<string | null>(null);

  constructor() {
    this.room
      .on(RoomEvent.TrackSubscribed, (track: RemoteTrack) => {
        if (track.kind === Track.Kind.Audio) {
          document.body.appendChild(track.attach());
        }
      })
      .on(RoomEvent.TrackUnsubscribed, (track: RemoteTrack) => {
        track.detach().forEach((el) => el.remove());
      })
      .on(RoomEvent.ParticipantConnected, () => this.actualizarParticipantes())
      .on(RoomEvent.ParticipantDisconnected, () => this.actualizarParticipantes())
      .on(RoomEvent.Disconnected, () => {
        this.estado.set('desconectado');
        this.participantes.set([]);
      });
  }

  async conectar(url: string, token: string): Promise<void> {
    this.error.set(null);
    this.estado.set('conectando');
    try {
      await this.room.connect(url.trim(), token.trim());
      // Se llama dentro del clic para que el navegador permita reproducir audio.
      await this.room.startAudio();
      await this.room.localParticipant.setMicrophoneEnabled(true);
      this.estado.set('conectado');
      this.actualizarParticipantes();
    } catch (e) {
      this.error.set(`No se pudo entrar a la sala: ${e instanceof Error ? e.message : String(e)}`);
      await this.room.disconnect();
      this.estado.set('desconectado');
    }
  }

  async salir(): Promise<void> {
    await this.room.disconnect();
  }

  private actualizarParticipantes(): void {
    const remotos = [...this.room.remoteParticipants.values()].map((p) => p.identity);
    this.participantes.set([`${this.room.localParticipant.identity} (tú)`, ...remotos]);
  }

  ngOnDestroy(): void {
    void this.room.disconnect();
  }
}
