import { conductorState } from './conductorState.svelte';

export interface UserSession {
  id: string;
  name: string;
  gender: 'm' | 'f';
  role: string;
  badge: string;
  shifts: number;
  token: string;
}

export interface LeaderboardMember {
  id: string;
  username: string;
  gender: 'm' | 'f';
  role: string;
  badge: string;
  shifts_count: number;
  loyalty_score: number;
  service_psychology: number;
  safety_tech: number;
  routine_discipline: number;
  first_aid: number;
  incidents_resolved: number;
  correct_decisions: number;
  accuracy_percent: number;
  streak_days: number;
  rating_score: number;
}

export type AppRoute = 'login' | 'trips' | 'dashboard' | 'leaderboard' | 'studio' | 'simulator';

const STORAGE_KEY = 'vsm_conductor_auth_session';

export class AuthStore {
  currentUser = $state<UserSession | null>(null);
  currentRoute = $state<AppRoute>('login');
  leaderboardData = $state<LeaderboardMember[]>([]);
  isLoadingLeaderboard = $state<boolean>(false);

  constructor() {
    if (typeof window !== 'undefined') {
      this.initSession();
      if (!window.location.hash || window.location.hash === '#') {
        window.location.replace(this.currentUser ? '#trips' : '#login');
      }
      this.syncRouteFromHash();
      window.addEventListener('hashchange', this.syncRouteFromHash);
    }
  }

  private initSession(): void {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const session: UserSession = JSON.parse(stored);
        this.currentUser = session;
        this.fetchMe();
      } else {
        this.currentUser = null;
      }
    } catch {
      this.currentUser = null;
    }
  }

  private syncRouteFromHash = (): void => {
    if (typeof window === 'undefined') return;
    const raw = window.location.hash.toLowerCase().replace('#', '').trim();

    if (!this.currentUser) {
      this.currentRoute = 'login';
      if (window.location.hash !== '#login') {
        window.location.replace('#login');
      }
      return;
    }

    const validRoutes: AppRoute[] = ['trips', 'dashboard', 'leaderboard', 'studio', 'simulator'];
    if (validRoutes.includes(raw as AppRoute)) {
      this.currentRoute = raw as AppRoute;
      if (raw === 'dashboard' || raw === 'leaderboard') {
        this.fetchLeaderboard();
        this.fetchMe();
      }
    } else {
      window.location.replace('#trips');
      this.currentRoute = 'trips';
    }
  };

  public setRoute(route: AppRoute): void {
    if (!this.currentUser && route !== 'login') {
      this.setRoute('login');
      return;
    }

    this.currentRoute = route;
    if (route === 'dashboard' || route === 'leaderboard') {
      this.fetchLeaderboard();
      this.fetchMe();
    }

    if (typeof window !== 'undefined') {
      const targetHash = `#${route}`;
      if (window.location.hash !== targetHash) {
        window.location.hash = targetHash;
      }
    }
  }

  public async loginAsGuest(
    roleType: 'trainee' | 'senior' = 'senior',
    gender: 'm' | 'f' = 'm'
  ): Promise<void> {
    const res = await fetch('/api/v1/auth/guest-login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ role: roleType, gender }),
    });

    if (!res.ok) {
      throw new Error(`Ошибка сервера SQLite: ${res.status}`);
    }

    const data = await res.json();
    const u = data.user;
    const session: UserSession = {
      id: u.id,
      name: u.username,
      gender: u.gender || gender,
      role: u.role,
      badge: u.badge,
      shifts: u.shifts_count,
      token: data.token || `vsm-session-${u.id}`,
    };

    this.applyUserData(session, u);
    this.setRoute('trips');
  }

  private applyUserData(session: UserSession, u: Record<string, any>): void {
    this.currentUser = session;
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    }

    conductorState.conductorProfile = {
      name: session.name,
      gender: u.gender || session.gender || 'm',
      role: session.role,
      badge: session.badge,
      shiftsCompleted: session.shifts,
      incidentsResolved: u.incidents_resolved ?? 0,
      correctDecisions: u.correct_decisions ?? 0,
      accuracyPercent: u.accuracy_percent ?? 100,
      streakDays: u.streak_days ?? 1,
      ratingScore: u.rating_score ?? 250,
    };

    if (typeof u.service_psychology === 'number') conductorState.skills.service_psychology = u.service_psychology;
    if (typeof u.safety_tech === 'number') {
      conductorState.skills.safety_tech = u.safety_tech;
      conductorState.safetyScore = u.safety_tech;
    }
    if (typeof u.routine_discipline === 'number') conductorState.skills.routine_discipline = u.routine_discipline;
    if (typeof u.first_aid === 'number') conductorState.skills.first_aid = u.first_aid;
    if (typeof u.loyalty_score === 'number') conductorState.loyaltyScore = u.loyalty_score;
  }

  public async fetchMe(): Promise<void> {
    if (!this.currentUser) return;
    try {
      const res = await fetch(`/api/v1/users/me?user_id=${encodeURIComponent(this.currentUser.id)}`, {
        headers: {
          'Accept': 'application/json',
          'Authorization': `Bearer ${this.currentUser.token}`,
        },
      });
      if (res.ok) {
        const u = await res.json();
        const updatedSession: UserSession = {
          id: u.id,
          name: u.username,
          gender: u.gender || 'm',
          role: u.role,
          badge: u.badge,
          shifts: u.shifts_count,
          token: this.currentUser.token,
        };
        this.applyUserData(updatedSession, u);
      }
    } catch {}
  }

  public async fetchLeaderboard(): Promise<void> {
    this.isLoadingLeaderboard = true;
    try {
      const res = await fetch('/api/v1/leaderboard', {
        headers: { 'Accept': 'application/json' },
      });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data.leaderboard)) {
          this.leaderboardData = data.leaderboard;
        }
      }
    } catch {
    } finally {
      this.isLoadingLeaderboard = false;
    }
  }

  public logout(): void {
    this.currentUser = null;
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem(STORAGE_KEY);
      } catch {}
    }
    this.setRoute('login');
  }

  public destroy(): void {
    if (typeof window !== 'undefined') {
      window.removeEventListener('hashchange', this.syncRouteFromHash);
    }
  }
}

export const authStore = new AuthStore();
