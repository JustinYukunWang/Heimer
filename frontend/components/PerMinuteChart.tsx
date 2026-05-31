'use client';

import { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { PerMinuteSnapshot } from '@/lib/api';

interface Props {
  timeline: PerMinuteSnapshot[];
  ranks: string[];
}

const RANK_COLORS: Record<string, string> = {
  CHALLENGER:  '#f0b232',
  GRANDMASTER: '#cd4545',
  MASTER:      '#9d5aad',
};

interface StatConfig {
  key: string;
  label: string;
  playerKey: keyof PerMinuteSnapshot;
  benchKey:  keyof PerMinuteSnapshot;
  higherBetter: boolean;
  fmt: (v: number) => string;
}

const STATS: StatConfig[] = [
  { key: 'cs',      label: 'CS',      playerKey: 'player_cs',      benchKey: 'benchmark_cs',      higherBetter: true,  fmt: (v) => v.toFixed(0) },
  { key: 'gold',    label: 'Gold',    playerKey: 'player_gold',    benchKey: 'benchmark_gold',    higherBetter: true,  fmt: (v) => v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v.toFixed(0) },
  { key: 'xp',      label: 'XP',      playerKey: 'player_xp',      benchKey: 'benchmark_xp',      higherBetter: true,  fmt: (v) => v.toFixed(0) },
  { key: 'level',   label: 'Level',   playerKey: 'player_level',   benchKey: 'benchmark_level',   higherBetter: true,  fmt: (v) => v.toFixed(1) },
  { key: 'kills',   label: 'Kills',   playerKey: 'player_kills',   benchKey: 'benchmark_kills',   higherBetter: true,  fmt: (v) => v.toFixed(2) },
  { key: 'deaths',  label: 'Deaths',  playerKey: 'player_deaths',  benchKey: 'benchmark_deaths',  higherBetter: false, fmt: (v) => v.toFixed(2) },
  { key: 'assists', label: 'Assists', playerKey: 'player_assists', benchKey: 'benchmark_assists', higherBetter: true,  fmt: (v) => v.toFixed(2) },
];

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CustomTooltip({ active, payload, label, fmt }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#111827] border border-[#1e2d3d] rounded-lg px-3 py-2 text-sm shadow-lg">
      <p className="text-gray-400 text-xs mb-1.5">Minute {label}</p>
      {payload.map((p: { name: string; value: number; color: string }) => (
        <p key={p.name} className="font-medium" style={{ color: p.color }}>
          {p.name}: {fmt(p.value)}
        </p>
      ))}
    </div>
  );
}

export default function PerMinuteChart({ timeline, ranks }: Props) {
  const [activeKey, setActiveKey] = useState('cs');

  const stat  = STATS.find((s) => s.key === activeKey)!;
  const benchLabel  = ranks.length === 3
    ? 'Master+'
    : ranks.map((r) => r[0] + r.slice(1).toLowerCase()).join('/');
  const benchColor = ranks.length === 1 ? RANK_COLORS[ranks[0]] : '#c89b3c';

  const rawData = timeline.map((s) => ({
    minute:    s.timestamp_minute,
    you:       s[stat.playerKey] as number,
    benchmark: s[stat.benchKey]  as number | null,
  }));

  // Fill benchmark gaps via linear interpolation between 5-min Neon data points
  const knownBench = rawData.filter((d) => d.benchmark !== null);
  const chartData = rawData.map((d) => {
    if (d.benchmark !== null) return d;
    const before = [...knownBench].reverse().find((p) => p.minute < d.minute);
    const after  = knownBench.find((p) => p.minute > d.minute);
    if (!before || !after) return d;
    const t = (d.minute - before.minute) / (after.minute - before.minute);
    return { ...d, benchmark: +(before.benchmark! + t * (after.benchmark! - before.benchmark!)).toFixed(2) };
  });

  return (
    <div>
      {/* Stat tabs */}
      <div className="flex gap-1.5 mb-5 flex-wrap">
        {STATS.map((s) => (
          <button
            key={s.key}
            onClick={() => setActiveKey(s.key)}
            className={`px-4 py-1.5 rounded text-sm font-medium border transition-colors ${
              activeKey === s.key
                ? 'bg-[#c89b3c] text-black border-[#c89b3c]'
                : 'text-gray-400 border-[#1e2d3d] hover:border-gray-500 hover:text-gray-200'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Insight line */}
      {(() => {
        const last = chartData.filter((d) => d.benchmark !== null).at(-1);
        if (!last) return null;
        const diff = last.you - last.benchmark!;
        const ahead = stat.higherBetter ? diff >= 0 : diff <= 0;
        return (
          <p className={`text-sm mb-3 font-medium ${ahead ? 'text-green-400' : 'text-red-400'}`}>
            {ahead ? '▲ Ahead' : '▼ Behind'} {benchLabel} by{' '}
            <span className="font-bold">{stat.fmt(Math.abs(diff))}</span>{' '}
            {stat.label.toLowerCase()} at minute {last.minute}
          </p>
        );
      })()}

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 5, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2d3d" vertical={false} />
          <XAxis
            dataKey="minute"
            stroke="#374151"
            tick={{ fill: '#6b7280', fontSize: 11 }}
            label={{ value: 'Minute', position: 'insideBottom', offset: -10, fill: '#4b5563', fontSize: 12 }}
          />
          <YAxis
            stroke="#374151"
            tick={{ fill: '#6b7280', fontSize: 11 }}
            tickFormatter={stat.fmt}
            width={48}
          />
          <Tooltip content={<CustomTooltip fmt={stat.fmt} />} />
          <Legend
            wrapperStyle={{ paddingTop: '16px', fontSize: '13px' }}
            formatter={(value) => (
              <span style={{ color: '#9ca3af' }}>{value}</span>
            )}
          />
          <Line
            type="monotone"
            dataKey="you"
            stroke="#0bc4c2"
            strokeWidth={2}
            dot={false}
            name="You"
            activeDot={{ r: 4, fill: '#0bc4c2' }}
          />
          <Line
            type="monotone"
            dataKey="benchmark"
            stroke={benchColor}
            strokeWidth={2}
            strokeDasharray="6 4"
            dot={false}
            connectNulls
            name={benchLabel}
            activeDot={{ r: 4, fill: benchColor }}
          />
        </LineChart>
      </ResponsiveContainer>

      <p className="text-gray-600 text-xs text-center mt-1">
        Benchmark measured at 5-min marks · values between are linearly interpolated
      </p>
    </div>
  );
}
