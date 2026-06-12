# Art Direction & Creative Brief — Research for AI Image Assistant Persona

**Purpose:** Substance for a "creative director / art director" assistant persona helping hobbyists
with no concrete idea go from vague impulse → realized AI-generated image via CLI (Flux/Qwen/Ideogram).

**Date:** 2026-06-10  
**Sources cited:** 10+ (URLs at bottom)

---

## 1. The Creative Brief Framework

A professional creative brief answers these questions before a single pixel is created.
Adapted here for the single-user AI-image context — the assistant asks these of the human.

### Canonical Brief Sections (in discovery order)

| # | Section | The question to ask | Why it matters |
|---|---------|---------------------|----------------|
| 1 | **Use / destination** | "Where will this live? Phone wallpaper, printed poster, Discord avatar, Notion header?" | Forces aspect ratio + density decision early |
| 2 | **Occasion / trigger** | "What made you think of this now?" | Often reveals the real subject |
| 3 | **Subject** | "What is *in* the image — person, object, scene, abstract?" | The content anchor |
| 4 | **Message / feeling** | "When someone sees this, what should they feel or think?" | Governs mood and palette |
| 5 | **Style / medium** | "Is this a photo, a painting, a drawing, a render?" | Single biggest variable in the prompt |
| 6 | **Mood / atmosphere** | "What's the emotional temperature? Dark and brooding? Warm and cozy? Sharp and editorial?" | Controls lighting + colour treatment |
| 7 | **Palette** | "Any colours you're drawn to? Or avoid?" | Fastest way to make an image feel cohesive |
| 8 | **References** | "Any images — doesn't have to be AI — that feel close to what you want?" | Worth more than all other answers combined |
| 9 | **Mandatories** | "Anything that MUST be in it? Anything that MUST NOT?" | Negative-space constraints that prevent wasted generations |
| 10 | **Deliverable spec** | Aspect ratio (see § 4.6), resolution intent | Technical gate before generation |

### Professional Framing (from Asana / Adobe / FigJam sources)

The brief is NOT a form to fill in — it is a *convergence device*. The goal is to leave the brief
session with:

- One sentence describing the image's purpose
- 3–5 adjectives that should describe the final image
- At least one visual reference (image link, screenshot, description)
- A style / medium anchor
- A destination / aspect ratio

---

## 2. Eliciting Intent From Someone With No Idea

The hardest case: the person opens the chat and says "I want to make something cool."
These techniques convert that vague impulse into a workable brief.

### 2.1 The Emotional-First Approach

Don't ask "what do you want to make?" Ask "how do you want to feel when you look at it?"
Emotions anchor style before subject:

```
"Peaceful and nostalgic"    → soft light, muted palette, vintage medium
"Powerful and edgy"         → high contrast, dark tones, bold composition
"Whimsical and delightful"  → saturated pastels, illustration style, playful subject
"Sleek and modern"          → clean lines, cool tones, minimal detail
```

### 2.2 Adjective Elicitation — Ask for 3–5 Words

"Describe the image you want using 3-5 adjectives. They don't have to make sense together."

These words become: mood → palette → lighting → medium.
Example: "dark, ancient, quiet, stone" → low-key lighting, desaturated earth tones, editorial photo or painterly medium, architectural/ruin subject.

### 2.3 This-or-That Binary Questions

Rapid-fire pairs that build a style profile without requiring design vocabulary:

**Medium:**
- Photograph vs. Painting/Illustration?
- Realistic vs. Stylized/Cartoon?
- Detailed and textured vs. Clean and minimal?

**Mood/Tone:**
- Bright and cheerful vs. Dark and moody?
- Warm tones (amber/gold/orange) vs. Cool tones (blue/silver/teal)?
- Sharp and bold vs. Soft and dreamy?

**Composition:**
- Wide establishing shot vs. Close-up portrait/detail?
- Centered and symmetric vs. Dynamic/asymmetric?
- Busy/intricate vs. Simple/breathing room?

**Genre:**
- Grounded/realistic vs. Fantasy/otherworldly?
- Natural/organic vs. Technological/futuristic?
- Human-focused vs. Landscape/environment?

After 5–6 pairs you have a style profile. Map it to a direction (§ 5).

### 2.4 Reference-First Elicitation

"Share anything — a movie still, a photo you like, a painting, a game screenshot, even a color.
I'll work backwards from what you show me."

References are worth more than any description. A single image eliminates 10 minutes of questioning.
Technique (from Adobe Creative Direction guide): extract a "context profile" from the reference —
composition angle, lighting quality, colour temperature, medium, mood — and use that as the brief.

### 2.5 Occasion / Trigger Question

"What made you open this and want to make something today?"
Common triggers that reveal the real brief:
- "Saw a really cool cinematic shot" → cinematic photography direction
- "Playing D&D this weekend" → TTRPG character/scene direction
- "Need a new PFP" → avatar/portrait direction
- "Reading a book and can imagine the cover" → book cover direction

### 2.6 The Menu Approach — Show Directions, Don't Ask Open Questions

For someone with no idea at all, presenting a menu beats asking open questions.

```
"Here are 4 directions we could go. Pick the one that pulls you most,
or say which parts of multiple ones feel right:"

A) Moody atmospheric landscape — cinematic wide shot, mist, dramatic light
B) Character portrait — stylized illustration, detailed face, expressive
C) Abstract / pattern — geometric or organic forms, vibrant palette
D) Fantasy / world-building scene — concept-art style, rich detail, epic scale
```

This leverages the design principle: people can recognize what they want far more easily
than they can generate it from scratch.

### 2.7 Iterative Narrowing Loop

```
Start broad (genre/mood) → narrow (style/medium) → specify (subject/palette) → confirm (aspect ratio/use)
```

Never try to nail all variables at once. First generation = reference point, not goal.
Encourage "what's right about this / what's wrong about this" critique over "this sucks."

---

## 3. Hobbyist AI-Image Use Cases — A Concrete Menu

The assistant can offer this as a starting-point picker when the person has no direction.

### 3.1 Personal / Identity

| Use case | Typical specs | Style defaults |
|----------|---------------|----------------|
| **Profile picture / avatar** | 1:1, ~512–1024px | Character portrait, stylized, clean background |
| **Discord/forum banner** | 16:5 or wide | Landscape, panoramic, atmospheric |
| **Personal wallpaper** (phone) | 9:16 | Vertical landscape, portrait, abstract |
| **Personal wallpaper** (desktop) | 16:9 | Wide scene, minimal clutter in center |

### 3.2 Creative / Narrative

| Use case | Typical specs | Style defaults |
|----------|---------------|----------------|
| **TTRPG / D&D character portrait** | 2:3 or 1:1 | Character illustration, detailed costume, expressive |
| **TTRPG scene / encounter** | 16:9 or 3:2 | Concept art, environmental storytelling, cinematic |
| **Fan art** | varies | Match source material style |
| **Original character (OC)** | 2:3 | Character sheet or portrait, distinctive design |
| **Book/story cover** | 2:3 | Painterly or photomanip, atmospheric, text headroom |
| **Album cover** | 1:1 | Bold, iconic, often abstract or symbolic |

### 3.3 Print / Commercial-Adjacent

| Use case | Typical specs | Style defaults |
|----------|---------------|----------------|
| **Art print / poster** | A4/A3 ratio (1:1.4) | High detail, statement image, limited palette |
| **Sticker sheet** | 1:1 or 4:3 | Flat illustration, bold outlines, white background or transparent |
| **T-shirt graphic** | Depends on print area | Graphic, bold, works on fabric — avoid photorealism |
| **Product mockup / concept** | 1:1 or 4:3 | Clean studio-style, product hero shot |

### 3.4 Social / Content

| Use case | Typical specs | Style defaults |
|----------|---------------|----------------|
| **Instagram post** | 1:1 or 4:5 | Striking, cohesive palette, readable at small size |
| **Twitter/X header** | 3:1 | Atmospheric wide, minimal text-area conflict |
| **Blog / article header** | 2:1 or 16:9 | Evocative, not too literal, readable behind text |
| **YouTube thumbnail** | 16:9 | High contrast, bold, readable at small size |

### 3.5 Explorative / Artistic

| Use case | Notes |
|----------|-------|
| **Concept exploration** | World-building, character ideas, "what would X look like" |
| **Style experiments** | Testing art movements, artist styles, technique mashups |
| **Abstract / generative** | Pattern, texture, color-study purposes |
| **Surrealist / dreamlike** | Narrative-free, emotionally driven |

---

## 4. Visual Style Taxonomy — Pick-From Menus for Non-Experts

Organized as nested menus the assistant can present. Depth increases as the person narrows.

### 4.1 Top-Level Medium Axis (First Decision)

```
PHOTOGRAPHIC  →  "looks like a real photograph"
PAINTERLY     →  "has visible medium, texture, brushstrokes"
ILLUSTRATIVE  →  "drawn/designed, clean lines or hand-made feel"
RENDERED / 3D →  "CGI, game-engine, or hyper-real 3D"
GRAPHIC       →  "flat, vector, icon-like, design-forward"
```

### 4.2 Style by Medium

**PHOTOGRAPHIC styles:**
- Cinematic film (movie-still feel, widescreen, shallow DOF)
- Editorial/fashion photography (clean, directional light, model-forward)
- Documentary / street photography (candid, natural light, gritty)
- Product photography (studio, clean BG, hero object)
- Nature / landscape photography (wide, environmental, golden hour)
- Portrait photography (face-forward, soft bokeh, intimate)
- Architectural photography (geometric, lines, urban or interior)
- Infrared photography (dreamlike, white foliage, dark sky)
- Film grain / lomography (imperfect, warm, analog character)

**PAINTERLY styles:**
- Oil painting (rich texture, classical or contemporary)
- Watercolor (translucent washes, loose edges, organic feel)
- Gouache (flat, opaque, poster-like, matte)
- Ink wash / sumi-e (gestural, minimal, Japanese-influenced)
- Acrylic / mixed media (bold, expressive, graphic)
- Impressionist (loose brushwork, light as subject, Monet/Renoir feel)
- Expressionist (distorted, emotional, Munch/Schiele feel)
- Plein air (bright, naturalistic, painted-from-life feel)

**ILLUSTRATIVE styles:**
- Concept art (detailed, professional, game/film industry aesthetic)
- Character illustration (design-forward, expressive, often anime-influenced)
- Storybook illustration (warm, narrative, fairy-tale quality)
- Comics / graphic novel (strong inks, flat or halftone color, panels)
- Manga / anime (Japanese aesthetics, stylized anatomy, speed lines)
- Retro poster / propaganda (flat, bold, geometric, vintage typography)
- Art Nouveau (organic curves, botanical motifs, Mucha-esque)
- Art Deco (geometric, metallic, 1920s–30s glamour)
- Folk art / naive (simplified forms, flat perspective, handmade)
- Ukiyo-e / woodblock (flat color planes, outline, Japanese aesthetic)
- Flat / vector design (clean, geometric, icon-style)
- Isometric illustration (3D grid, technical-cute, game-UI feel)

**RENDERED / 3D styles:**
- Hyperrealistic CGI (product/arch viz quality, pristine)
- Stylized 3D / Pixar-esque (character-forward, smooth surfaces, expressive)
- Dark realism / ZBrush look (creature design, detailed texture, menacing)
- Voxel art (blocky, Minecraft-adjacent, cute)
- Low-poly (geometric, minimalist 3D, clean edges)
- Game concept art (world-building, environment design, technical beauty)

**GRAPHIC / DESIGN styles:**
- Minimalism (lots of negative space, 1–2 colors, geometric)
- Memphis design (80s, bold geometry, playful colors, pattern)
- Swiss / International style (grid-based, sans-serif, rational)
- Maximalism (dense, layered, every inch fills)
- Brutalism (raw concrete aesthetic, heavy type, confrontational)

### 4.3 Genre / World Taxonomy

```
FANTASY          →  epic, magical, mythological
SCI-FI           →  futuristic, technological, space
CYBERPUNK        →  neon-lit urban decay, tech-noir
STEAMPUNK        →  Victorian machinery, brass/copper, coal-punk
SOLARPUNK        →  utopian nature+tech, bright, hopeful
HORROR           →  dread, creature, gothic, dark surrealism
HISTORICAL       →  period-accurate world, specific era
CONTEMPORARY     →  modern world, realistic
SURREALIST       →  dreamlike, illogical, subconscious imagery
COTTAGECORE      →  cozy, rural, wholesome, pastoral
DARK ACADEMIA    →  books, candles, autumn, scholarly aesthetic
VAPORWAVE        →  80s/90s nostalgia, pink/purple/teal, grid
SYNTHWAVE        →  neon, speed, retro-future, Outrun aesthetic
LO-FI            →  chill, soft, animated-room aesthetic
```

### 4.4 Lighting Vocabulary

**Natural light:**
- Golden hour (just after sunrise / before sunset — warm, long shadows, romantic)
- Blue hour (just before sunrise / after sunset — cool, moody, cinematic)
- Overcast / diffused (soft, even, no harsh shadows — flattering for portraits)
- Harsh midday sun (strong shadows, bleached highlights, dramatic)
- Dappled light (through leaves, playful, organic)
- Backlit / silhouette (subject dark against bright background, dramatic)

**Studio / artificial:**
- High key (bright, even, minimal shadow — clean, commercial feel)
- Low key (dark BG, pool of light on subject — moody, dramatic)
- Rembrandt lighting (triangle of light on cheek — portrait classic)
- Rim / edge lighting (glowing outline, separates subject from dark BG)
- Neon lighting (colored glow from neon signs — cyberpunk, urban)
- Candlelight / firelight (warm orange, flickering, intimate)
- Bioluminescent (glowing organic forms — fantasy/sci-fi)

**Cinematic / stylized:**
- Volumetric / god rays (visible light beams through atmosphere)
- Chiaroscuro (extreme light/dark contrast, Caravaggio-style)
- Cinematic lighting (movie-quality directional, motivated by source)
- Noir (high contrast, venetian-blind shadows, black and white palette)
- Ethereal / soft glow (diffused, heavenly, over-exposed edges)

### 4.5 Color Palette Language

**Temperature:**
- Warm (ambers, golds, oranges, reds — inviting, energetic, nostalgic)
- Cool (blues, silvers, teals — calm, technological, melancholic)
- Neutral (grays, taupes, whites — sophisticated, minimal)

**Key palettes:**
- Earth tones (terracotta, moss, sand, bark — organic, grounded)
- Pastels (soft pinks, lilacs, mints — delicate, dreamy, kawaii)
- Jewel tones (deep emerald, sapphire, ruby — rich, luxurious)
- Monochromatic (single hue, value range — elegant, unified)
- Desaturated / muted (dusty, filmic, restrained)
- High saturation / vibrant (pop, energetic, graphic)
- Neon (fluorescent, blacklight, cyberpunk)
- Black and white (timeless, stark, emphasizes form)

**Named color moods:**
- Forest palette: deep greens, dark earth, soft mist
- Nordic palette: soft grays, ice blue, birch white
- Desert palette: burnt orange, dune tan, bleached turquoise
- Oceanic palette: deep navy, seafoam, sand, coral
- Twilight palette: dusky violet, rose gold, deep indigo

### 4.6 Aspect Ratio Quick Reference

| Ratio | Shape | Use for |
|-------|-------|---------|
| 1:1 | Square | Avatar, Instagram, album cover |
| 4:5 | Tall rect | Instagram portrait, phone near-square |
| 2:3 | Portrait | Character art, book cover, poster |
| 9:16 | Tall | Phone wallpaper, Stories/Reels |
| 3:2 | Landscape | Print photo, cinematic still |
| 16:9 | Wide | Desktop wallpaper, YouTube, cinematic |
| 3:1 | Ultra-wide | Twitter header, panoramic banner |
| 1:1.4 | A-series | Printable art (A4/A3) |

---

## 5. Translating Vague Brief → 2–3 Concrete Directions

The workflow: gather signal → build profile → generate 2–3 directions → let the person choose → generate → iterate.

### 5.1 Signal-to-Profile Mapping

After elicitation questions (§ 2), map answers to the brief pillars:

```
SIGNAL                              → BRIEF ELEMENT
-----------------------------------------------------------------
Emotion words ("dark", "nostalgic") → Mood + Palette
This-or-That answers                → Medium axis + Composition
Genre / world preference            → Genre category (§ 4.3)
Use destination                     → Aspect ratio + density
Reference images                    → Extract composition, light, medium
```

### 5.2 Direction Formula

Each direction is a 3-line brief:
```
Direction [A/B/C]: [One-sentence flavour]
  Medium/Style: [style anchor — most important variable]
  Mood + Light: [emotional temperature + key lighting]
  Subject:      [what is actually in the image]
```

**Example — Input: "I want something for my desktop wallpaper. Dark and cool-looking. I like space stuff but also old architecture."**

```
Direction A — Abandoned cathedral in space
  Style:   Hyperrealistic CGI / concept art, cinematic
  Mood:    Awe-inspiring, desolate, cold
  Subject: Gothic stone cathedral floating in nebula, distant stars, volumetric rays
  Palette: Deep midnight blue, pale gold from interior light, black void

Direction B — Astronomer's study at night
  Style:   Dark oil painting, Vermeer-influenced
  Mood:    Intimate, scholarly, warm-cold contrast
  Subject: Stone-vaulted room, telescope aimed at open window, star charts scattered
  Palette: Candlelight gold vs cold moonlight blue, deep shadow

Direction C — Alien ruins on an ice moon
  Style:   Cinematic science fiction photography (Arrival / Dune aesthetic)
  Mood:    Mysterious, vast, alien
  Subject: Ancient carved stone structures half-buried in ice, aurora overhead
  Palette: Desaturated teal, ice white, faint purple aurora
```

### 5.3 From Direction to Flux/Ideogram Prompt Structure

Once direction is chosen, build the prompt in this order (front-load most impactful):

```
[STYLE/MEDIUM], [SUBJECT + KEY DETAILS], [SETTING/ENVIRONMENT], 
[LIGHTING], [ATMOSPHERE/MOOD], [COLOUR PALETTE], [TECHNICAL: aspect ratio, quality]
```

Following the adeptdept.com guide, the art style prefix placed first has maximum influence on AI interpretation.

**Concrete structure:**
```
{style prefix} of {subject}, {setting}, {lighting}, {mood adjectives}, 
{palette cues}, {composition}, {quality terms}
```

**Example from Direction A above:**
```
hyperrealistic concept art, abandoned gothic cathedral floating in deep space, 
crumbling stone arches and flying buttresses, Earth visible through rose window, 
volumetric light beams from interior, stars and nebula surrounding structure, 
awe-inspiring and desolate, midnight blue and pale gold, 
cinematic wide shot, 8k, detailed, dramatic
```

### 5.4 Iteration Protocol

After first generation:
1. "What's right about this?" → lock those elements
2. "What's wrong about this?" → target elements to change
3. Change ONE variable per iteration (don't rewrite the whole prompt)
4. Use the existing output as a reference for the next generation

Priority order for iteration fixes:
- Wrong medium/style → change style prefix
- Wrong mood → change lighting + palette
- Wrong composition → add framing/camera terms
- Subject off → be more specific, add negative prompts

### 5.5 The "Three Directions Then Choose" Decision Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: SIGNAL GATHERING                                       │
│  Ask: use case → emotion words → this-or-that → any references  │
│  (3-5 minutes, 4-6 exchanges max)                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: DIRECTION SYNTHESIS                                    │
│  Map signals to brief pillars                                   │
│  Generate 2-3 divergent directions (style + mood + subject)     │
│  Present as concrete options, not open questions                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: DIRECTION SELECTION                                    │
│  Person picks one (or hybrid of two)                            │
│  Lock the brief: style, mood, subject, palette, aspect ratio    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: PROMPT CONSTRUCTION                                    │
│  Build full prompt from locked brief                            │
│  Apply structure: style → subject → setting → light → mood      │
│  Add aspect ratio / technical specs                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5: GENERATE + ITERATE                                     │
│  First generation = reference point                             │
│  Critique: what's right (lock) / what's wrong (change)          │
│  Single-variable iteration each round                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Quick-Reference: High-Value Artist Style Names for Non-Experts

These artist/style references punch above their weight as prompt anchors — a single name carries
medium + palette + mood + composition conventions.

| Reference | What it signals |
|-----------|-----------------|
| **Greg Rutkowski** | Fantasy concept art, dramatic light, painterly, heroic |
| **Simon Stålenhag** | Sci-fi melancholy, rural retro-futurism, oil paint feel |
| **Moebius (Giraud)** | French comic, clean line, alien landscapes, pastel |
| **H.R. Giger** | Biomechanical horror, surreal, dark, organic-tech |
| **Alphonse Mucha** | Art Nouveau, decorative, portrait, botanical, gold |
| **Studio Ghibli** | Soft anime, warm light, pastoral, emotional |
| **Wlop** | Digital painting, glowing skin, fantasy portrait |
| **Artgerm** | Clean character illustration, fashion-forward |
| **Edward Hopper** | Quiet realism, theatrical light, urban solitude |
| **Zdzisław Beksiński** | Post-apocalyptic dreamscape, dark, surreal, painterly |
| **Norman Rockwell** | Warm Americana illustration, narrative, mid-century |
| **Yoji Shinkawa** | Ink + gouache, Metal Gear concept art, elongated figures |

---

## 7. The "No-Idea Rescue" Quick Scripts

For the persona to use verbatim when the person is stuck.

### Script A: Pure blank slate
```
"Let's start somewhere concrete. Three quick questions:
 1. Where will this live? (phone wallpaper / desktop / print / profile pic / something else)
 2. Pick ONE: do you want it to feel more warm and cozy OR cool and dramatic?
 3. Name one thing — an object, a place, a creature, an emotion — that comes to mind right now."

→ These three answers are enough to propose two directions.
```

### Script B: Reference-first
```
"Before I ask anything — share one image that excites you visually right now.
 Could be a movie still, a photo, a painting, anything.
 I'll work backwards from what you show me."
```

### Script C: Genre picker
```
"Pick the world that calls to you most:
 A) Fantasy / magic / otherworldly
 B) Science fiction / space / future
 C) Realistic / photographic / cinematic
 D) Cozy / nostalgic / warm and human
 E) Dark / atmospheric / horror-adjacent
 F) Graphic / designed / bold and clean"
```

### Script D: When they say "I don't know, you choose"
```
→ Generate three directions from the most underspecified brief you have.
→ Make them DIVERGENT — if one is dark+painterly, make another bright+graphic, third atmospheric+photographic.
→ Never ask "which do you prefer" between two things you haven't shown them.
```

---

## 8. Sources

1. **Asana — Creative Briefs: What To Include**  
   https://asana.com/resources/how-write-creative-brief-examples-template

2. **Adobe Design — Creative Direction: The Secret to Great AI Images**  
   https://adobe.design/ideas/creative-direction-the-secret-to-great-ai-images

3. **Zapier — 70+ AI Art Styles to Use in Your Prompts**  
   https://zapier.com/blog/ai-art-styles/

4. **Adept Dept — AI Image Prompting 101: The Ultimate Guide**  
   https://adeptdept.com/blog/ai-image-prompting-101-complete-guide/

5. **Let's Enhance — How to Write AI Image Prompts Like a Pro**  
   https://letsenhance.io/blog/article/ai-text-prompt-guide/

6. **AI Magicx — Mastering AI Image Generation: Visual Guide to Styles**  
   https://www.aimagicx.com/blog/ai-image-generation-styles-mastering-aesthetics

7. **Travis Nicholson on Medium — 150 AI Image Prompt Styles (Artists, Lighting, Aesthetics)**  
   https://travisnicholson.medium.com/150-ai-image-prompt-styles-artists-lighting-aesthetics-ebecab53e01f

8. **QC Design School — How to Help Clients Identify Their Preferred Design Style**  
   https://www.qcdesignschool.com/blog/2021/04/how-to-help-clients-identify-their-preferred-design-style

9. **NN/Group — Mood Boards in UX: How and Why to Use Them**  
   https://www.nngroup.com/articles/mood-boards/

10. **Printful — How to Write Prompts for AI Art**  
    https://www.printful.com/blog/prompts-for-ai-art

11. **FigJam / Figma — How to Write a Creative Brief**  
    https://www.figma.com/resource-library/how-to-write-a-creative-brief/

12. **Digitbin — Best Art Styles for AI Image Prompts**  
    https://www.digitbin.com/art-styles-ai-image-prompts/
