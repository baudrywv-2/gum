import type { Metadata } from "next";
import { Fraunces, JetBrains_Mono, Sora } from "next/font/google";
import { AppShell } from "@/components/AppShell";
import "./globals.css";

const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
  display: "swap",
});

const sora = Sora({
  variable: "--font-sora",
  subsets: ["latin"],
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "GUM — Opportunity Intelligence",
  description:
    "Discover problems first, evaluate evidence, then recommend what to build.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${fraunces.variable} ${sora.variable} ${jetbrains.variable} antialiased font-sans`}
      >
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
