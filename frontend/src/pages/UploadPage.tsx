import { useCallback, useEffect, useState } from "react";
import { deleteDocument, listDocuments, uploadDocument } from "../api/client";
import type { Document } from "../types";

export function UploadPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [deletingDocumentId, setDeletingDocumentId] = useState<number | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setDocuments(await listDocuments());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported");
      return;
    }
    setUploading(true);
    setError(null);
    setSuccess(null);
    try {
      const doc = await uploadDocument(file);
      setSuccess(`Uploaded "${doc.filename}" (${doc.chunk_count} chunks indexed)`);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) void handleFile(file);
  };

  const handleDelete = async (doc: Document) => {
    const confirmed = window.confirm(
      `Delete "${doc.filename}" and all its indexed chunks?`,
    );
    if (!confirmed) return;

    setDeletingDocumentId(doc.id);
    setError(null);
    setSuccess(null);
    try {
      const response = await deleteDocument(doc.id);
      setSuccess(`${response.message} (#${response.document_id})`);
      await refresh();
    } catch (err) {
      const details = err instanceof Error ? err.message : "Unknown error";
      setError(`Could not delete "${doc.filename}". Please try again. (${details})`);
    } finally {
      setDeletingDocumentId(null);
    }
  };

  return (
    <div className="flex flex-1 flex-col overflow-y-auto p-8">
      <header className="mb-8">
        <h2 className="text-2xl font-semibold text-white">Upload documents</h2>
        <p className="mt-1 text-slate-400">
          Add PDFs to your knowledge base. Text is chunked and embedded for chat
          search.
        </p>
      </header>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={[
          "mb-8 flex flex-col items-center justify-center rounded-2xl border-2 border-dashed px-8 py-16 transition-colors",
          dragOver
            ? "border-indigo-400 bg-indigo-500/10"
            : "border-slate-700 bg-slate-900/50",
          uploading ? "pointer-events-none opacity-60" : "",
        ].join(" ")}
      >
        <p className="text-lg font-medium text-slate-200">
          {uploading ? "Uploading and indexing…" : "Drop a PDF here"}
        </p>
        <p className="mt-2 text-sm text-slate-500">or choose a file</p>
        <label className="mt-6 cursor-pointer rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-500">
          Browse files
          <input
            type="file"
            accept=".pdf,application/pdf"
            className="hidden"
            disabled={uploading}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void handleFile(file);
              e.target.value = "";
            }}
          />
        </label>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
          {success}
        </div>
      )}

      <section>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-500">
          Indexed documents
        </h3>
        {loading ? (
          <p className="text-slate-500">Loading…</p>
        ) : documents.length === 0 ? (
          <p className="rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-8 text-center text-slate-500">
            No documents yet. Upload a PDF to get started.
          </p>
        ) : (
          <ul className="divide-y divide-slate-800 overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50">
            {documents.map((doc) => (
              <li
                key={doc.id}
                className="flex items-center justify-between gap-4 px-4 py-3"
              >
                <div className="min-w-0">
                  <p className="truncate font-medium text-slate-100">
                    {doc.filename}
                  </p>
                  <p className="text-xs text-slate-500">
                    {new Date(doc.created_at).toLocaleString()} ·{" "}
                    {doc.chunk_count} chunks
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <span className="rounded-full bg-slate-800 px-2.5 py-0.5 text-xs text-slate-400">
                    #{doc.id}
                  </span>
                  <button
                    type="button"
                    onClick={() => void handleDelete(doc)}
                    disabled={deletingDocumentId === doc.id}
                    className="rounded-md border border-red-500/40 px-2.5 py-1 text-xs font-medium text-red-300 hover:bg-red-500/10 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {deletingDocumentId === doc.id ? "Deleting..." : "Delete"}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
