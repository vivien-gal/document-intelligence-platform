import { useState, type ReactNode } from "react";
import { generateProjectAnalysis } from "../api/client";
import type { ProjectAnalysis } from "../types";

function SectionCard({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-indigo-300">
        {title}
      </h3>
      {children}
    </section>
  );
}

function ListOrEmpty({ items }: { items: string[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-slate-500">Not found</p>;
  }
  return (
    <ul className="list-inside list-disc space-y-1 text-sm text-slate-200">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}

export function ProjectAnalystPage() {
  const [analysis, setAnalysis] = useState<ProjectAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      setAnalysis(await generateProjectAnalysis());
    } catch (err) {
      setAnalysis(null);
      setError(
        err instanceof Error
          ? err.message
          : "Failed to generate project analysis. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-1 flex-col overflow-y-auto p-8">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-white">
            AI Project Analyst
          </h2>
          <p className="mt-1 max-w-2xl text-slate-400">
            Rule-based analysis over your uploaded documents using semantic
            search and structured field extraction. No external AI APIs.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void runAnalysis()}
          disabled={loading}
          className="rounded-xl bg-indigo-600 px-5 py-3 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Analyzing…" : "Generate Project Analysis"}
        </button>
      </header>

      {error && (
        <div className="mb-6 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {loading && (
        <p className="text-slate-400">Retrieving chunks and building analysis…</p>
      )}

      {analysis && !loading && (
        <div className="grid gap-5 lg:grid-cols-2">
          <SectionCard title="Project summary">
            <p className="text-sm leading-relaxed text-slate-200">
              {analysis.project_summary}
            </p>
          </SectionCard>

          <SectionCard title="Source documents">
            {analysis.source_documents.length === 0 ? (
              <p className="text-sm text-slate-500">Not found</p>
            ) : (
              <ul className="space-y-1 text-sm text-slate-200">
                {analysis.source_documents.map((name) => (
                  <li key={name}>{name}</li>
                ))}
              </ul>
            )}
          </SectionCard>

          <SectionCard title="Key dates">
            <ListOrEmpty items={analysis.key_dates} />
          </SectionCard>

          <SectionCard title="Budget information">
            <ListOrEmpty items={analysis.budget_information} />
          </SectionCard>

          <SectionCard title="Risks">
            <ListOrEmpty items={analysis.risks} />
          </SectionCard>

          <SectionCard title="Open tasks">
            <ListOrEmpty items={analysis.open_tasks} />
          </SectionCard>

          <SectionCard title="Stakeholders">
            <ListOrEmpty items={analysis.stakeholders} />
          </SectionCard>
        </div>
      )}

      {!analysis && !loading && !error && (
        <p className="rounded-xl border border-dashed border-slate-700 bg-slate-900/40 px-6 py-10 text-center text-slate-500">
          Upload PDFs, then click Generate Project Analysis to extract a
          structured project overview.
        </p>
      )}
    </div>
  );
}
