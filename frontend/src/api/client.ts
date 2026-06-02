import type { ChatResponse, DeleteDocumentResponse, Document } from "../types";

const baseUrl = import.meta.env.VITE_API_URL ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, init);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export function listDocuments(): Promise<Document[]> {
  return request<Document[]>("/documents");
}

export async function uploadDocument(file: File): Promise<Document> {
  const form = new FormData();
  form.append("file", file);
  return request<Document>("/documents/upload", {
    method: "POST",
    body: form,
  });
}

export function deleteDocument(documentId: number): Promise<DeleteDocumentResponse> {
  return request<DeleteDocumentResponse>(`/documents/${documentId}`, {
    method: "DELETE",
  });
}

export function sendChat(message: string, limit = 5): Promise<ChatResponse> {
  return request<ChatResponse>("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, limit }),
  });
}
