import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState, type FormEvent } from "react";
import {
  ArrowRight,
  CalendarDays,
  Camera,
  Download,
  Images,
  MapPin,
  Plus,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { api, friendlyApiMessage, mediaUrl, type AlbumCreate, type TripAlbum } from "../lib/api";
import { useAuth } from "../lib/auth";
import {
  MAX_PHOTO_SIZE_MB,
  MAX_PHOTOS_PER_ALBUM,
  prepareImageForUpload,
  validateImageFile,
} from "../lib/imageUpload";

export const Route = createFileRoute("/albums")({
  component: AlbumsPage,
  head: () => ({ meta: [{ title: "Trip Albums — StoryMiles" }] }),
});

const emptyForm: AlbumCreate = {
  title: "",
  destination: "",
  description: "",
  trip_start: "",
  trip_end: "",
};

function AlbumsPage() {
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const [albums, setAlbums] = useState<TripAlbum[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<AlbumCreate>(emptyForm);
  const [files, setFiles] = useState<File[]>([]);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{
    index: number;
    total: number;
    percent: number;
    label: string;
  } | null>(null);
  const [fileErrors, setFileErrors] = useState<string[]>([]);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      void navigate({ to: "/auth" });
      return;
    }
    api.albums()
      .then((result) => {
        setAlbums(result);
        setSelectedId(result[0]?.id ?? null);
      })
      .catch((cause) => setError(messageFrom(cause)))
      .finally(() => setLoading(false));
  }, [authLoading, user, navigate]);

  const selected = albums.find((album) => album.id === selectedId) ?? null;

  const createAlbum = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const album = await api.createAlbum(cleanAlbumRequest(form));
      setAlbums((current) => [album, ...current]);
      setSelectedId(album.id);
      setForm(emptyForm);
      setShowCreate(false);
    } catch (cause) {
      setError(messageFrom(cause));
    } finally {
      setSaving(false);
    }
  };

  const uploadPhotos = async () => {
    if (!selected || files.length === 0) return;
    const remaining = Math.max(0, MAX_PHOTOS_PER_ALBUM - selected.photos.length);
    if (remaining === 0) {
      setError(`Album full (max ${MAX_PHOTOS_PER_ALBUM} photos)`);
      return;
    }

    const queue = files.slice(0, remaining);
    setUploading(true);
    setError("");
    setFileErrors([]);
    setUploadProgress({ index: 0, total: queue.length, percent: 0, label: "Starting…" });

    const errors: string[] = [];
    let latestPhotos = selected.photos;

    for (let index = 0; index < queue.length; index++) {
      const file = queue[index];
      setUploadProgress({
        index,
        total: queue.length,
        percent: Math.round((index / queue.length) * 100),
        label: `Uploading ${file.name} (${index + 1}/${queue.length})`,
      });

      const clientError = validateImageFile(file);
      if (clientError) {
        errors.push(`${file.name}: ${clientError}`);
        continue;
      }

      try {
        const prepared = await prepareImageForUpload(file);
        const batch = await api.uploadAlbumPhoto(selected.id, prepared.file);
        URL.revokeObjectURL(prepared.previewUrl);
        latestPhotos = batch.photos;
        setAlbums((current) =>
          current.map((album) => (album.id === selected.id ? { ...album, photos: batch.photos } : album)),
        );
        for (const result of batch.results) {
          if (!result.ok && result.error) {
            errors.push(`${result.filename}: ${result.error}`);
          }
        }
      } catch (cause) {
        errors.push(`${file.name}: ${friendlyApiMessage(cause, "Upload failed")}`);
      }
    }

    setFiles([]);
    setFileErrors(errors);
    setUploadProgress({
      index: queue.length,
      total: queue.length,
      percent: 100,
      label: errors.length ? "Finished with some errors" : "All photos uploaded",
    });
    if (errors.length && latestPhotos.length === selected.photos.length) {
      setError(errors[0]);
    } else if (queue.length < files.length) {
      setError(`Album can hold ${MAX_PHOTOS_PER_ALBUM} photos — uploaded ${queue.length}, skipped the rest.`);
    }
    setUploading(false);
    window.setTimeout(() => setUploadProgress(null), 1500);
  };

  const downloadPdf = async () => {
    if (!selected) return;
    setDownloading(true);
    setError("");
    try {
      const blob = await api.downloadAlbumPdf(selected.id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${slugify(selected.title)}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (cause) {
      setError(messageFrom(cause));
    } finally {
      setDownloading(false);
    }
  };

  const deleteAlbum = async () => {
    if (!selected || !window.confirm(`Delete "${selected.title}"?`)) return;
    setError("");
    try {
      await api.deleteAlbum(selected.id);
      const remaining = albums.filter((album) => album.id !== selected.id);
      setAlbums(remaining);
      setSelectedId(remaining[0]?.id ?? null);
    } catch (cause) {
      setError(messageFrom(cause));
    }
  };

  if (authLoading || loading) {
    return <div className="mx-auto max-w-6xl px-5 py-20 label-mono">Loading albums…</div>;
  }

  return (
    <div className="mx-auto max-w-6xl px-5 py-10 md:py-14">
      <div className="flex items-end justify-between gap-5 flex-wrap">
        <div>
          <div className="eyebrow">Your memories</div>
          <h1 className="mt-3 font-display text-4xl md:text-5xl">Trip photo albums</h1>
          <p className="mt-3 text-charcoal/70 max-w-xl">
            Turn the photos from your trip into a beautiful keepsake you can revisit or download as a PDF.
          </p>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          <Plus size={16} /> New album
        </button>
      </div>

      {error && (
        <div className="mt-6 rounded-xl border border-poppy/30 bg-poppy/10 p-3.5 text-sm text-poppy">
          {error}
        </div>
      )}

      {albums.length === 0 ? (
        <EmptyState onCreate={() => setShowCreate(true)} />
      ) : (
        <div className="mt-10 grid lg:grid-cols-[280px_1fr] gap-7 items-start">
          <aside className="space-y-3 lg:sticky lg:top-24">
            <div className="label-mono mb-3">{albums.length} album{albums.length === 1 ? "" : "s"}</div>
            {albums.map((album) => {
              const cover = album.photos[0];
              const active = album.id === selectedId;
              return (
                <button
                  key={album.id}
                  onClick={() => { setSelectedId(album.id); setFiles([]); }}
                  className={`w-full p-3 rounded-2xl text-left flex items-center gap-3 border transition ${
                    active
                      ? "bg-ink text-horizon border-ink shadow-lg"
                      : "bg-white border-ink/10 hover:border-ink/25 hover:-translate-y-0.5"
                  }`}
                >
                  <div className={`w-14 h-14 rounded-xl overflow-hidden shrink-0 flex items-center justify-center ${
                    active ? "bg-white/10" : "bg-stamp"
                  }`}>
                    {cover ? (
                      <img src={mediaUrl(cover.public_url)} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <Images size={20} className={active ? "opacity-70" : "text-ink/45"} />
                    )}
                  </div>
                  <div className="min-w-0">
                    <div className="font-semibold truncate">{album.title}</div>
                    <div className={`text-xs mt-1 truncate ${active ? "text-horizon/60" : "text-charcoal/55"}`}>
                      {album.photos.length} photos{album.destination ? ` · ${album.destination}` : ""}
                    </div>
                  </div>
                </button>
              );
            })}
          </aside>

          {selected && (
            <main>
              <section className="relative overflow-hidden rounded-3xl bg-ink min-h-56 shadow-xl">
                {selected.photos[0] && (
                  <img
                    src={mediaUrl(selected.photos[0].public_url)}
                    alt=""
                    className="absolute inset-0 w-full h-full object-cover opacity-45"
                  />
                )}
                <div className="absolute inset-0 bg-gradient-to-r from-ink/95 via-ink/70 to-ink/25" />
                <div className="relative px-6 md:px-8 py-8 md:py-10 text-horizon">
                  <div className="label-mono !text-horizon/60">Trip album</div>
                  <h2 className="mt-2 font-display italic text-3xl md:text-4xl !text-horizon">{selected.title}</h2>
                  <div className="mt-3 flex flex-wrap gap-4 text-sm text-horizon/75">
                    {selected.destination && (
                      <span className="inline-flex items-center gap-1.5"><MapPin size={14} /> {selected.destination}</span>
                    )}
                    {selected.trip_start && (
                      <span className="inline-flex items-center gap-1.5">
                        <CalendarDays size={14} /> {formatDates(selected.trip_start, selected.trip_end)}
                      </span>
                    )}
                    <span className="inline-flex items-center gap-1.5">
                      <Camera size={14} /> {selected.photos.length} photos
                    </span>
                  </div>
                  {selected.description && (
                    <p className="mt-4 max-w-xl text-sm text-horizon/70 leading-relaxed">{selected.description}</p>
                  )}
                  <div className="mt-6 flex flex-wrap gap-2">
                    <button
                      className="btn-primary !py-2.5"
                      disabled={selected.photos.length === 0 || downloading}
                      onClick={downloadPdf}
                    >
                      <Download size={15} /> {downloading ? "Building PDF…" : "Download PDF"}
                    </button>
                    <button
                      className="btn-secondary !py-2.5 !bg-white/10 !text-horizon !border-horizon/30 hover:!bg-white hover:!text-ink"
                      onClick={deleteAlbum}
                    >
                      <Trash2 size={15} /> Delete
                    </button>
                  </div>
                </div>
              </section>

              <PhotoUploader
                files={files}
                setFiles={setFiles}
                uploading={uploading}
                uploadProgress={uploadProgress}
                fileErrors={fileErrors}
                photoCount={selected.photos.length}
                onUpload={uploadPhotos}
              />

              {selected.photos.length > 0 && (
                <section className="mt-8">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="eyebrow">The gallery</div>
                      <h3 className="mt-2 font-display text-2xl">Your trip in pictures</h3>
                    </div>
                  </div>
                  <div className="mt-5 columns-2 md:columns-3 gap-4">
                    {selected.photos.map((photo, index) => (
                      <figure
                        key={photo.id}
                        className="mb-4 break-inside-avoid overflow-hidden rounded-2xl bg-white border border-ink/8 shadow-sm group"
                      >
                        <img
                          src={mediaUrl(photo.public_url)}
                          alt={photo.caption || `Trip photo ${index + 1}`}
                          className="w-full h-auto transition-transform duration-500 group-hover:scale-[1.03]"
                          loading="lazy"
                        />
                        <figcaption className="px-3 py-2.5 text-xs text-charcoal/60 truncate">
                          {photo.caption || photo.filename}
                        </figcaption>
                      </figure>
                    ))}
                  </div>
                </section>
              )}
            </main>
          )}
        </div>
      )}

      {showCreate && (
        <CreateAlbumModal
          form={form}
          setForm={setForm}
          saving={saving}
          onClose={() => { setShowCreate(false); setForm(emptyForm); setError(""); }}
          onSubmit={createAlbum}
        />
      )}
    </div>
  );
}

function PhotoUploader({
  files,
  setFiles,
  uploading,
  uploadProgress,
  fileErrors,
  photoCount,
  onUpload,
}: {
  files: File[];
  setFiles: (files: File[]) => void;
  uploading: boolean;
  uploadProgress: { index: number; total: number; percent: number; label: string } | null;
  fileErrors: string[];
  photoCount: number;
  onUpload: () => void;
}) {
  const remaining = Math.max(0, MAX_PHOTOS_PER_ALBUM - photoCount);

  const pickFiles = (list: FileList | null) => {
    const next = Array.from(list ?? []);
    const accepted: File[] = [];
    const rejected: string[] = [];
    for (const file of next) {
      const err = validateImageFile(file);
      if (err) rejected.push(`${file.name}: ${err}`);
      else accepted.push(file);
    }
    setFiles(accepted.slice(0, Math.max(remaining, 0)));
  };

  return (
    <section className="mt-7 ticket-card">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <div className="label-mono">Add memories</div>
          <h3 className="mt-1 font-display text-xl">Upload your trip photos</h3>
          <p className="mt-1 text-xs text-charcoal/55">
            {photoCount}/{MAX_PHOTOS_PER_ALBUM} photos · max {MAX_PHOTO_SIZE_MB}MB each · auto-compressed
          </p>
        </div>
        {files.length > 0 && (
          <button className="btn-primary !py-2.5" disabled={uploading || remaining === 0} onClick={onUpload}>
            <Upload size={15} />{" "}
            {uploading
              ? `Uploading… ${uploadProgress?.percent ?? 0}%`
              : `Upload ${files.length} photo${files.length === 1 ? "" : "s"}`}
          </button>
        )}
      </div>

      {uploadProgress && (
        <div className="mt-4">
          <div className="flex justify-between text-xs text-charcoal/60 mb-1.5">
            <span>{uploadProgress.label}</span>
            <span>{uploadProgress.percent}%</span>
          </div>
          <div className="h-2 rounded-full bg-ink/10 overflow-hidden">
            <div
              className="h-full bg-poppy transition-all duration-300"
              style={{ width: `${uploadProgress.percent}%` }}
            />
          </div>
        </div>
      )}

      <label className="mt-5 block cursor-pointer rounded-2xl border-2 border-dashed border-ink/15 bg-stamp/35 p-7 text-center hover:border-poppy/50 hover:bg-poppy/5 transition">
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          className="hidden"
          disabled={uploading || remaining === 0}
          onChange={(event) => {
            pickFiles(event.target.files);
            event.target.value = "";
          }}
        />
        <div className="w-11 h-11 rounded-xl bg-ink text-horizon flex items-center justify-center mx-auto">
          <Images size={19} />
        </div>
        <div className="mt-3 font-medium text-ink">
          {remaining === 0
            ? `Album full (max ${MAX_PHOTOS_PER_ALBUM} photos)`
            : files.length
              ? `${files.length} photos ready`
              : "Choose photos to upload"}
        </div>
        <div className="mt-1 label-mono">
          JPG, PNG or WebP · up to {MAX_PHOTO_SIZE_MB}MB · {remaining} slot{remaining === 1 ? "" : "s"} left
        </div>
      </label>

      {fileErrors.length > 0 && (
        <ul className="mt-4 space-y-1.5 text-sm text-poppy">
          {fileErrors.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

function CreateAlbumModal({
  form,
  setForm,
  saving,
  onClose,
  onSubmit,
}: {
  form: AlbumCreate;
  setForm: (form: AlbumCreate) => void;
  saving: boolean;
  onClose: () => void;
  onSubmit: (event: FormEvent) => void;
}) {
  return (
    <div className="fixed inset-0 z-50 bg-ink/55 backdrop-blur-sm p-4 flex items-center justify-center" onMouseDown={onClose}>
      <div className="ticket-card w-full max-w-lg !p-7 md:!p-8 max-h-[90vh] overflow-y-auto" onMouseDown={(event) => event.stopPropagation()}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="eyebrow">New keepsake</div>
            <h2 className="mt-2 font-display text-3xl">Create a trip album</h2>
          </div>
          <button className="btn-ghost !p-2" onClick={onClose} aria-label="Close">
            <X size={19} />
          </button>
        </div>
        <form className="mt-7 space-y-4" onSubmit={onSubmit}>
          <label className="block">
            <span className="label-mono">Album title</span>
            <input
              required
              maxLength={200}
              className="input-field mt-1.5"
              placeholder="Summer in Lisbon"
              value={form.title}
              onChange={(event) => setForm({ ...form, title: event.target.value })}
            />
          </label>
          <label className="block">
            <span className="label-mono">Destination</span>
            <input
              className="input-field mt-1.5"
              placeholder="Lisbon, Portugal"
              value={form.destination}
              onChange={(event) => setForm({ ...form, destination: event.target.value })}
            />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="label-mono">Start date</span>
              <input
                type="date"
                className="input-field mt-1.5"
                value={form.trip_start}
                onChange={(event) => setForm({ ...form, trip_start: event.target.value })}
              />
            </label>
            <label className="block">
              <span className="label-mono">End date</span>
              <input
                type="date"
                className="input-field mt-1.5"
                value={form.trip_end}
                onChange={(event) => setForm({ ...form, trip_end: event.target.value })}
              />
            </label>
          </div>
          <label className="block">
            <span className="label-mono">A short note</span>
            <textarea
              rows={3}
              maxLength={3000}
              className="input-field mt-1.5 resize-none"
              placeholder="The trip we'll never forget…"
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
            />
          </label>
          <button className="btn-primary w-full" disabled={saving}>
            {saving ? "Creating…" : "Create album"} <ArrowRight size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}

function EmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <section className="mt-12 ticket-card max-w-2xl mx-auto text-center !py-14">
      <div className="w-16 h-16 rounded-2xl bg-ink text-horizon flex items-center justify-center mx-auto shadow-lg">
        <Images size={27} />
      </div>
      <h2 className="mt-5 font-display text-3xl">Your first album starts here</h2>
      <p className="mt-3 text-sm text-charcoal/65 max-w-md mx-auto">
        Create an album, upload your favorite trip photos, and StoryMiles will turn them into a downloadable PDF keepsake.
      </p>
      <button className="btn-primary mt-7" onClick={onCreate}>
        <Plus size={16} /> Create an album
      </button>
    </section>
  );
}

function cleanAlbumRequest(form: AlbumCreate): AlbumCreate {
  return Object.fromEntries(
    Object.entries(form).filter(([, value]) => value !== "")
  ) as AlbumCreate;
}

function messageFrom(cause: unknown) {
  return cause instanceof Error ? cause.message : "Something went wrong";
}

function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") || "trip-album";
}

function formatDates(start: string, end: string | null) {
  const first = new Date(`${start}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  if (!end) return first;
  const last = new Date(`${end}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  return `${first} — ${last}`;
}
