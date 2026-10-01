const Youtube = require("simple-youtube-api");

const apiKey = process.env.GOOGLE_API_KEY;
const hasApiKey = Boolean(apiKey) && !apiKey.startsWith("<");
const youtubeApi = hasApiKey ? new Youtube(apiKey) : null;

const extractVideoId = (url = "") => {
  const match = String(url).match(/(?:youtu\.be\/|[?&]v=|\/embed\/|\/shorts\/|\/live\/)([\w-]{11})/);
  return match ? match[1] : null;
};

// Fallback when no YouTube Data API key is configured: read the duration
// from the public watch page, which embeds `"lengthSeconds":"<n>"`.
const getDurationFromWatchPage = async (videoId) => {
  const response = await fetch(`https://www.youtube.com/watch?v=${videoId}`, {
    headers: { "Accept-Language": "en-US,en;q=0.9", "User-Agent": "Mozilla/5.0" },
  });
  if (!response.ok) throw new Error(`YouTube watch page returned ${response.status}`);
  const html = await response.text();
  const match = html.match(/"lengthSeconds":"(\d+)"/);
  if (!match) throw new Error("Couldn't read video duration from YouTube");
  return parseInt(match[1], 10);
};

const getVideo = async (url) => {
  const videoId = extractVideoId(url);
  if (!videoId) throw new Error("Invalid YouTube URL");

  if (youtubeApi) {
    try {
      const { durationSeconds } = await youtubeApi.getVideo(url);
      return { durationSeconds };
    } catch (error) {
      console.log("YouTube API failed, falling back to watch page:", error.message || error);
    }
  }

  return { durationSeconds: await getDurationFromWatchPage(videoId) };
};

module.exports = { youtube: { getVideo }, extractVideoId };
