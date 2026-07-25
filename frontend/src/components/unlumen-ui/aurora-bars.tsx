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
  barCount = 6,
  colors = [
    "rgba(220, 38, 38, 0.45)", // Unified Aegis Red
  ],
}: AuroraBarsProps) {
  const bars = Array.from({ length: barCount });

  return (
    <div
      className={`absolute inset-0 overflow-hidden pointer-events-none flex justify-around items-center z-5 opacity-75 ${className}`}
      aria-hidden="true"
    >
      {bars.map((_, i) => {
        const color = colors[0];
        const duration = 4 + (i % 3) * 1.5;
        const delay = i * 0.5;
        const initialHeight = 45 + (i % 4) * 10;
        const targetHeight = 80 + (i % 3) * 8;

        return (
          <motion.div
            key={i}
            className="w-16 sm:w-24 h-full rounded-full blur-2xl transform-gpu"
            style={{
              background: `linear-gradient(180deg, ${color} 0%, rgba(185, 28, 28, 0.1) 60%, rgba(0, 0, 0, 0) 100%)`,
            }}
            initial={{ height: `${initialHeight}%`, opacity: 0.3 }}
            animate={{
              height: [`${initialHeight}%`, `${targetHeight}%`, `${initialHeight}%`],
              opacity: [0.35, 0.75, 0.35],
              scaleX: [1, 1.25, 1],
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
