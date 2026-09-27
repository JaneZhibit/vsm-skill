// frontend/src/lib/stores/cabinState.svelte.ts
import { apiFetch } from '../services/api';
import { convertSeatInfoToPassengerSeat, type PassengerSeat, type CabinManifestResponse, type StationEventResponse } from '../config/cabinConfig';
import { conductorState } from './conductorState.svelte';
import { authStore } from './authStore.svelte';

export type PassengerMood = 'empty' | 'calm' | 'annoyed' | 'sleeping' | 'sick' | 'working' | 'drunk';
export type CabinView = 'aisle' | 'seat';

// Изолируем логику работы с бэкендом (Сетевой слой)
class CabinApiHandler {
  constructor(private store: CabinStateStore) {}

  public async loadCabinManifest(): Promise<void> {
    try {
      this.store.isLoadingManifest = true;
      const res = await apiFetch('/api/v1/simulation/cabin-manifest');
      if (res.ok) {
        const data: CabinManifestResponse = await res.json();
        if (data?.seats) this.store.seats = data.seats.map(convertSeatInfoToPassengerSeat);
      }
    } catch (err) { console.warn('Manifest load error:', err); } finally { this.store.isLoadingManifest = false; }
  }

  public async startNewTripManifest(): Promise<void> {
    try {
      this.store.isLoadingManifest = true;
      const res = await apiFetch('/api/v1/simulation/trip/new', { method: 'POST' });
      if (res.ok) {
        const rawData = await res.json();
        const manifest = rawData.manifest || rawData;
        if (manifest?.seats) this.store.seats = manifest.seats.map(convertSeatInfoToPassengerSeat);
      }
    } catch (err) { console.warn('Trip restart error:', err); } finally { this.store.isLoadingManifest = false; }
  }

  public async triggerStationEvent(stationIndex: number): Promise<StationEventResponse | null> {
    try {
      this.store.isStationEventLoading = true;
      const res = await apiFetch('/api/v1/simulation/trip/station-event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ station_index: stationIndex }),
      });
      if (res.ok) {
        const data: StationEventResponse = await res.json();
        if (data?.manifest?.seats) {
          this.store.seats = data.manifest.seats.map(convertSeatInfoToPassengerSeat);
          if (this.store.selectedSeat && !this.store.selectedSeat.isOccupied) {
            const firstOccupied = this.store.seats.find((s) => s.isOccupied);
            if (firstOccupied) this.store.selectedSeatId = firstOccupied.id;
          }
        }
        return data;
      }
    } catch (err) { console.error('Station event error:', err); } finally { this.store.isStationEventLoading = false; }
    return null;
  }

  private applyConductorStats(user: any) {
    conductorState.loyaltyScore = user.loyalty_score;
    conductorState.safetyScore = user.safety_tech;
    conductorState.skills.service_psychology = user.service_psychology;
    conductorState.skills.safety_tech = user.safety_tech;
    conductorState.skills.routine_discipline = user.routine_discipline;
    conductorState.skills.first_aid = user.first_aid;

    conductorState.conductorProfile.incidentsResolved = user.incidents_resolved;
    conductorState.conductorProfile.correctDecisions = user.correct_decisions;
    if (user.incidents_resolved > 0) {
      conductorState.conductorProfile.accuracyPercent = Math.round((user.correct_decisions / user.incidents_resolved) * 100);
    }

    authStore.fetchMe();

    // 🏆 ЛОВИМ НОВЫЕ АЧИВКИ!
    if (user.new_achievements && user.new_achievements.length > 0) {
      conductorState.showAchievementBanner(user.new_achievements[0]);
    }
  }

  public async resolveIncident(incidentId: string, optionId: string): Promise<any> {
    try {
      this.store.isStationEventLoading = true;
      const res = await apiFetch('/api/v1/simulation/resolve-incident', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ incident_id: incidentId, option_id: optionId }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.manifest?.seats) this.store.seats = data.manifest.seats.map(convertSeatInfoToPassengerSeat);
        if (data.user) {
          this.applyConductorStats(data.user);
        }
        if (data.incident_result) this.store.passengerMood = data.incident_result.mood;
        return data.incident_result;
      }
    } catch (err) { console.error('Incident resolution error:', err); } finally { this.store.isStationEventLoading = false; }
    return null;
  }

  public async resolveVoiceIncident(
    incidentId: string,
    audioBlob: Blob | null,
    conductorText?: string,
    passengerPrompt?: string,
    expectedRule?: string
  ): Promise<any> {
    try {
      this.store.isStationEventLoading = true;

      let audioBase64: string | undefined = undefined;
      if (audioBlob) {
        audioBase64 = await new Promise<string>((resolve) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result as string);
          reader.readAsDataURL(audioBlob);
        });
      }

      const res = await apiFetch('/api/v1/simulation/trip/voice-resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          incident_id: incidentId,
          audio_base64: audioBase64,
          conductor_text: conductorText || '',
          passenger_prompt: passengerPrompt || '',
          expected_rule: expectedRule || '',
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.manifest?.seats) this.store.seats = data.manifest.seats.map(convertSeatInfoToPassengerSeat);
        if (data.user) {
          this.applyConductorStats(data.user);
        }
        if (data.incident_result) this.store.passengerMood = data.incident_result.mood;
        return data.incident_result;
      } else {
        console.error('Ошибка сервера при оценке голоса:', res.status);
      }
    } catch (err) {
      console.error('Voice incident resolution error:', err);
    } finally {
      this.store.isStationEventLoading = false;
    }
    return null;
  }
}

// Главный стор, отвечающий ТОЛЬКО за состояние визуального салона
export class CabinStateStore {
  seats = $state<PassengerSeat[]>([]);
  selectedSeatId = $state<string>('2A');
  isLoadingManifest = $state<boolean>(false);
  isStationEventLoading = $state<boolean>(false);
  passengerMood = $state<PassengerMood>('calm');
  currentView = $state<CabinView>('aisle');

  private api = new CabinApiHandler(this);

  get selectedSeat(): PassengerSeat | undefined {
    return this.seats.find((s) => s.id === this.selectedSeatId);
  }

  get currentPassengerSprite(): string | null {
    const seat = this.selectedSeat;
    if (!seat || !seat.isOccupied || !seat.passenger) return null;
    return seat.passenger.sprite_url;
  }

  get occupiedSeatsCount(): number { return this.seats.filter((s) => s.isOccupied).length; }
  get validatedCount(): number { return this.seats.filter((s) => s.isOccupied && s.ticketStatus === 'validated').length; }
  get alertSeatsCount(): number {
    return this.seats.filter(
      (s) => s.isOccupied && s.activeIncident != null && (typeof s.activeIncident === 'string' || s.activeIncident.phase !== 'passive')
    ).length;
  }

  get tverPassengers(): PassengerSeat[] { return this.seats.filter((s) => s.isOccupied && s.destination === 'Тверь'); }
  get tverPassengersCount(): number { return this.tverPassengers.length; }
  get tverRemindedCount(): number { return this.tverPassengers.filter((s) => s.isTverReminded).length; }

  public getNextStationExitingPassengers(nextStationLabel: string): PassengerSeat[] {
    if (!nextStationLabel) return [];
    return this.seats.filter(s => s.isOccupied && s.passenger && (s.passenger.destination.includes(nextStationLabel) || nextStationLabel.includes(s.passenger.destination)));
  }

  public switchView(view: CabinView): void { this.currentView = view; }
  public selectSeat(seatId: string): void { this.selectedSeatId = seatId; }
  public setPassengerMood(mood: PassengerMood): void { this.passengerMood = mood; }

  public inspectSeat(seatId: string): void {
    this.selectedSeatId = seatId;
    const seat = this.selectedSeat;
    if (seat) this.passengerMood = seat.isOccupied ? seat.condition : 'empty';
    this.switchView('seat');
  }

  public nextOccupiedSeat(): void {
    const occupied = this.seats.filter((s) => s.isOccupied);
    if (occupied.length === 0) return;
    const idx = occupied.findIndex((s) => s.id === this.selectedSeatId);
    this.selectSeat(occupied[(idx + 1) % occupied.length].id);
  }

  public prevOccupiedSeat(): void {
    const occupied = this.seats.filter((s) => s.isOccupied);
    if (occupied.length === 0) return;
    const idx = occupied.findIndex((s) => s.id === this.selectedSeatId);
    this.selectSeat(occupied[(idx - 1 + occupied.length) % occupied.length].id);
  }

  public resetScenario(): void {
    this.passengerMood = 'annoyed';
    this.currentView = 'aisle';
  }

  public validateCurrentSeat(seatId?: string): void {
    const targetId = seatId || this.selectedSeatId;
    const seat = this.seats.find((s) => s.id === targetId);
    if (seat && seat.isOccupied && seat.passenger) {
      const wasAlreadyValidated = seat.passenger.ticket_status === 'validated';
      seat.passenger.ticket_status = 'validated';
      seat.ticketStatus = 'validated';
      if (!wasAlreadyValidated) conductorState.skills.routine_discipline = Math.min(100, conductorState.skills.routine_discipline + 1);
    }
  }

  public remindTverPassenger(seatId?: string): void {
    const seat = this.seats.find((s) => s.id === (seatId || this.selectedSeatId));
    if (seat && seat.isOccupied) {
      seat.isTverReminded = true;
      if (seat.passenger) seat.passenger.ticket_status = 'validated';
      conductorState.skills.routine_discipline = Math.min(100, conductorState.skills.routine_discipline + 1);
    }
  }

  public remindStationPassenger(seatId?: string): void {
    const seat = this.seats.find((s) => s.id === (seatId || this.selectedSeatId));
    if (seat && seat.isOccupied) {
      seat.isStationExitReminded = true;
      if (seat.passenger) seat.passenger.ticket_status = 'validated';
      conductorState.skills.routine_discipline = Math.min(100, conductorState.skills.routine_discipline + 1);
    }
  }

  // --- Делегируем API-запросы ---
  public async loadCabinManifest() { return this.api.loadCabinManifest(); }
  public async startNewTripManifest() { return this.api.startNewTripManifest(); }
  public async triggerStationEvent(stationIndex: number) { return this.api.triggerStationEvent(stationIndex); }
  public async resolveIncident(incidentId: string, optionId: string) { return this.api.resolveIncident(incidentId, optionId); }
  public async resolveVoiceIncident(incidentId: string, audioBlob: Blob | null, conductorText?: string, passengerPrompt?: string, expectedRule?: string) {
    return this.api.resolveVoiceIncident(incidentId, audioBlob, conductorText, passengerPrompt, expectedRule);
  }
}

export const cabinState = new CabinStateStore();