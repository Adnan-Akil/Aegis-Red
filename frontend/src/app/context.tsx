"use client";

import React, { createContext, useContext, useState } from "react";

interface AppContextType {
  userName: string;
  setUserName: (val: string) => void;
  headlessMode: boolean;
  setHeadlessMode: (val: boolean) => void;
  maxMutations: number;
  setMaxMutations: (val: number) => void;
  maxIterations: number;
  setMaxIterations: (val: number) => void;
  // Scanning state
  isScanning: boolean;
  setIsScanning: (val: boolean) => void;
  statusText: string;
  setStatusText: (val: string) => void;
  scanUrl: string;
  setScanUrl: (val: string) => void;
  // Live scan metrics
  targetName: string;
  setTargetName: (val: string) => void;
  elapsedSeconds: number;
  setElapsedSeconds: (val: number | ((prev: number) => number)) => void;
  currentIteration: number;
  setCurrentIteration: (val: number) => void;
  currentMutation: number;
  setCurrentMutation: (val: number) => void;
  currentSeverity: number;       // 0–100
  setCurrentSeverity: (val: number) => void;
  logLines: string[];
  setLogLines: (val: string[] | ((prev: string[]) => string[])) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [userName, setUserName] = useState("Operator");
  const [headlessMode, setHeadlessMode] = useState(true);
  const [maxMutations, setMaxMutations] = useState(3);
  const [maxIterations, setMaxIterations] = useState(5);

  const [isScanning, setIsScanning] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [scanUrl, setScanUrl] = useState("");

  // Live metrics
  const [targetName, setTargetName] = useState("");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [currentIteration, setCurrentIteration] = useState(0);
  const [currentMutation, setCurrentMutation] = useState(0);
  const [currentSeverity, setCurrentSeverity] = useState(0);
  const [logLines, setLogLines] = useState<string[]>([]);

  return (
    <AppContext.Provider value={{
      userName, setUserName,
      headlessMode, setHeadlessMode,
      maxMutations, setMaxMutations,
      maxIterations, setMaxIterations,
      isScanning, setIsScanning,
      statusText, setStatusText,
      scanUrl, setScanUrl,
      targetName, setTargetName,
      elapsedSeconds, setElapsedSeconds,
      currentIteration, setCurrentIteration,
      currentMutation, setCurrentMutation,
      currentSeverity, setCurrentSeverity,
      logLines, setLogLines,
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (!context) throw new Error("useAppContext must be used within AppProvider");
  return context;
}
