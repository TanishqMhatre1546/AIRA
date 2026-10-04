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

export const sampleEpistaxisResult = {
  response_type: "ANSWER",
  triage_level: "SELF_CARE",
  headline: "Guideline Self-Care Advice",
  message: "Most nosebleeds can be managed at home with simple first aid.",
  sections: {
    guidelines_say: [
      {
        text: "Sit upright and lean slightly forward, do not tilt the head back, as this causes blood to flow down the throat and may cause vomiting or choking.",
        citation_ids: [1],
      },
    ],
    do_now: [
      {
        text: "Pinch the soft part of the nose (just below the bony bridge) firmly with your thumb and index finger, this is called Trotter's position.",
        citation_ids: [1],
      },
    ],
    watch_for: [
      {
        text: "Nosebleed that does not stop after 20 minutes of correct first aid.",
        citation_ids: [1],
      },
    ],
  },
  citations: [
    {
      id: 1,
      title: "Standard Treatment Workflow (STW) for the Management of Epistaxis",
      source_title: "Standard Treatment Workflow (STW) for the Management of Epistaxis",
      publisher: "Department of Health Research, Ministry of Health and Family Welfare, Government of India",
      source_publisher:
        "Department of Health Research, Ministry of Health and Family Welfare, Government of India",
      year: "October 2019",
      source_year: "October 2019",
      url: "https://stw.icmr.org.in",
      source_url: "https://stw.icmr.org.in",
      page: 1,
    },
  ],
  mode: "extractive",
  disclaimer: "General information from published guidelines. Not a diagnosis.",
};
