import type { Metadata } from "next";
import localFont from "next/font/local";
import { AppProvider } from "./context";
import "./globals.css";

const chasteFont = localFont({
  src: "../../public/fonts/Chaste.otf",
  variable: "--font-chaste",
});

export const metadata: Metadata = {
  title: "Aegis-Red | Autonomous AI Red-Teaming Framework",
  description: "Enterprise autonomous AI red-teaming framework for probing, stress-testing, and security auditing Chatbots, RAG applications, and Tool Agents.",
  openGraph: {
    title: "Aegis-Red | Autonomous AI Security Framework",
    description: "Autonomous AI Red-Teaming & Vulnerability Assessment Platform",
    url: "https://aegis-red.dev",
    siteName: "Aegis-Red",
    images: [
      {
        url: "/assets/aegis-preview.png",
        width: 1200,
        height: 630,
        alt: "Aegis-Red Cyber Security Platform Preview",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Aegis-Red | Autonomous AI Security Framework",
    description: "Autonomous AI Red-Teaming & Vulnerability Assessment Platform",
    images: ["/assets/aegis-preview.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${chasteFont.variable} antialiased`}>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Elms+Sans:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet" />
      </head>
      <body className="bg-zinc-900 text-zinc-300 select-none">
        <AppProvider>
          {children}
        </AppProvider>
      </body>
    </html>
  );
}
