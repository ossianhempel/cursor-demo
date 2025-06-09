# Cursor Demo

## Vad är Cursor?
- AI-baserad IDE som har byggts utifrån VSCode, ser mer eller mindre likadan ut förutom ytterligare features
- Om du har är van vid Copilot i VSCode är Cursor en liknande upplevelse (fast bättre)
- LLM:en kan läsa din kodbas och använda det som kontext för att göra ändringar
- Grunden till "vibe coding"

## Varför Cursor? 
- Produktivitet - AI kan skriva boilerplate och repetetiv kod åt dig -> lägg mer tid på det som skapar värde (t.ex. användning, arkitektur, flöden, beslut, etc.)
  - För Data Engineering, tänk API-connectors, schemas, tester, SQL
- Lägre alternativkostnad -> du kan testa saker mycket snabbare än innan -> utforska fler potentiella lösningar/frameworks/metoder, prova på saker som innan var för tidskrävande för att vara värda att sätta sig in i

## Säkerhet
- Aktivera "Privacy Mode" i Cursor Settings så lagras aldrig kod/prompts hos Cursor/andra tredjeparter
- Kodbasen "indexeras" för att kunna läsas effektivt av LLM-modellerna
  - Små bitar av kodbasen laddas upp i "chunks" där den blir till embeddings (numerisk representation ej textformat längre), endast embeddings sparas 

## Features att visa:
- Tab
- Agent mode
- Multi-file context
- Inline editing
- Chat 
- Rules

## Demo
- Se om Cursor kan lösa todo-listan utan att vi skriver någon kod (bara prompta)

## Lärdomar
- Överberoende leder till "Brain drain" 
  - Glömmer bort grundläggande syntax (hur var det man skrev en for-loop nu igen?)
  - Man förstår inte sin "egna" kod
  - Överlåter beslutsfattande till AI - vilken kan funka - men inte säkert den har tillräckligt kontext för att ta rätt beslut i din situation
- "Test-driven generation" kan vara effektivt -> 
  - Skriv eller generera tester för funktionaliteten du vill bygga, be AI köra testerna efter varje ändring så du kan ha koll på att allt fungerar 
- Väldig effektivt för demos/MVPs
  - Demonstrera funktionalitet och liknande visuellt/interaktivt INNAN börjar bygga komplexa pipelins/rapporter etc., t.ex. genom Streamlit
- Inkludera extern API-dokumentation i promptet/lägg i en markdownfil i repot och låt Cursor referera den när den bygger