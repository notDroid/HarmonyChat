import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";
export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: "HarmonyChat",
  description: "A Simple Chat App built with next.js and fastapi.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`antialiased`}
      >
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
