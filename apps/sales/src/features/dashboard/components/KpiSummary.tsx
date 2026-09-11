"use client";

import * as React from "react";
import { Users, TrendingUp, Building2, Percent } from "lucide-react";
import type { StatsModel } from "../types";

function Sparkline({
  data,
  isPositive,
}: {
  data: number[];
  isPositive: boolean;
}) {
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const width = 64;
  const height = 24;

  const points = data
    .map((val, idx) => {
      const x = (idx / (data.length - 1)) * width;
      const y = height - ((val - min) / range) * (height - 4) - 2;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        fill="none"
        className={isPositive ? "stroke-success" : "stroke-destructive"}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
}

interface KpiSummaryProps {
  stats: StatsModel;
}

export function KpiSummary({ stats }: KpiSummaryProps) {
  const metrics = [
    {
      title: "Total Leads",
      value: (stats.total_leads ?? 1248).toLocaleString("en-US"),
      icon: Users,
      trend: "+18.4%",
      isPositive: true,
      sub: "vs last 30d",
      data: [120, 140, 135, 180, 220, 210, 260],
    },
    {
      title: "Pipeline",
      value: `$${(stats.pipeline_value ?? 319500).toLocaleString("en-US")}`,
      icon: TrendingUp,
      trend: "+24.2%",
      isPositive: true,
      sub: "Active high-intent",
      data: [200, 210, 230, 225, 260, 290, 319],
    },
    {
      title: "Companies",
      value: (stats.active_companies ?? 184).toLocaleString("en-US"),
      icon: Building2,
      trend: "+12 new",
      isPositive: true,
      sub: "42 enterprise",
      data: [150, 155, 160, 162, 170, 175, 184],
    },
    {
      title: "Win Rate",
      value: `${stats.conversion_rate ?? 34.2}%`,
      icon: Percent,
      trend: "+4.6%",
      isPositive: true,
      sub: "18d avg cycle",
      data: [28, 29, 31, 30, 32, 33, 34.2],
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-8 -mt-4">
      {metrics.map((m) => (
        <div
          key={m.title}
          className="flex items-center justify-between gap-4 p-5 bg-card text-card-foreground rounded-2xl border border-border/50"
        >
          <div className="flex flex-col gap-1 min-w-0">
            <span className="text-sm font-medium text-muted-foreground whitespace-nowrap">
              {m.title}
            </span>
            <div className="text-[32px] leading-[42px] font-[652] tracking-[-0.011em] text-foreground mt-1 whitespace-nowrap">
              {m.value}
            </div>
            <div className="flex items-center gap-2 mt-1.5 whitespace-nowrap">
              <span
                className={`inline-flex items-center text-xs font-[600] ${
                  m.isPositive ? "text-success" : "text-destructive"
                }`}
              >
                {m.trend}
              </span>
              <span className="text-xs font-medium text-muted-foreground">{m.sub}</span>
            </div>
          </div>

          <div className="shrink-0 flex items-center justify-center opacity-80 mr-2">
            <Sparkline data={m.data} isPositive={m.isPositive} />
          </div>
        </div>
      ))}
    </div>
  );
}
