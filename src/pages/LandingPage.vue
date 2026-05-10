<template>
  <q-page class="landing-page">
    <div class="bg-orbs">
      <span class="orb orb-1" />
      <span class="orb orb-2" />
      <span class="orb orb-3" />
    </div>

    <header class="landing-header">
      <div class="row items-center q-gutter-sm">
        <img
          src="/icons/vigilant.png"
          alt="Vigilant Eye logo"
          class="brand-logo"
        />
        <span class="text-h6 text-weight-bold text-white">Vigilant Eye</span>
      </div>
      <q-btn
        unelevated
        color="accent"
        label="Sign In"
        icon-right="arrow_forward"
        @click="goToLogin"
      />
    </header>

    <section class="hero">
      <div class="hero-copy">
        <q-chip
          square
          color="accent"
          text-color="white"
          icon="visibility"
          class="hero-chip"
        >
          AI-powered home surveillance
        </q-chip>
        <h1 class="hero-title">
          Eyes on every corner,<br />
          <span class="text-accent">smarts behind every frame.</span>
        </h1>
        <p class="hero-subtitle">
          Vigilant Eye turns a Raspberry Pi camera into a private, on-prem
          security system. It streams live video, recognizes faces you've
          trained it on, records footage to local storage, and pings you on
          Telegram the moment something it doesn't recognize walks into view.
        </p>
        <div class="hero-actions">
          <q-btn
            size="lg"
            color="accent"
            label="Try Demo"
            icon-right="login"
            push
            @click="goToLogin"
          />
          <q-btn
            size="lg"
            outline
            color="white"
            label="Learn More"
            icon="arrow_downward"
            @click="scrollToFeatures"
          />
        </div>
      </div>

      <div class="hero-visual">
        <div class="visual-frame">
          <div class="frame-grid" />
          <q-icon name="videocam" class="frame-icon" />
          <div class="frame-pulse" />
          <div class="frame-tag">
            <q-icon name="circle" color="red" size="10px" class="q-mr-xs" />
            LIVE
          </div>
        </div>
      </div>
    </section>

    <section ref="featuresSection" class="features">
      <h2 class="section-title">What it does</h2>
      <div class="features-grid">
        <div
          v-for="feature in features"
          :key="feature.title"
          class="feature-card"
        >
          <q-icon :name="feature.icon" size="36px" color="accent" />
          <h3 class="feature-title">{{ feature.title }}</h3>
          <p class="feature-desc">{{ feature.desc }}</p>
        </div>
      </div>
    </section>

    <section class="how-it-works">
      <h2 class="section-title">How it works</h2>
      <div class="steps">
        <div v-for="(step, idx) in steps" :key="step.title" class="step">
          <div class="step-number">{{ idx + 1 }}</div>
          <div>
            <h4 class="step-title">{{ step.title }}</h4>
            <p class="step-desc">{{ step.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="cta">
      <h2 class="cta-title">Ready to keep watch?</h2>
      <p class="cta-subtitle">
        Sign in to start streaming, train new faces, and review saved footage.
      </p>
      <q-btn
        size="lg"
        color="accent"
        label="Sign In"
        icon-right="arrow_forward"
        push
        @click="goToLogin"
      />
    </section>

    <footer class="landing-footer">
      <span>Vigilant Eye 2023-2024</span>
    </footer>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const featuresSection = ref<HTMLElement | null>(null);

const features = [
  {
    icon: 'live_tv',
    title: 'Live MJPEG Stream',
    desc: 'Watch your camera in real time from any browser on the LAN. Pause, resume, and start recordings on demand.',
  },
  {
    icon: 'face_retouching_natural',
    title: 'Face Recognition',
    desc: "Train it on the people you know. The Pi loads your encodings and flags anyone it doesn't recognize as an intruder.",
  },
  {
    icon: 'notifications_active',
    title: 'Telegram Alerts',
    desc: 'Get instant messages when motion is detected or an unknown face appears. Rate-limited so your phone stays sane.',
  },
  {
    icon: 'video_library',
    title: 'Media Library',
    desc: 'All recordings and snapshots are saved to local storage and organized by date. Browse, rename, and download from the dashboard.',
  },
  {
    icon: 'memory',
    title: 'GPIO Peripherals',
    desc: 'Drive a buzzer, servo, LED, and PIR sensor straight from the dashboard or via Telegram bot commands.',
  },
  {
    icon: 'lock',
    title: 'Stays On Your Network',
    desc: 'No cloud, no third-party video pipeline. Footage and face data never leave the Pi unless you tell them to.',
  },
];

const steps = [
  {
    title: 'Train',
    desc: 'Upload a folder of photos for each known person. The Pi rebuilds its face encodings.',
  },
  {
    title: 'Stream',
    desc: 'The dashboard pulls a live MJPEG feed straight from the camera service running on port 5002.',
  },
  {
    title: 'Detect & Alert',
    desc: 'Faces are matched on every frame. Unknown matches and PIR motion fire a Telegram notification.',
  },
  {
    title: 'Review',
    desc: 'Recordings land in dated folders. Browse, rename, or pull them down from the Media Library tab.',
  },
];

const goToLogin = () => {
  router.push('/login');
};

const scrollToFeatures = () => {
  featuresSection.value?.scrollIntoView({ behavior: 'smooth' });
};
</script>

<style lang="scss" scoped>
.landing-page {
  position: relative;
  min-height: 100vh;
  background: radial-gradient(
      ellipse at top,
      rgba(76, 6, 92, 0.6),
      transparent 60%
    ),
    linear-gradient(180deg, #1a0529 0%, #0c0218 100%);
  color: #f4eef9;
  overflow-x: hidden;
}

.bg-orbs {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.45;
}
.orb-1 {
  width: 480px;
  height: 480px;
  top: -120px;
  left: -120px;
  background: #6a1b9a;
}
.orb-2 {
  width: 380px;
  height: 380px;
  top: 35%;
  right: -100px;
  background: #c2185b;
}
.orb-3 {
  width: 300px;
  height: 300px;
  bottom: -80px;
  left: 30%;
  background: #4c065c;
}

.landing-header,
.hero,
.features,
.how-it-works,
.cta,
.landing-footer {
  position: relative;
  z-index: 1;
}

.landing-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 64px;
}

.brand-logo {
  height: 44px;
  width: auto;
  object-fit: contain;
  display: block;
}

.hero {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 48px;
  align-items: center;
  padding: 64px 64px 96px;
  max-width: 1280px;
  margin: 0 auto;
}

.hero-chip {
  margin-bottom: 24px;
  font-weight: 500;
}

.hero-title {
  font-size: 3.5rem;
  line-height: 1.1;
  font-weight: 800;
  margin: 0 0 24px;
  letter-spacing: -0.02em;
}

.hero-subtitle {
  font-size: 1.125rem;
  line-height: 1.6;
  color: rgba(244, 238, 249, 0.75);
  max-width: 560px;
  margin: 0 0 32px;
}

.hero-actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.hero-visual {
  display: flex;
  justify-content: center;
}

.visual-frame {
  position: relative;
  width: 360px;
  height: 360px;
  border-radius: 24px;
  background: linear-gradient(135deg, #2a0a3d, #4c065c);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 30px 80px rgba(76, 6, 92, 0.5);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.frame-grid {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(
      rgba(255, 255, 255, 0.05) 1px,
      transparent 1px
    ),
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 30px 30px;
}

.frame-icon {
  font-size: 120px;
  color: rgba(255, 255, 255, 0.85);
  z-index: 1;
}

.frame-pulse {
  position: absolute;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  border: 2px solid rgba(194, 24, 91, 0.6);
  animation: pulse 2.5s infinite ease-out;
}

@keyframes pulse {
  0% {
    transform: scale(0.6);
    opacity: 0.8;
  }
  100% {
    transform: scale(1.4);
    opacity: 0;
  }
}

.frame-tag {
  position: absolute;
  top: 16px;
  left: 16px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  display: flex;
  align-items: center;
}

.section-title {
  font-size: 2.25rem;
  font-weight: 700;
  text-align: center;
  margin: 0 0 48px;
  letter-spacing: -0.01em;
}

.features {
  padding: 64px 64px;
  max-width: 1280px;
  margin: 0 auto;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.feature-card {
  padding: 32px 28px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(8px);
  transition: transform 0.25s ease, border-color 0.25s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  border-color: rgba(194, 24, 91, 0.6);
}

.feature-title {
  margin: 16px 0 8px;
  font-size: 1.25rem;
  font-weight: 700;
}

.feature-desc {
  margin: 0;
  color: rgba(244, 238, 249, 0.7);
  line-height: 1.55;
}

.how-it-works {
  padding: 64px 64px;
  max-width: 1080px;
  margin: 0 auto;
}

.steps {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 32px;
}

.step {
  display: flex;
  gap: 20px;
  align-items: flex-start;
  padding: 24px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.step-number {
  flex: 0 0 44px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #c2185b, #6a1b9a);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.125rem;
}

.step-title {
  margin: 0 0 6px;
  font-size: 1.125rem;
  font-weight: 700;
}

.step-desc {
  margin: 0;
  color: rgba(244, 238, 249, 0.7);
  line-height: 1.5;
}

.cta {
  text-align: center;
  padding: 96px 32px;
  max-width: 720px;
  margin: 0 auto;
}

.cta-title {
  font-size: 2.5rem;
  font-weight: 800;
  margin: 0 0 16px;
}

.cta-subtitle {
  color: rgba(244, 238, 249, 0.7);
  font-size: 1.125rem;
  margin: 0 0 32px;
}

.landing-footer {
  text-align: center;
  padding: 32px;
  color: rgba(244, 238, 249, 0.45);
  font-size: 0.875rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

@media (max-width: 900px) {
  .landing-header,
  .hero,
  .features,
  .how-it-works {
    padding-left: 24px;
    padding-right: 24px;
  }
  .hero {
    grid-template-columns: 1fr;
    text-align: center;
  }
  .hero-subtitle {
    margin-left: auto;
    margin-right: auto;
  }
  .hero-actions {
    justify-content: center;
  }
  .hero-title {
    font-size: 2.5rem;
  }
  .features-grid {
    grid-template-columns: 1fr;
  }
  .steps {
    grid-template-columns: 1fr;
  }
}
</style>
