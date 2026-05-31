'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  fetchPlayer, fetchAnalysis, fetchTimeline,
  PlayerData, FilteredAnalysis, PerMinuteSnapshot,
  ROLES, ALL_RANKS,
} from '@/lib/api';
import ProfileHeader from '@/components/ProfileHeader';
import MatchHistory from '@/components/MatchHistory';
import AnalysisSection from '@/components/AnalysisSection';

interface Props {
  gameName: string;
  tagLine: string;
}

const RANK_META = [
  { key: 'CHALLENGER',  label: 'Challenger',  color: '#f0b232' },
  { key: 'GRANDMASTER', label: 'Grandmaster', color: '#cd4545' },
  { key: 'MASTER',      label: 'Master',      color: '#9d5aad' },
] as const;

export default function PlayerPage({ gameName, tagLine }: Props) {
  const [data, setData] = useState<PlayerData | null>(null);
  const [loadingPlayer, setLoadingPlayer] = useState(true);
  const [playerError, setPlayerError] = useState('');

  // Filter state
  const [role, setRole] = useState('');
  const [champion, setChampion] = useState('');
  const [selectedRanks, setSelectedRanks] = useState<string[]>([...ALL_RANKS]);

  // Analysis state
  const [analysis, setAnalysis] = useState<FilteredAnalysis | null>(null);
  const [timeline, setTimeline] = useState<PerMinuteSnapshot[]>([]);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [analysisError, setAnalysisError] = useState('');

  useEffect(() => {
    fetchPlayer(gameName, tagLine)
      .then(setData)
      .catch((e) => setPlayerError(e.message))
      .finally(() => setLoadingPlayer(false));
  }, [gameName, tagLine]);

  function toggleRank(rank: string) {
    setSelectedRanks((prev) => {
      if (prev.includes(rank)) {
        // Keep at least one selected
        if (prev.length === 1) return prev;
        return prev.filter((r) => r !== rank);
      }
      return [...prev, rank];
    });
  }

  async function handleAnalyze() {
    if (!data) return;
    setLoadingAnalysis(true);
    setAnalysisError('');
    setAnalysis(null);
    setTimeline([]);

    const [a, t] = await Promise.all([
      fetchAnalysis(gameName, tagLine, 'na1', role || undefined, champion || undefined),
      fetchTimeline(gameName, tagLine, 'na1', role || undefined, champion || undefined, selectedRanks),
    ]);

    setLoadingAnalysis(false);
    if (!a) {
      setAnalysisError(`No games found for ${champion || 'any champion'} as ${role || 'any role'}.`);
    } else {
      setAnalysis(a);
      setTimeline(t);
    }
  }

  const ddragonVersion = data?.profile.profile_icon_url.split('/')[4] ?? '16.11.1';
  const champions = data
    ? [...new Set(data.recent_matches.map((m) => m.champion))].sort()
    : [];

  if (loadingPlayer) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-[#c89b3c] text-2xl font-bold mb-2 animate-pulse">HEIMER</div>
          <p className="text-gray-500 text-sm">Fetching {gameName}#{tagLine}…</p>
        </div>
      </div>
    );
  }

  if (playerError) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{playerError}</p>
          <Link href="/" className="text-[#c89b3c] text-sm hover:underline">← Search again</Link>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="min-h-screen">
      {/* Top bar */}
      <div className="border-b border-[#1e2d3d] px-6 py-3 flex items-center gap-4">
        <Link href="/" className="text-[#c89b3c] font-bold tracking-widest text-sm">HEIMER</Link>
        <span className="text-gray-600 text-sm">{gameName}#{tagLine}</span>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8 flex flex-col gap-6">

        {/* Section 1: Profile + champion pool side-by-side */}
        <ProfileHeader
          profile={data.profile}
          matches={data.recent_matches}
          championPool={data.champion_pool}
          ddragonVersion={ddragonVersion}
        />

        {/* Sections 4+5: Filter → Analysis (hero feature, right below profile) */}
        <section>
          <div className="bg-[#111827] border border-[#1e2d3d] rounded-lg p-4 flex flex-col gap-4">

            {/* Rank slicer */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs text-gray-500 uppercase tracking-wide">Compare against</label>
              <div className="flex gap-2">
                {RANK_META.map(({ key, label, color }) => {
                  const active = selectedRanks.includes(key);
                  return (
                    <button
                      key={key}
                      onClick={() => toggleRank(key)}
                      className="px-3 py-1.5 rounded text-xs font-bold border transition-all"
                      style={{
                        borderColor: color,
                        color: active ? '#0a0d13' : color,
                        backgroundColor: active ? color : 'transparent',
                        opacity: active ? 1 : 0.5,
                      }}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Role + champion filters */}
            <div className="flex flex-wrap gap-3 items-end">
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500">Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="bg-[#0a0d13] border border-[#1e2d3d] text-gray-200 rounded px-3 py-2 text-sm focus:outline-none focus:border-[#c89b3c]"
                >
                  <option value="">Any role</option>
                  {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-500">Champion</label>
                <select
                  value={champion}
                  onChange={(e) => setChampion(e.target.value)}
                  className="bg-[#0a0d13] border border-[#1e2d3d] text-gray-200 rounded px-3 py-2 text-sm focus:outline-none focus:border-[#c89b3c]"
                >
                  <option value="">Any champion</option>
                  {champions.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <button
                onClick={handleAnalyze}
                disabled={loadingAnalysis}
                className="bg-[#c89b3c] hover:bg-[#b8892c] disabled:opacity-50 text-black font-bold px-6 py-2 rounded text-sm transition-colors"
              >
                {loadingAnalysis ? 'Analyzing…' : 'Analyze'}
              </button>
            </div>
          </div>

          {analysisError && (
            <p className="text-red-400 text-sm mt-3">{analysisError}</p>
          )}

          {analysis && (
            <div className="mt-4">
              <AnalysisSection
                analysis={analysis}
                timeline={timeline}
                role={role}
                champion={champion}
                ranks={selectedRanks}
              />
            </div>
          )}
        </section>

        {/* Section 2: Match History (below the analysis) */}
        <section>
          <h2 className="text-xs font-bold tracking-widest text-gray-500 mb-3 uppercase">
            Match History
          </h2>
          <MatchHistory matches={data.recent_matches} ddragonVersion={ddragonVersion} />
        </section>

      </div>
    </div>
  );
}
