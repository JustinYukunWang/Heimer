import { PlayerProfile, MatchSummary, ChampionStats, championIconUrl } from '@/lib/api';

interface Props {
  profile: PlayerProfile;
  matches: MatchSummary[];
  championPool: ChampionStats[];
  ddragonVersion: string;
}

function mostPlayedRole(matches: MatchSummary[]): string {
  const counts: Record<string, number> = {};
  for (const m of matches) {
    if (m.role) counts[m.role] = (counts[m.role] || 0) + 1;
  }
  return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? '—';
}

function rankColor(rank: string): string {
  if (rank.startsWith('CHALLENGER'))  return '#f0b232';
  if (rank.startsWith('GRANDMASTER')) return '#cd4545';
  if (rank.startsWith('MASTER'))      return '#9d5aad';
  if (rank.startsWith('DIAMOND'))     return '#576bcd';
  if (rank.startsWith('EMERALD'))     return '#1ba57a';
  if (rank.startsWith('PLATINUM'))    return '#27b0a0';
  if (rank.startsWith('GOLD'))        return '#c89b3c';
  if (rank.startsWith('SILVER'))      return '#a0aec0';
  return '#718096';
}

export default function ProfileHeader({ profile, matches, championPool, ddragonVersion }: Props) {
  const topRole = mostPlayedRole(matches);
  const color   = rankColor(profile.rank);
  const top5    = championPool.slice(0, 5);

  return (
    <div className="bg-[#111827] border border-[#1e2d3d] rounded-lg p-5 flex items-start gap-6">

      {/* Profile icon */}
      <div className="relative shrink-0">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={profile.profile_icon_url}
          alt="Profile icon"
          width={80}
          height={80}
          className="rounded-full border-2 border-[#1e2d3d]"
          onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
        />
        <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 bg-[#0a0d13] border border-[#1e2d3d] text-gray-400 text-xs px-1.5 py-0.5 rounded whitespace-nowrap">
          Lv {profile.summoner_level}
        </span>
      </div>

      {/* Name + rank + record */}
      <div className="flex flex-col gap-1.5 min-w-[160px]">
        <h1 className="text-xl font-bold text-gray-100 leading-none">
          {profile.game_name}
          <span className="text-gray-500 font-normal text-base">#{profile.tag_line}</span>
        </h1>
        <p className="text-sm font-semibold" style={{ color }}>
          {profile.rank === 'Unranked' ? 'Unranked' : `${profile.rank} — ${profile.lp} LP`}
        </p>
        <p className="text-gray-400 text-sm">
          {profile.wins}W&nbsp;/&nbsp;{profile.losses}L&nbsp;&nbsp;
          <span className={profile.winrate >= 0.5 ? 'text-green-400' : 'text-red-400'}>
            {(profile.winrate * 100).toFixed(0)}%&nbsp;WR
          </span>
        </p>
        <p className="text-gray-600 text-xs">{topRole}</p>
      </div>

      {/* Divider */}
      <div className="hidden sm:block w-px self-stretch bg-[#1e2d3d] mx-1" />

      {/* Top-5 champion pool */}
      <div className="hidden sm:flex flex-col gap-1.5 flex-1 min-w-0">
        <p className="text-xs text-gray-600 uppercase tracking-wide mb-0.5">Champion Pool</p>
        {top5.map((c) => {
          const kda = c.avg_deaths === 0
            ? '∞'
            : ((c.avg_kills + c.avg_assists) / c.avg_deaths).toFixed(2);
          return (
            <div key={c.champion} className="flex items-center gap-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={championIconUrl(c.champion, ddragonVersion)}
                alt={c.champion}
                width={24}
                height={24}
                className="rounded shrink-0"
                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
              />
              <span className="text-gray-300 text-sm w-24 truncate">{c.champion}</span>
              <span className="text-gray-500 text-xs w-8">{c.games}g</span>
              <span className={`text-xs w-10 font-medium ${c.winrate >= 0.6 ? 'text-green-400' : c.winrate >= 0.5 ? 'text-gray-300' : 'text-red-400'}`}>
                {(c.winrate * 100).toFixed(0)}%
              </span>
              <span className="text-gray-500 text-xs">
                {c.avg_kills.toFixed(1)}/{c.avg_deaths.toFixed(1)}/{c.avg_assists.toFixed(1)}
                <span className="text-gray-600 ml-1">({kda})</span>
              </span>
            </div>
          );
        })}
      </div>

    </div>
  );
}
