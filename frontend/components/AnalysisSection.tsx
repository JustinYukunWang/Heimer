import { FilteredAnalysis, PerMinuteSnapshot } from '@/lib/api';
import PerMinuteChart from '@/components/PerMinuteChart';

const RANK_COLORS: Record<string, string> = {
  CHALLENGER:  '#f0b232',
  GRANDMASTER: '#cd4545',
  MASTER:      '#9d5aad',
};

interface Props {
  analysis: FilteredAnalysis;
  timeline: PerMinuteSnapshot[];
  role: string;
  champion: string;
  ranks: string[];
}

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-[#0a0d13] rounded-lg p-3 text-center">
      <p className="text-gray-500 text-xs uppercase tracking-wide mb-1">{label}</p>
      <p className="text-gray-100 text-lg font-bold">{value}</p>
      {sub && <p className="text-gray-500 text-xs mt-0.5">{sub}</p>}
    </div>
  );
}

export default function AnalysisSection({ analysis, timeline, role, champion, ranks }: Props) {
  const filterLabel = [champion, role ? `(${role})` : ''].filter(Boolean).join(' ') || 'All games';

  return (
    <div className="flex flex-col gap-4">

      {/* Section 4: Aggregate stats */}
      <div className="bg-[#111827] border border-[#1e2d3d] rounded-lg p-4">
        <p className="text-xs text-gray-500 uppercase tracking-wide mb-3">
          {filterLabel} &nbsp;·&nbsp; {analysis.games_analyzed} games
        </p>
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
          <StatCard
            label="Win Rate"
            value={`${(analysis.winrate * 100).toFixed(0)}%`}
            sub={`${Math.round(analysis.winrate * analysis.games_analyzed)}W ${Math.round((1 - analysis.winrate) * analysis.games_analyzed)}L`}
          />
          <StatCard
            label="KDA"
            value={analysis.avg_deaths === 0 ? 'Perfect' : ((analysis.avg_kills + analysis.avg_assists) / analysis.avg_deaths).toFixed(2)}
            sub={`${analysis.avg_kills.toFixed(1)} / ${analysis.avg_deaths.toFixed(1)} / ${analysis.avg_assists.toFixed(1)}`}
          />
          <StatCard label="CS / min"   value={analysis.avg_cs_per_min.toFixed(1)} />
          <StatCard label="Gold / min" value={analysis.avg_gold_per_min.toFixed(0)} />
          <StatCard label="Avg Vision" value={analysis.avg_vision_score.toFixed(1)} />
          <StatCard label="Avg Damage" value={(analysis.avg_damage / 1000).toFixed(1) + 'k'} />
        </div>
      </div>

      {/* Section 5: Per-minute line charts */}
      {timeline.length > 0 ? (
        <div className="bg-[#111827] border border-[#1e2d3d] rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <p className="text-xs text-gray-500 uppercase tracking-wide">
              Per-Minute Breakdown — {filterLabel}
            </p>
            <div className="flex items-center gap-2">
              <span className="text-gray-600 text-xs">vs</span>
              {ranks.map((r) => (
                <span
                  key={r}
                  className="text-xs font-medium px-1.5 py-0.5 rounded border"
                  style={{ color: RANK_COLORS[r], borderColor: RANK_COLORS[r] + '55' }}
                >
                  {r[0] + r.slice(1).toLowerCase()}
                </span>
              ))}
            </div>
          </div>
          <PerMinuteChart timeline={timeline} ranks={ranks} />
        </div>
      ) : (
        <div className="bg-[#111827] border border-[#1e2d3d] rounded-lg p-6 text-center">
          <p className="text-gray-500 text-sm">
            No benchmark timeline data yet for this filter.
            Populates as the daily pipeline collects more Master+ matches.
          </p>
        </div>
      )}

    </div>
  );
}
