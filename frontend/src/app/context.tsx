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
  // Shared Scanning State
  isScanning: boolean;
  setIsScanning: (val: boolean) => void;
  statusText: string;
  setStatusText: (val: string) => void;
  scanUrl: string;
  setScanUrl: (val: string) => void;
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

  return (
    <AppContext.Provider value={{
      userName, setUserName,
      headlessMode, setHeadlessMode,
      maxMutations, setMaxMutations,
      maxIterations, setMaxIterations,
      isScanning, setIsScanning,
      statusText, setStatusText,
      scanUrl, setScanUrl
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
