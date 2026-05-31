import { MatchSummary, championIconUrl, itemIconUrl, formatDuration, formatGold } from '@/lib/api';

interface Props {
  matches: MatchSummary[];
  ddragonVersion: string;
}

export default function MatchHistory({ matches, ddragonVersion }: Props) {
  return (
    <div className="bg-[#111827] border border-[#1e2d3d] rounded-lg overflow-hidden">
      {matches.map((m) => (
        <div
          key={m.match_id}
          className={`flex items-center gap-3 px-3 py-2 border-b border-[#1e2d3d] last:border-0 border-l-4 ${
            m.win ? 'border-l-green-500 bg-green-950/10' : 'border-l-red-500 bg-red-950/10'
          }`}
        >
          {/* Champion portrait — larger and prominent */}
          <div className="relative shrink-0">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={championIconUrl(m.champion, ddragonVersion)}
              alt={m.champion}
              width={44}
              height={44}
              className="rounded-md"
              onError={(e) => {
                const el = e.target as HTMLImageElement;
                el.style.display = 'none';
              }}
            />
            {/* Win/Loss badge on the icon */}
            <span className={`absolute -bottom-1 -right-1 text-[10px] font-bold px-1 rounded ${
              m.win ? 'bg-green-500 text-black' : 'bg-red-500 text-white'
            }`}>
              {m.win ? 'W' : 'L'}
            </span>
          </div>

          {/* Champion name + role */}
          <div className="w-28 shrink-0">
            <p className="text-gray-200 text-sm font-medium truncate">{m.champion}</p>
            <p className="text-gray-500 text-xs">{m.role || '—'}</p>
          </div>

          {/* KDA */}
          <div className="w-20 shrink-0">
            <p className="text-gray-200 text-sm font-mono">{m.kills}/{m.deaths}/{m.assists}</p>
            <p className="text-gray-500 text-xs">
              {m.deaths === 0 ? 'Perfect' : (((m.kills + m.assists) / m.deaths)).toFixed(2)} KDA
            </p>
          </div>

          {/* CS + Gold */}
          <div className="w-20 shrink-0 hidden sm:block">
            <p className="text-gray-400 text-sm">{m.cs} CS</p>
            <p className="text-[#c89b3c] text-xs">{formatGold(m.gold)}</p>
          </div>

          {/* Duration */}
          <span className="text-gray-500 text-xs w-10 shrink-0 hidden md:block">
            {formatDuration(m.duration)}
          </span>

          {/* Items */}
          <div className="flex gap-0.5 flex-wrap flex-1">
            {m.items.slice(0, 6).map((id, i) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                key={i}
                src={itemIconUrl(id, ddragonVersion)}
                alt={String(id)}
                width={22}
                height={22}
                className="rounded"
                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
              />
            ))}
          </div>

          {/* Patch */}
          <span className="text-gray-600 text-xs shrink-0 hidden lg:block">{m.patch}</span>
        </div>
      ))}
    </div>
  );
}
