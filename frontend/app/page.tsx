'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  const [input, setInput] = useState('');
  const [error, setError] = useState('');

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const parts = input.trim().split('#');
    if (parts.length !== 2 || !parts[0] || !parts[1]) {
      setError('Enter in the format: GameName#TAG');
      return;
    }
    setError('');
    router.push(`/player/${encodeURIComponent(parts[0])}/${encodeURIComponent(parts[1])}`);
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-md text-center">
        <h1 className="text-5xl font-bold tracking-widest text-[#c89b3c] mb-2">
          HEIMER
        </h1>
        <p className="text-gray-400 text-sm mb-10 tracking-wide">
          Find your weakness. Fix it.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="TheKun#Wang"
            className="w-full bg-[#111827] border border-[#1e2d3d] rounded-lg px-4 py-3 text-gray-100 placeholder-gray-600 focus:outline-none focus:border-[#c89b3c] transition-colors text-center text-lg"
          />
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button
            type="submit"
            className="w-full bg-[#c89b3c] hover:bg-[#b8892c] text-black font-bold py-3 rounded-lg transition-colors tracking-wide"
          >
            ANALYZE
          </button>
        </form>

        <p className="text-gray-600 text-xs mt-6">
          NA · EUW · KR · and more supported
        </p>
      </div>
    </div>
  );
}
