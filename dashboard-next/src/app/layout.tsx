import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "Savia Salud EPS · Analítica Geoespacial",
  description: "Dashboard predictivo geoespacial — Gestión de riesgo en salud",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="flex min-h-screen bg-slate-100">
        <Sidebar />
        <main className="flex-1 ml-[240px] min-h-screen overflow-x-hidden">
          {children}
        </main>
      </body>
    </html>
  );
}
