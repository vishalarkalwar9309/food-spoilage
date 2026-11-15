import React from 'react';
import { ShieldCheck, Info } from 'lucide-react';

export const EngineeringDisclaimer: React.FC = () => {
  return (
    <footer className="mt-8 mb-4 border-t border-dark-800 pt-6 pb-4 text-xs font-mono text-slate-500">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-2.5 max-w-3xl">
          <Info className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong className="text-slate-400 font-semibold">Engineering &amp; Biosafety Scope Disclaimer: </strong>
            This system continuously calculates an empirical, duration-weighted environmental spoilage risk estimate derived from headspace psychrometric deviations (DHT22) and volatile reducing gas responses (MQ-135). It serves as an assistive preservation decision support system and does not scientifically confirm biochemical sterility, bacteriological proliferation, or definitive edibility.
          </p>
        </div>

        <div className="text-right text-[11px] text-slate-500 font-mono whitespace-nowrap self-end md:self-auto">
          <span>Smart Food Storage Spoilage Predictor v1.0.0</span>
          <br />
          <span>Local SQLite + Flask + Vite React IoT Stack</span>
        </div>
      </div>
    </footer>
  );
};
