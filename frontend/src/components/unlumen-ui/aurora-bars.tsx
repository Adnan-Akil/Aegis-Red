"use client";

import React from "react";
import { motion } from "framer-motion";

interface AuroraBarsProps {
  className?: string;
  barCount?: number;
  colors?: string[];
}

export function AuroraBars({
  className = "",
  barCount = 14,
  colors = [
    "rgba(239, 68, 68, 0.70)",  // Vivid Red
    "rgba(168, 85, 247, 0.65)", // Vivid Purple
    "rgba(244, 63, 94, 0.60)",  // Rose Red
    "rgba(192, 132, 252, 0.55)", // Bright Violet
  ],
}: AuroraBarsProps) {
  const bars = Array.from({ length: barCount });

  return (
    <div
      className={`absolute inset-0 overflow-hidden pointer-events-none flex justify-between items-center z-5 opacity-90 ${className}`}
      aria-hidden="true"
    >
      {bars.map((_, i) => {
        const color = colors[i % colors.length];
        const duration = 3.5 + (i % 5) * 1.2;
        const delay = (i % 7) * 0.3;
        const initialHeight = 50 + (i % 5) * 10;
        const targetHeight = 90 + (i % 3) * 5;

        return (
          <motion.div
            key={i}
            className="flex-1 mx-[4px] h-full rounded-full blur-xl transform-gpu"
            style={{
              background: `linear-gradient(180deg, ${color} 0%, rgba(220, 38, 38, 0.15) 50%, rgba(0, 0, 0, 0) 100%)`,
            }}
            initial={{ height: `${initialHeight}%`, opacity: 0.5 }}
            animate={{
              height: [`${initialHeight}%`, `${targetHeight}%`, `${initialHeight}%`],
              opacity: [0.5, 0.95, 0.5],
              scaleX: [1, 1.4, 1],
            }}
            transition={{
              duration,
              delay,
              repeat: Infinity,
              repeatType: "mirror",
              ease: "easeInOut",
            }}
          />
        );
      })}
    </div>
  );
}

export default AuroraBars;
