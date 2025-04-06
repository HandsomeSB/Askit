import type { Metadata } from "next";
import { Ubuntu } from "next/font/google";
import "./globals.css";

const ubuntu = Ubuntu({ weight: ['300', '400', '500', '700'], subsets: ["latin"], display: 'swap' });

export const metadata: Metadata = {
  title: "Askit - Semantic Search Engine",
  description: "A powerful semantic search engine that understands your queries",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={ubuntu.className}>{children}</body>
    </html>
  );
}
