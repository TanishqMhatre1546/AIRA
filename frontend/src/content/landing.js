export const landingContent = {
  hero: {
    title: "Check what Indian health guidelines say about your symptoms",
    paragraph:
      "AIRA matches the symptoms you describe against a written rule table and shows how urgent they are. Each answer lists the guideline document and page it comes from. AIRA does not diagnose illness and does not give medicine doses.",
    checkSymptomsButton: "Check symptoms",
    howItWorksLink: "How it works",
    emergencyNotice: "If this is an emergency, call 112 now.",
  },
  whatYouGet: {
    heading: "What you get",
    items: [
      {
        lead: "An urgency level.",
        text: "Emergency, see a doctor soon, or can usually be managed at home.",
      },
      {
        lead: "What the guidelines say.",
        text: "A short summary written only from guideline passages, with the document and page.",
      },
      {
        lead: "Signs to watch for.",
        text: "The warning signs the guidelines list for your condition.",
      },
    ],
  },
  whoFor: {
    heading: "Who it is for",
    text: "Adults in India with everyday symptoms and the people who look after them, and community health workers who want to look up a protocol quickly.",
  },
  coverage: {
    heading: "Conditions covered",
    loadingText: "Loading the list",
    fallbackText: "The full list is on the Sources page.",
    sourcesLinkText: "Sources page",
  },
  howItWorks: {
    heading: "How it works",
    steps: [
      "Fixed rules check your message first. Emergency signs, thoughts of self-harm, requests for a diagnosis or a dose, and messages about children are handled by written rules before any AI is used. For an emergency, AIRA shows a fixed message and helplines and writes nothing else.",
      "A rule table sets the urgency. The level comes from a table that cites its guideline source. The AI cannot change it.",
      "A short summary is written from guideline passages only. Every statement points to a source. If the text cannot be checked against the passages, AIRA shows the passages themselves.",
    ],
    reviewPending: "Clinical review: pending.",
    reviewDonePrefix: "Clinically reviewed: yes, by ",
  },
  limits: {
    heading: "What AIRA does not do",
    items: [
      "It does not diagnose.",
      "It does not give medicine doses or advice on mixing medicines.",
      "It is for adults only (messages about babies and children get a notice to see a doctor).",
      "It is in English only.",
      "It covers only the listed conditions.",
      "It is not a replacement for a doctor or emergency services.",
    ],
  },
};
