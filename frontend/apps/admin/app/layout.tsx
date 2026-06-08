import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "YurPass Admin",
  description: "YurPass admin cockpit",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body className="antialiased">{children}</body>
    </html>
  );
}
