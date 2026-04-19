# FRONTEND THEME — Skeuomorphic Design System

## Overview

**Product**: SOLV.ai  
**Design Style**: Pure Skeuomorphism  
**Theme**: Dark Mode with Realistic Depth

## Design Philosophy

Skeuomorphism creates realistic, tactile interfaces that mimic physical objects. Every element has:
- **Depth through shadows** — Light source from top-left (135° angle)
- **Realistic textures** — Gradients simulating material surfaces
- **Pressed vs. raised states** — Visible depth changes on interaction
- **Premium feel** — Refined, expensive aesthetic with careful attention to detail

---

## Color Palette

### Background Colors — Cool Dark Theme

| Role | Color | HEX | Usage |
|---|---|---|---|
| **Primary BG** | Deep Black | `#0D0D0F` | Main page background |
| **Secondary BG** | Charcoal | `#1A1A1D` | Cards, elevated surfaces |
| **Tertiary BG** | Dark Gray | `#2A2A2E` | Inputs, buttons, pressed states |
| **Card BG** | Soft Black | `#1C1C1F` | Card backgrounds |

### Primary Colors — Reddish Saffron

| Role | Color | HEX | Usage |
|---|---|---|---|
| **Primary** | Saffron Orange | `#FF4500` | CTAs, accents, headings |
| **Primary Light** | Light Saffron | `#FF6B35` | Hover states, gradients |
| **Primary Dark** | Dark Saffron | `#CC3700` | Active states, shadows |

### Text Colors

| Role | Color | HEX | Usage |
|---|---|---|---|
| **Primary Text** | Off White | `#F5F5F5` | Body text, important content |
| **Secondary Text** | Gray | `#9CA3AF` | Secondary text, labels |
| **Muted Text** | Dark Gray | `#6B7280` | Placeholder text, hints |

### Priority Colors — Clear Visual Hierarchy

| Priority | Color | HEX | Dark Shade | Usage |
|---|---|---|---|---|
| **Low** | Green | `#22C55E` | `#166534` | Standard items |
| **Medium** | Blue | `#3B82F6` | `#1E40AF` | Elevated attention |
| **High** | Red | `#EF4444` | `#B91C1C` | Critical urgency |

---

## Typography

### Headings — Tall, Formal, Impactful

```css
.heading-display {
  font-family: 'SF Pro Display', -apple-system, sans-serif;
  font-weight: 800;
  font-stretch: 125%;      /* Makes text taller */
  text-transform: uppercase;
  letter-spacing: 0.02em;
  line-height: 0.92;
  transform: scaleY(1.12); /* Additional height stretch */
}
```

**Heading Scale:**
- `heading-sm`: 1.75rem
- `heading-md`: 2.5rem
- `heading-lg`: 3.5rem
- `heading-xl`: 5rem
- `heading-2xl`: 6.5rem

### Body Text

```css
body {
  font-family: 'SF Pro Display', -apple-system, sans-serif;
  font-size: 15px;
  line-height: 1.6;
  color: #F5F5F5;
  background: #0D0D0F;
}
```

---

## Skeuomorphic Shadows

### Light Source
- **Direction**: Top-left (135° angle)
- **Highlights**: Top and left edges
- **Shadows**: Bottom and right edges

### Shadow System

```css
/* Raised Elements */
--shadow-raised: 
  8px 8px 16px rgba(0, 0, 0, 0.8),        /* Bottom-right shadow */
  -8px -8px 16px rgba(255, 255, 255, 0.03), /* Top-left highlight */
  inset 1px 1px 2px rgba(255, 255, 255, 0.05); /* Inner top-left glow */

/* Pressed Elements */
--shadow-pressed: 
  inset 6px 6px 12px rgba(0, 0, 0, 0.8),     /* Inner shadow */
  inset -6px -6px 12px rgba(255, 255, 255, 0.02); /* Inner highlight */

/* Cards */
--shadow-card: 
  12px 12px 24px rgba(0, 0, 0, 0.7),
  -12px -12px 24px rgba(255, 255, 255, 0.02),
  inset 1px 1px 2px rgba(255, 255, 255, 0.05);

/* Buttons — Primary */
--shadow-button: 
  0 4px 0 #CC3700,                              /* Bottom border for 3D effect */
  0 8px 16px rgba(255, 69, 0, 0.3),            /* Drop shadow */
  inset 0 1px 0 rgba(255, 255, 255, 0.3);       /* Top highlight */

/* Buttons — Active/Pressed */
--shadow-button-active:
  0 0 0 #CC3700,                                /* No bottom border when pressed */
  0 2px 8px rgba(255, 69, 0, 0.3),
  inset 0 2px 4px rgba(0, 0, 0, 0.3);           /* Inner shadow */
```

---

## Components

### Cards

```css
.card-skeuo {
  background: linear-gradient(165deg, #2A2A2E 0%, #1C1C1F 100%);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 
    12px 12px 24px rgba(0, 0, 0, 0.7),
    -12px -12px 24px rgba(255, 255, 255, 0.02),
    inset 1px 1px 2px rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.03);
}

.card-skeuo::before {
  /* Top highlight line */
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.08), transparent);
}

.card-pressed {
  background: #2A2A2E;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 
    inset 6px 6px 12px rgba(0, 0, 0, 0.8),
    inset -6px -6px 12px rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(0, 0, 0, 0.3);
}
```

### Buttons

#### Primary Button (with Press Animation)

```css
.btn-primary-skeuo {
  background: linear-gradient(165deg, #FF6B35 0%, #FF4500 50%, #CC3700 100%);
  color: #000;
  border: none;
  border-radius: 12px;
  padding: 14px 32px;
  font-weight: 700;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  box-shadow: 
    0 4px 0 #CC3700,                    /* 3D depth */
    0 8px 16px rgba(255, 69, 0, 0.3),   /* Drop shadow */
    inset 0 1px 0 rgba(255, 255, 255, 0.3); /* Top shine */
  transform: translateY(0);
  transition: all 0.15s ease;
}

.btn-primary-skeuo:hover {
  box-shadow: 
    0 5px 0 #CC3700,
    0 10px 20px rgba(255, 69, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.btn-primary-skeuo:active,
.btn-primary-skeuo.pressed {
  box-shadow: 
    0 0 0 #CC3700,                     /* Loses depth when pressed */
    0 2px 8px rgba(255, 69, 0, 0.3),
    inset 0 2px 4px rgba(0, 0, 0, 0.3); /* Inner shadow */
  transform: translateY(4px);           /* Moves down */
}
```

#### Secondary Button

```css
.btn-skeuo {
  background: linear-gradient(165deg, #2A2A2E 0%, #1C1C1F 100%);
  color: #F5F5F5;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 14px 32px;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.6),
    -6px -6px 12px rgba(255, 255, 255, 0.04),
    inset 1px 1px 1px rgba(255, 255, 255, 0.1);
}

.btn-skeuo:hover {
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.7),
    -4px -4px 8px rgba(255, 255, 255, 0.03);
  transform: translateY(-1px);
}

.btn-skeuo:active {
  box-shadow: 
    inset 4px 4px 8px rgba(0, 0, 0, 0.8),
    inset -4px -4px 8px rgba(255, 255, 255, 0.02);
  transform: translateY(1px) scale(0.98);
}
```

### Input Fields (Inset Style)

```css
.input-skeuo {
  background: #2A2A2E;
  border: none;
  border-radius: 12px;
  padding: 16px 20px;
  font-size: 15px;
  color: #F5F5F5;
  width: 100%;
  box-shadow: 
    inset 4px 4px 8px rgba(0, 0, 0, 0.6),
    inset -4px -4px 8px rgba(255, 255, 255, 0.02);
}

.input-skeuo:focus {
  box-shadow: 
    inset 4px 4px 8px rgba(0, 0, 0, 0.7),
    inset -4px -4px 8px rgba(255, 255, 255, 0.02),
    0 0 0 2px rgba(255, 69, 0, 0.3);    /* Focus ring */
}
```

### Priority Tags (3D Pills)

```css
/* Low Priority - Green */
.tag-low {
  background: linear-gradient(165deg, #22C55E 0%, #16A34A 50%, #15803D 100%);
  color: #000;
  border-radius: 9999px;
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  box-shadow: 
    0 2px 0 #166534,
    0 4px 8px rgba(34, 197, 94, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

/* Medium Priority - Blue */
.tag-medium {
  background: linear-gradient(165deg, #3B82F6 0%, #2563EB 50%, #1D4ED8 100%);
  color: #fff;
  box-shadow: 
    0 2px 0 #1E40AF,
    0 4px 8px rgba(59, 130, 246, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

/* High Priority - Red */
.tag-high {
  background: linear-gradient(165deg, #EF4444 0%, #DC2626 50%, #B91C1C 100%);
  color: #fff;
  box-shadow: 
    0 2px 0 #991B1B,
    0 4px 8px rgba(239, 68, 68, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}
```

### Progress Bar (Inset Track)

```css
.progress-track-skeuo {
  background: #2A2A2E;
  border-radius: 9999px;
  height: 12px;
  overflow: hidden;
  box-shadow: 
    inset 4px 4px 8px rgba(0, 0, 0, 0.6),
    inset -4px -4px 8px rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(0, 0, 0, 0.3);
}

.progress-fill-skeuo {
  height: 100%;
  background: linear-gradient(165deg, #FF4500 0%, #CC3700 100%);
  border-radius: 9999px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.3);
}
```

### Display Panel (Screen Effect)

```css
.display-panel {
  background: linear-gradient(180deg, #2A2A2E 0%, #1C1C1F 50%, #151518 100%);
  border-radius: 12px;
  box-shadow: 
    inset 4px 4px 8px rgba(0, 0, 0, 0.6),
    inset -4px -4px 8px rgba(255, 255, 255, 0.02),
    0 0 0 1px rgba(255, 255, 255, 0.05);
  padding: 16px;
  position: relative;
}

.display-panel::after {
  /* Screen reflection */
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.03) 0%, transparent 10%);
  pointer-events: none;
}
```

---

## GSAP Animations

### Button Press Animation

```typescript
const handleButtonPress = (e: React.MouseEvent<HTMLButtonElement>) => {
  const button = e.currentTarget;
  
  gsap.to(button, {
    y: 4,
    scale: 0.98,
    boxShadow: '0 0 0 #CC3700, 0 2px 8px rgba(255, 69, 0, 0.3), inset 0 2px 4px rgba(0, 0, 0, 0.3)',
    duration: 0.1,
    ease: 'power2.inOut',
  });
};

const handleButtonRelease = (e: React.MouseEvent<HTMLButtonElement>) => {
  const button = e.currentTarget;
  
  gsap.to(button, {
    y: 0,
    scale: 1,
    boxShadow: '0 4px 0 #CC3700, 0 8px 16px rgba(255, 69, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.3)',
    duration: 0.15,
    ease: 'power3.out',
  });
};
```

### Hero Text Reveal

```typescript
const tl = gsap.timeline({ delay: 0.3 });

tl.fromTo(
  '.hero-title-line',
  { opacity: 0, y: 60, rotateX: -30 },
  {
    opacity: 1,
    y: 0,
    rotateX: 0,
    duration: 0.9,
    stagger: 0.15,
    ease: 'power3.out',
  }
);
```

### Card Stagger Reveal (ScrollTrigger)

```typescript
gsap.fromTo(
  '.card',
  { opacity: 0, y: 80, rotateX: -15 },
  {
    opacity: 1,
    y: 0,
    rotateX: 0,
    duration: 0.8,
    stagger: 0.12,
    ease: 'power3.out',
    scrollTrigger: {
      trigger: '.cards-container',
      start: 'top 80%',
      toggleActions: 'play none none none',
    },
  }
);
```

---

## Navigation

```css
.nav-skeuo {
  background: linear-gradient(165deg, #252528 0%, #1A1A1D 100%);
  box-shadow: 
    0 4px 0 rgba(0, 0, 0, 0.5),
    0 8px 32px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}

.nav-item-skeuo {
  background: transparent;
  border-radius: 12px;
  padding: 10px 18px;
  color: #9CA3AF;
  font-weight: 500;
  font-size: 14px;
  border: 1px solid transparent;
  transition: all 0.2s ease;
}

.nav-item-skeuo:hover {
  background: #2A2A2E;
  color: #F5F5F5;
  box-shadow: 
    inset 4px 4px 8px rgba(0, 0, 0, 0.6),
    inset -4px -4px 8px rgba(255, 255, 255, 0.02);
}

.nav-item-skeuo.active {
  background: #2A2A2E;
  color: #FF4500;
  box-shadow: 
    inset 4px 4px 8px rgba(0, 0, 0, 0.6),
    inset -4px -4px 8px rgba(255, 255, 255, 0.02);
  border-color: rgba(255, 69, 0, 0.3);
}
```

---

## Scrollbar Styling

```css
::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

::-webkit-scrollbar-track {
  background: #1A1A1D;
  box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.5);
}

::-webkit-scrollbar-thumb {
  background: #2A2A2E;
  border-radius: 5px;
  box-shadow: 
    inset 1px 1px 2px rgba(255, 255, 255, 0.05),
    2px 2px 4px rgba(0, 0, 0, 0.3);
}

::-webkit-scrollbar-thumb:hover {
  background: #3A3A3E;
}
```

---

## Accessibility

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
  
  /* Disable all transforms on reduced motion */
  .btn-skeuo:hover,
  .btn-primary-skeuo:hover,
  .card-skeuo:hover {
    transform: none !important;
  }
}
```

---

## Key Implementation Notes

1. **Light Source Consistency**: All shadows assume light from top-left at 135°
2. **Depth Hierarchy**: Use multiple shadow layers for realistic depth
3. **Press Animation**: Primary buttons have a physical 3D press effect using `translateY(4px)`
4. **Inset Elements**: Inputs and pressed states use `inset` shadows
5. **Highlight Lines**: Add subtle gradient lines at top of raised elements
6. **Smooth Transitions**: All interactive elements have 0.15-0.2s transitions
7. **Lenis Smooth Scroll**: Always connect to GSAP ScrollTrigger for sync
