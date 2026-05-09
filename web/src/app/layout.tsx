import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ZEROGATE / SENTINEL-AI WAR ROOM",
  description:
    "Purple Team DevSecOps Command Center — Real-time vulnerability scanning, adversarial simulation, and autonomous patching.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="noise grid-bg min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
