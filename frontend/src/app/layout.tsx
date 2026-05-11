import type { Metadata } from "next";
import localFont from "next/font/local";
import { AppShell } from "@/components/AppShell";
import "./globals.css";

const chasteFont = localFont({
  src: "../../public/fonts/Chaste.otf",
  variable: "--font-chaste",
});

import { AppProvider } from "./context";
import { AuthWrapper } from "@/components/AuthWrapper";

export const metadata: Metadata = {
  title: "Aegis-Red Dashboard",
  description: "Autonomous Multi-Agent AI Security Framework",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${chasteFont.variable} antialiased h-screen w-screen overflow-hidden`}>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Elms+Sans:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet" />
      </head>
      <body className="h-full w-full bg-zinc-900 text-zinc-300 flex flex-col select-none">
        <AppProvider>
          <AuthWrapper>
            <AppShell>
              {children}
            </AppShell>
          </AuthWrapper>
        </AppProvider>
      </body>
    </html>
  );
}
