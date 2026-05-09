// Mock data used when settingsStore.demoMode is true (e.g. on a public Vercel
// deployment with no reachable Pi backend). All URLs point at public placeholder
// hosts so the gallery and dataset pages have something to render.

export interface DemoVideo {
  filename: string;
  url: string;
  thumbnail: string;
}

export interface DemoVideoFolder {
  name: string;
  videos: DemoVideo[];
}

export interface DemoImageEntry {
  filename: string; // used for the on-image caption + v-for key
  url: string; // full URL the <q-img> actually loads
}

export interface DemoImageFolder {
  name: string;
  images: DemoImageEntry[];
}

// Mixkit CDN urban / surveillance-style clips (no API key, free for demo use):
//   4148 — people walking on a busy city street
//   4002 — pedestrians crossing a busy street
//   2740 — traffic on a highway, time lapse
const sampleMp4 = 'https://assets.mixkit.co/videos/4148/4148-720.mp4';
const sampleMp4Alt = 'https://assets.mixkit.co/videos/4002/4002-720.mp4';
const sampleMp4Alt2 = 'https://assets.mixkit.co/videos/2740/2740-720.mp4';

const cctvThumb = (seed: number) =>
  `https://picsum.photos/seed/vigilant-cctv-${seed}/640/360`;

export const demoVideoFolders: DemoVideoFolder[] = [
  {
    name: 'May, 07, 2025 - 14:23:45',
    videos: [
      {
        filename: '2025-05-07_14-23-45.mp4',
        url: sampleMp4,
        thumbnail: cctvThumb(1),
      },
      {
        filename: '2025-05-07_15-02-11.mp4',
        url: sampleMp4Alt,
        thumbnail: cctvThumb(2),
      },
    ],
  },
  {
    name: 'May, 06, 2025 - 09:15:02',
    videos: [
      {
        filename: '2025-05-06_09-15-02.mp4',
        url: sampleMp4Alt,
        thumbnail: cctvThumb(3),
      },
    ],
  },
  {
    name: 'May, 05, 2025 - 22:48:30',
    videos: [
      {
        filename: '2025-05-05_22-48-30.mp4',
        url: sampleMp4Alt2,
        thumbnail: cctvThumb(4),
      },
      {
        filename: '2025-05-05_23-12-08.mp4',
        url: sampleMp4,
        thumbnail: cctvThumb(5),
      },
      {
        filename: '2025-05-05_23-44-52.mp4',
        url: sampleMp4Alt,
        thumbnail: cctvThumb(6),
      },
    ],
  },
  {
    name: 'May, 04, 2025 - 17:31:20',
    videos: [
      {
        filename: '2025-05-04_17-31-20.mp4',
        url: sampleMp4Alt2,
        thumbnail: cctvThumb(7),
      },
    ],
  },
];

// Build a synthetic per-person dataset using randomuser.me's portrait API.
// Each call returns the same person for a given (gender, n), so we end up
// with non-overlapping ranges per folder — Alice always uses women 0–49,
// Bob always uses men 0–49, etc. — which gives the visual feel of a real
// face-recognition dataset (lots of photos per identity, no cross-folder
// duplicates).
const portrait = (gender: 'women' | 'men', n: number) =>
  `https://randomuser.me/api/portraits/${gender}/${n}.jpg`;

const buildDataset = (
  personSlug: string,
  gender: 'women' | 'men',
  startN: number,
  count: number
): DemoImageEntry[] => {
  const entries: DemoImageEntry[] = [];
  for (let i = 0; i < count; i++) {
    const n = startN + i;
    entries.push({
      filename: `${personSlug}_${String(i + 1).padStart(3, '0')}.jpg`,
      url: portrait(gender, n),
    });
  }
  return entries;
};

export const demoImageFolders: DemoImageFolder[] = [
  { name: 'Alice', images: buildDataset('alice', 'women', 0, 50) },
  { name: 'Bob', images: buildDataset('bob', 'men', 0, 50) },
  { name: 'Carol', images: buildDataset('carol', 'women', 50, 50) },
  { name: 'David', images: buildDataset('david', 'men', 50, 50) },
];

export const findDemoVideoFolder = (name: string) =>
  demoVideoFolders.find((f) => f.name === name);

export const findDemoImageFolder = (name: string) =>
  demoImageFolders.find((f) => f.name === name);

export interface DemoLogEntry {
  event_type: 'motion' | 'unknown' | 'known';
  timestamp: number; // seconds into the clip
  extra?: { name?: string };
}

// Per-video deterministic detection log: same set of entries every time you
// open a given clip, so seek-on-click feels like real recorded data instead
// of reshuffling on every render.
export const buildDemoLogs = (videoFilename: string): DemoLogEntry[] => {
  let seed = 2166136261;
  for (let i = 0; i < videoFilename.length; i++) {
    seed ^= videoFilename.charCodeAt(i);
    seed = Math.imul(seed, 16777619) >>> 0;
  }
  const rand = () => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    return seed / 0xffffffff;
  };

  // Demo clips are ~10s. Spread 3–5 events across the timeline.
  const count = 3 + Math.floor(rand() * 3);
  const entries: DemoLogEntry[] = [];
  let t = 0.5 + rand() * 0.8;
  for (let i = 0; i < count; i++) {
    if (t > 9) break;
    const roll = rand();
    const event_type: DemoLogEntry['event_type'] =
      roll < 0.4 ? 'motion' : roll < 0.75 ? 'known' : 'unknown';
    const entry: DemoLogEntry = {
      event_type,
      timestamp: Math.round(t * 10) / 10,
    };
    if (event_type === 'known') {
      entry.extra = {
        name: demoKnownNames[Math.floor(rand() * demoKnownNames.length)],
      };
    } else if (event_type === 'unknown') {
      entry.extra = { name: 'Intruder' };
    }
    entries.push(entry);
    t += 1.2 + rand() * 2.4;
  }
  return entries;
};

// Synthetic notification feed used when demoMode is on. Mix of friendly +
// alarming events so the side panel feels alive on the live-stream page.
const demoKnownNames = ['Alice', 'Bob', 'Carol', 'David'];

const formatDemoTime = (d = new Date()) =>
  d.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });

export interface DemoNotification {
  message: string;
  // Quasar Notify type: 'positive' | 'negative' | 'warning' | 'info'
  level: 'positive' | 'negative' | 'warning' | 'info';
}

// Demo Telegram operators — names rotate so the chat feels populated rather
// than a single user spamming commands.
const demoTelegramOperators = ['@john', '@maria', '@admin'];

export const buildRandomDemoNotification = (): DemoNotification => {
  const time = formatDemoTime();
  const known =
    demoKnownNames[Math.floor(Math.random() * demoKnownNames.length)];
  const op =
    demoTelegramOperators[
      Math.floor(Math.random() * demoTelegramOperators.length)
    ];
  const angle = Math.floor(Math.random() * 181); // 0–180
  const pool: DemoNotification[] = [
    // Sensor / vision events
    {
      message: `[${time}] Motion detected by PIR sensor.`,
      level: 'warning',
    },
    {
      message: `[${time}] Known face recognized: ${known}.`,
      level: 'positive',
    },
    {
      message: `[${time}] Unknown face detected — possible intruder.`,
      level: 'negative',
    },
    {
      message: `[${time}] ${known} entered the frame.`,
      level: 'info',
    },
    {
      message: `[${time}] No motion for 60s — area clear.`,
      level: 'info',
    },
    {
      message: `[${time}] Servo patrol completed a sweep.`,
      level: 'info',
    },
    {
      message: `[${time}] Buzzer triggered by intruder alert.`,
      level: 'warning',
    },
    // Telegram bot command triggers (mirrors the handlers in Server.py)
    {
      message: `[${time}] Telegram: ${op} sent /enable_motion — motion sensor armed.`,
      level: 'info',
    },
    {
      message: `[${time}] Telegram: ${op} sent /disable_motion — motion sensor disarmed.`,
      level: 'warning',
    },
    {
      message: `[${time}] Telegram: ${op} sent /enable_sound — buzzer enabled.`,
      level: 'info',
    },
    {
      message: `[${time}] Telegram: ${op} sent /disable_sound — buzzer muted.`,
      level: 'info',
    },
    {
      message: `[${time}] Telegram: ${op} sent /enable_led — LED on.`,
      level: 'positive',
    },
    {
      message: `[${time}] Telegram: ${op} sent /disable_led — LED off.`,
      level: 'info',
    },
    {
      message: `[${time}] Telegram: ${op} sent /enable_servo — servo enabled.`,
      level: 'info',
    },
    {
      message: `[${time}] Telegram: ${op} sent /disable_servo — servo locked.`,
      level: 'info',
    },
    {
      message: `[${time}] Telegram: ${op} sent /servo_angle ${angle} — moved to ${angle}°.`,
      level: 'info',
    },
    {
      message: `[${time}] Telegram: ${op} sent /patrol — sweeping 0°→180°→0°.`,
      level: 'info',
    },
    {
      message: `[${time}] Telegram: ${op} sent /snap — snapshot pushed to chat.`,
      level: 'positive',
    },
    {
      message: `[${time}] Telegram: ${op} sent /status — system report delivered.`,
      level: 'info',
    },
  ];
  return pool[Math.floor(Math.random() * pool.length)];
};

// Pre-seeded notifications so the side panel isn't empty on first load.
export const buildDemoNotificationSeed = (): DemoNotification[] => {
  const now = Date.now();
  const t = (offsetSec: number) =>
    formatDemoTime(new Date(now - offsetSec * 1000));
  return [
    {
      message: `[${t(210)}] Camera service started.`,
      level: 'info',
    },
    {
      message: `[${t(168)}] Telegram: @admin sent /enable_motion — motion sensor armed.`,
      level: 'info',
    },
    {
      message: `[${t(122)}] Known face recognized: Alice.`,
      level: 'positive',
    },
    {
      message: `[${t(75)}] Motion detected by PIR sensor.`,
      level: 'warning',
    },
    {
      message: `[${t(40)}] Telegram: @john sent /snap — snapshot pushed to chat.`,
      level: 'positive',
    },
    {
      message: `[${t(12)}] Unknown face detected — possible intruder.`,
      level: 'negative',
    },
  ];
};
