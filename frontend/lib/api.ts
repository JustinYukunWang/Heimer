const API = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

// ── Types ────────────────────────────────────────────────────────────────────

export interface PlayerProfile {
  puuid: string;
  game_name: string;
  tag_line: string;
  summoner_level: number;
  profile_icon_url: string;
  rank: string;
  lp: number;
  wins: number;
  losses: number;
  winrate: number;
}

export interface MatchSummary {
  match_id: string;
  champion: string;
  role: string;
  kills: number;
  deaths: number;
  assists: number;
  cs: number;
  gold: number;
  damage: number;
  vision_score: number;
  win: boolean;
  duration: number;
  game_timestamp: string;
  items: number[];
  patch: string;
}

export interface ChampionStats {
  champion: string;
  games: number;
  wins: number;
  winrate: number;
  avg_kills: number;
  avg_deaths: number;
  avg_assists: number;
}

export interface FilteredAnalysis {
  games_analyzed: number;
  winrate: number;
  avg_kills: number;
  avg_deaths: number;
  avg_assists: number;
  avg_cs_per_min: number;
  avg_gold_per_min: number;
  avg_vision_score: number;
  avg_damage: number;
}

export interface PerMinuteSnapshot {
  timestamp_minute: number;
  player_cs: number;
  player_gold: number;
  player_xp: number;
  player_level: number;
  player_kills: number;
  player_deaths: number;
  player_assists: number;
  benchmark_cs: number | null;
  benchmark_gold: number | null;
  benchmark_xp: number | null;
  benchmark_level: number | null;
  benchmark_kills: number | null;
  benchmark_deaths: number | null;
  benchmark_assists: number | null;
}

export interface PlayerData {
  profile: PlayerProfile;
  recent_matches: MatchSummary[];
  champion_pool: ChampionStats[];
}

// ── Fetch functions ───────────────────────────────────────────────────────────

export async function fetchPlayer(
  gameName: string,
  tagLine: string,
  platform = 'na1'
): Promise<PlayerData> {
  const res = await fetch(`${API}/player/${gameName}/${tagLine}?platform=${platform}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Player not found' }));
    throw new Error(err.detail || 'Player not found');
  }
  return res.json();
}

export async function fetchAnalysis(
  gameName: string,
  tagLine: string,
  platform = 'na1',
  role?: string,
  champion?: string
): Promise<FilteredAnalysis | null> {
  const params = new URLSearchParams({ platform });
  if (role) params.set('role', role);
  if (champion) params.set('champion', champion);
  const res = await fetch(`${API}/player/${gameName}/${tagLine}/analysis?${params}`);
  if (!res.ok) return null;
  return res.json();
}

export const ALL_RANKS = ['CHALLENGER', 'GRANDMASTER', 'MASTER'] as const;
export type Rank = typeof ALL_RANKS[number];

export async function fetchTimeline(
  gameName: string,
  tagLine: string,
  platform = 'na1',
  role?: string,
  champion?: string,
  ranks: string[] = [...ALL_RANKS],
): Promise<PerMinuteSnapshot[]> {
  const params = new URLSearchParams({ platform });
  if (role) params.set('role', role);
  if (champion) params.set('champion', champion);
  ranks.forEach((r) => params.append('ranks', r));
  const res = await fetch(`${API}/player/${gameName}/${tagLine}/timeline?${params}`);
  if (!res.ok) return [];
  return res.json();
}

// ── DDragon helpers ───────────────────────────────────────────────────────────

export function getDDragonVersion(profileIconUrl: string): string {
  // "https://ddragon.leagueoflegends.com/cdn/16.11.1/img/..." → index 4
  return profileIconUrl.split('/')[4] || '16.11.1';
}

export function championIconUrl(championName: string, version: string): string {
  return `https://ddragon.leagueoflegends.com/cdn/${version}/img/champion/${championName}.png`;
}

export function itemIconUrl(itemId: number, version: string): string {
  return `https://ddragon.leagueoflegends.com/cdn/${version}/img/item/${itemId}.png`;
}

// ── Formatting helpers ────────────────────────────────────────────────────────

export function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

export function formatGold(gold: number): string {
  return gold >= 1000 ? `${(gold / 1000).toFixed(1)}k` : String(gold);
}

export const ROLES = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'];
