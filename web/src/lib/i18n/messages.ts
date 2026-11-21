/**
 * Interface strings (W07). English is the source. Sinhala and Tamil are machine drafts
 * (`status: "draft-machine"`): D-012 and W07 say no machine translation ships without human
 * review, so they appear only when a visitor opts in, under a banner saying so. When a
 * reviewer approves a locale, record them in `docs/translation/README.md` and set its status.
 */

export type Locale = "en" | "si" | "ta";

export const LOCALES: { id: Locale; label: string; status: "source" | "draft-machine" | "reviewed" }[] = [
  { id: "en", label: "English", status: "source" },
  { id: "si", label: "සිංහල", status: "draft-machine" },
  { id: "ta", label: "தமிழ்", status: "draft-machine" },
];

export const EN = {
  "nav.atlas": "Atlas",
  "nav.tables": "Tables",
  "nav.indicators": "Indicators",
  "nav.elections": "Elections",
  "nav.areas": "Areas",
  "nav.data": "Data",
  "nav.methods": "Methods",
  "nav.about": "About",
  "nav.resolution": "Finest view",
  "lens.geography": "Geography",
  "lens.profile": "Profile",
  "lens.change": "Change",
  "lens.elections": "Elections",
  "lens.landscape": "Landscape",
  "picker.indicator": "Indicator",
  "picker.layer": "Layer",
  "panel.compared": "Compared to where?",
  "panel.neighbours": "Neighbours",
  "panel.similar": "Similar places",
  "panel.similarLandscapes": "Similar landscapes",
  "panel.country": "Sri Lanka",
  "panel.whatsHere": "What is here",
  "panel.sources": "Sources for these numbers",
  "panel.keyFacts": "Key facts",
  "language.label": "Interface language",
  "language.draft": "Machine draft translation, not yet reviewed. Place names come from official sources.",
} as const;

export type MessageKey = keyof typeof EN;

const SI: Partial<Record<MessageKey, string>> = {
  "nav.atlas": "සිතියම",
  "nav.tables": "වගු",
  "nav.indicators": "දර්ශක",
  "nav.elections": "මැතිවරණ",
  "nav.areas": "ප්‍රදේශ",
  "nav.data": "දත්ත",
  "nav.methods": "ක්‍රමවේද",
  "nav.about": "අප ගැන",
  "nav.resolution": "සියුම්ම දසුන",
  "lens.geography": "භූගෝලය",
  "lens.profile": "පැතිකඩ",
  "lens.change": "වෙනස",
  "lens.elections": "මැතිවරණ",
  "lens.landscape": "භූ දර්ශනය",
  "picker.indicator": "දර්ශකය",
  "picker.layer": "ස්තරය",
  "panel.compared": "කොහේට සාපේක්ෂව?",
  "panel.neighbours": "අසල්වාසී ප්‍රදේශ",
  "panel.similar": "සමාන ස්ථාන",
  "panel.similarLandscapes": "සමාන භූ දර්ශන",
  "panel.country": "ශ්‍රී ලංකාව",
  "panel.whatsHere": "මෙහි ඇත්තේ කුමක්ද",
  "panel.sources": "මෙම සංඛ්‍යාවල මූලාශ්‍ර",
  "panel.keyFacts": "ප්‍රධාන කරුණු",
  "language.label": "අතුරුමුහුණත් භාෂාව",
  "language.draft":
    "යන්ත්‍රයෙන් සැකසූ පරිවර්තන කෙටුම්පතකි; තවමත් සමාලෝචනය කර නැත. ස්ථාන නාම නිල මූලාශ්‍රවලින් ය.",
};

const TA: Partial<Record<MessageKey, string>> = {
  "nav.atlas": "வரைபடம்",
  "nav.tables": "அட்டவணைகள்",
  "nav.indicators": "குறிகாட்டிகள்",
  "nav.elections": "தேர்தல்கள்",
  "nav.areas": "பகுதிகள்",
  "nav.data": "தரவு",
  "nav.methods": "முறைகள்",
  "nav.about": "எங்களைப் பற்றி",
  "nav.resolution": "நுண்ணிய பார்வை",
  "lens.geography": "புவியியல்",
  "lens.profile": "விவரம்",
  "lens.change": "மாற்றம்",
  "lens.elections": "தேர்தல்கள்",
  "lens.landscape": "நிலப்பரப்பு",
  "picker.indicator": "குறிகாட்டி",
  "picker.layer": "அடுக்கு",
  "panel.compared": "எதனுடன் ஒப்பிடும்போது?",
  "panel.neighbours": "அண்டைப் பகுதிகள்",
  "panel.similar": "ஒத்த இடங்கள்",
  "panel.similarLandscapes": "ஒத்த நிலப்பரப்புகள்",
  "panel.country": "இலங்கை",
  "panel.whatsHere": "இங்கே என்ன உள்ளது",
  "panel.sources": "இந்த எண்களின் மூலங்கள்",
  "panel.keyFacts": "முக்கிய உண்மைகள்",
  "language.label": "இடைமுக மொழி",
  "language.draft":
    "இயந்திர மொழிபெயர்ப்பு வரைவு; இன்னும் சரிபார்க்கப்படவில்லை. இடப் பெயர்கள் அதிகாரப்பூர்வ மூலங்களிலிருந்து.",
};

export const MESSAGES: Record<Locale, Partial<Record<MessageKey, string>>> = { en: EN, si: SI, ta: TA };

/** The string for a key in a locale, falling back to English for a whole label. */
export function translate(locale: Locale, key: MessageKey): string {
  return MESSAGES[locale][key] ?? EN[key];
}
