/**
 * Client-side image validation + compression before upload.
 *
 * Mirrors server limits so users get fast feedback. Server always re-validates
 * magic bytes and re-compresses — never trust these checks alone.
 *
 * Compression: longest edge ≤ 1920px, JPEG quality 0.85 — same rationale as
 * the Pillow pipeline (gallery/PDF/Gemini don't need 12MP originals).
 */

export const MAX_PHOTO_SIZE_MB = Number(import.meta.env.VITE_MAX_PHOTO_SIZE_MB || 10);
export const MAX_PHOTO_SIZE_BYTES = MAX_PHOTO_SIZE_MB * 1024 * 1024;
export const MAX_PHOTOS_PER_ALBUM = Number(import.meta.env.VITE_MAX_PHOTOS_PER_ALBUM || 50);
export const IMAGE_MAX_DIMENSION = Number(import.meta.env.VITE_IMAGE_MAX_DIMENSION || 1920);
export const IMAGE_JPEG_QUALITY = Number(import.meta.env.VITE_IMAGE_JPEG_QUALITY || 0.85);

const ALLOWED_TYPES = new Set(["image/jpeg", "image/png", "image/webp", "image/jpg", "image/heic", "image/heif"]);

export type PreparedImage = {
  file: File;
  previewUrl: string;
};

export function validateImageFile(file: File): string | null {
  const type = (file.type || "").toLowerCase();
  // Some cameras omit type; allow empty and let server magic-byte check decide.
  if (type && !ALLOWED_TYPES.has(type) && !type.startsWith("image/")) {
    return "Unsupported file type — use JPG, PNG, or WebP";
  }
  if (file.size > MAX_PHOTO_SIZE_BYTES) {
    return `Photo too large (max ${MAX_PHOTO_SIZE_MB}MB)`;
  }
  return null;
}

export async function prepareImageForUpload(file: File): Promise<PreparedImage> {
  const early = validateImageFile(file);
  if (early) throw new Error(early);

  const compressed = await compressImageFile(file);
  if (compressed.size > MAX_PHOTO_SIZE_BYTES) {
    throw new Error(`Photo too large (max ${MAX_PHOTO_SIZE_MB}MB)`);
  }
  return {
    file: compressed,
    previewUrl: URL.createObjectURL(compressed),
  };
}

async function compressImageFile(file: File): Promise<File> {
  // If already small enough JPEG under dimension guess, still re-encode for consistency.
  const bitmap = await createImageBitmap(file).catch(() => null);
  if (!bitmap) {
    // Browser couldn't decode (e.g. HEIC on some desktops) — send original;
    // server Pillow path will accept/reject.
    return file;
  }

  const scale = Math.min(1, IMAGE_MAX_DIMENSION / Math.max(bitmap.width, bitmap.height));
  const width = Math.max(1, Math.round(bitmap.width * scale));
  const height = Math.max(1, Math.round(bitmap.height * scale));

  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    bitmap.close();
    return file;
  }
  ctx.drawImage(bitmap, 0, 0, width, height);
  bitmap.close();

  const blob = await new Promise<Blob | null>((resolve) =>
    canvas.toBlob(resolve, "image/jpeg", IMAGE_JPEG_QUALITY),
  );
  if (!blob) return file;

  const stem = file.name.replace(/\.[^.]+$/, "") || "photo";
  return new File([blob], `${stem}.jpg`, { type: "image/jpeg", lastModified: Date.now() });
}

/** Upload files one-by-one to avoid overwhelming the server; report per-file status. */
export async function uploadSequentially<T>(
  files: File[],
  uploadOne: (file: File, index: number) => Promise<T>,
  onProgress?: (info: {
    index: number;
    total: number;
    file: File;
    status: "uploading" | "ok" | "error";
    error?: string;
    percent?: number;
  }) => void,
): Promise<{ ok: T[]; errors: { file: File; error: string }[] }> {
  const ok: T[] = [];
  const errors: { file: File; error: string }[] = [];
  for (let index = 0; index < files.length; index++) {
    const file = files[index];
    onProgress?.({ index, total: files.length, file, status: "uploading", percent: Math.round((index / files.length) * 100) });
    try {
      const prepared = await prepareImageForUpload(file);
      const result = await uploadOne(prepared.file, index);
      URL.revokeObjectURL(prepared.previewUrl);
      ok.push(result);
      onProgress?.({
        index,
        total: files.length,
        file,
        status: "ok",
        percent: Math.round(((index + 1) / files.length) * 100),
      });
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : "Upload failed";
      errors.push({ file, error: message });
      onProgress?.({ index, total: files.length, file, status: "error", error: message });
    }
  }
  return { ok, errors };
}
