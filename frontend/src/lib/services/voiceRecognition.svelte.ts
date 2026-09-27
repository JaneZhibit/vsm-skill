import { playClickSound, playErrorSound } from '../utils/audio';

export class VoiceRecognitionService {
  isRecording = $state<boolean>(false);
  recordingSeconds = $state<number>(0);
  micError = $state<string | null>(null);

  finalTranscript = $state<string>('');
  interimTranscript = $state<string>('');

  private recognition: any = null;
  private recordingTimer: ReturnType<typeof setInterval> | null = null;

  public start() {
    this.micError = null;
    this.finalTranscript = '';
    this.interimTranscript = '';

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      this.micError = 'Браузер не поддерживает распознавание речи.';
      playErrorSound();
      return;
    }

    if (!this.recognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.lang = 'ru-RU';
      this.recognition.continuous = true;
      this.recognition.interimResults = true;

      this.recognition.onresult = (event: any) => {
        let interim = '';
        let final = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) final += transcript + ' ';
          else interim += transcript;
        }
        this.finalTranscript += final;
        this.interimTranscript = interim;
      };

      this.recognition.onerror = (event: any) => {
        if (event.error === 'not-allowed') this.micError = 'Доступ к микрофону запрещен.';
      };

      this.recognition.onend = () => {
        if (this.isRecording) {
          try { this.recognition.start(); } catch(e) {}
        }
      };
    }

    try {
      this.recognition.start();
      this.isRecording = true;
      this.recordingSeconds = 0;
      this.recordingTimer = setInterval(() => this.recordingSeconds++, 1000);
      playClickSound();
    } catch (err) {
      this.micError = 'Не удалось запустить микрофон.';
    }
  }

  public stop(): string {
    if (this.isRecording) {
      this.isRecording = false;
      if (this.recordingTimer) clearInterval(this.recordingTimer);
      if (this.recognition) {
        try { this.recognition.stop(); } catch(e) {}
      }
      playClickSound();
    }
    return (this.finalTranscript + ' ' + this.interimTranscript).trim();
  }

  public reset() {
    this.stop();
    this.micError = null;
    this.finalTranscript = '';
    this.interimTranscript = '';
  }
}

export const voiceRecognition = new VoiceRecognitionService();