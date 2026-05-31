import { ChampionStats, championIconUrl } from '@/lib/api';

interface Props {
  pool: ChampionStats[];
  ddragonVersion: string;
}

export default function ChampionPool({ pool, ddragonVersion }: Props) {
  return (
    <div className="bg-[#111827] border border-[#1e2d3d] rounded-lg overflow-hidden">
      {/* Header */}
      <div className="grid grid-cols-[2fr_1fr_1fr_1fr] px-4 py-2 border-b border-[#1e2d3d] text-xs text-gray-500 uppercase tracking-wide">
        <span>Champion</span>
        <span className="text-right">Games</span>
        <span className="text-right">Win Rate</span>
        <span className="text-right">KDA</span>
      </div>

      {pool.map((c) => {
        const kda = c.avg_deaths === 0
          ? 'Perfect'
          : ((c.avg_kills + c.avg_assists) / c.avg_deaths).toFixed(2);

        return (
          <div
            key={c.champion}
            className="grid grid-cols-[2fr_1fr_1fr_1fr] px-4 py-2.5 border-b border-[#1e2d3d] last:border-0 items-center"
          >
            <div className="flex items-center gap-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={championIconUrl(c.champion, ddragonVersion)}
                alt={c.champion}
                width={28}
                height={28}
                className="rounded"
                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
              />
              <span className="text-gray-200 text-sm">{c.champion}</span>
            </div>

            <span className="text-gray-400 text-sm text-right">{c.games}</span>

            <span
              className={`text-sm text-right font-medium ${
                c.winrate >= 0.6 ? 'text-green-400' :
                c.winrate >= 0.5 ? 'text-gray-200' : 'text-red-400'
              }`}
            >
              {(c.winrate * 100).toFixed(0)}%
            </span>

            <div className="text-right">
              <span className="text-gray-200 text-sm">{kda}</span>
              <div className="text-gray-500 text-xs">
                {c.avg_kills.toFixed(1)}/{c.avg_deaths.toFixed(1)}/{c.avg_assists.toFixed(1)}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
