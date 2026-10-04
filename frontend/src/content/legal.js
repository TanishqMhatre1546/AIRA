export const legalContent = {
  lastUpdated: "4 October 2026",
  privacy: {
    heading: "Privacy",
    statements: [
      "AIRA does not store your messages. There is no account and no database of messages.",
      "Messages that match an emergency, self-harm, refusal or child rule are handled on the AIRA server and are not sent to Google.",
      "Other messages are sent to Google's Gemini API: first to turn the message into a search vector and, when the model is enabled, to write the summary.",
      "Google handles those messages under its terms.",
      "AIRA server logs do not contain message text.",
      "The site sets no cookies and uses no analytics or advertising trackers.",
      "The hosting provider, Render, may record technical request data such as IP addresses in its own logs.",
      "The printed summary is created in your browser and is not sent anywhere.",
    ],
    googleTermsText: "Google Gemini API terms",
    googleTermsUrl: "https://ai.google.dev/gemini-api/terms",
  },
  terms: {
    heading: "Terms of use",
    statements: [
      "AIRA gives general information from published guidelines. It is not medical advice, not a diagnosis, and not a substitute for a doctor.",
      "In an emergency, call 112 or go to the nearest hospital. Do not wait for AIRA.",
      "AIRA is a prototype. Its clinical content has not been reviewed by a doctor unless the review status above says so.",
      "Guideline documents belong to their publishers. AIRA links to them on the Sources page.",
      "The service may be slow, unavailable or change without notice. Free hosting can pause it when it is idle, and the first request after a pause can take about a minute.",
      "You decide what to do with the information. The people who built AIRA are not responsible for decisions made using it, to the extent the law allows.",
    ],
    sourcesLinkLabel: "Guideline documents used by AIRA",
  },
};
