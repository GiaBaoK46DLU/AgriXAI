/** Trích id video từ vài dạng URL YouTube phổ biến, trả về URL nhúng
 * `youtube.com/embed/<id>`. Trả `null` nếu không nhận ra dạng URL. */
export function toYoutubeEmbedUrl(url: string): string | null {
  try {
    const parsed = new URL(url);
    let id: string | null = null;

    if (parsed.hostname.includes("youtu.be")) {
      id = parsed.pathname.slice(1);
    } else if (parsed.hostname.includes("youtube.com")) {
      if (parsed.pathname === "/watch") {
        id = parsed.searchParams.get("v");
      } else if (parsed.pathname.startsWith("/embed/")) {
        id = parsed.pathname.replace("/embed/", "");
      } else if (parsed.pathname.startsWith("/shorts/")) {
        id = parsed.pathname.replace("/shorts/", "");
      }
    }

    return id ? `https://www.youtube.com/embed/${id}` : null;
  } catch {
    return null;
  }
}
